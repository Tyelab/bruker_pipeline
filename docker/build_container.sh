#!/bin/bash

# Determine the day's date that the ripper is being run
d=$(date "+%Y%m%d")

# Create filename for the log file
log_identifier="$1-$d"

log_filename="$log_identifier".log

# Write information from python script to log file
# Order of variables (from beyblade.py):
# 1. Animal name used for container name
# 2. Full path for raw data
# 3. Truncated path for mounting data directory in container
# 4. Version of ripper to use
# 5. Total number of images to be converted
echo $1 >> logs/$log_filename
echo $2 >> logs/$log_filename
echo $3 >> logs/$log_filename
echo $4 >> logs/$log_filename
echo $5 >> logs/$log_filename


sudo docker run \
       --rm \
       --volume=$2:/data \
       --volume=/snl/scratch25/snlkt-2p/:/tmp \
       --volume=/snlkt/data/bruker_pipeline/logs:/logs \
       --env=USER_NAME=${USER} \
       --env=USER_UID=$(id -u ${USER}) \
       --env=USER_GID=$(id -g ${USER}) \
       --env=USER_HOME=${HOME} \
       --workdir=/home/${USER} \
       --env=USE_XVFB=yes \
       --env=XVFB_SERVER=:3 \
       --env=XVFB_SCREEN=0 \
       --env=XVFB_RESOLUTION=320x240x8 \
       --env=DISPLAY=:3 \
       --env=TZ=America/Los_Angeles \
       --cpus 2 \
       --shm-size=1g \
       --name=$1 \
       snlkt-bruker-ripper:latest \
       /apps/runscript.sh $3 $4 $log_filename
       

# sudo docker run \
#        -it \
#        --rm \
#        --volume=$1:/data \
#        --volume=/snl/scratch25/snlkt-playground/:/tmp \
#        --env=USER_NAME=${USER} \
#        --env=USER_UID=$(id -u ${USER}) \
#        --env=USER_GID=$(id -g ${USER}) \
#        --env=USER_HOME=${HOME} \
#        --workdir=/home/${USER} \
#        --env=USE_XVFB=yes \
#        --env=XVFB_SERVER=:95 \
#        --env=XVFB_SCREEN=0 \
#        --env=XVFB_RESOLUTION=320x240x8 \
#        --env=DISPLAY=${DISPLAY} \
#        --hostname=bruker-ripper \
#        --name=bruker-ripper \
#        --shm-size=1g \
#        --env=TZ=America/Los_Angeles \
#        test:test