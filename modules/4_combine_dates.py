# combines all data from each dated file with all station data into one master file with all dates
# it is important that this runs after the script that combines the station data
# this also has to run after the data is parsed (parsed_data) and scraped (scraper)

import os
import pandas as pd


def accumulate_all_data():
    """
    Accumulates all station CSV files into a master CSV file named "all_stations_all_dates.csv".

    This script looks in the "data/ALL_STATIONS" directory, loads all CSV files (excluding the master file),
    and if a master file already exists, loads it as well. It then concatenates all the data,
    eliminates duplicate rows, and writes the accumulated data back to the master CSV file.

    All CSV files are assumed to share the same format.
    """
    # Define the base directory (project root) and the ALL_STATIONS directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    all_stations_dir = os.path.join(base_dir, "data", "ALL_STATIONS")

    # Define the path for the master file
    master_file = os.path.join(all_stations_dir, "all_stations_all_dates.csv")

    # List to accumulate DataFrames
    all_dfs = []

    # If the master file exists, load it first so we include previously accumulated data
    if os.path.exists(master_file):
        try:
            master_df = pd.read_csv(master_file)
            all_dfs.append(master_df)
            print(f"Loaded existing master file: {master_file}")
        except Exception as e:
            print(f"Error reading master file {master_file}: {e}")

    # Look for all CSV files in the directory (excluding the master file)
    for filename in os.listdir(all_stations_dir):
        if filename.endswith(".csv") and filename != "all_stations_all_dates.csv":
            file_path = os.path.join(all_stations_dir, filename)
            try:
                df = pd.read_csv(file_path)
                all_dfs.append(df)
                print(f"Loaded file: {file_path}")
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

    # Combine all DataFrames if any are found
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        # Remove duplicate rows
        combined_df = combined_df.drop_duplicates()

        # Write the combined, de-duplicated DataFrame back to the master file
        combined_df.to_csv(master_file, index=False)
        print(f"Accumulated data saved to master file: {master_file}")
    else:
        print("No CSV files found to accumulate.")


if __name__ == "__main__":
    accumulate_all_data()