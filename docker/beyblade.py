# Jeremy Delahanty January 2022
# Assistance from Chris Roat, Stanford University Deisseroth Lab August 2021
# https://github.com/chrisroat
# https://github.com/deisseroth-lab/two-photon/
# Adapted for the Tye Lab by Jeremy Delahanty @ Salk Institute


from pathlib import Path
import lxml.etree
import subprocess
import re
import shutil
import os

# Import Tuple typing for typehints in documentation
from typing import Union

# The directory with all the different ripping versions is static on our server
RIPPER_DIRECTORY = Path("/snlkt/data/bruker_pipeline/docker/prairie_view/")

# The directory to look for files requiring conversion/transfer is static and located here
TRANSFER_DIRECTORY = Path("/snlkt/data/bruker_pipeline/raw_conversion")

# The directory for where executed conversions are stored is static and located here. This
# is where the raw path .txt file will go after the containers have been started.
EXECUTED_DIRECTORY = Path("/snlkt/data/bruker_pipeline/executed_conversion")

# TODO: Create something which will check for whether or not the conversion was successful
# or exited safely from the log files of previously executed. If the conversion failed for
# some reason, another job should be scheduled for that conversion if possible.


# TODO: Put checks for raw files/if tiffs or H5/zarrs exist already

class RippingError(Exception):
    """Error raised if problems encountered during data conversion."""


def xml_parser(xml_path: Path) -> lxml.etree._ElementTree:
    """
    Parse Prairie View's xml with lxml.

    Prairie View's xml that's contained in the .xml and .env files is
    inconsistent with versioning. Using lxml allows for use of a parser
    that can escape errors when it finds badly formed xml.

    Args:
        xml_path:
            Absolute path to the file needing to be parsed.
    
    Returns:
        Root of xml tree.
    """

    # Define lxml parser that's used for reading the tree with
    # recover=True so it can pass badly formed XML lines
    parser = lxml.etree.XMLParser(recover=True)

    # Get the "root" of the tree for parsing specific elements
    root = lxml.etree.parse(str(xml_path), parser).getroot()
    
    return root


def parse_env_file(raw_dir: Path) -> Union[str, int]:
    """
    Parse Prairie View .env file by calling xml_parser()

    Prairie View's .env file has a large quantity of metadata available inside
    that can be used when building NWB files, spawning converters, and for
    generally helpful information about the recording session. This will
    parse the environment file for spawning ripping containers later. If a
    matching ripper version is found by determine_ripper(), the version of the
    ripper is returned. If no version is found, determine_ripper() will throw an
    exception.

    Args:
        raw_dir:
            Directory to raw data that needs conversion.

    Returns:
        ripper:
            Ripper version as in major.minor.64.minor (ie 5.5.64.500).
        num_channels:
            Number of channels recorded from during the session.
    """

    # Generate list of environment files inside the raw directory
    env_files = [file for file in raw_dir.glob("*.env")]

    # An exception is thrown if more than one environment file is found. Something has gone wrong
    # if more than one is present.
    if len(env_files) != 1:
        raise RippingError("Only expected 1 env file in %s, but found: %s" % (raw_dir, env_files))

    # Get the root of xml tree
    root = xml_parser(env_files[0])

    # Get the version of the ripper required for file conversion
    ripper = determine_ripper(root)

    # Get the number of channels used during a recording
    num_channels = determine_channels(root)

    return ripper, num_channels


def determine_ripper(root: lxml.etree._ElementTree) -> str:
    """
    Grab the version of Prairie View used for conversion.

    The version of Prairie View that collected the data must
    be the exact same as the version of ripper and specifically
    'daq_int.dll' library. This will attempt to find the ripper in
    the prairie_view directory inside docker/. If it finds a matching
    version, it will grab the version number for use later. If it fails
    to find a matching version, an exception is raised.

    Args:
        root:
            Root of parsed xml tree
    
    Returns:
        ripper
    """

    # The version of Prairie View used for recording is found on the top
    # level of the .env file's xml tree and accessed through the attribute
    # 'version'
    version = root.attrib['version']

    # Assemble the full path for the ripper, should it exist
    ripper = RIPPER_DIRECTORY / f'{version}' / 'Image-BlockRippingUtility.exe'

    # If the path generated returns None, a matching ripper was not found.
    # Throw an exception.
    if ripper is None:
        raise RippingError("Could not find matching ripper!")

    # If the ripper version was found, grab the version number for the
    # ripping utility which is the parent directory of the executable
    else:
        ripper = ripper.parent.name

    return ripper

def determine_channels(root: lxml.etree._ElementTree) -> int:
    """
    Determine the number of channels used during a given recording.

    The number of channels used will determine the number of images that
    come out of the conversion process. This number is used later in the container
    for killing the ripper when the number of tiffs found equals the number of 
    expected images. However many number of images were collected is multiplied
    by the value found here to calculate the total number of images to expect.

    Args:
        root:
            Root of parsed xml tree
    
    Returns:
        channels:
            Number of channels recorded from during an imaging session.

    """
    
    # The xpath to the channel attributes in a recording are found here
    xpath = ".//PVStateValue[@key='channel']"

    # Search the tree for this specific xpath
    element = root.find(xpath)

    #TODO: If this fails for some reason, an exception should be thrown probably...

    # Bruker doesn't encode boolean values in their XML for these tags, so they must be evaluated
    # as strings. If the channel was active during the recording, append that channel index to
    # the list of used channels. Finally, get the length of the number of channels used to determine
    # the number of channels recorded from during the session.
    channels = len([channel.attrib["index"] for channel in element if channel.attrib["value"] == "True"])

    return channels


