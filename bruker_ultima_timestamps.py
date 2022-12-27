# CSV From Bruker to Events Timestamps

from pathlib import Path
import pandas as pd
import os

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
    output_filename = behavior_csv.parent / "_".join([behavior_csv.stem, "events.csv"])

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

    # File must be run inside the staging area. cd to that location and then run it
    staging_directory = os.getcwd()

    # Get list of files from csv staging "to_be_processed" folder, somewhere similar

    raw_csvs = [file for file in staging_directory.glob("*.csv")]

    for file in raw_csvs:

        get_behavior_timestamps(file)