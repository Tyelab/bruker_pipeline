from pathlib import Path
from attr import Attribute
import lxml.etree
import subprocess
import re

from matplotlib import container

RIPPER_DIRECTORY = Path("/snlkt/data/bruker_pipeline/docker/prairie_view/")
TRANSFER_DIRECTORY = Path("/snlkt/data/bruker_pipeline/docker")


# TODO: Put checks for raw files/if tiffs or H5/zarrs exist already

class RippingError(Exception):
    """Error raised if problems encountered during data conversion."""

def xml_parser(xml_path: Path) -> lxml.etree._ElementTree:
    """
    Parse xml files with lxml.
    """

    # Define lxml parser that's used for reading the tree with
    # recover=True so it can pass badly formed XML lines
    parser = lxml.etree.XMLParser(recover=True)

    # Get the "root" of the tree for parsing specific elements
    root = lxml.etree.parse(str(xml_path), parser).getroot()
    
    return root

def parse_env_file(raw_dir):

    env_files = [file for file in raw_dir.glob("*.env")]

    if len(env_files) != 1:
        raise RippingError("Only expected 1 env file in %s, but found: %s" % (raw_dir, env_files))

    root = xml_parser(env_files[0])

    ripper = determine_ripper(root)

    num_channels = determine_channels(root)

    return ripper, num_channels


def determine_ripper(root):

    version = root.attrib['version']

    ripper = RIPPER_DIRECTORY / f'{version}' / 'Image-BlockRippingUtility.exe'

    if ripper is None:
        raise RippingError("Could not find matching ripper!")

    return ripper

def determine_channels(root):
    
    xpath = ".//PVStateValue[@key='channel']"
    element = root.find(xpath)

    # Bruker doesn't encode boolean values in their XML for these tags, so they must be evaluated
    # as strings. If the channel was active during the recording, append that channel index to
    # the list of used channels.
    channels = len([channel.attrib["index"] for channel in element if channel.attrib["value"] == "True"])

    return channels


def determine_num_images(raw_dir, num_channels):

    dir_glob_pattern = raw_dir.name + ".xml"

    xml_files = [file for file in raw_dir.glob(dir_glob_pattern)]

    if len(xml_files) != 1:
        raise RippingError("Expected 1 recording XML file in %s, but found: %s" % (raw_dir, xml_files))

    root = xml_parser(xml_files[0])

    # Navigate on the recording's xml root path to the last
    # frame collected
    last_frame = root.xpath("Sequence/Frame[last()]")

    # Parse the xml element for index of this final frame and multiply
    # this value by the number of channels to get total number of
    # images that were collected.
    num_images = int(last_frame[0].attrib["index"] * num_channels)

    return num_images

def get_raw_data(recording_list_dir: Path) -> list:

    recordings = [file for file in recording_list_dir.glob("*.txt")]

    raw_dirs = []

    for file in recordings:
        with open(file, "r") as f:
            for path in f:
                # Use rstrip to remove trailing characters at the
                # end of each path. Creating files for conversion
                # using text editors yields newlines (\n)
                # when read into Python's open function it seems.
                directory = Path(path.rstrip("\n"))
                raw_dirs.append(directory)
                
    return raw_dirs

# Command order: build_container.sh which is the shell script that actually puts the container together
# Args:
# 1: Animal Name and plane used for the ripper container name
# 2: Directory of raw data
# 3: Truncated name for appending to /data/ directory in container.
# 4: Version of ripper to use
# 5: Total number of images the container should expect to find when conversion is finished.


if __name__ == "__main__":

    conversion_list = get_raw_data(TRANSFER_DIRECTORY)

    for directory in conversion_list:

        ripper, num_channels = parse_env_file(directory)
        num_images = determine_num_images(directory, num_channels)

        try:
            plane_number = re.search("plane\d", directory.name).group()

        except AttributeError:
            
            plane_number = "0"

        container_name = "-".join([directory.parents[1].name, plane_number, "SNLKT-ripper"])

        cmd = ["docker/build_container.sh %s %s %s %s %s" % (container_name, str(directory.parent), directory.name, ripper.parent.name, num_images)]

        process = subprocess.Popen(cmd, shell=True)

        print("Starting container for:", container_name)

