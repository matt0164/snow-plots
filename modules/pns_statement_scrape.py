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
        "city": None
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

    # Attempt to extract state, county, and city if present
    for line in lines:
        if "State:" in line:
            metadata["state"] = line.split("State:")[1].strip()
        if "County:" in line:
            metadata["county"] = line.split("County:")[1].strip()
        if "City:" in line:
            metadata["city"] = line.split("City:")[1].strip()

    return metadata

def extract_observations(text):
    observations = []
    in_metadata_section = False

    for line in text:
        # Detect start of metadata section
        if "**METADATA**" in line:
            in_metadata_section = True
            logging.info("Entering metadata section.")
            continue

        # Process metadata lines
        if in_metadata_section:
            if not line.strip():
                continue  # Skip empty lines
            try:
                # Parse the line as CSV
                row = next(csv.reader([line.strip()]))
                if len(row) < 14:
                    logging.warning(f"Skipping malformed line: {line.strip()}")
                    continue

                # Clean up unwanted character (":") in the date field
                date_cleaned = row[0].lstrip(":").strip()

                observation = {
                    "date": row[0],        # Date (e.g., 1/19/2025)
                    "time": row[1],        # Time (e.g., 1000 PM)
                    "state": row[2],       # State (e.g., CT)
                    "county": row[3],      # County (e.g., Fairfield)
                    "city": row[4],        # City (e.g., Stamford)
                    "latitude": float(row[7]) if row[7] else None,  # Latitude
                    "longitude": float(row[8]) if row[8] else None, # Longitude
                    "type": row[9] if row[9] else "UNKNOWN",        # Observation type
                    "value": float(row[10]) if row[10] else None,    # Value
                    "unit": row[11] if row[11] else "UNKNOWN",      # Unit
                    "source": row[12] if row[12] else "UNKNOWN",    # Source
                    "description": row[13] if len(row) > 13 else "UNKNOWN" # Description
                }

                observations.append(observation)
                logging.debug(f"Added metadata observation: {observation}")
            except Exception as e:
                logging.error(f"Error parsing line in metadata section: {line.strip()} - {e}")

    if not observations:
        logging.warning("No observations matched in metadata section.")
    return observations

def save_dataframes(metadata, observations, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df_metadata = pd.DataFrame([metadata])
    df_observations = pd.DataFrame(observations)

    # Save metadata and observations to CSV files
    df_metadata.to_csv(output_dir / "metadata.csv", index=False)
    if not df_observations.empty:
        df_observations.to_csv(output_dir / "observations.csv", index=False)
        logging.info(f"Saved observations to {output_dir / 'observations.csv'}")
    else:
        logging.warning("No observations to save.")

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

if __name__ == "__main__":
    input_file = "data/pns_reports.csv"  # Path to your input file
    output_dir = "data/parsed_reports"   # Directory to save outputs

    try:
        main(input_file, output_dir)
    except FileNotFoundError as e:
        logging.error(e)
