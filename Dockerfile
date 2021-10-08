# Builds Bruker Image Ripping Utility
# Written by Chris Roat, Deisseroth Lab @ Stanford University
# Adapted for the Tye Lab at the Salk Institute by Jeremy Delahanty

# Uses Wine to run Windows programs on the Linux kernel
FROM scottyhardy/docker-wine:stable-5.0.2-nordp

# Metadata describing the image maintainer
# The author of the original Dockerfile is Chris Roat, but Jeremy is the lab's
# local developer managing this container. Credit is due to Chris for creating
# the container and this script, but if using the Tye Lab's repository users
# can contact Jeremy.
LABEL maintainer="Jeremy Delahanty <jdelahanty@salk.edu>"

# The entrypoint wrapper runs the wine setup as wineuser.
# The xvfb-run wrapper redirects all displays to a virtual (unseen) display.
# This adds about 1.6 GB to the image size.
RUN /usr/bin/entrypoint xvfb-run winetricks -q vcrun2015

ENV PATH /opt/conda/bin:$PATH

# Conda install is 250 MB
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# The Tye lab does not have data collected from Prairie View 5.4, but v5.4 has
# been maintained here in case other groups need it.
COPY ["Prairie View 5.4/", "/apps/Prairie View 5.4/"]
COPY ["Prairie View 5.5/", "/apps/Prairie View 5.5/"]

# Environment is ~700 MB
# COPY environment.yml .
# RUN conda env update --quiet --name base --file environment.yml \
#     && conda clean --all -f -y \
#     && rm environment.yml

# Copy code last to avoid busting the cache.
COPY *.py /apps/
COPY runscript.sh /apps/runscript.sh

CMD /apps/runscript.sh
