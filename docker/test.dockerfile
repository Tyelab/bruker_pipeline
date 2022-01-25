# docker-wine is a compatability layer between Windows and Linux.  Allows you to run Windows programs on Linux machines.
# NOTE: Do NOT use latest docker-wine repo, it will fail to use Visual C++ correctly for some reason...
FROM ubuntu:latest

# All credit for this Dockerfile and associated ripping tools goes to Chris Roat, a software engineer at Stanford in the Deisseroth Lab
# His work has been adapted for use in the Tye Lab at the Salk Institute by Jeremy Delahanty.
# If someone is using the Tye Lab's version, they can contact Jeremy at the email below.
LABEL maintainer="Jeremy Delahanty <jdelahanty@salk.edu>"

# This adds about 1.6 GB to the image size.
# The entrypoint wrapper runs the wine setup as wineuser. This is required as it otherwise installs Wine as root causing permission problems later
# The xvfb-run wrapper redirects all displays to a virtual (unseen) display. Wine expects a display to be available.
# Winetricks
# Install visual studio C++ 2015
# This all needs to be run on the same line for some reason, otherwise it crashes

# The Tye lab does not have data collected from Prairie View 5.4, but v5.4 has
# been maintained here in case other groups need it.
COPY ["prairie_view", "/apps/prairie_view/"]

# Copy code last to avoid busting the cache.
COPY *.py /apps/
COPY runscript.sh /apps/runscript.sh
COPY test.sh /apps/test.sh

# In order to use interactive mode properly, /bin/bash must be executed so there's a terminal available
# RUN /apps/test.sh
# RUN /bin/bash
