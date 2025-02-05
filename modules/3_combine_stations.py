"""
Concatonates individual files for each station into one for all stations
designed to run daily as part of master script
it is important that it runs after parser
"""

import os
import pandas as pd
from datetime import datetime


def combine_pns_metadata():
    """
    Combines all `pns_metadata.csv` files from station subfolders (data/<station>/raw_metadata/)
    and saves the merged file in data/ALL_STATIONS/ with a timestamp.

    Cleaning steps include:
      - Removing rows that only contain a station identifier (i.e. every column except 'Station' is missing)
      - Dropping duplicate rows
      - Renaming the columns to a specified header list
      - Dropping rows that appear to be text notes (e.g. rows with invalid dates in the "Date" column)
      - Dropping the first column ("METADATA") since it is blank for all rows
    """
    # Define paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Root of the project
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(data_dir, "ALL_STATIONS")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_filename = f"all_stations_pns_data_{timestamp}.csv"
    output_path = os.path.join(output_dir, output_filename)

    # List to store all DataFrames
    all_data = []

    # Scan the data directory for station folders and load each metadata CSV
    for folder in os.listdir(data_dir):
        station_path = os.path.join(data_dir, folder, "raw_metadata", "pns_metadata.csv")
        if os.path.exists(station_path):
            try:
                df = pd.read_csv(station_path)
                df["Station"] = folder  # Add or update the station identifier column
                all_data.append(df)
                print(f"✅ Loaded {station_path}")
            except Exception as e:
                print(f"❌ Error reading {station_path}: {e}")

    # Combine all station data into a single DataFrame if any data was found
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        # Replace empty strings with NA (to standardize missing data)
        combined_df = combined_df.replace(r'^\s*$', pd.NA, regex=True)

        # Remove rows that only contain a station identifier (i.e. every column except 'Station' is missing)
        mask_identifier_only = combined_df.drop(columns=["Station"]).isna().all(axis=1)
        combined_df = combined_df[~mask_identifier_only]

        # Remove duplicate rows
        combined_df = combined_df.drop_duplicates()

        # Define new headers.
        # These headers correspond to the desired CSV header:
        # METADATA,Station,Date,Time,ST,City,County,,,Lat,Long,Report_Type,Amount,Amount_Unit,Source,Report_type,,
        new_headers = [
            "METADATA", "Station", "Date", "Time", "ST", "City", "County",
            "", "", "Lat", "Long", "Report_Type", "Amount", "Amount_Unit",
            "Source", "Report_type", "", ""
        ]
        if len(combined_df.columns) == len(new_headers):
            combined_df.columns = new_headers
        else:
            print("⚠️ Warning: Column count mismatch. Headers not applied.")

        # Filter out rows that appear to be text notes by checking for a valid Date.
        # Any row where the "Date" column cannot be parsed is dropped.
        if "Date" in combined_df.columns:
            combined_df["Date_parsed"] = pd.to_datetime(combined_df["Date"],
                                                        errors="coerce",
                                                        infer_datetime_format=True)
            before_count = len(combined_df)
            combined_df = combined_df[combined_df["Date_parsed"].notna()]
            after_count = len(combined_df)
            filtered_count = before_count - after_count
            if filtered_count:
                print(f"Filtered out {filtered_count} text rows based on invalid dates in 'Date' column.")
            combined_df = combined_df.drop(columns=["Date_parsed"])
        else:
            print("⚠️ 'Date' column not found. Skipping text row filtering based on date.")

        # Drop the first column ("METADATA") since it is blank for all rows
        if "METADATA" in combined_df.columns:
            combined_df = combined_df.drop(columns=["METADATA"])

        # Save the combined and cleaned file
        combined_df.to_csv(output_path, index=False)
        print(f"✅ Combined PNS metadata saved as: {output_path}")
    else:
        print("⚠️ No valid PNS metadata files found.")


if __name__ == "__main__":
    combine_pns_metadata()