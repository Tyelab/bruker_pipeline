# bruker_pipeline
Data processing pipeline for data from the Bruker Ultima microscope in conjunction with bruker_control.

## Purpose
Converting data from the RAW format Bruker outputs into .ome.tiff files and then to .h5/.zarr requires a pipeline of its own. The goals for this repository are as follows:
- Perform image ripping in a standardized way that can be performed without requiring the use of the local machine (although it will be possible to do it on the local machine and perhaps always done there after we have upgraded ethernet, to be determined)
- Voltage Recording ripping should similarly be performed but without the intermittant file generation (as there are no files other than the raw data generated)
- Write .ome.tiff files to snlscratch25 and then put concatenated .h5/.zarr data back onto the `snlktdata/_DATA` directory. This will then be linked to an `NWB File` in the `raw` folder of the subject that had their images ripped.
- This processing should follow an event driven architecture where the moment a file transfer is complete to the server, a machine like Cheetos can immediately perform ripping, concatenation, and, preferrably, pre-processing via Suite2p/ezCalcium if a known template for a brain structure/project is available.
- Suite2p/ezCalcium processing of these concatenated files will be done preferentially in the cluster but will not be made exclusive to it. Until we have 10GB lines to/from our server (which is allegedly something coming in the future) to our lab's workstation machines, processing on the cluster should be the first choice in my (Jeremy's) opinion.

This repository will remain specific for the ripping process from Bruker. Other 2P procesing could maybe follow a similar structure to the Deisseroth's lab's two-photon repo that is forked here.


## Notes:
- /usr/bin/entrypoint

- [xvfb](https://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml)

An X server (which runs the X Window System on local machines) that handles access to graphics cards, display screens, and input devices.
It's a cross-platform free client-server system that manages GUIs on single computers or networks of computers. Allows for server program
to accomodate the requests of multiple clients. X server-client comms are managed by the X protocol that first processes client requests,
the response by the server, and the sending of events/errors from the server back to the client.

Its primary use case was intended for testing servers with no display hardware and no physical input devices.

One forum I found states that [Wine assumes there to be a display available](https://github.com/Winetricks/winetricks/issues/934).

- winetricks -q
Wine tricks is a more powerful version of winecfg. Winecfg gives the ability to change settings of WINE itself. Winetricks allows you to
modify the actual Windows layer and install important components like .dlls and system fonts and the ability to edit the Windows registry.
I have yet been able to find what the -q command means here.

- vcrun2015
I believe that this references an installation of Visual Studio C++ code, but am not certain yet...

- ENV PATH /opt/conda/bin:$PATH
This is a way for Docker to instantiate an ENV, or environment, variable. I believe it creates this path for the image.

- RUN wget --quiet miniconda link
Installs miniconda to the image

- -O ~/miniconda.sh
Renames downloaded file to miniconda.sh; I believe this is here for ease of use with the next commands

- miniconda.sh -b -p /opt/conda
Unsure what -b stands for, I'm guessing that -p means to set a path. Unsure why the `/opt/conda` path is written here.

- conda clean -tipsy
Unsure what -tipsy does, can't find documentation for it. Conda clean removes any unusued packages.

Tipsy is simply the list of flags -t -i -p -s -y.

-t or --tarballs
-i or --index-cache
-p or --packages
-s or ... eh that was not documented, it probably relates to --source-cache and this issue
-y or --yes

https://github.com/jupyter/docker-stacks/issues/861
Per this issue, using `-all -f -y` are the correct flags.

Interestingly, Chris uses `-all -f -y` later in the Dockerfile.

- ln -s
Unsure what the ln and the -s does, I believe it has to do with setting links but can't be sure.

- echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc
Adds conda.sh to the startup script for container

- echo "conda activate base" >> ~/.bashrc
Adds command to activate conda base to startup command for container.




