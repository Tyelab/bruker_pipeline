# Jeremy Delahanty January 2022
# Timestamp Creation written by Deryn LeDuke, Kyle Fischer PhD 2021
# Main library written by Chris Roat, Stanford University Deisseroth Lab August 2021
# https://github.com/chrisroat
# https://github.com/deisseroth-lab/two-photon/
# Adapted for the Tye Lab by Jeremy Delahanty @ Salk Institute for Dr. Kay Tye's Lab

"""Library for running Bruker image ripping utility."""

import argparse
import atexit
import logging
from pathlib import Path
import platform
import subprocess
import time
import os
import shutil
import pandas as pd

logger = logging.getLogger(__name__)

# Ripping process does not end cleanly, so the filesystem is polled to detect the
# processing finishing.  The following variables relate to the timing of that polling
# process.

# Total wait time is very large in case of multiple channels being recorded
# This is just in case the ripper is stuck hanging for some long period of time
# so it can be automatically killed.
RIP_TOTAL_WAIT_SECS = 7200  # Total time to wait for ripping before killing it.
RIP_EXTRA_WAIT_SECS = 10  # Extra time to wait after ripping is detected to be done.
RIP_POLL_SECS = 10  # Time to wait between polling the filesystem.

# Name of the ripping utility, spaces are removed because Python interprets a space
# in the string as the end of a given command.
RIPPER_NAME = Path("Image-BlockRippingUtility.exe")

# Inside the container, there's a specified directory where all Prairie View Ripping
# versions are held. The directory is called /apps/prairie_view/version#
RIPPER_DIRECTORY = Path("/apps/prairie_view/")

# The local scratch directory, called /scratch, is named as /temp/ in the container
# This is where the ripper will be writing data to.
SCRATCH_DIRECTORY = Path("/temp/")

# The data directory is where the raw data is located that needs conversion
# In the docker container, the specific directory being converted is mounted
# as /data/
DATA_DIRECTORY = Path("/data/")


class RippingError(Exception):
    """Error raised if problems encountered during data conversion."""


