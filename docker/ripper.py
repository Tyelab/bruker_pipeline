# Bruker Image Ripping Utility Main Function
# Bruker Image Ripping Utility written by Bruker Microscopy
# Code written by Chris Roat, Deisseroth Lab @ Stanford University
# https://github.com/chrisroat
# https://github.com/deisseroth-lab/two-photon/blob/main/two_photon/
# Adapted for the Tye Lab @ The Salk Institute by Jeremy Delahanty October 2021

__version__ = "0.0.1"

# Import rip_utils to run ripping procedures
import rip_utils

# Import argparse for runtime control
import argparse

# Import pathlib for creating valid choices for teams
from pathlib import Path

# Static directory for teams in the raw directory of Docker Container
# teams_path = Path("/data/")

# Make list of authorized teams that can use the Bruker Scope for imaging
# authorized_teams = ["specialk", "Deryn"]

# Generate valid team choices for argparser variable "team" by checking the
# directories accessible to the container
# team_choices = [
#     team.name for team in teams_path.glob("*") if team.name in authorized_teams
# ]

###############################################################################
# Main Function
###############################################################################


if __name__ == "__main__":

    # Create argument parser processing raw files
    rip_parser = argparse.ArgumentParser(
        description="Perform Bruker Raw Image Ripping",
        epilog="Let it rip!",
        prog="Bruker Image Ripping Utility"
        )
        
    # Add project name argument
    rip_parser.add_argument(
        '-p', '--project',
        type=str,
        action='store',
        dest='project',
        help='Project Name ie. specialk_cs (Required)',
        required=True
    )

    rip_parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s v.' + __version__
    )

    rip_args = vars(rip_parser.parse_args())

    rip_utils.rip(rip_args)
