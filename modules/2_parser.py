#!/usr/bin/env python
"""
2_parser.py

Description:
    This script processes raw PNS (Public Notification Statement) reports for one or more NWS field offices.
    It extracts metadata, observations, and header metadata from each station’s raw data file and writes
    three CSV files into data/{station}/:
        - observations_<date>_<time>.csv
        - metadata_<date>_<time>.csv
        - header_metadata_<date>_<time>.csv

The date and time are extracted from the report content rather than the system run time.
If output files for a station with the same issuance date and time already exist, processing for that station is skipped.
"""

from typing import List, Tuple, Dict, Any
from pathlib import Path
import pandas as pd
import re
import csv
import logging
from datetime import datetime

# Setup logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define the project root.
# Assuming this script is in "modules/", the project root is one level up.
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Compile regex patterns for efficiency
ISSUANCE_PATTERN = re.compile(
    r'(\d{1,4}\s?[AP]M).*?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(\d{4})'
)
NOUS_PATTERN = re.compile(r"^(NOUS\d{2}\s[A-Z]{3,4})")
CTZ_PATTERN = re.compile(r"(CTZ\d{3}>\d{3}.*)")
SIX_DIGIT_PATTERN = re.compile(r"(\d{6})")


def extract_issuance_timestamp(lines: List[str]) -> Tuple[str, str]:
    """
    Scan the report lines for a line that appears to contain the issuance time and date.
    Expected sample format: "831 AM EST Mon Feb 3 2025"
    Returns a tuple: (formatted_date, formatted_time)
      e.g., ("2025-02-03", "831AM")
    """
    for line in lines:
        match = ISSUANCE_PATTERN.search(line)
        if match:
            time_part = match.group(1).strip().replace(" ", "")  # e.g., "831AM"
            month = match.group(2)
            day = match.group(3)
            year = match.group(4)
            date_str = f"{month} {day} {year}"
            try:
                parsed_date = datetime.strptime(date_str, "%b %d %Y").strftime("%Y-%m-%d")
            except Exception as e:
                logging.error(f"Error parsing date from '{date_str}': {e}")
                parsed_date = "unknown_date"
            return parsed_date, time_part
    return "unknown_date", "unknown_time"


def extract_header_metadata(lines: List[str]) -> List[str]:
    """
    Extract the header metadata from the report.
    This is assumed to be all lines before the "Public Information Statement" line.
    """
    header_lines: List[str] = []
    for line in lines:
        if "Public Information Statement" in line:
            break
        header_lines.append(line.strip())
    return header_lines


def extract_metadata(lines: List[str]) -> Dict[str, Any]:
    """
    Extract metadata fields from the report when a **METADATA header is present.
    """
    metadata: Dict[str, Any] = {
        "issuance_code": None,
        "region_codes": None,
        "timestamp": None,
        "public_info": None,
        "nws_office": None,
        "nws_time": None
    }
    if lines:
        match = NOUS_PATTERN.search(lines[0])
        if match:
            metadata["issuance_code"] = match.group(1)
        match = CTZ_PATTERN.search(lines[0])
        if match:
            metadata["region_codes"] = match.group(1)
        match = SIX_DIGIT_PATTERN.search(lines[0])
        if match:
            try:
                metadata["timestamp"] = datetime.strptime(match.group(1), "%y%m%d").strftime("%Y-%m-%d")
            except Exception as e:
                logging.error(f"Error parsing timestamp: {e}")
    for i, line in enumerate(lines):
        if "Public Information Statement" in line:
            metadata["public_info"] = line.strip()
        if "National Weather Service" in line:
            metadata["nws_office"] = lines[i + 1].strip() if (i + 1) < len(lines) else None
        if re.match(r"\d{3,4}\s[AP]M\s", line):
            metadata["nws_time"] = line.strip()
    return metadata


