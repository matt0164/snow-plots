"""
Script Name: parse_pns_data.py

Description:
    This script processes raw PNS (Public Notification Statement) reports for one or more NWS field offices
    from their respective `pns_metadata.csv` files. It extracts metadata, parses observations, and organizes
    the processed data into structured CSV files.

Project Structure:
    Each station (e.g., OKX) has its own input and output file structure:
        - Input File Location: `data/<station>/raw_metadata/pns_metadata.csv`
        - Output Folder: `data/<station>/parsed_reports/`
    Debug HTML files (if present) are saved to: `logs/debug/`

Key Features:
    1. Metadata Extraction:
        - Extracts key metadata fields from the station's raw PNS reports.
    2. Observations Parsing:
        - Parses relevant observation fields (date, time, region, type, values, etc.).
    3. Data Organization:
        - Metadata and observations are saved in station-specific folders (e.g., `OKX/parsed_reports/`).
        - Observations are grouped by region, event category, and date.

Output Structure:
    - All outputs are saved under `data/<station>/parsed_reports/`:
        - `metadata.csv`: Contains extracted metadata.
        - `observations.csv`: Contains all observations.
        - `regions/`: CSVs grouped by state.
        - `events/`: Subdirectories for observation categories (e.g., Wind, Winter, Flooding).
        - `dates/`: CSVs grouped by date.

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

# Setup logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define the project root.
# Assuming this script is in "snow-plots/modules/", the project root is one level up.
BASE_DIR = Path(__file__).resolve().parent.parent

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

    # Extract issuance code and region codes from the first line (if available)
    match = re.search(r"^(NOUS\d{2}\s[A-Z]{4})", lines[0])
    if match:
        metadata["issuance_code"] = match.group(1)

    match = re.search(r"(CTZ\d{3}>\d{3}-NJZ\d{3}>\d{3})", lines[0])
    if match:
        metadata["region_codes"] = match.group(1)

    # Extract timestamp from the first line (assuming a 6-digit date code is present)
    match = re.search(r"(\d{6})", lines[0])
    if match:
        try:
            metadata["timestamp"] = datetime.strptime(match.group(1), "%y%m%d").strftime("%Y-%m-%d")
        except Exception as e:
            logging.error(f"Error parsing timestamp: {e}")

    # Extract additional metadata details
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
    Extract observations from the raw PNS report when **METADATA is present.
    This function expects CSV-like rows with at least 14 columns.
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

    # Remove duplicates and return as list of dictionaries.
    return pd.DataFrame(observations).drop_duplicates().to_dict(orient="records")

def extract_alternative_metadata(lines):
    """
    Extract metadata from the alternative report format (when no **METADATA header exists).

    This function looks for key lines such as one starting with "NOUS" and the
    "National Weather Service" line with the following timestamp.
    """
    metadata = {
        "issuance_code": None,
        "nws_office": None,
        "nws_time": None,
        "product": None  # e.g., "PNSDLH", "PNSGRB", etc.
    }
    # Look for a line starting with "NOUS" (e.g., "NOUS43 KDLH 211941")
    for line in lines:
        if line.startswith("NOUS"):
            metadata["issuance_code"] = line.strip()
            break

    try:
        idx = next(i for i, line in enumerate(lines) if line.startswith("NOUS"))
        if (idx + 1) < len(lines):
            metadata["product"] = lines[idx + 1].strip()
    except StopIteration:
        pass

    for i, line in enumerate(lines):
        if line.startswith("National Weather Service"):
            metadata["nws_office"] = line.strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                metadata["nws_time"] = lines[j].strip()
            break

    return metadata

def extract_alternative_observations(lines):
    """
    Extract observations from the alternative report format.

    This function searches for the table header (e.g., a line containing "Location" and either "Temp" or "Amount")
    and then parses subsequent lines using whitespace splitting.
    It skips county header lines (e.g., those starting with "..." and containing "County").
    """
    observations = []
    header_line = None
    header_index = None

    for i, line in enumerate(lines):
        if "Location" in line and ("Temp" in line or "Amount" in line):
            header_line = line.strip()
            header_index = i
            break

    if not header_line:
        logging.error("Could not find observation table header in alternative format.")
        return observations

    headers = re.split(r'\s{2,}', header_line)
    logging.debug(f"Observation headers found: {headers}")

    for line in lines[header_index + 1:]:
        line = line.strip()
        if line.startswith("...") and "County" in line:
            continue
        if not line:
            continue

        columns = re.split(r'\s{2,}', line)
        if len(columns) != len(headers):
            logging.warning(f"Skipping malformed observation line: '{line}'")
            continue

        observation = dict(zip(headers, columns))
        observations.append(observation)

    return observations

def save_dataframes(metadata, observations, output_dir):
    """
    Save parsed observations and metadata into the structured directory for the station.
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

    # Organize observations by regions (grouped by state)
    regions_dir = output_dir / "regions"
    regions_dir.mkdir(exist_ok=True)
    if "state" in df.columns:
        for state, group in df.groupby("state"):
            group_file = regions_dir / f"{state.lower()}_observations.csv"
            group.to_csv(group_file, index=False)
            logging.info(f"Saved regional observations to {group_file}")
    else:
        logging.debug("No 'state' column found for regional grouping.")

    # Organize observations by event type (example categorization)
    event_categories = {"Winter": ["SNOW"], "Wind": ["PKGUST"], "Other": []}
    events_dir = output_dir / "events"
    events_dir.mkdir(exist_ok=True)
    if "type" in df.columns:
        for event, group in df.groupby("type"):
            category = next((key for key, values in event_categories.items() if event in values), "Other")
            category_dir = events_dir / category
            category_dir.mkdir(exist_ok=True)
            group_file = category_dir / f"{event.lower()}_observations.csv"
            group.to_csv(group_file, index=False)
            logging.info(f"Saved {event} observations to {group_file}")
    else:
        logging.debug("No 'type' column found for event categorization.")

    # Organize observations by date
    date_dir = output_dir / "dates"
    date_dir.mkdir(exist_ok=True)
    if "date" in df.columns:
        for obs_date, group in df.groupby("date"):
            date_file = date_dir / f"{obs_date}_observations.csv"
            group.to_csv(date_file, index=False)
            logging.info(f"Saved observations for {obs_date} to {date_file}")
    else:
        logging.debug("No 'date' column found for date grouping.")