def raw_to_tiff(raw_dir: Path, ripper_version: str, num_images: int):
    """Convert Bruker RAW files to TIFF/.csv files using ripping utility specified with `ripper`.
    
    From the specified data directory, grabs the raw file lists, raw/unconverted data,
    and checks to ensure that no tiffs currently reside in output directory. Executes
    a subprocess that starts the ripper. The lab's naming convention has the Voltage Recording
    converted first, so the output directory is polled for size of the .csv being built. When
    the file size has remained the same between polls, the voltage conversion is detected as being
    completed. It will immediately begin converting the imaging data into tiffs and poll the file
    system for the number of tiffs in the output directory. Once the number of tiffs is the same
    as the expected number of images, the ripper detects that the conversion process is finished.
    This will kill the subprocess for ripping and start performing permission bit changes. Once this
    is completed, files will be moved or removed depending on their existence in the raw directory.
    Finally, after completion, the container will be destroyed.

    Args:
        raw_dir:
            Path to raw data that needs converting.
        ripper_version:
            Version of ripper to use, as in major.minor.64.minor (ie 5.6.64.200)
        num_images:
            Total number of images to poll for before killing the ripper.
    
    """

    # Generate full path and name for the ripper being used
    ripper = RIPPER_DIRECTORY / ripper_version / RIPPER_NAME

    # Generate full data directory for the raw data
    data_dir = DATA_DIRECTORY / raw_dir

    # Generate temporary directory on the scratch space on the machine
    tmp_tiff_dir = SCRATCH_DIRECTORY / raw_dir

    # Dat used for logger to state which path is being read from
    dat = str(data_dir)

    logger.info("Path available %s" % dat)

    # Get file lists
    def get_filelists():
        return list(sorted((data_dir).glob('*Filelist.txt')))

    # Get the raw data files
    def get_rawdata():
        return list(sorted((data_dir).glob('*RAWDATA*')))

    # Get the number of tiffs in the output directory
    def get_tiffs():
        return set((tmp_tiff_dir).glob('*.ome.tif'))

    def copy_back_files():
        """
        Copies back metadata files that Bruker copied to output directory.
        This helps preserve the input directory contents.
        """
        # Get list of paths in the output directory for files that are not tif files. These must be moved
        # back to their original directories
        paths_to_copy = [path for path in tmp_tiff_dir.iterdir() if not path.name.endswith("ome.tif")]
        
        # For each path in the list, if the path links to a file
        for path in paths_to_copy:
            if path.is_file():

                # Assign a temporary data directory for the file using the directory it would have originated from
                tmp_data_dir = data_dir / path.name

                # If the file exists in the original directory, the file would have been copied and not moved
                # by Bruker's ripper. Delete the file with unlink and log that it was done.
                if tmp_data_dir.exists():
                    logger.info("File was COPIED, not MOVED. Removing file...")
                    path.unlink()
                    logger.info("File deleted")
                
                # Otherwise, try moving the file and log any errors that occur in case an exception is thrown.
                else:
                    logger.info("Moving file: %s" % path)
                    try:
                        shutil.move(str(path), str(data_dir))
                        logger.info("File moved to origin")
                    except PermissionError:
                        logger.warning("Error: ", PermissionError.strerror)
                    except AttributeError:
                        logger.warning("Error: Attribute Error, likely 'PosixPath' object has no attribute 'rstrip'")
                        logger.warning("Check if paths were turned into strings in the shutil move call")
                    except:
                        logger.warning("Unknown error...")
            
            # If the path is a directory, it is likely a useless directory like the References directory which we don't
            # require. Log that it was found and try removing it. If removal fails, log that an error occurred.
            elif path.is_dir:
                try:
                    logger.info("Found directory, unlinking %s" % path)
                    shutil.rmtree(path)
                except OSError:
                    logger.warning("Error: ", OSError.strerror)
                except:
                    logger.warning("Unknown directory removal error...")


    filelists = get_filelists()

    if not filelists:
        raise RippingError('No *Filelist.txt files present in data directory')

    rawdata = get_rawdata()
    if not rawdata:
        raise RippingError('No RAWDATA files present in %s' % raw_dir)

    # The output directory should not have any tiffs present. If so, raise an exception and exit.
    tiffs = get_tiffs()
    if tiffs:
        raise RippingError('Cannot rip because tiffs already exist in %s (%d found)' % (raw_dir, len(tiffs)))

    logger.info('Ripping from:\n %s\n %s', '\n '.join([str(f) for f in filelists]),
                '\n '.join([str(f) for f in rawdata]))

    logger.info("Ripping to: %s" % tmp_tiff_dir)

    # If using the ripper on a Linux system, run Wine for converting Windows calls to Unix calls on the fly
    system = platform.system()
    if system == 'Linux':
        cmd = ['wine']
    else:
        cmd = []

    # Normally, the fname is passed to -AddRawFile.  But there is a bug in the software, so
    # we have to pop up one level and use -AddRawFileWithSubFolders.
    # The order of the commands in this list will tell the subprocess to:
    # 1. Execute the ripper
    # 2. Keep the raw data
    # 3. Do not rip to the input directory, instead rip to a different place
    # 4. Include the subfolder
    # 5. Add raw file with subfolders, as per bug above
    # 6. Provide the raw file directory as a string, it must be a string for it to work
    # 7. Set output directory
    # 8. Provide the output directory as a string, it must be a string for it to work
    # 9. Convert, which will tell the ripper to actually start the conversion process.

    cmd += [
        ripper,
        "-KeepRaw",
        "-DoNotRipToInputDirectory",
        "-IncludeSubFolders",
        "-AddRawFileWithSubFolders",
        str(data_dir),
        "-SetOutputDirectory",
        str(SCRATCH_DIRECTORY),
        "-Convert"
    ]

    # Run a subprocess to execute the ripping.  Note this is non-blocking because the
    # ripper never exists.  (If we blocked waiting for it, we'd wait forever.)  Instead,
    # we wait for the input files to be consumed and/or output files to be finished.
    process = subprocess.Popen(cmd)

    logger.info("Ripping has started!")

    # Given how filenames are created/named from Prairie View and Bruker Control, the
    # csv files are converted first. Because we started the ripper just before this point,
    # a csv file should now be present in the tmp_tiff_dir. We can poll the size of this
    # with os.stat(path).st_size after globbing it from the path

    # TODO: Ripping .csv and ripping tiffs should be their own functions inside this script
    # TODO: Should make a check to see if there are voltage recordings to convert. If there are,
    # the csv converter should be called. If not, it should be skipped.

    # It takes a few seconds for the ripper to get started and create the csv file
    # Sleep the program and get the csv file
    time.sleep(20)

    behavior_glob = tmp_tiff_dir.glob("*")

    # There are no other ways to generate a .csv in this process, so the only .csv
    # that's available is the correct one to poll
    behavior_csv = [file for file in behavior_glob][0]

    logger.info("Found .csv file for behavior: %s" % behavior_csv)

    # Create a flag for ripping the csv file, used in the while loop next
    ripping_csv = True

    # Get the size of the csv file
    behavior_csv_size = os.stat(behavior_csv).st_size

    logger.info("Voltage Recording .csv size: %s" % behavior_csv_size)

    # While the converter is ripping the .csv file
    while ripping_csv:

        # Wait the RIP_POLL_SECS delay before moving foward with the check
        time.sleep(RIP_POLL_SECS)

        # Get the latest csv file size
        new_behavior_csv_size = os.stat(behavior_csv).st_size

        logger.info("Voltage Recording .csv size: %s" % new_behavior_csv_size)

        # Check if the current size is the same as the previous size
        diff_csv_size = (behavior_csv_size != new_behavior_csv_size)

        # If the sizes are different
        if diff_csv_size:

            # The most recent size is assigned as the previous size
            behavior_csv_size = new_behavior_csv_size

            logger.info("Still ripping voltage recording...")
        
        # If the sizes are NOT different, the ripper is done with the .csv!
        # Exit the loop by setting ripping_csv to false
        else:

            ripping_csv = False
    
    logger.info("Voltage .csv Ripping Complete!")

    logger.info("Cleaning voltage recording into timestamps...")

    get_behavior_timestamps(behavior_csv)

    logger.info("Cleaned behavior file written!")

    # Register a cleanup function that will kill the ripping subprocess.  This handles the cases
    # where someone hits Cntrl-C, or the main program exits for some other reason.  Without
    # this cleanup function, the subprocess will just continue running in the background.
    def cleanup():
        timeout_sec = 5
        p_sec = 0
        for _ in range(timeout_sec):
            if process.poll() == None:
                time.sleep(1)
                p_sec += 1
        if p_sec >= timeout_sec:
            process.kill()
        logger.info('Cleaned up!')

    atexit.register(cleanup)

    remaining_sec = RIP_TOTAL_WAIT_SECS

    logger.info("Starting to rip tiff files...")

    while remaining_sec >= 0:
        logger.info('Watching for ripper to finish for %d more seconds', remaining_sec)
        remaining_sec -= RIP_POLL_SECS
        time.sleep(RIP_POLL_SECS)

        # get_tiffs returns set, meaning unique instances of, tiff paths
        tiffs = get_tiffs()

        # The length of this set is the number of images that have been converted.
        num_tiffs = len(tiffs)

        logging.info('  Found this many tiff files: %s', len(tiffs))

        # In order to use f string methods, we can't have empty brackets in the statement
        # which the bash command requires for executing the permission commands
        # Assuming there's a need to change permissions is a safe bet because not everyone in
        # the lab will have the 002 umask in their .login files  So we create a variable brackets
        # to use in the f string

        brackets = "{}"

        # If the number of tiffs converted is the same as the number of images expected, kill the
        # ripper.
        if num_tiffs == num_images:
            logger.info('Detected ripping is complete')
            time.sleep(RIP_EXTRA_WAIT_SECS)  # Wait before terminating ripper, just to be safe.
            logger.info('Killing ripper')
            process.kill()
            logger.info('Ripper has been killed')

            # Change permissions of the data so any SNLKT member can use them
            logger.info("Changing permissions of directory...")

            # Code 775 allows the owner and members of the group all permissions: read, write, and execute
            # Others are only allowed to read the directories
            dir_permissions_command = [f"find {tmp_tiff_dir} -type d -exec chmod 775 {brackets} +"]

            try:
                # Run the permissions change as a subprocess that uses the available Linux shell
                dir_permissions_status = subprocess.run(dir_permissions_command, capture_output=True, shell=True)
            
            except:
                logger.warning("Permissions subprocess failed: Directories")

            # A return code of 0 indicates that the subprocess completed without any errors. Log the success.
            if dir_permissions_status.returncode == 0:
                logger.info("Permissions for directory changed successfully")
            
            # Any other code indicates something went wrong. Log that and record the error that was encountered...
            else:
                logger.warning("Permissions change failed")
                logger.info(dir_permissions_status.stderr.decode())


            logger.info("Changing permissions of files in %s" % tmp_tiff_dir)

            # Code 664 allows owner and members of the group permissions to: read, write. Execute permissions are
            # unnecessary for these files because they are not executable (meaning you can't "execute" a .ome.tif)
            # Others can read the file but do nothing else.
            file_permissions_command = [f"find {tmp_tiff_dir} -type f -exec chmod 664 {brackets} +"]

            try:

                # Run the permissions change as a subprocess that uses the available Linux shell
                file_permissions_status = subprocess.run(file_permissions_command, capture_output=True, shell=True)

            except:
                logger.warning("Permissions subprocess failed: Files")

            if file_permissions_status.returncode == 0:
                logger.info("Permissions for file changed successfully")
            
            else:
                logger.warning("Permissions change failed: Files")
                logger.info(file_permissions_status.stderr.decode())

            try:
                logger.info("Copying events file and metadata back to raw_data directory...")
                copy_back_files()
            
            except:
                logger.warning("Unknown error")

            
            # Lastly, we want the folder to have "_tiffs" appended to it for clarity and for copying later
            # to the server.
            tmp_tiff_dir.rename(str(tmp_tiff_dir) + "_tiffs")


            return

    raise RippingError('Killed ripper because it did not finish within %s seconds' % RIP_TOTAL_WAIT_SECS)