def determine_num_images(raw_dir: Path, num_channels: int) -> int:
    """
    Determine the number of images the ripper should expect to convert.

    The ripping subprocess will continue to run until the script polling the
    output directory reaches the number of expected tiffs. So this value is used
    in a while loop during the ripping process until the conversion is complete.
    The raw directory is used again in this function because it is the main .xml
    file that is parsed and not the .env file, which is parsed earlier.

    Args:
        raw_dir:
            Directory to raw data that needs conversion.
        num_channels:
            Number of channels used during a recording
    
    Returns:
        num_images

    """

    # Prairie View outputs the main .xml file as the name of the recording
    # Grab the directory's name and append .xml to it.
    dir_glob_pattern = raw_dir.name + ".xml"

    # Get a list of the xml files matching this pattern 
    xml_files = [file for file in raw_dir.glob(dir_glob_pattern)]

    # There should be only 1 xml file with this exact name. If there's not just one, something is
    # wrong. Throw an exception if this happens.
    if len(xml_files) != 1:
        raise RippingError("Expected 1 recording XML file in %s, but found: %s" % (raw_dir, xml_files))

    # Get the root of the main .xml file
    root = xml_parser(xml_files[0])

    # Navigate on the recording's xml root path to the last
    # frame collected. Using the last() method gets you the
    # final entry of that particular xpath.
    last_frame = root.xpath("Sequence/Frame[last()]")

    # Parse the xml element for index of this final frame.
    # The Sequence/Frame xpath is a tuple, so access the tuple
    # with [0] and get the index of the last frame. Multiply this
    # value by the number of channels to get total number of
    # images that were collected.
    num_images = int(last_frame[0].attrib["index"] * num_channels)

    return num_images

def get_raw_data(recording_list_dir: Path) -> list:
    """
    Get the raw data that needs conversion.

    A .txt file is generated when the file transfer from the local
    Bruker machine is completed. This contains the paths of the microscopy
    recordings that were completed for that day. `get_raw_data()` will
    grab this file and parse it to make a list of directories that needs
    converting. These will be passed to a subprocess that spawns the
    containers one by one.

    Args:
        recording_list_dir:
            Directory where datasets needing conversion in a txt file are held
    
    Returns:
        raw_dirs
    """

    # Get text file used for converting the recordings.
    recordings = [file for file in recording_list_dir.glob("*.txt")]

    # Create empty list to read directories into from the txt file
    raw_dirs = []

    # Read each text file found in the recordings
    for file in recordings:

        # Open the files and read each line for the directory needing conversion
        with open(file, "r") as f:
            for path in f:
                # Use rstrip to remove trailing characters at the
                # end of each path. Creating files for conversion
                # using text editors/shell scripting yields newlines (\n)
                # when read into Python's open function it seems...
                directory = Path(path.rstrip("\n"))
                raw_dirs.append(directory)
                
    return raw_dirs


# Main function
if __name__ == "__main__":

    # Gather the list of directories needing conversion.
    conversion_list = get_raw_data(TRANSFER_DIRECTORY)

    # For each directory in the list, determine the ripper, number of channels
    # recorded from, number of images to expect, and the date of the recording session.
    for directory in conversion_list:

        ripper, num_channels = parse_env_file(directory)
        num_images = determine_num_images(directory, num_channels)
        recording_date = directory.parents[0].name

        # Try searching for a plane number. If none exists for some reason,
        # give the plane number a value of zero.
        try:
            plane_number = re.search("plane\d", directory.name).group()

        except AttributeError:
            
            plane_number = "0"

        # Generate the name of the container that will be spawned. Each container must have a unique name.
        # The names generated will be: AnimalName-Plane#-RecordingDateYYYYMMDD-SNLKT-ripper
        # Example: CSE012-plane1-20211112-SNLKT-ripper
        container_name = "-".join([directory.parents[1].name, plane_number, recording_date, "SNLKT-ripper"])

        # Create a list of commands and arguments the subprocess will execute. The commmand is build_container.sh.
        # It has the following arguments:
        # 1: Animal Name, plane, and date used for the ripper container name
        # 2: Directory of raw data
        # 3: Truncated name for appending to /data/ directory in container.
        # 4: Version of ripper to use
        # 5: Total number of images the container should expect to find when conversion is finished.

        cmd = ["docker/build_container.sh %s %s %s %s %s" % (container_name, str(directory.parent), directory.name, ripper, num_images)]

        process = subprocess.Popen(cmd, shell=True)

        print("Starting container for:", container_name)

    # Once the containers have been started, move the raw file conversion .txt file to the executed
    # directory on the server.

    # Get the list of files in the transfer directory
    # TODO: Should get_raw_data() also return this list? Seems unnecessary to do this again...
    executed_conversions = os.listdir(TRANSFER_DIRECTORY)
 
    # Once the containers have all been started, move the conversion file list to the executed
    # file directory.
    for file in executed_conversions:

        # Shutil expects the paths to be converted into strings for transferring it seems, but not
        # for the path it's supposed to move the files to...
        shutil.move(str(TRANSFER_DIRECTORY / file), EXECUTED_DIRECTORY)
