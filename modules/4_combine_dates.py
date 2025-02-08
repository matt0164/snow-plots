"""
Combines all data from each dated file with all station data into one master file with all dates.
It is important that this runs after the script that combines station data.
This also has to run after the data is parsed (parsed_data) and scraped (scraper).
"""

from pathlib import Path
import pandas as pd
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
            logging.FileHandler(logs_dir / "accumulate_all_data.log", mode="a", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


def accumulate_all_data():
    """
    Accumulates all station CSV files into a master CSV file named "all_stations_all_dates.csv".

    The script scans the "data/ALL_STATIONS" directory, loads all station-specific CSV files 
    (excluding the master file), and if a master file already exists, loads it as well. Then, it:
      - Combines all data into a single DataFrame.
      - Removes duplicate rows.
      - Writes the accumulated data back to the master CSV file.

    All input CSV files are assumed to share the same format.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    all_stations_dir = base_dir / "data" / "ALL_STATIONS"
    master_file = all_stations_dir / "all_stations_all_dates.csv"

    # Ensure the output directory exists
    all_stations_dir.mkdir(parents=True, exist_ok=True)

    # Collect DataFrames
    all_dfs = []

    # Load the existing master file if it exists
    if master_file.exists():
        try:
            master_df = pd.read_csv(master_file, encoding="utf-8")
            all_dfs.append(master_df)
            logging.info(f"Loaded existing master file: {master_file}")
        except Exception as e:
            logging.error(f"Error reading master file {master_file}: {e}")

    # Process each CSV file in the directory excluding the master file
    for csv_file in all_stations_dir.glob("*.csv"):
        if csv_file.name != "all_stations_all_dates.csv":
            try:
                df = pd.read_csv(csv_file, encoding="utf-8")
                all_dfs.append(df)
                logging.info(f"Loaded file: {csv_file}")
            except Exception as e:
                logging.error(f"Error reading file {csv_file}: {e}")

    # Combine all DataFrames
    if all_dfs:
        try:
            combined_df = pd.concat(all_dfs, ignore_index=True)

            # Remove duplicates
            before_dedup = len(combined_df)
            combined_df = combined_df.drop_duplicates()
            after_dedup = len(combined_df)
            logging.info(f"Removed {before_dedup - after_dedup} duplicate rows.")

            # Save the combined data
            combined_df.to_csv(master_file, index=False, encoding="utf-8")
            logging.info(f"Accumulated data saved to master file: {master_file}")

        except Exception as e:
            logging.error(f"Error combining data: {e}")
    else:
        logging.warning("No CSV files found to accumulate.")


if __name__ == "__main__":
    setup_logging()
    accumulate_all_data()
