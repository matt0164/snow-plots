from pathlib import Path
import pandas as pd
import csv
import logging
import os


# Setup centralized logging with both file and console outputs
def setup_logging():
    log_file = Path("logs/parse_pns.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)  # Create logs directory if missing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),  # Log to file
            logging.StreamHandler(),  # Log to console
        ],
    )


# Extract metadata
def extract_metadata(lines):
    """
    Extract metadata fields from the raw PNS report.

    Args:
        lines (list): Lines of raw text from the input file.

    Returns:
        dict: Extracted metadata.
    """
    metadata = {
        "issuance_code": None,
        "region_codes": None,
        "timestamp": None,
        "public_info": None,
        "nws_office": None,
    }

    # Process specific metadata lines (add logic as needed)
    for line in lines:
        if "Public Information Statement" in line:
            metadata["public_info"] = line.strip()
        elif "National Weather Service" in line:
            metadata["nws_office"] = line.strip()

    logging.info(f"Extracted metadata: {metadata}")
    return metadata


def extract_observations(lines):
    """
    Extract observations from the raw PNS reports.

    Args:
        lines (list): Text lines from the input file.

    Returns:
        list: A list of dictionaries, where each dict represents a parsed observation.
    """
    observations = []
    logging.info(f"Processing total input lines: {len(lines)}")

    # Identify where to start parsing valid rows
    valid_start_index = 0
    for i, line in enumerate(lines):
        if line.startswith("DATA START") or "Column 1" in line:
            valid_start_index = i + 1
            logging.debug(f"Identified data start at line {valid_start_index}")
            break

    for i, line in enumerate(lines[valid_start_index:], start=valid_start_index + 1):
        row = line.strip()
        try:
            # Ignore empty, malformed, or header-like lines
            if not row or "Column" in row:
                logging.debug(f"Skipping non-data row {i}: '{row}'")
                continue

            # Parse row assuming valid CSV-style data
            row_data = next(csv.reader([row]))

            # Ensure row contains the required number of columns
            if len(row_data) < 14:
                logging.warning(f"Skipping malformed row {i}: '{row}'")
                continue

            # Create observation dictionary
            observation = {
                "date": row_data[0].strip(),
                "time": row_data[1].strip(),
                "state": row_data[2].strip(),
                "county": row_data[3].strip(),
                "city": row_data[4].strip(),
                "latitude": float(row_data[7]) if row_data[7].strip() else None,
                "longitude": float(row_data[8]) if row_data[8].strip() else None,
                "type": row_data[9].strip().upper() if row_data[9].strip() else "UNKNOWN",
                "value": float(row_data[10]) if row_data[10].strip() else None,
                "unit": row_data[11].strip() if row_data[11].strip() else None,
                "source": row_data[12].strip() if row_data[12].strip() else "UNKNOWN",
                "description": row_data[13].strip() if len(row_data) > 13 else "N/A",
            }

            observations.append(observation)

        except Exception as e:
            logging.error(f"Error parsing line {i}: '{row}'. Exception: {e}")

    logging.info(f"Total observations parsed: {len(observations)}")
    return observations


def save_dataframes(metadata, observations, output_dir):
    """
    Save extracted metadata and observations to structured CSV files.

    Args:
        metadata (dict): Dictionary of metadata fields.
        observations (list[dict]): List of processed observations.
        output_dir (Path): Directory path to save the data.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata if available
    metadata_path = output_dir / "metadata.csv"
    if metadata:
        pd.DataFrame([metadata]).to_csv(metadata_path, index=False)
        logging.info(f"Metadata saved to: {metadata_path}")
    else:
        logging.warning("No metadata available to save.")

    # Save observations if available
    observations_path = output_dir / "observations.csv"
    if observations:
        pd.DataFrame(observations).to_csv(observations_path, index=False)
        logging.info(f"Observations saved to: {observations_path}")
    else:
        logging.warning("No observations available to save. File will not be created.")


def main(field_office_code):
    """
    Main function for processing PNS data for a specific field office.

    Args:
        field_office_code (str): The field office (e.g., "OKX") for which to process data.
    """
    base_dir = Path(__file__).resolve().parent.parent
    input_file = base_dir / f"data/{field_office_code}/raw_metadata/pns_metadata.csv"
    output_dir = base_dir / f"data/{field_office_code}/parsed_reports"

    logging.info(f"Processing field office: {field_office_code}")
    logging.info(f"Input file: {input_file}")
    logging.info(f"Output directory: {output_dir}")

    # Ensure the input file exists
    if not input_file.is_file():
        logging.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Read raw file
    with input_file.open("r") as f:
        lines = f.readlines()

    if not lines:
        logging.error("Input file is empty. Exiting.")
        raise ValueError("Input file is empty.")

    # Process metadata and observations
    metadata = extract_metadata(lines)
    observations = extract_observations(lines)

    # Save processed data
    save_dataframes(metadata, observations, output_dir)


if __name__ == "__main__":
    try:
        setup_logging()
        main("OKX")  # Example field office
    except Exception as e:
        logging.critical(f"Critical error during processing: {e}")
