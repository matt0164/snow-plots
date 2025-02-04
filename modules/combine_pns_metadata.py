import os
import pandas as pd
from datetime import datetime


def combine_pns_metadata():
    """
    Combines all `pns_metadata.csv` files from station subfolders (`raw_metadata/`)
    and saves the merged file in `/data/ALL_STATIONS/` with a timestamp.
    """
    # Define paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Root of the project
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(data_dir, "ALL_STATIONS")  # Updated output directory

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_filename = f"all_stations_pns_data_{timestamp}.csv"  # Updated filename
    output_path = os.path.join(output_dir, output_filename)

    # List to store all DataFrames
    all_data = []

    # Scan the `/data/` directory for station folders
    for folder in os.listdir(data_dir):
        station_path = os.path.join(data_dir, folder, "raw_metadata", "pns_metadata.csv")

        # Check if the metadata file exists inside `raw_metadata/`
        if os.path.exists(station_path):
            try:
                df = pd.read_csv(station_path)
                df["Station"] = folder  # Add station identifier
                all_data.append(df)
                print(f"✅ Loaded {station_path}")
            except Exception as e:
                print(f"❌ Error reading {station_path}: {e}")

    # Combine all station data into a single DataFrame
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        # Save the combined file
        combined_df.to_csv(output_path, index=False)
        print(f"✅ Combined PNS metadata saved as: {output_path}")
    else:
        print("⚠️ No valid PNS metadata files found.")


if __name__ == "__main__":
    combine_pns_metadata()