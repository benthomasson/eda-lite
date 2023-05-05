# FASTAPI application

import asyncio
import base64
import json
import logging
import os
import shutil
import uuid
from contextlib import asynccontextmanager

import starlette.websockets
import yaml
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ssh_agent = shutil.which("ssh-agent")
ansible_rulebook = shutil.which("ansible-rulebook")

# types


class Action(BaseModel):

    name: str
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


class Inventory(BaseModel):

    inventory: str
# globals

enable = False
ruleset = Ruleset(name="ifthisthenthat", rules=[], sources=[])
rulebook = Rulebook(rulesets=[ruleset])
extravars = {}
inventory = Inventory(inventory='')
rulebook_task = None
log_lines = []


def build_rulebook():
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
                            "name": rule.action.name,
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

def load_extravars():
    global extravars

    if os.path.exists("extravars.yml"):
        with open("extravars.yml", "r") as f:
            extravars = yaml.safe_load(f)

            print(extravars)

def load_inventory():
    global inventory

    if os.path.exists("inventory.yml"):
        with open("inventory.yml", "r") as f:
            inventory = Inventory(inventory=f.read())

            print(inventory)

def load_rulebook():
    global rulebook
    global rulesets
    sources = []
    rules = []

    if os.path.exists("rulebook.yml"):
        with open("rulebook.yml", "r") as f:
            rulebook_data = yaml.safe_load(f)
            print(yaml.safe_dump(rulebook_data, default_flow_style=False))
            if not rulebook_data:
                return
            ruleset_data = rulebook_data[0]
            for source in ruleset_data["sources"]:
                source_type = list(source.keys())[0]
                sources.append(Source(source_type=source_type,
                                      source_args=source[source_type]))
            for rule in ruleset_data["rules"]:
                rules.append(Rule(name=rule["name"],
                                  condition=Condition(condition=rule["condition"]),
                                  action=Action(name=rule["action"]["run_module"]["name"],
                                                module_args=rule["action"]["run_module"]["module_args"])))

        ruleset = Ruleset(name="ifthisthenthat", rules=rules, sources=sources)
        rulebook = Rulebook(rulesets=[ruleset])

        print(rulebook)


def save_rulebook():
    global rulebook
    with open("rulebook.yml", "w") as f:
        yaml.safe_dump(build_rulebook(), f, default_flow_style=False)


# API


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_extravars()
    load_inventory()
    load_rulebook()
    yield
    save_rulebook()


app = FastAPI(
    title="EDA: If This Then That",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Get the list of available modules
@app.get("/available-modules")
async def get_available_modules():
    return {"modules": ["community.general.slack"]}

# Get the list of available sources
@app.get("/available-sources")
async def get_available_sources():
    return {"sources": [{"name": "ansible.eda.range", "args": {"limit": "int", "delay": "int"}},
                        {"name": "ansible.eda.webhook", "args": {}},
                       ]}



# Get the list of sources
@app.get("/sources")
async def get_sources():
    return {"sources": rulebook.rulesets[0].sources}


# Get the list of rules
@app.get("/rules")
async def get_rules():
    return {"rules": rulebook.rulesets[0].rules}

# Enable rulebook
@app.post("/enable")
async def enable_rulebook():
    global enable
    if not enable:
        enable = True
        await run_rulebook()
    return {"enable": enable}


# Disable rulebook
@app.post("/disable")
async def disable_rulebook():
    global enable
    if enable:
        enable = False
        if rulebook_task:
            await rulebook_task.cancel()
    return {"enable": enable}


# Get the list of module conditions
@app.get("/conditions")
async def get_conditions():
    return {"conditions": ["event.i == 1", "event.i == 2"]}


# Set the extravars
@app.post("/extravars")
async def set_extravars(new_extravars: dict):
    global extravars
    extravars = new_extravars
    return {"extravars": extravars}


# Get the extravars
@app.get("/extravars")
async def get_extravars():
    return {"extravars": extravars}


# Set the inventory
@app.post("/inventory")
async def set_inventory(new_inventory: Inventory):
    global inventory
    inventory = new_inventory
    return inventory


# Get the inventory
@app.get("/inventory")
async def get_inventory():
    return inventory

# Get the rulebook
@app.get("/rulebook")
async def get_rulebook():
    return build_rulebook()

# Add a source
@app.post("/sources")
async def add_source(source: Source):
    ruleset.sources.append(source)
    save_rulebook()
    if enable:
        await run_rulebook()
    return {"source": source}


# Add a rule
@app.post("/rules")
async def add_rule(rule: Rule):
    ruleset.rules.append(rule)
    save_rulebook()
    if enable:
        await run_rulebook()
    return {"rule": rule}


# Get log lines
@app.get("/logs")
async def get_logs():
    return {"logs": log_lines}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def send(data):
        await websocket.send_text(json.dumps(data))

    try:
        while True:
            data = await websocket.receive_text()
            print("websocket:", data, type(data))
            message = json.loads(data)
            if message["type"] == "Worker":
                await send(
                    {
                        "type": "Inventory",
                        "data": base64.b64encode(
                            inventory.inventory.encode("utf-8")
                        ).decode("utf-8"),
                    }
                )
                await send(
                    {
                        "type": "ExtraVars",
                        "data": base64.b64encode(
                            yaml.safe_dump(extravars).encode("utf-8")
                        ).decode("utf-8"),
                    }
                )
                await send(
                    {
                        "type": "Rulebook",
                        "data": base64.b64encode(
                            yaml.safe_dump(build_rulebook()).encode("utf-8")
                        ).decode("utf-8"),
                    }
                )
                await send({"type": "EndOfResponse"})
    except starlette.websockets.WebSocketDisconnect as e:
        logger.error("websocket_endpoint %s", e)
        print("websocket_endpoint %s", e)


# Run the rulebook
async def run_rulebook():

    global rulebook_task
    global log_lines

    if rulebook_task:
        rulebook_task.cancel()

    if not enable:
        return

    log_lines = []

    activation_id = str(uuid.uuid4())

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
