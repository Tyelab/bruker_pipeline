# Image Ripping: Going from RAW to .OME.tif

Bruker's microscope and software encodes images into a proprietary binary file format while the recording takes place. This format is not readable or usable for analysis purposes.In order to analyze these images, we have to convert the RAW format into a usable file format for our analysis. For more about the outputs of the currently existing system see the docs [here](https://bruker-control.readthedocs.io/en/latest/outputs/index.html). 

The process by which you convert these files into a usable images is called "Image Ripping" and is performed by `Bruker's Image-Ripping Application`. Somewhat confusingly, the "Image Ripping" tool also converts the Voltage Recordings from the RAW format to a .csv file that can be used for analysis.

## The .OME.tif Format
The OME (or [Open Microscopy Environment](https://www.openmicroscopy.org/index.html)) format has been developed through the partnership of many different labs, companies, and foundations for the analysis, collection, and manipulation of microscopy data. It is a commonly used file format for many different kinds of imaging across many disciplines and is also easy to use and analyze. Typically, .OME.tif files contain different kinds of metadata about the image in its header as well as the values each pixel contains. Unfortunately, this format is limited in several ways.

The primary weakness of the .OME.tif is that there is a hard file size limit of 4GB per "stack" of these images. This is due to the encoding of .tif files using a 32bit storage format. The stacks simply run out of room! For imaging data collected in the lab's experiments on the Bruker, the data size can reach up to 70GB. Although you can manage different tiff stacks, it can be cumbersome to have to track and move stacks of files or worse, individual tiffs, programmatically.

One solution to this problem is use of a different file format called HDF5, or [Hierarchical Data Format 5](https://www.hdfgroup.org/solutions/hdf5), which can store enormous amounts of data that can be flexibly organized in various ways within a binarized file structure. Another is [zarr](https://zarr.readthedocs.io/en/stable/index.html) which is a new and improved file format that has the same attributes of HDF5 without some of the drawbacks of H5 files. The differences are that HDF5 is portable across languages while zarr is restricted to Python. Another is that zarr is [easier to integrate into cloud storage](https://medium.com/pangeo/cloud-performant-netcdf4-hdf5-with-zarr-fsspec-and-intake-3d3a3e7cb935) solutions like AWS/Google Cloud/Microsoft Azure through librarys like [fsspec](https://filesystem-spec.readthedocs.io/en/latest/) and is allegedly easier to perform both parallel read and write operations upon through libraries like [Dask](https://www.dask.org/). A further solution is to pipe the tiff files through the [ffmpeg](https://ffmpeg.org/) library and use lossless [H264 encoding](https://www.vcodex.com/an-overview-of-h264-advanced-video-coding/) to have data written to a binary. An additional solution is to use the [BigTiff](https://www.awaresystems.be/imaging/tiff/bigtiff.html) format which uses 64bit offsets instead of 32bit offsets as the original format does.

## File Ripping Particulars: Bruker's Versioning and Updates

The image ripping tool is tied explicitly to the version of Prairie View that acquired the data. These versions have the following structure:

- MajorVersion.MinorVersion.BitNumber.UpdateNumber
- Ex: 5.5.64.500

Prairie View has somewhat frequent updates as the software engineering team at Bruker make improvements or squash bugs. One of their senior software engineers, Michael Fox, has been instrumental in getting the system functioning properly with bruker_control.py and deserves a firm handshake or high-five if you ever meet him one day. Updates can be found [here](https://pvupdate.blogspot.com/). Each update has it's own security code. You can email Bruker directly for this password, but the main place you should get the code is from the window that opens when Prairie View starts up. At the end of the initialization procedure, a message about new updates will be present and it will tell you the installation code.

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/prairieview_update.png)

Once you've installed the update, the previous version will have been copied to the Program Files location on the local machine with its specific version as the filename. Inside each installation, you'll find a folder called "Utilities". Here's what that looks like:

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/prairieview_tree.png)

Inside "Utilities" you'll find a bunch of different files with the extension .dll. This stands for [Dynamic Link Library](https://docs.microsoft.com/en-us/troubleshoot/windows-client/deployment/dynamic-link-library) and is what the Windows OS uses to have software libraries communicate with each other and the operating system. One of these files is called `daq_int.dll` and it's critical to the ripping process.

Prairie View, and therefore the ripper, enforces a rule that the version of the software that acquired the data is the exact same as the version that's converting it from RAW to ome.tif format. This is to ensure that the ripping process converts the data correctly without any risk of failure that might corrupt the RAW format or output malformed ome.tif files. If you attempt to rip a dataset collected in a version different from the ripper's, you'll be greeted with this message:

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/ripper_version_error.png)

Per Michael Fox, the only way this will change in the future is if Bruker moves away from offline conversion entirely and instead always performs image conversion at runtime. On 11/30/21, Michael detailed that the "plan is to eventually eliminate raw files and just write multi-page TIFFs directly, with perhaps a legacy fallback for older computers which can’t keep up with that.  That could start as early as later next year depending on how other projects are going.  It is an extremely popular feature/request so the sooner the better."

Thus, you'll have to check the version of the dataset by investigating the recording's .env file described above. You can open this file in any text editor you'd like. Notepad works just fine.

The second row of this file will contain the version of Prairie View that collected the data. It looks like this:

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/xml_version.png)

