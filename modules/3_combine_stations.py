"""
Concatenates individual raw_data.csv files for each station into one combined file for all stations.
Designed to run daily as part of the master script and must run after the parser.

This script:
  - Combines all raw_data.csv files from station subfolders (data/<station>/raw_data.csv)
  - Saves the merged file in data/ALL_STATIONS/ with a timestamp.
  - Cleans the data by:
      * Removing rows that only contain a station identifier (i.e. every column except 'Station' is missing)
      * Dropping duplicate rows
      * Selecting only the desired columns and applying a new header list (based on the observation dictionary)
      * Filtering out rows with invalid dates (if possible)
"""

import os
import pandas as pd
from datetime import datetime


def combine_pns_metadata():
    # Define paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Project root
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(data_dir, "ALL_STATIONS")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate a timestamped filename for the combined file
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_filename = f"all_stations_{timestamp}.csv"
    output_path = os.path.join(output_dir, output_filename)

    # List to store DataFrames from each station file
    all_data = []

    # For each folder in the data directory, look for a raw_data.csv file.
    for folder in os.listdir(data_dir):
        station_file = os.path.join(data_dir, folder, "raw_data.csv")
        if os.path.isfile(station_file):
            try:
                # Read the CSV with no header, all as string
                df = pd.read_csv(station_file, header=None, dtype=str)
                # Select only the columns corresponding to the observation dictionary.
                # Based on your observation definition:
                # row[0] = date, row[1] = time, row[2] = state, row[3] = county,
                # row[4] = city, row[7] = latitude, row[8] = longitude,
                # row[9] = type, row[10] = value, row[11] = unit, row[12] = source, row[13] = description.
                # This selects 12 columns.
                df = df.iloc[:, [0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13]]
                # Add a "Station" column
                df["Station"] = folder
                all_data.append(df)
                print(f"✅ Loaded {station_file}")
            except Exception as e:
                print(f"❌ Error reading {station_file}: {e}")

    # Combine all station data if any files were loaded
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        # Replace empty strings with NA (to standardize missing data)
        combined_df = combined_df.replace(r'^\s*$', pd.NA, regex=True)

        # Remove rows that only contain a station identifier (i.e. every column except 'Station' is missing)
        if "Station" in combined_df.columns:
            mask_identifier_only = combined_df.drop(columns=["Station"]).isna().all(axis=1)
            combined_df = combined_df[~mask_identifier_only]
        else:
            print("⚠️ 'Station' column not found. Skipping row removal based on identifier.")

        # Remove duplicate rows
        combined_df = combined_df.drop_duplicates()

        # Define new headers based on your observation dictionary and the Station column.
        # Order: date, time, state, county, city, latitude, longitude, type, value, unit, source, description, Station
        new_headers = [
            "date", "time", "state", "county", "city", "latitude", "longitude",
            "type", "value", "unit", "source", "description", "Station"
        ]
        if combined_df.shape[1] == len(new_headers):
            combined_df.columns = new_headers
        else:
            print(f"⚠️ Warning: Expected {len(new_headers)} columns but found {combined_df.shape[1]}. Headers not applied.")

        # Filter out rows that appear to be text notes by checking if the "date" column can be parsed.
        if "date" in combined_df.columns:
            combined_df["date_parsed"] = pd.to_datetime(combined_df["date"],
                                                        errors="coerce",
                                                        infer_datetime_format=True)
            before_count = len(combined_df)
            combined_df = combined_df[combined_df["date_parsed"].notna()]
            after_count = len(combined_df)
            filtered_count = before_count - after_count
            if filtered_count:
                print(f"Filtered out {filtered_count} text rows based on invalid dates in 'date' column.")
            combined_df = combined_df.drop(columns=["date_parsed"])
        else:
            print("⚠️ 'date' column not found. Skipping date filtering.")

        # Save the combined and cleaned file
        combined_df.to_csv(output_path, index=False)
        print(f"✅ Combined PNS metadata saved as: {output_path}")
    else:
        print("⚠️ No valid PNS metadata files found.")

def cleanup_debug_files(base_dir):
    """Deletes all debug_html files in the project directory."""
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file == "debug_html":
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"🗑️ Deleted: {file_path}")
                except Exception as e:
                    print(f"❌ Error deleting {file_path}: {e}")

    # Call function to delete debug_html files
    cleanup_debug_files(base_dir)

if __name__ == "__main__":
    combine_pns_metadata()