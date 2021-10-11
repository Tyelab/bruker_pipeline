FROM scottyhardy/docker-wine:stable-5.0.2-nordp

LABEL maintainer="Jeremy Delahanty <jdelahanty@salk.edu>"

# The xvfb-run wrapper redirects all displays to a virtual (unseen) display.
# This adds about 1.6 GB to the image size.
RUN /usr/bin/entrypoint
RUN xvfb-run
RUN winetricks -q
RUN vcrun2015

# The Tye lab does not have data collected from Prairie View 5.4, but v5.4 has
# been maintained here in case other groups need it.
COPY ["Prairie View 5.4/", "/apps/Prairie View 5.4/"]
COPY ["Prairie View 5.5/", "/apps/Prairie View 5.5/"]

# Copy code last to avoid busting the cache.
COPY *.py /apps/

RUN build.sh