def save_debug_html(station):
    """
    If a debug HTML file exists in the data folder for the station,
    copy it to the logs/debug folder.
    """
    source = BASE_DIR / "data" / f"{station}_debug.html"
    debug_dir = BASE_DIR / "logs" / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    if source.is_file():
        destination = debug_dir / f"{station}_debug.html"
        shutil.copyfile(source, destination)
        logging.info(f"Copied debug HTML file for station {station} to {destination}")
    else:
        logging.info(f"No debug HTML file found for station {station}")

def process_station(station):
    """
    Process a single station: read the raw metadata, extract and save the parsed data,
    and copy any debug HTML file to the logs/debug folder.
    """
    input_file = BASE_DIR / "data" / station / "raw_metadata" / "pns_metadata.csv"
    output_dir = BASE_DIR / "data" / station / "parsed_reports"

    if not input_file.is_file():
        logging.error(f"Input file not found at {input_file}")
        return

    with input_file.open("r") as f:
        lines = f.readlines()

    if any("**METADATA" in line for line in lines):
        logging.info(f"Using standard metadata extraction for station {station}.")
        metadata = extract_metadata(lines)
        observations = extract_observations(lines)
    else:
        logging.info(f"**METADATA header not found for station {station}; using alternative extraction logic.")
        metadata = extract_alternative_metadata(lines)
        observations = extract_alternative_observations(lines)

    save_dataframes(metadata, observations, output_dir)
    save_debug_html(station)

def main():
    """
    Prompt the user for station(s) to process (comma-separated or 'ALL_STATIONS') and process each one.
    """
    stations_input = input("Enter station(s) to parse (comma-separated or 'ALL_STATIONS' for all available): ").strip()
    if stations_input.upper() == "ALL_STATIONS":
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