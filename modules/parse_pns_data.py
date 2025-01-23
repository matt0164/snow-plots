"""
Script Name: parse_pns_data.py

Description:
    This script processes a raw `pns_reports.csv` file containing weather-related notification reports from the National Weather Service (NWS).
    It extracts metadata, parses observations, and organizes the processed data into structured CSV files. The parsed information is
    saved into directories based on regions, event types, and dates for better categorization and easy accessibility. It is run AFTER the
    pns_statement_scraper.py script has been run.

Key Features:
    1. Metadata Extraction:
        - Extracts key metadata fields such as issuance code, event type, region codes, timestamp, and location (state, county, city).
    2. Observations Parsing:
        - Reads observations data from the raw file.
        - Each row contains details like observation date, time, state, county, event type, values, and description.
    3. Data Organization:
        - Saves metadata as `metadata.csv`.
        - Saves all parsed observations as `observations.csv`.
        - Creates region-based CSVs within `parsed_reports/regions/` directory (e.g., `NJ_observations.csv`).
        - Creates event-type-based directories and places observation files in appropriate subdirectories (e.g., `parsed_reports/events/Wind/`).
        - Creates date-based directories for observations grouped by date (e.g., `parsed_reports/events/Date/`).

Output:
    - All outputs are saved under a directory named `parsed_reports/` within the `data/` folder:
        - `metadata.csv`: Contains extracted metadata.
        - `observations.csv`: Contains all parsed observations.
        - `regions/`: Contains CSVs grouped by state.
        - `events/`: Groups observations into subdirectories for event categories (e.g., Wind, Winter) and dates.

Usage:
    This script must be run *first* as part of your data processing workflow. It processes the raw file and prepares structured outputs
    for further analysis. Ensure that:
        1. The raw file (`pns_reports.csv`) exists in the `data/` directory.
        2. You have write permissions to create folders/files within `data/`.

How to Run:
    1. Place this script in your project directory.
    2. Ensure the input CSV file (`pns_reports.csv`) is located in the `data/` directory.
    3. Run this script using a Python interpreter:
        ```bash
        python parse_pns_data.py
        ```
    4. The outputs will be saved in `data/parsed_reports/`.

Dependencies:
    - Python >= 3.6
    - pandas
    - re (Regular Expressions)
    - datetime
    - pathlib
    - os
    - logging

Errors and Logging:
    - Detailed logs are saved in the `logs/parse_pns_data.log` file.
    - Common errors:
        - FileNotFoundError: Raised when the input file (`pns_reports.csv`) is not found.
        - Malformed Line: Skips malformed or incomplete lines during observation parsing, with a warning in the log.

"""

import pandas as pd
import re
import csv
from datetime import datetime
from pathlib import Path
import os
import logging

# Setup logging
log_dir = Path(__file__).resolve().parents[1] / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_dir / "parse_pns_data.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_metadata(lines):
    metadata = {
        "issuance_code": None,
        "event_type": None,
        "region_codes": None,
        "timestamp": None,
        "state": None,
        "county": None,
        "city": None,
        "report": None,
        "public_info": None,
        "nws_office": None,
        "nws_time": None,
        "latitude": None,
        "longitude": None
    }

    # Extract issuance code and event type
    match = re.search(r"^(NOUS\d{2}\s[A-Z]{4})", lines[0])
    if match:
        metadata["issuance_code"] = match.group(1)

    # Extract region codes
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
            metadata["nws_office"] = lines[i + 1].strip()  # Assuming the office name is on the next line
        if re.match(r"\d{3,4}\s[AP]M\s[A-Za-z]{3}\s[A-Za-z]{3}\s\d{2}\s\d{4}", line):
            metadata["nws_time"] = line.strip()
        if line.strip().isdigit():
            metadata["report"] = line.strip()

    return metadata

def extract_observations(text):
    observations = []
    in_metadata_section = False

    for line in text:
        if "**METADATA**" in line:
            in_metadata_section = True
            logging.info("Entering metadata section.")
            continue

        if in_metadata_section:
            if not line.strip():
                continue
            try:
                row = next(csv.reader([line.strip()]))
                if len(row) < 14:
                    logging.warning(f"Skipping malformed line: {line.strip()}")
                    continue

                observation = {
                    "date": row[0],
                    "time": row[1],
                    "state": row[2],
                    "county": row[3],
                    "city": row[4],
                    "latitude": float(row[7]) if row[7] else None,
                    "longitude": float(row[8]) if row[8] else None,
                    "type": row[9] if row[9] else "UNKNOWN",
                    "value": float(row[10]) if row[10] else None,
                    "unit": row[11] if row[11] else "UNKNOWN",
                    "source": row[12] if row[12] else "UNKNOWN",
                    "description": row[13] if len(row) > 13 else "UNKNOWN"
                }
                observations.append(observation)
                logging.debug(f"Added observation: {observation}")
            except Exception as e:
                logging.error(f"Error parsing line in metadata section: {line.strip()} - {e}")

    if not observations:
        logging.warning("No observations matched in metadata section.")

    # Deduplication step
    unique_observations = pd.DataFrame(observations).drop_duplicates().to_dict(orient="records")
    if len(observations) != len(unique_observations):
        logging.info(f"Removed {len(observations) - len(unique_observations)} duplicate observations.")
    return unique_observations

