#!/bin/bash

# Written by Chris Roat for the Deisseroth Lab at Stanford
# https://github.com/chrisroat
# https://github.com/deisseroth-lab/two-photon/
# Adapted for the Tye Lab by Jeremy Delahanty @ Salk Institute for Dr. Kay Tye's Lab
# The container executable that performs environment setup.

# Set environment variable for linux shell
set -e

# USE_XVFB means xvfb is already running.  If it is unset, xvfb-run should wrap commands.
[[ -z "${USE_XVFB}" ]] && CMDPREFIX=xvfb-run

# Unsure why exporting the temporary directory with .wine is necessary...
TEMPDIR="$(mktemp -d)"
export WINEPREFIX="${TEMPDIR}/.wine"
export WINEARCH="win64"

cp -r /home/wineuser/.wine "${WINEPREFIX}"

${CMDPREFIX} -a python3 /apps/rip.py --directory $1 --ripper_version $2 --log_file $3 --num_images $4