Once you know which version of Prairie View was used to collect the data, you can find the specific version of Prairie View's ripper to match it with. There are multiple ways of performing this conversion and they're discussed below. Two require your hand holding the directories through the process, one is intended to be automated and event driven but is still under development.

## File Ripping Particulars: Ripper Functionality

This section paraphrases information from Michael Fox about how the ripper performs its operations

### Memory Allocation
For the ripper to work, it must allocate 4 bytes per channel per pixel of memory to the process. If the ripper can't find enough contiguous memory when you call it, an error is raised that requires a restart of the computer. See the next section below for more information about the error that is raised. Memory is allocated just once per dataset, meaning once per Filelist.txt described above by a call to a convert function in the daq_int.dll library and then freed afterwards. While running, the ripper only uses approximately 0.5GB of memory. See [here](https://github.com/Tyelab/bruker_pipeline/issues/20#issuecomment-1157071798).

### Processor Use
The ripping utility is single core and essentially operates as a for loop iterating through the raw files found in the Filelist.txt. Therefore, allocating additional cores to an individual instance of the ripper should not impact performance. It has been found that the ripper does sometimes appear to use more than one core while operating, but it's possible that this is for the actual processing of reading and writing to/from disk.

Michael states that, in theory, multiple conversions can be run concurrently where each ripper instance is allocated one core. This has been done in practice on the microscope's machine and also through the Docker + Wine implementation.

### File I/O
Input/output operations can also be computationally intensive. The speed of the processor used for ripping as well as the speeds of the hard-drives that are being used for reading/writing files all change how fast the ripper can perform.  For best performance, using a *local* SSD or, preferentially, an NVMe drive, and a fast processing core should be used. Writing many individual .tif files over NFS will incur overhead that slows the procedure down to a crawl. See below.

## Ripping Utility Crashes

It has been discovered that there are different cases where the ripper can crash or choke. These crashes present themselves differently depending on how the ripping is being conducted.

### Errors When Ripping with the GUI on Windows

#### Memory Allocation Error

There is a potential situation where the application fails to allocate a sufficiently large block of contiguous memory for its processing. It appears that this is a rare occurrence, but to minimize the chances of this occurring make sure that you close all other applications running on the computer before starting the process.

The exact computer science behind this is complex, but in short RAM is accessible by referencing specific physical locations. The operating system coordinates how different programs access these physical locations and, sometimes, it is most efficient to spread these processes out across several locations. This is known as memory fragmentation. Below is a paraphrase of an answer that Michael Foxprovided for how this can lead to issues with the ripper.

For the ripper to work, it must allocate 4 bytes per channel per pixel of memory to the process. If the ripper can't find enough continuous memory when you call it, an error is raised that requires a restart of the computer. Note that this is not because there's not enough total memory available. The error message below, therefore, is somewhat misleading.

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/file_conversion_memory_problem.png)

If you encounter this error while doing the ripping locally on Bruker, exit Prairie View and then restart the machine.

#### Spontaneous Crashes

On occasion, when processing longer recordings (approx 40k + images, 25 minutes), there are times where the ripper will crash without warning and without notifying the user. As of 11/23/21, it is unknown why this happens. It has occurred when running the ripper both remotely on a VM as well as locally on Bruker. To minimize the risk of this rare event occurring, do not run any other programs while the ripping process is underway.

There are only two ways to tell if the ripper fails in this manner:

1. Check the total number of converted images
- For a 60 trial, single recording session with ITIs between 15-30 seconds at approximately 30FPS, you can expect a range of 44k - 46k files.
- For a 20 trial, single recording session with ITIs between 15-30 seconds, you can expect a range of 18k - 20k files.
2. The ripper has disappeared from the screen.
- If the ripper completes successfully, you will see the ripper waiting for your command with the "Status" found in the bottom left corner as "Idle."

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/idle_ripper.png)

