#this script checks all csv files and removes all duplicate rows that can result from multiple reports over time from the same station

import pandas as pd
from pathlib import Path


def check_and_remove_duplicates(directory, remove_duplicates=False):
    """
    Checks all CSV files in the given directory for duplicate rows, and optionally removes them.

    Args:
        directory (str or Path): Path to the directory containing the CSV files to process.
        remove_duplicates (bool): If True, removes duplicate rows and overwrites the files.
    """
    directory = Path(directory)

    # Ensure the directory exists
    if not directory.exists() or not directory.is_dir():
        print(f"Directory {directory} does not exist or is not a valid directory.")
        return

    # Get all CSV files in the directory
    csv_files = list(directory.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {directory}.")
        return

    print(f"Checking {len(csv_files)} CSV files for duplicate rows in {directory}...")

    for file_path in csv_files:
        try:
            # Load the CSV file into a DataFrame
            df = pd.read_csv(file_path)

            # Check for duplicate rows
            duplicate_rows = df[df.duplicated()]

            if not duplicate_rows.empty:
                print(f"Duplicate rows found in file: {file_path}")
                print(duplicate_rows)

                if remove_duplicates:
                    # Remove duplicates and save back to the file
                    df = df.drop_duplicates()
                    df.to_csv(file_path, index=False)
                    print(f"Removed duplicates from file: {file_path}")
            else:
                print(f"No duplicates found in file: {file_path}")
        except Exception as e:
            print(f"Failed to process file: {file_path} - Error: {e}")


# Paths to events and regions directories
events_dir = "data/parsed_reports/events"  # Update the path as per your structure
regions_dir = "data/parsed_reports/regions"  # Update the path as per your structure

# Check for duplicates in both directories (set remove_duplicates=True to fix them)
check_and_remove_duplicates(events_dir, remove_duplicates=True)
check_and_remove_duplicates(regions_dir, remove_duplicates=True)
