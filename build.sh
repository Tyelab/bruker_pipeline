#!/bin/bash

echo "Hello!"

sudo docker run \
       -it \
       --rm \
       --volume=${2}:/data \
       --env=USER_NAME=${USER} \
       --env=USER_UID=$(id -u ${USER}) \
       --env=USER_GID=$(id -g ${USER}) \
       --env=USER_HOME=${HOME} \
       --workdir=/home/${USER} \
