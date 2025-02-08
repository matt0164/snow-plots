"""
Concatenates individual files for each station into a single file for all stations.
Designed to run daily as part of the master script.
It is important that it runs AFTER the parser script.
"""

from pathlib import Path
import pandas as pd
from datetime import datetime
import logging


def setup_logging():
    """
    Sets up logging for the script.
    """
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(logs_dir / "combine_pns_metadata.log", mode="a", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


def combine_pns_metadata():
    """
    Combines all `pns_metadata.csv` files from station subfolders (data/<station>/raw_metadata/)
    and saves the merged file into data/ALL_STATIONS/ with a timestamp.

    Steps:
    - Reads individual station files (pns_metadata.csv) and combines them.
    - Cleans the data:
        - Removes rows with only a station identifier.
        - Drops duplicates.
        - Renames columns based on a specified header list.
        - Filters rows with invalid dates in the "Date" column.
        - Drops the "METADATA" column if blank.
    - Saves the combined file into the "ALL_STATIONS" directory with a timestamp.
    """
    # Paths
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    output_dir = data_dir / "ALL_STATIONS"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Timestamp for the output filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_file = output_dir / f"all_stations_pns_data_{timestamp}.csv"

    # List to store all DataFrames
    all_data = []

    # Scan the "data" directory for station subfolders with pns_metadata.csv
    for folder in data_dir.iterdir():
        station_file = folder / "raw_metadata" / "pns_metadata.csv"
        if station_file.is_file():
            try:
                df = pd.read_csv(station_file, encoding="utf-8")
                df["Station"] = folder.name  # Add "Station" column to identify the station
                all_data.append(df)
                logging.info(f"✅ Loaded {station_file}")
            except Exception as e:
                logging.error(f"❌ Error reading {station_file}: {e}")

    # Combine all DataFrames if data exists
    if all_data:
        try:
            combined_df = pd.concat(all_data, ignore_index=True)
            logging.info("✅ Successfully combined all station files.")

            # Data cleaning
            combined_df = combined_df.replace(r'^\s*$', pd.NA, regex=True)  # Replace empty strings with NA

            # Remove rows with only a station identifier
            mask_identifier_only = combined_df.drop(columns=["Station"]).isna().all(axis=1)
            combined_df = combined_df[~mask_identifier_only]
            logging.info(f"✅ Removed rows with only a 'Station' identifier.")

            # Remove duplicate rows
            before_dedup = len(combined_df)
            combined_df = combined_df.drop_duplicates()
            logging.info(f"✅ Removed {before_dedup - len(combined_df)} duplicate rows.")

            # Rename columns to match desired headers
            new_headers = [
                "METADATA", "Station", "Date", "Time", "ST", "City", "County",
                "", "", "Lat", "Long", "Report_Type", "Amount", "Amount_Unit",
                "Source", "Report_type", "", ""
            ]
            if len(combined_df.columns) == len(new_headers):
                combined_df.columns = new_headers
                logging.info("✅ Renamed columns to match desired headers.")
            else:
                logging.warning("⚠️ Column count mismatch. Headers were not applied.")

            # Filter out rows with invalid dates in the "Date" column
            if "Date" in combined_df.columns:
                combined_df["Date_parsed"] = pd.to_datetime(
                    combined_df["Date"], errors="coerce", infer_datetime_format=True
                )
                before_filter = len(combined_df)
                combined_df = combined_df[combined_df["Date_parsed"].notna()]
                logging.info(f"✅ Removed {before_filter - len(combined_df)} rows with invalid dates.")
                combined_df = combined_df.drop(columns=["Date_parsed"])
            else:
                logging.warning("⚠️ 'Date' column not found. Skipping date filtering.")

            # Drop "METADATA" column if it exists and is blank
            if "METADATA" in combined_df.columns:
                combined_df = combined_df.drop(columns=["METADATA"])
                logging.info("✅ Dropped 'METADATA' column.")

            # Save combined file
            combined_df.to_csv(output_file, index=False, encoding="utf-8")
            logging.info(f"✅ Combined PNS metadata saved as: {output_file}")

        except Exception as e:
            logging.error(f"❌ Error during combination and cleaning: {e}")
    else:
        logging.warning("⚠️ No valid PNS metadata files found to combine.")


if __name__ == "__main__":
    setup_logging()
    combine_pns_metadata()
