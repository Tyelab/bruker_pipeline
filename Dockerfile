FROM scottyhardy/docker-wine:latest

LABEL maintainer="Jeremy Delahanty <jdelahanty@salk.edu>"

# The xvfb-run wrapper redirects all displays to a virtual (unseen) display.
# This adds about 1.6 GB to the image size.
# For some reason, you have to run all this at once otherwise it crashes...
RUN /usr/bin/entrypoint xvfb-run winetricks -q vcrun2015

# The Tye lab does not have data collected from Prairie View 5.4, but v5.4 has
# been maintained here in case other groups need it.
COPY ["Prairie View 5.4/", "/apps/Prairie View 5.4/"]
COPY ["Prairie View 5.5/", "/apps/Prairie View 5.5/"]

# Copy code last to avoid busting the cache.
COPY *.py /apps/
COPY build.sh .

RUN ls

CMD build.sh
