#!/bin/bash

echo
echo "Hello! Welcome to the Bruker Image Ripper"
echo
echo "Containerized using Linux Wine, Winetricks, and Docker"
echo
echo "Written by Chris Roat, Deisseroth Lab @ Stanford"
echo "Adapted for the Tye Lab by Jeremy Delahanty @ Salk"
echo

sudo docker run \
       -it \
       --rm \
       --volume=/snlkt/data/raw:/data \
       --env=USER_NAME=${USER} \
       --env=USER_UID=$(id -u ${USER}) \
       --env=USER_GID=$(id -g ${USER}) \
       --env=USER_HOME=${HOME} \
       --workdir=/home/${USER} \
       --name=bruker-ripper \
       --hostname=bruker-ripper \
       snlkt-bruker-ripper:latest
