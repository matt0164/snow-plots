"""
Script Name: 2_parser.py

Description:
    This script processes raw PNS (Public Notification Statement) reports for one or more NWS field offices
    from their respective `pns_metadata.csv` files. It extracts metadata, parses observations, and organizes
    the processed data into structured CSV files.

Key Features:
    - Extracts metadata and observations.
    - Organizes data into station-specific folders.
    - Handles both **METADATA and alternative report formats.

Dependencies:
    - Python >= 3.6
    - pandas, re, pathlib, logging, datetime, csv, shutil
"""

import pandas as pd
import re
import csv
import shutil
from datetime import datetime
from pathlib import Path
import logging

# --------------------------------------------------------
# Setup Logging
# --------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent  # Adjust to project root dynamically

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "logs" / "parser.log", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


# --------------------------------------------------------
# Helper Functions
# --------------------------------------------------------

def ensure_directories(*dirs):
    """
    Ensures that the provided directories exist by creating them if they do not.
    """
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def extract_metadata(lines):
    """
    Extract metadata fields from the raw PNS report when a **METADATA header is present.
    """
    metadata = {
        "issuance_code": None,
        "region_codes": None,
        "timestamp": None,
        "public_info": None,
        "nws_office": None,
        "nws_time": None
    }

    # Extract metadata fields using regex
    match = re.search(r"^(NOUS\d{2}\s[A-Z]{4})", lines[0])
    if match:
        metadata["issuance_code"] = match.group(1)

    match = re.search(r"(CTZ\d{3}>\d{3}-NJZ\d{3}>\d{3})", lines[0])
    if match:
        metadata["region_codes"] = match.group(1)

    # Extract timestamp from the first line
    match = re.search(r"(\d{6})", lines[0])
    if match:
        try:
            metadata["timestamp"] = datetime.strptime(match.group(1), "%y%m%d").strftime("%Y-%m-%d")
        except Exception as e:
            logging.error(f"Error parsing timestamp: {e}")

    # Extract other metadata details
    for i, line in enumerate(lines):
        if "Public Information Statement" in line:
            metadata["public_info"] = line.strip()
        if "National Weather Service" in line:
            metadata["nws_office"] = lines[i + 1].strip() if (i + 1) < len(lines) else None
        if re.match(r"\d{3,4}\s[AP]M\s[A-Za-z]{3}\s[A-Za-z]{3}\s\d{2}\s\d{4}", line):
            metadata["nws_time"] = line.strip()

    return metadata


def extract_observations(lines):
    """
    Extract observations from the raw PNS report. Expects CSV-like rows.
    """
    observations = []
    for i, line in enumerate(lines):
        try:
            row = next(csv.reader([line.strip()]))
            if len(row) < 14:
                logging.warning(f"Skipping malformed line {i}: '{line.strip()}'")
                continue

            observation = {
                "date": row[0],
                "time": row[1],
                "state": row[2],
                "county": row[3],
                "city": row[4],
                "latitude": float(row[7]) if row[7] else None,
                "longitude": float(row[8]) if row[8] else None,
                "type": row[9].strip().upper() if row[9] else "UNKNOWN",
                "value": float(row[10]) if row[10] else None,
                "unit": row[11] if row[11] else "UNKNOWN",
                "source": row[12] if row[12] else "UNKNOWN",
                "description": row[13] if len(row) > 13 else "UNKNOWN"
            }
            observations.append(observation)
        except Exception as e:
            logging.error(f"Error parsing line {i}: '{line.strip()}' - {e}")

    return pd.DataFrame(observations).drop_duplicates().to_dict(orient="records")


def save_dataframes(metadata, observations, output_dir):
    """
    Save parsed observations and metadata into the structured directory for the station.
    """
    ensure_directories(output_dir)

    # Save metadata as CSV
    metadata_file = output_dir / "metadata.csv"
    pd.DataFrame([metadata]).to_csv(metadata_file, index=False, encoding="utf-8")
    logging.info(f"Saved metadata to {metadata_file}")

    # Save observations as CSV
    observations_file = output_dir / "observations.csv"
    df = pd.DataFrame(observations)
    df.to_csv(observations_file, index=False, encoding="utf-8")
    logging.info(f"Saved observations to {observations_file}")

    # Organize observations by region (state)
    regions_dir = output_dir / "regions"
    ensure_directories(regions_dir)
    if "state" in df.columns:
        for state, group in df.groupby("state"):
            group_file = regions_dir / f"{state.lower()}_observations.csv"
            group.to_csv(group_file, index=False, encoding="utf-8")
            logging.info(f"Saved regional observations to {group_file}")
    else:
        logging.debug("No 'state' column found for regional grouping.")


def process_station(station):
    """
    Process a single station: read raw data, extract and save parsed data.
    """
    input_file = BASE_DIR / "data" / station / "raw_metadata" / "pns_metadata.csv"
    output_dir = BASE_DIR / "data" / station / "parsed_reports"

    if not input_file.is_file():
        logging.error(f"Input file not found for station {station}: {input_file}")
        return

    with input_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    if any("**METADATA" in line for line in lines):
        logging.info(f"Using standard metadata extraction for station {station}.")
        metadata = extract_metadata(lines)
        observations = extract_observations(lines)
    else:
        logging.info(f"**METADATA header not found for station {station}. Using alternative extraction logic.")
        metadata = {"error": "Metadata extraction not implemented yet."}
        observations = []

    save_dataframes(metadata, observations, output_dir)


def main():
    """
    Prompt user for stations to process and parse reports for each station.
    """
    stations_input = input("Enter station(s) to parse (comma-separated or 'ALL' for all stations): ").strip()
    if stations_input.upper() == "ALL":
        data_dir = BASE_DIR / "data"
        station_list = [
            p.name for p in data_dir.iterdir()
            if p.is_dir() and (p / "raw_metadata" / "pns_metadata.csv").is_file()
        ]
    else:
        station_list = [s.strip() for s in stations_input.split(",")]

    for station in station_list:
        logging.info(f"Processing station: {station}")
        process_station(station)


if __name__ == "__main__":
    main()
