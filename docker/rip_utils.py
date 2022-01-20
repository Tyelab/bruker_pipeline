import re
import xml.etree.ElementTree as ET
from pathlib import Path
import atexit
import platform
import subprocess
import time
import logging
import lxml.etree
import sys

BASE_PATH = Path("/data/specialk/lh/2p/LHE042/20211009/20211009_LHE042_plane1_-336.525_raw-102")
RIPPER_PATH = Path("/apps/prairie_view/")

local_path = Path("C:/Users/jdelahanty.SNL/Desktop/test_env/")

logger = logging.getLogger(__name__)

# Ripping process does not end cleanly, so the filesystem is polled to detect the
# processing finishing.  The following variables relate to the timing of that polling
# process.
RIP_TOTAL_WAIT_SECS = 3600  # Total time to wait for ripping before killing it.
RIP_EXTRA_WAIT_SECS = 10  # Extra time to wait after ripping is detected to be done.
RIP_POLL_SECS = 10  # Time to wait between polling the filesystem.


class RippingError(Exception):
    """Error raised if problems encountered during data conversion."""

def rip_images(rip_args: dict):
    """
    Unites ripping functions together to perform Raw Image Ripping

    Takes functions within rip_utils.py and puts them into one function that
    is called in the __main__ script.

    Args:
        rip_args:
            Arguments from command line used to determine which team and
            project will be processed.
    """

    project = rip_args["project"]

    # needs_conversion = conversion_check(project)

    ripper = determine_ripper(BASE_PATH, RIPPER_PATH)

    # raw_to_tiff(needs_conversion[0], ripper)

def determine_ripper(data_dir, ripper_dir):
    """Determine which version of the Prairie View ripper to use based on reading metadata."""
    env_files = [path for path in data_dir.glob('*.env')]
    print(env_files)

    if len(env_files) != 1:
        raise RippingError('Only expected 1 env file in %s, but found: %s' % (data_dir, env_files))

    try:

        tree = ET.parse(str(env_files[0]))
        root = tree.getroot()
    
    except ET.ParseError:

        print("Caught exception")

        parser = lxml.etree.XMLParser(recover=True)
        root = lxml.etree.parse(str(env_files[0]), parser).getroot()

    
    version = root.attrib['version']

    print(version)

    sys.exit()


    # Prairie View versions are given in the form A.B.C.D.
    match = re.match(r'^\d+\.\d+\.\d+\.\d+$', version)

    if not match:
        raise RippingError('Could not parse version (expected A.B.C.D): %s' % version)

    version = match.group(0)

    # For some reason f string doesn't work here, so this string is built in the version line above
    ripper = ripper_dir / version / 'Utilities' / 'Image-Block Ripping Utility.exe'

    logger.info('Data created with Prairie version %s, using ripper: %s', version, ripper)

    return ripper

def raw_to_tiff(dirname, ripper):
    """Convert Bruker RAW files to TIFF files using ripping utility specified with `ripper`."""
    def get_filelists():
        return list(sorted(dirname.glob('*Filelist.txt')))

    def get_rawdata():
        return list(sorted(dirname.glob('*RAWDATA*')))

    def get_tiffs():
        return set(dirname.glob('tiffs/*.ome.tif'))

    filelists = get_filelists()
    if not filelists:
        raise RippingError('No *Filelist.txt files present in data directory')

    rawdata = get_rawdata()
    if not rawdata:
        raise RippingError('No RAWDATA files present in %s' % dirname)

    tiffs = get_tiffs()
    if tiffs:
        raise RippingError('Cannot rip because tiffs already exist in %s (%d found)' % (dirname, len(tiffs)))

    logger.info('Ripping from:\n %s\n %s', '\n '.join([str(f) for f in filelists]),
                '\n '.join([str(f) for f in rawdata]))

    print(logger)
    system = platform.system()
    if system == 'Linux':
        cmd = ['wine']
    else:
        cmd = []

    # Normally, the fname is passed to -AddRawFile.  But there is a bug in the software, so
    # we have to pop up one level and use -AddRawFileWithSubFolders.
    cmd += [
        ripper,
        "-KeepRaw",
        "-DoNotRipToInputDirectory",
        "-IncludeSubFolders",
        "-AddRawFileWithSubFolders",
        str(dirname.parent),
        "-SetOutputDirectory",
        dirname.name + "/tiffs",
        "-Convert",
    ]

    # Run a subprocess to execute the ripping.  Note this is non-blocking because the
    # ripper never exists.  (If we blocked waiting for it, we'd wait forever.)  Instead,
    # we wait for the input files to be consumed and/or output files to be finished.
    process = subprocess.Popen(cmd)

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
        logger.info('cleaned up!')

    atexit.register(cleanup)

    # Wait for the file list and raw data to disappear
    remaining_sec = RIP_TOTAL_WAIT_SECS
    last_tiffs = {}
    while remaining_sec >= 0:
        logging.info('Watching for ripper to finish for %d more seconds', remaining_sec)
        remaining_sec -= RIP_POLL_SECS
        time.sleep(RIP_POLL_SECS)

        filelists = get_filelists()
        rawdata = get_rawdata()

        tiffs = get_tiffs()
        tiffs_changed = (last_tiffs != tiffs)
        last_tiffs = tiffs

        logging.info('  Found filelist files: %s', filelists or None)
        logging.info('  Found rawdata files: %s', rawdata or None)
        logging.info('  Found this many tiff files: %s', len(tiffs))

        if not filelists and not rawdata and not tiffs_changed:
            logging.info('Detected ripping is complete')
            time.sleep(RIP_EXTRA_WAIT_SECS)  # Wait before terminating ripper, just to be safe.
            logging.info('Killing ripper')
            process.kill()
            logging.info('Ripper has been killed')
            return

    raise RippingError('Killed ripper because it did not finish within %s seconds' % RIP_TOTAL_WAIT_SECS)


def conversion_check(project: str) -> list:

    raw_path = BASE_PATH / project

    raw_paths = [
        path for path in raw_path.glob("*/*_raw") if path.is_dir()
    ]

    has_tiffs = [
        path.parent for path in raw_path.glob("*/*_raw*/tiffs")
    ]

    needs_conversion = list(set(raw_paths) - set(has_tiffs))

    return needs_conversion