#### Performance Issues
If you have sufficiently long recordings (greater than 15k images), writing outputs of the ripper over NFS (or a network file system) will inevitably slow to a crawl. In short, each file transfer invokes a series of steps the network must accomplish to ensure the data is sent and received properly. Although these steps don't take much time individually, a large sum of files makes these steps add up quickly.  Although the datacenter is linked together by fast ethernet connections, the transfer of so many individual files that individually invoke their own numerous steps during transfer incurs a substantial overhead that will slow the file writing speed to a crawl. Further, there is a network cache that is available that fills up if data isn't written to disk on the recieving machine quickly enough. Therefore, for best performance, it is best to write the new data to a local disk rather than over the network. This is what the Docker Containers running on cheetos do. Users then can invoke a transfer script to put the files into their appropriate location. Ideally you would convert the files into H5/zarr/bigtiff/H264 binaries before moving them.

### Errors When Ripping with Docker Containers
It is possible that the Docker Containers hosted on Cheetos could run into the errors described above. However, as of 11/23/21, they have not been knowingly encountered there.

The primary error one could run into is if the dataset scheduled for ripping has a version that the container does not have available. If this occurs, an exception will be thrown that kills both the ripping process as well as the container. This can happen when an update was performed on Bruker to a newer Prairie View version, and therefore a newer ripper, but either:

1. The ripper wasn't copied into the appropriate directory on `snlkt/data/bruker_pipeline/docker/prairie_view` when an update occured
- Only members of Team2P should perform these updates and copying procedures until a script is created to copy the necessary files.
2. The container image wasn't rebuilt with the updated directory
- Only Jeremy or, more generally, Docker Group members can perform this function. Documentation on this will probably not arrive as the Docker method is likely to be deprecated.

A secondary error that the container can run into is if there's badly formed XML in the recording's environment file. See [nwb_utils.py](https://github.com/Tyelab/bruker_pipeline/blob/a0f863508b873450a7150f0332895c9d37da6ef3/nwb_utils.py#L213) for an example of using `lxml` to avoid this crash.

While testing with previous versions, there were cases where the regular expression used to match the .env version with the appropriate ripper were insufficient resulting in a situation where the container would "choke", or fail but not raise an error/exception.

Essentially, the program runs continuously and polls the folder it's writing out tiffs to despite there being no new tif files written in between checks. The program did not detect a problem. It will continue this polling behavior until it reaches the max amount of time for checking and then kill the ripper and container. This behavior has not occured as of early 2022 due to some fixes implemented by Team2P.

## Ripping Files Through GUI on BRUKER/Elsewhere

In the future ripping files locally on the microscope's machine should be discouraged for experimental datasets as things will be transferred to the server through methods Annie is developing.

Prairie View's image ripper can be found within the main window of the software under the "Applications" tab. This should only be used if you're converting the raw data to images after a recording you just completed. For the reasons in the above section, this ripper will only work on the data that was just collected by the software.

After selecting the application, a new window will appear...

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/image_block_ripper.png)

The ripper has several options available to it. When ripping locally on Bruker, you can write the images to your local directory.

You should *NOT* delete your original data after creating the images as this will be retained and transferred to snlktdata. Deselect this box. The reason for this is due to the spontaneous crashes that have occured previously as described above. If the ripper is converting images and crashes midway, you will have corrupted the binary data and made it irrecoverable!

Next, click the "Add Folder" button. A new window will open.

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/image_ripping_utility.png)

You can navigate to the other raw data drive, but a common practice is to just navigate to the "Raw Data" drive located on Drive "E:" and select the "microscopy" folder.

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/raw_drive.png)

After selecting the microscopy folder, you will see the different file lists that the ripper has found.

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/ripping_selected_folder.png)

While it's processing files, the ripper looks like this. Notice on the bottom left corner that the "Status" is listed as "Converting File List 1 of n" where n is the number of sessions being converted.

For a typical session, there will be two File Lists present: one for the imaging and one for the voltage recording.

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/actively_converting.png)

When complete, the ripper looks just like it did before you got started. However, you'll notice in the bottom left corner that the "Status" is listed as "Idle".

!(https://github.com/Tyelab/bruker_pipeline/blob/main/docs/images/ripping_completed.png)

When complete, the ripper looks just like it did before you got started. However, you'll notice in the bottom left corner that the "Status" is listed as "Idle".

*Congratulations!* You're now the proud owner of a large number of tiff files!