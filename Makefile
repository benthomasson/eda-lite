
.PHONY: all build push

IMAGE_NAME=quay.io/bthomass/eda-ifthisthenthat
IMAGE_TAG=latest

all: build push

build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

push:
	docker push $(IMAGE_NAME):$(IMAGE_TAG)



