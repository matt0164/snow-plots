"""
Script Name: parse_pns_data.py

Description:
    This script processes raw PNS (Public Notification Statement) reports for a specific NWS field office (e.g., OKX) from its `pns_metadata.csv` file.
    It extracts metadata, parses observations, and organizes the processed data into structured CSV files.

Project Structure:
    Each station (e.g., OKX) has its own input and output file structure:
    - Input File Location: `data/<field_office>/raw_metadata/pns_metadata.csv`
    - Output Folder: `data/<field_office>/parsed_reports/`

Key Features:
    1. Metadata Extraction:
        - Extracts key metadata fields from the station's raw PNS reports.
    2. Observations Parsing:
        - Parses relevant observation fields (date, time, region, type, values, etc.).
    3. Data Organization:
        - Metadata and observations are saved in station-specific folders (e.g., `OKX/parsed_reports/`).
        - Observations are grouped by region, event category, and date.

Output Structure:
    - All outputs are saved under `data/<field_office>/parsed_reports/`:
        - `metadata.csv`: Contains extracted metadata.
        - `observations.csv`: Contains all observations.
        - `regions/`: CSVs grouped by state.
        - `events/`: Subdirectories for observation categories (e.g., Wind, Winter, Flooding).

Dependencies:
    - Python >= 3.6
    - pandas, re, pathlib, logging, datetime, csv
"""

import pandas as pd
import re
import csv
from datetime import datetime
from pathlib import Path
import logging

# Setup logging to dynamically create logs for better debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def extract_metadata(lines):
    """
    Extract metadata fields from the raw PNS report.

    Args:
        lines (list): Lines of raw text from the input file.

    Returns:
        dict: Extracted metadata, with fields such as issuance code, timestamp, and NWS office information.
    """
    metadata = {
        "issuance_code": None,
        "region_codes": None,
        "timestamp": None,
        "public_info": None,
        "nws_office": None,
        "nws_time": None
    }

    # Extract issuance code and region codes
    match = re.search(r"^(NOUS\d{2}\s[A-Z]{4})", lines[0])
    if match:
        metadata["issuance_code"] = match.group(1)

    match = re.search(r"(CTZ\d{3}>\d{3}-NJZ\d{3}>\d{3})", lines[0])
    if match:
        metadata["region_codes"] = match.group(1)

    # Extract timestamp
    match = re.search(r"(\d{6})", lines[0])
    if match:
        metadata["timestamp"] = datetime.strptime(match.group(1), "%y%m%d").strftime("%Y-%m-%d")

    # Extract additional metadata
    for i, line in enumerate(lines):
        if "Public Information Statement" in line:
            metadata["public_info"] = line.strip()
        if "National Weather Service" in line:
            metadata["nws_office"] = lines[i + 1].strip()
        if re.match(r"\d{3,4}\s[AP]M\s[A-Za-z]{3}\s[A-Za-z]{3}\s\d{2}\s\d{4}", line):
            metadata["nws_time"] = line.strip()

    return metadata


def extract_observations(lines):
    """
    Extract observations from the raw PNS report.

    Args:
        lines (list): Raw text lines from the metadata file.

    Returns:
        list: A list of dictionaries representing parsed observations.
    """
    observations = []

    for i, line in enumerate(lines):
        try:
            row = next(csv.reader([line.strip()]))
            if len(row) < 14:
                logging.warning(f"Skipping malformed line {i}: '{line.strip()}'")
                continue

            # Parse individual observation fields
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

    # Remove duplicates
    return pd.DataFrame(observations).drop_duplicates().to_dict(orient="records")


def save_dataframes(metadata, observations, output_dir):
    """
    Save parsed observations and metadata into the structured directory for the specified station.

    Args:
        metadata (dict): Extracted metadata dictionary.
        observations (list[dict]): List of parsed observations.
        output_dir (Path): Output directory for saving data.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata CSV
    metadata_file = output_dir / "metadata.csv"
    pd.DataFrame([metadata]).to_csv(metadata_file, index=False)
    logging.info(f"Saved metadata to {metadata_file}")

    # Save observations CSV
    observations_file = output_dir / "observations.csv"
    df = pd.DataFrame(observations)
    df.to_csv(observations_file, index=False)
    logging.info(f"Saved observations to {observations_file}")

    # Organize observations by regions
    regions_dir = output_dir / "regions"
    regions_dir.mkdir(exist_ok=True)
    for state, group in df.groupby("state"):
        group_file = regions_dir / f"{state.lower()}_observations.csv"
        group.to_csv(group_file, index=False)
        logging.info(f"Saved regional observations to {group_file}")

    # Organize observations by event type
    event_categories = {"Winter": ["SNOW"], "Wind": ["PKGUST"], "Other": []}
    events_dir = output_dir / "events"
    events_dir.mkdir(exist_ok=True)
    for event, group in df.groupby("type"):
        category = next((key for key, values in event_categories.items() if event in values), "Other")
        category_dir = events_dir / category
        category_dir.mkdir(exist_ok=True)
        group_file = category_dir / f"{event.lower()}_observations.csv"
        group.to_csv(group_file, index=False)
        logging.info(f"Saved {event} observations to {group_file}")

    # Organize observations by date
    date_dir = output_dir / "dates"
    date_dir.mkdir(exist_ok=True)
    for obs_date, group in df.groupby("date"):
        date_file = date_dir / f"{obs_date}_observations.csv"
        group.to_csv(date_file, index=False)
        logging.info(f"Saved observations for {obs_date} to {date_file}")


def main(field_office_code):
    """
    Main script execution.

    Args:
        field_office_code (str): The field office code for which the script will process data (e.g., "OKX").
    """
    # Define input paths and output paths based on field office
    input_file = Path(f"data/{field_office_code}/raw_metadata/pns_metadata.csv")
    output_dir = Path(f"data/{field_office_code}/parsed_reports")

    # Ensure input file exists
    if not input_file.is_file():
        logging.error(f"Input file not found at {input_file}")
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    # Process the file
    with input_file.open("r") as f:
        lines = f.readlines()

    metadata = extract_metadata(lines)
    observations = extract_observations(lines)

    # Save parsed data
    save_dataframes(metadata, observations, output_dir)


if __name__ == "__main__":
    # Replace "OKX" with the field office code for your use case
    main("OKX")
