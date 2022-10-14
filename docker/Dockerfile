# docker-wine is a compatability layer between Windows and Linux.  Allows you to run Windows programs on Linux machines.
# NOTE: Do NOT use latest docker-wine repo, it will fail to use Visual C++ correctly for some reason...
FROM scottyhardy/docker-wine:latest

# All credit for this Dockerfile and associated ripping tools goes to Chris Roat, a former software engineer at Stanford in the Deisseroth Lab
# https://github.com/chrisroat
# His work has been adapted for use in the Tye Lab at the Salk Institute by Jeremy Delahanty.
# 
# If someone is using the Tye Lab's version, they can contact Jeremy at the email below.
LABEL maintainer="Jeremy Delahanty <jdelahanty@salk.edu>"

# This adds about 1.6 GB to the image size.
# The entrypoint wrapper runs the wine setup as wineuser. This is required as it otherwise installs Wine as root causing permission problems later
# The xvfb-run wrapper redirects all displays to a virtual (unseen) display. Wine expects a display to be available.
# Winetricks
# Install visual studio C++ 2015
# This all needs to be run on the same line for some reason, otherwise it crashes
RUN /usr/bin/entrypoint xvfb-run winetricks -q vcrun2015

# Create path for conda and add it to the container's path
ENV PATH /opt/conda/bin:$PATH

# Install conda by running webget (wget) then rename download to miniconda.sh and place in home directory
# Run the miniconda installation script in the path /opt/conda
# Once installed, remove the miniconda.sh install script
# conda clean removes cached installation files: -a=all, -f=force presumably, -y=yes to all prompts
# Create soft link to conda profile.d and conda.sh
# Echo the conda shell script into bashrc so it starts when container is created
# Echo conda activate base into the bashrc so you're in base environment at start
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh \
    && /bin/bash ~/miniconda.sh -b -p /opt/conda \
    && rm ~/miniconda.sh \
    && /opt/conda/bin/conda clean -a -f -y \
    && ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh \
    && echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc \
    && echo "conda activate base" >> ~/.bashrc

# Environment is 1KB
COPY environment.yml .
RUN conda env update --quiet --name base --file environment.yml \
    && conda clean --all -f -y \
    && rm environment.yml

# The Tye lab does not have data collected from Prairie View 5.4, but v5.4 has
# been maintained here in case other groups need it.
COPY ["prairie_view", "/apps/prairie_view/"]

# Copy code last to avoid busting the cache.
COPY *.py /apps/
COPY runscript.sh /apps/runscript.sh
