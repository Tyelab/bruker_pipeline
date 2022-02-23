# bruker_pipeline
Data pre-processing pipeline for data from the Bruker Ultima multi-photon microscope in conjunction with bruker_control.

## Purpose
Converting data from the RAW format Bruker outputs into .ome.tiff files and then to .h5/.zarr requires a pipeline of its own. The code in this repository adapts what was written by
[Chris Roat](https://github.com/chrisroat) and [Tyler Benster](https://github.com/tbenst) for the [Deisseroth Lab](https://github.com/deisseroth-lab/two-photon). It also uses code written by Deryn LeDuke and Kyle Fischer PhD for the [Tye Lab](https://github.com/Tyelab).

This repository will remain specific for the ripping process for data coming off microscopes manufactured by Bruker.

## User Guide

The main executable is a program called `beyblade.sh`. In short, this will grab a list of directories that need conversion from a directory called `raw_conversion`,
spawn a Docker container for each ripper, and write out .ome.tif files to a folder locally. Conversions from tiffs to H5 can be executed via a separate script in `MATLAB`
or `Python` depending on your use case. The steps are as follows:

1. Sign into `cheetos.snl.salk.edu`. This is currently the only machine with the Docker image reproduced on it. You can use either `MobaXterm` or the Windows `Powershell`.

2. Navigate to `/snlkt/data/bruker_pipeline` via the `cd` command, as in: `cd /snlkt/data/bruker_pipeline/`

3. Create a `.txt` file containing the *full paths* to your data on the server. The file should look something like this:

```
/snlkt/data/_DATA/specialk_cs/2p/raw/CSC013/20211104/20211104_CSC013_plane1_-538.875_raw-003
/snlkt/data/_DATA/specialk_cs/2p/raw/CSC013/20211111/20211111_CSC013_plane1_-367.25_raw-026
/snlkt/data/_DATA/specialk_cs/2p/raw/CSC013/20211118/20211118_CSC013_plane1_-749.075_raw-046
/snlkt/data/_DATA/specialk_cs/2p/raw/CSC013/20211125/20211125_CSC013_plane1_-357.625_raw-067
/snlkt/data/_DATA/specialk_cs/2p/raw/CSC013/20211202/20211202_CSC013_plane1_-727.1_raw-085
/snlkt/data/_DATA/specialk_cs/2p/raw/CSC013/20211209/20211209_CSC013_plane1_-746.175_raw-103
/snlkt/data/_DATA/specialk_cs/2p/raw/CSC013/20211214/20211214_CSC013_plane1_-362.075_raw-121
```

Substitute the paths to your *raw* directories. As of 2/23/22, it appears that performance is maintained for up to 7 rippers running at once. This file must be saved in
in the `raw_conversion` directory. Ideally, it would be given a unique filename in the following format:

- YYYYMMDD_project#conversion: `20220223_specialk_cs1`

If you run a second conversion on the same day for the same project, increment the `#conversion`, as in `20220223_specialk_cs2`.

4. Ensure that you have your Docker permissions active by typing `sudo docker images`. The terminal will ask for your `SNL` password. Remember that the password will not be displayed as you type. If successful, you should see a list of images including `snlkt-bruker-ripper`. This is the image that the ripper uses.

5. If you have no errors to this point, type: `./beyblade.sh`. You will be presented with messages stating which containers are being started for you. Next, you will see multiple error and fixme messages. These are expected and related to internal workarounds that `Wine` has to use to run Windows software on Linux machines.

6. When these messages have been completed, hit enter to be returned to your terminal.

The amount of time it takes to perform conversions to ome.tif depends on how many planes you ran as well as how many channels you recorded from. Although performance varies slightly depending on network traffic and how busy Cheetos is at a given moment, you can expect things to take a couple minutes longer than the recording you took. In other words:
- 30 minute imaging session is complete in about 35 minutes.

If you want to ensure your containers are running, you can:

- Type `sudo docker container ls -a` which will display all the containers you have spawned to the terminal for you.

- Go into the folder titled `logs` and find the recording you are converting for. The ripper logs what it is working on and if there's any issues with execution.

If you have VS Code installed, updates made to the file will be presented to you in real time. If not, you'll have to close and reload the file to see progress.
