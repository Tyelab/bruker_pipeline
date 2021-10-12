FROM scottyhardy/docker-wine:latest

LABEL maintainer="Jeremy Delahanty <jdelahanty@salk.edu>"

# The entrypoint wrapper runs the wine setup as wineuser. This is required as it otherwise installs Wine as root which causes severe permission problems later...
# The xvfb-run wrapper redirects all displays to a virtual (unseen) display.
# This adds about 1.6 GB to the image size.
# For some reason, you have to run all this at once otherwise it crashes...
RUN /usr/bin/entrypoint xvfb-run winetricks -q vcrun2015

# Create path for conda and add it to the container's path
ENV PATH /opt/conda/bin:$PATH

# Install conda by running webget (wget)
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -all -f -y && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# The Tye lab does not have data collected from Prairie View 5.4, but v5.4 has
# been maintained here in case other groups need it.
COPY ["Prairie View 5.4/", "/apps/Prairie View 5.4/"]
COPY ["Prairie View 5.5/", "/apps/Prairie View 5.5/"]

# Copy code last to avoid busting the cache.
COPY *.py /apps/
COPY build.sh .

CMD /bin/bash
