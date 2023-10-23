
.PHONY: all build push

IMAGE_NAME=quay.io/bthomass/eda-ifthisthenthat
IMAGE_TAG=latest
AA_IMAGE_NAME=quay.io/bthomass/eda-ifthisthenthat-aa
AA_IMAGE_TAG=latest
APP_ROOT=/opt/app-root/src/eda-ifthisthenthat

all: build push

build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

push:
	docker push $(IMAGE_NAME):$(IMAGE_TAG)

run:
	docker run -it --rm -p 8000:8000 -v${PWD}/certs/localhost.key:/etc/ssl/certs/ssl-cert.key -v${PWD}/certs/localhost.crt:/etc/ssl/certs/ssl-cert.crt -v${PWD}/inventory.yml:/opt/app-root/src/eda-ifthisthenthat/inventory.yml -v${PWD}/.env:/opt/app-root/src/eda-ifthisthenthat/.env -v${PWD}/user_db.json:${APP_ROOT}/user_db.json $(IMAGE_NAME):$(IMAGE_TAG) 

run2:
	docker run -it --rm -p 8000:8000 -v${PWD}/rulebook.yml:/opt/app-root/src/eda-ifthisthenthat/rulebook.yml -v${PWD}/inventory.yml:/opt/app-root/src/eda-ifthisthenthat/inventory.yml -v${PWD}/extravars.yml:/opt/app-root/src/eda-ifthisthenthat/extravars.yml $(IMAGE_NAME):$(IMAGE_TAG)

shell:
	docker run -it --rm $(IMAGE_NAME):$(IMAGE_TAG) /bin/bash

aa-build:
	ansible-builder build -f application-environment.yml -t ${AA_IMAGE_NAME}:${AA_IMAGE_TAG}

aa-push:
	docker push $(AA_IMAGE_NAME):$(AA_IMAGE_TAG)

aa-run:
	docker run -it --rm -p 8000:8000 $(AA_IMAGE_NAME):$(AA_IMAGE_TAG)

aa-run2:
	docker run -it --rm -p 8000:8000 -eDEFAULT_LOCAL_TMP=/tmp -v${PWD}/rulebook.yml:/runner/rulebook.yml -v${PWD}/inventory.yml:/runner/inventory.yml -v${PWD}/extravars.yml:/runner/extravars.yml $(AA_IMAGE_NAME):$(AA_IMAGE_TAG)

aa-shell:
	docker run -it --rm $(AA_IMAGE_NAME):$(AA_IMAGE_TAG) /bin/bash

aa-shell2:
	docker run -it --rm -p 8000:8000 -eANSIBLE_LOCAL_TMP=/tmp -v${PWD}/rulebook.yml:/runner/rulebook.yml -v${PWD}/inventory.yml:/runner/inventory.yml -v${PWD}/extravars.yml:/runner/extravars.yml $(AA_IMAGE_NAME):$(AA_IMAGE_TAG) /bin/bash
