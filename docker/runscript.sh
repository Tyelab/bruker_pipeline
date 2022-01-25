#!/bin/bash

# The container executable.  This script takes no arguments, and just performs 
# minimal environment setup prior to running main script.

set -e

# USE_XVFB means xvfb is already running.  If it is unset, xvfb-run should wrap commands.
[[ -z "${USE_XVFB}" ]] && CMDPREFIX=xvfb-run

# Unsure why exporting the temporary directory with .wine is necessary...
TEMPDIR="$(mktemp -d)"
export WINEPREFIX="${TEMPDIR}/.wine"
export WINEARCH="win64"

cp -r /home/wineuser/.wine "${WINEPREFIX}"

${CMDPREFIX} -a /usr/bin/python3 /apps/rip.py --directory $1 --ripper_version $2 --log_file $3
