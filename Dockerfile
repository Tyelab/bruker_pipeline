FROM scottyhardy/docker-wine:latest

LABEL maintainer="Jeremy Delahanty <jdelahanty@salk.edu>"

# This adds about 1.6 GB to the image size.

 # The entrypoint wrapper runs the wine setup as wineuser. This is required as it otherwise installs Wine as root causing permission problems later
RUN /usr/bin/entrypoint \

# The xvfb-run wrapper redirects all displays to a virtual (unseen) display. Wine expects a display to be available.
    && xvfb-run \
    && winetricks -q \

# Install visual studio C++ code from 2015
    && vcrun2015 \

# Create path for conda and add it to the container's path
ENV PATH /opt/conda/bin:$PATH

# Install conda by running webget (wget) then rename download to miniconda.sh and place in home directory
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh \

    # Run the miniconda installation script in the path /opt/conda
    && /bin/bash ~/miniconda.sh -b -p /opt/conda \

    # Once installed, remove the miniconda.sh install script
    && rm ~/miniconda.sh \

    # conda clean removes cached installation files: -a=all, -f=?, -y=yes to all prompts
    && /opt/conda/bin/conda clean -a -f -y \

    # Create soft link to conda profile.d and conda.sh
    && ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh \

    # Echo the conda shell script into bashrc so it starts when container is created
    && echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc \

    # Echo conda activate base into the bashrc so you're in base environment at start
    && echo "conda activate base" >> ~/.bashrc

# The Tye lab does not have data collected from Prairie View 5.4, but v5.4 has
# been maintained here in case other groups need it.
COPY ["Prairie View 5.4/", "/apps/Prairie View 5.4/"]
COPY ["Prairie View 5.5/", "/apps/Prairie View 5.5/"]

# Copy code last to avoid busting the cache.
COPY *.py /apps/