def save_dataframes(metadata, observations, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add observation-level metadata to metadata file
    observation_keys = {
        "issuance_code": "The unique code assigned to the product issuance, indicating the type of product and issuing office. See https://forecast.weather.gov/product_sites.php?product=PNS&site=NWS&utm_source=chatgpt.com and https://www.weather.gov/nwr/eventcodes",
        "event_type": "The specific type of event or statement being reported (e.g., [Public Information Statement]). See https://www.weather.gov/nwr/eventcodes",
        "region_codes": "Codes representing the geographic regions affected, typically denoted by state and zone numbers (e.g., CTZ005>012).",
        "timestamp": "The date and time when the report was issued, formatted as YYYY-MM-DD.",
        "date": "Observation date",
        "time": "Observation time",
        "state": "State where the observation occurred",
        "county": "County where the observation occurred",
        "city": "City where the observation occurred",
        "report": "The unique identifier for the report, assigned by the National Weather Service.",
        "public_info": "The main content of the Public Information Statement, detailing the observations and relevant information.",
        "nws_office": "The name of the National Weather Service office that issued the report. See https://forecast.weather.gov/product_sites.php?product=PNS&site=NWS&utm_source=chatgpt.com",
        "nws_time": "The time the report was issued by the NWS, in 24-hour AM/PM format (e.g. :1/19/2025,1000 PM",
        "latitude": "Latitude of observation location",
        "longitude": "Longitude of observation location",
        "type": "Type of observation (e.g., snow, wind)",
        "value": "Measured value",
        "unit": "Unit of measurement",
        "source": "Source of observation",
        "description": "Detailed description of observation"
    }
    metadata.update(observation_keys)

    # Save metadata CSV
    df_metadata = pd.DataFrame([metadata])
    df_metadata.to_csv(output_dir / "metadata.csv", index=False)

    # Save observations CSV
    df_observations = pd.DataFrame(observations)
    if df_observations.empty:
        logging.warning("No observations to save.")
        return

    # Save the main observations file
    df_observations.to_csv(output_dir / "observations.csv", index=False)
    logging.info(f"Saved observations to {output_dir / 'observations.csv'}")

    # Create directories for event-based files
    events_dir = output_dir / "events"
    regions_dir = output_dir / "regions"
    events_dir.mkdir(exist_ok=True)
    regions_dir.mkdir(exist_ok=True)

    # Save region-based files
    for region, group in df_observations.groupby("state"):
        region_file = regions_dir / f"{region.replace(' ', '_').lower()}_observations.csv"
        group.drop_duplicates().to_csv(region_file, index=False)
        logging.info(f"Saved region-based observations to {region_file}")

    # Process event-based files
    event_categories = {
        "Winter": ["SNOW", "SNOW_24"],
        "Wind": ["PKGUST"],
        "Flooding": ["FLOOD"],
        "Temps": ["COLD", "HEAT", "TEMP"],
        "Other": []  # Catch-all for undefined or unmatched event types
    }

    for event_type, group in df_observations.groupby("type"):
        # Determine which category the event belongs to
        category = next(
            (key for key, values in event_categories.items() if event_type in values),
            "Other"
        )

        # Create directory for the event category
        event_dir = events_dir / category
        event_dir.mkdir(exist_ok=True)

        # Save file for the specific event type
        event_file = event_dir / f"{event_type.replace(' ', '_').lower()}_observations.csv"
        group.drop_duplicates().to_csv(event_file, index=False)
        logging.info(f"Saved {event_type} observations to {event_file}")

    # Save files by date inside events/Date/
    date_dir = events_dir / "Date"
    date_dir.mkdir(exist_ok=True)

    for date, group in df_observations.groupby("date"):
        date_file = date_dir / f"{date}_observations.csv"
        group.drop_duplicates().to_csv(date_file, index=False)
        logging.info(f"Saved date-based observations to {date_file}")

def create_metadata_description(metadata, output_dir):
    description_file = output_dir / "metadata_description.txt"
    with description_file.open("w") as f:
        f.write("Metadata Fields and Definitions:\n")
        f.write("------------------------------\n")
        for key, value in metadata.items():
            f.write(f"{key}: {value or 'No description available'}\n")
    logging.info(f"Saved metadata description to {description_file}")

def main(input_file, output_dir):
    # Resolve paths relative to the project root
    project_root = Path(__file__).resolve().parents[1]
    input_file = project_root / input_file
    output_dir = project_root / output_dir

    # Debugging: Check resolved paths
    logging.info(f"Project root: {project_root}")
    logging.info(f"Input file path: {input_file}")
    logging.info(f"Output directory path: {output_dir}")

    if not input_file.exists():
        logging.error(f"The input file '{input_file}' does not exist. Please ensure the file is correctly placed.")
        raise FileNotFoundError(f"The input file '{input_file}' does not exist. Please ensure the file is correctly placed.")

    with input_file.open("r") as file:
        lines = file.readlines()

    # Step 1: Extract Metadata
    metadata = extract_metadata(lines)
    logging.info(f"Extracted metadata: {metadata}")

    # Step 2: Extract Observations
    observations = extract_observations(lines)
    if not observations:
        logging.warning("No observations were extracted!")
    else:
        logging.info(f"Extracted {len(observations)} observations.")

    # Step 3: Save Dataframes
    save_dataframes(metadata, observations, output_dir)

    # Step 4: Create Metadata Description
    create_metadata_description(metadata, output_dir)

if __name__ == "__main__":
    input_file = "data/pns_reports.csv"  # Path to your input file
    output_dir = "data/parsed_reports"   # Directory to save outputs

    try:
        main(input_file, output_dir)
    except FileNotFoundError as e:
        logging.error(e)
