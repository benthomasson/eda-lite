
.PHONY: all build push

IMAGE_NAME=quay.io/bthomass/eda-ifthisthenthat
IMAGE_TAG=latest

all: build push

build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

push:
	docker push $(IMAGE_NAME):$(IMAGE_TAG)


run:
	docker run -it --rm -p 8000:8000 $(IMAGE_NAME):$(IMAGE_TAG)

shell:
	docker run -it --rm $(IMAGE_NAME):$(IMAGE_TAG) /bin/bash