def get_behavior_timestamps(behavior_csv: Path):
    """
    Cleans raw .csv file into timestamps.

    The ripper outputs a large .csv file that includes every sample that the DAQ takes regardless of
    the sample's value. There is no way to change this behavior so it only records timestamps. Therefore,
    we have to read in the file, get the start and stop times of the events, and then write out those
    timestamps to a new .csv file. This file will be written to the raw data's directory.

    Args:
        behavior_csv:
            Path to converted .csv file that has been converted and written to the machine's scratch space

    """

    # Output timestamps to the input directory and append _events to the filename
    output_filename = DATA_DIRECTORY / "_".join([behavior_csv.stem, "events.csv"])

    logger.info("Writing cleaned behavior file to: %s" % str(output_filename))

    # Read in the csv file and strip the columns of beginning space that Prairie View gives for some reason
    raw_behavior_df = pd.read_csv(behavior_csv, index_col="Time(ms)").rename(columns=lambda col:col.strip())

    # Anything below 2V in these files is certainly noise; remove them with this filter
    raw_behavior_df = raw_behavior_df > 2

    # Assign the datatypes to integer values, take the difference between neighboring values, and fill
    # any NaN values with 0s, although there shouldn't be any
    raw_behavior_df = raw_behavior_df.astype(int).diff().fillna(0)

    behavior_keys = []

    clean_behavior_dict = {}

    # Grab columns and create on/off keys for writing out timestamps later
    for key in raw_behavior_df.columns:

        behavior_keys.append("_".join([key, "on"]))
        behavior_keys.append("_".join([key, "off"]))

    # For each key, append values where there's a value of 1, meaning ON, to the ON keys
    # and where there's a value of -1 append to the OFF keys.
    for key in behavior_keys:
        if "on" in key:
            clean_behavior_dict[key] = raw_behavior_df.query(key.split("_")[0] + " == 1").index.tolist()
        else:
            clean_behavior_dict[key] = raw_behavior_df.query(key.split("_")[0] + " == -1").index.tolist()

    # Create new dataframe from the dictionary and transpose from rows to columns so .csv is written correctly
    output_dataframe = pd.DataFrame.from_dict(clean_behavior_dict, orient="index").transpose()

    output_dataframe.to_csv(output_filename)
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess 2-photon raw data into individual tiffs.')
    parser.add_argument('--directory',
                        type=str,
                        required=True,
                        help='Directory containing RAWDATA and Filelist.txt files for ripping.')
    parser.add_argument('--ripper_version',
                        type=str,
                        help='Prairie View version from environment file.')
    # TODO: Implement number of images check so it's not using time
    parser.add_argument('--num_images',
                        type=int,
                        required=True,
                        help='Total number of images to be converted for the recording.')
    parser.add_argument('--log_file',
                        type=str,
                        required=True,
                        dest="log",
                        help='Name of logfile for container.')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                    filename="/logs/" + args.log,
                    format='%(asctime)s.%(msecs)03d %(module)s:%(lineno)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


    logging.info("Container starting for %s" % args.directory)

    raw_to_tiff(args.directory, args.ripper_version, args.num_images)
