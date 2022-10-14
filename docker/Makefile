IMAGE_TAG=20221014
IMAGE_NAME=snlkt-bruker-ripper

build: build_docker

build_docker:
	sudo docker build -t $(IMAGE_NAME):$(IMAGE_TAG) -f Dockerfile .
	sudo docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(IMAGE_NAME):latest
