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
       --volume=/snl/scratch25/snlkt-playground/:/tmp \
       --env=USER_NAME=${USER} \
       --env=USER_UID=$(id -u ${USER}) \
       --env=USER_GID=$(id -g ${USER}) \
       --env=USER_HOME=${HOME} \
       --workdir=/home/${USER} \
       --env=USE_XVFB=yes \
       --env=XVFB_SERVER=:95 \
       --env=XVFB_SCREEN=0 \
       --env=XVFB_RESOLUTION=320x240x8 \
       --env=DISPLAY=:95 \
       --hostname=bruker-ripper \
       --name=bruker-ripper \
       --shm-size=1g \
       --env=TZ=America/Los_Angeles \
       snlkt-bruker-ripper:latest
