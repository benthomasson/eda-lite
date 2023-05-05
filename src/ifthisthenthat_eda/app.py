# FASTAPI application

import asyncio
import base64
import json
import logging
import shutil
import uuid
import starlette.websockets

import yaml
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ssh_agent = shutil.which("ssh-agent")
ansible_rulebook = shutil.which("ansible-rulebook")


app = FastAPI(
    title="If This Then That EDA",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Action(BaseModel):

    module_name: str
    module_args: dict


class Condition(BaseModel):

    condition: str


class Rule(BaseModel):

    name: str
    condition: Condition
    action: Action


class Source(BaseModel):

    source_type: str
    source_args: dict


class Ruleset(BaseModel):

    name: str
    rules: list[Rule]
    sources: list[Source]


class Rulebook(BaseModel):

    rulesets: list[Ruleset]


ruleset = Ruleset(name="ifthisthenthat", rules=[], sources=[])
rulebook = Rulebook(rulesets=[ruleset])
extravars = {}
rulebook_task = None
log_lines = []


# Get the list of modules
@app.get("/modules")
async def get_modules():
    return {"modules": ["community.general.slack"]}


# Get the list of sources
@app.get("/sources")
async def get_sources():
    return {
        "sources": [
            "ansible.eda.range",
        ]
    }


# Get the list of module conditions
@app.get("/conditions")
async def get_conditions():
    return {"conditions": ["event.i == 1", "event.i == 2"]}


# Add a source
@app.post("/sources")
async def add_source(source: Source):
    ruleset.sources.append(source)
    await run_rulebook()
    return {"source": source}


# Add a rule
@app.post("/rules")
async def add_rule(rule: Rule):
    ruleset.rules.append(rule)
    await run_rulebook()
    return {"rule": rule}

# Get log lines
@app.get("/logs")
async def get_logs():
    return {"logs": log_lines}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print("websocket:", data, type(data))
            message = json.loads(data)
            if message["type"] == "Worker":
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ExtraVars",
                            "data": base64.b64encode(
                                yaml.safe_dump(extravars).encode("utf-8")
                            ).decode("utf-8"),
                        }
                    )
                )
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "Rulebook",
                            "data": base64.b64encode(
                                yaml.safe_dump(get_rulebook()).encode("utf-8")
                            ).decode("utf-8"),
                        }
                    )
                )
                await websocket.send_text(json.dumps({"type": "EndOfResponse"}))
    except starlette.websockets.WebSocketDisconnect as e:
        logger.error("websocket_endpoint %s", e)
        print("websocket_endpoint %s", e)


def get_rulebook():
    data = []
    for ruleset in rulebook.rulesets:
        rules = []
        for rule in ruleset.rules:
            rules.append(
                {
                    "name": rule.name,
                    "condition": rule.condition.condition,
                    "action": {
                        "run_module": {
                            "module_name": rule.action.module_name,
                            "module_args": rule.action.module_args,
                        }
                    },
                }
            )
        sources = []
        for source in ruleset.sources:
            sources.append(
                {
                    source.source_type: source.source_args,
                }
            )
            data.append(
                {
                    "name": ruleset.name,
                    "rules": rules,
                    "sources": sources,
                    "hosts": "all",
                    "gather_facts": False,
                }
            )



    print(yaml.safe_dump(data, default_flow_style=False))
    return data


# Run the rulebook
async def run_rulebook():

    global rulebook_task

    activation_id = str(uuid.uuid4())

    # for local development this is better
    cmd_args = [
        ansible_rulebook,
        "--worker",
        "--websocket-address",
        "ws://localhost:8000/ws",
        "--id",
        str(activation_id),
        "-vvv",
    ]
    logger.debug(ansible_rulebook)
    print(ansible_rulebook)
    logger.debug(cmd_args)
    print(cmd_args)

    proc = await asyncio.create_subprocess_exec(
        ssh_agent,
        *cmd_args,
        cwd=".",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    rulebook_task = asyncio.create_task(
        read_output(proc, activation_id),
        name=f"read_output {proc.pid}",
    )
    print(f"rulebook_task: {rulebook_task}")


async def read_output(proc, activation_instance_id):

    try:
        logger.debug(
            "read_output %s %s",
            proc.pid,
            activation_instance_id,
        )
        while True:
            buff = await proc.stdout.readline()
            if not buff:
                break
            buff = buff.decode()
            log_lines.append(buff)
            logger.debug("read_output %s", buff)
            print("read_output %s", buff)

    except Exception as e:
        logger.error("read_output %s", e)
        print("read_output %s", e)
    finally:
        logger.info("read_output complete")
        print("read_output complete")