def extract_observations(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Extract observations from the report when **METADATA is present.
    Expects CSV-like rows with at least 14 columns.
    """
    observations: List[Dict[str, Any]] = []
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
    return observations


def extract_alternative_metadata(lines: List[str]) -> Dict[str, Any]:
    """
    Extract metadata from the alternative report format (when no **METADATA header exists).
    """
    metadata: Dict[str, Any] = {
        "issuance_code": None,
        "nws_office": None,
        "nws_time": None,
        "product": None
    }
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


def extract_alternative_observations(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Extract observations from the alternative report format.
    This function looks for a table header (e.g., a line containing "Location" and "Temp" or "Amount")
    and then parses subsequent lines.
    """
    observations: List[Dict[str, Any]] = []
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


def save_output_files(
    station: str,
    metadata: Dict[str, Any],
    observations: List[Dict[str, Any]],
    header_metadata: List[str],
    issuance_date: str,
    issuance_time: str
) -> None:
    """
    Save metadata, observations, and header metadata into CSV files within the station folder.
    Filenames include the extracted issuance date and time.
    """
    output_dir: Path = BASE_DIR / "data" / station
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_filename = output_dir / f"metadata_{issuance_date}_{issuance_time}.csv"
    observations_filename = output_dir / f"observations_{issuance_date}_{issuance_time}.csv"
    header_metadata_filename = output_dir / f"header_metadata_{issuance_date}_{issuance_time}.csv"

    # Check if files already exist
    if metadata_filename.exists() and observations_filename.exists() and header_metadata_filename.exists():
        logging.info(f"Files for station {station} with timestamp {issuance_date} {issuance_time} already exist. Skipping.")
        return

    # Save metadata
    pd.DataFrame([metadata]).to_csv(metadata_filename, index=False)
    logging.info(f"Saved metadata to {metadata_filename}")

    # Save observations
    pd.DataFrame(observations).to_csv(observations_filename, index=False)
    logging.info(f"Saved observations to {observations_filename}")

    # Save header metadata (one header line per row)
    if header_metadata:
        pd.DataFrame(header_metadata, columns=["header_line"]).to_csv(header_metadata_filename, index=False)
        logging.info(f"Saved header metadata to {header_metadata_filename}")
    else:
        logging.info(f"No header metadata found for station {station}.")


def process_station(station: str) -> None:
    """
    Process a single station:
      - Read the raw data file from data/{station}/raw_data.csv.
      - Extract issuance timestamp from the file.
      - If output files for that timestamp already exist, skip processing.
      - Otherwise, extract metadata, observations, and header metadata.
      - Merge observations from the structured and alternative extraction methods (if applicable).
      - Save output CSV files to data/{station}/.
    """
    # Updated to use raw_data.csv
    input_file: Path = BASE_DIR / "data" / station / "raw_data.csv"
    if not input_file.is_file():
        logging.error(f"Input file not found at {input_file} for station {station}.")
        return

    try:
        lines: List[str] = input_file.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        logging.error(f"Error reading {input_file}: {e}")
        return

    issuance_date, issuance_time = extract_issuance_timestamp(lines)
    logging.info(f"Extracted issuance timestamp for station {station}: {issuance_date} {issuance_time}")

    output_dir: Path = BASE_DIR / "data" / station
    meta_file: Path = output_dir / f"metadata_{issuance_date}_{issuance_time}.csv"
    obs_file: Path = output_dir / f"observations_{issuance_date}_{issuance_time}.csv"
    header_file: Path = output_dir / f"header_metadata_{issuance_date}_{issuance_time}.csv"
    if meta_file.exists() and obs_file.exists() and header_file.exists():
        logging.info(f"Output files for station {station} with timestamp {issuance_date} {issuance_time} already exist. Skipping.")
        return

    # Extract header metadata (the lines before the Public Information Statement)
    header_metadata = extract_header_metadata(lines)

    # Merge extraction methods
    if any("**METADATA" in line for line in lines):
        logging.info(f"Using structured extraction for station {station}.")
        metadata_structured = extract_metadata(lines)
        observations_structured = extract_observations(lines)
        observations_alternative = extract_alternative_observations(lines)
        df_structured = pd.DataFrame(observations_structured)
        df_alternative = pd.DataFrame(observations_alternative)
        if not df_structured.empty and not df_alternative.empty:
            df_merged = pd.concat([df_structured, df_alternative]).drop_duplicates()
            observations = df_merged.to_dict(orient="records")
        else:
            observations = observations_structured or observations_alternative
        metadata = metadata_structured
    else:
        logging.info(f"Using alternative extraction for station {station}.")
        metadata = extract_alternative_metadata(lines)
        observations = extract_alternative_observations(lines)

    save_output_files(station, metadata, observations, header_metadata, issuance_date, issuance_time)


def main() -> None:
    """
    Automatically process all stations in data/ that contain a raw_data.csv file.
    """
    data_dir: Path = BASE_DIR / "data"
    station_list: List[str] = [
        p.name for p in data_dir.iterdir()
        if p.is_dir() and (p / "raw_data.csv").is_file()
    ]
    logging.info(f"Found stations: {station_list}")
    for station in station_list:
        logging.info(f"Processing station: {station}")
        process_station(station)


if __name__ == "__main__":
    main()