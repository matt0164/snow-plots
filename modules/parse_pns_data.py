from pathlib import Path
import pandas as pd
import csv
import logging


# Set up centralized logging
def setup_logging():
    log_file = Path("../logs/parse_pns.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure logs directory exists
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),  # Log to file
            logging.StreamHandler(),  # Log to console
        ],
    )


# Sanitize file/folder names
def sanitize_path_component(component):
    """Sanitize a string for use in a file path."""
    return str(component).strip().replace("/", "_").replace("\\", "_")


# Extract metadata
def extract_metadata(lines):
    metadata = {
        "issuance_code": None,
        "region_codes": None,
        "timestamp": None,
        "public_info": None,
        "nws_office": None,
    }

    for line in lines:
        if "Public Information Statement" in line:
            metadata["public_info"] = line.strip()
        elif "National Weather Service" in line:
            metadata["nws_office"] = line.strip()

    logging.info(f"Extracted metadata: {metadata}")
    return metadata


# Extract observations
def extract_observations(lines):
    observations = []
    logging.info(f"Processing total input lines: {len(lines)}")

    valid_start_index = 0
    for i, line in enumerate(lines):
        if line.startswith("DATA START") or "Column 1" in line:
            valid_start_index = i + 1
            break

    for i, line in enumerate(lines[valid_start_index:], start=valid_start_index + 1):
        row = line.strip()
        try:
            if not row or "Column" in row:
                continue

            row_data = next(csv.reader([row]))
            if len(row_data) < 14:
                continue

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


# Save metadata and observations
def save_dataframes(metadata, observations, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = output_dir / "metadata.csv"
    if metadata:
        pd.DataFrame([metadata]).to_csv(metadata_path, index=False)
        logging.info(f"Metadata saved to: {metadata_path}")
    else:
        logging.warning("No metadata available to save.")

    observations_path = output_dir / "observations.csv"
    if observations:
        pd.DataFrame(observations).to_csv(observations_path, index=False)
        logging.info(f"Observations saved to: {observations_path}")
    else:
        logging.warning("No observations available to save.")


# Main function
def main(field_office_code):
    base_dir = Path(__file__).resolve().parent.parent
    input_file = base_dir / f"data/{field_office_code}/raw_metadata/pns_metadata.csv"
    parsed_reports_dir = base_dir / f"data/{field_office_code}/parsed_reports"

    logging.info(f"Processing field office: {field_office_code}")

    if not input_file.is_file():
        logging.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with input_file.open("r") as f:
        lines = f.readlines()

    if not lines:
        logging.error("Input file is empty.")
        raise ValueError("Input file is empty.")

    metadata = extract_metadata(lines)
    observations = extract_observations(lines)

    event_category_mapping = {
        "SNOW": "Winter",
        "SNOW_24": "Winter",
        "TEMPERATURE": "Temperatures",
        "WIND": "Wind",
    }

    for observation in observations:
        event_type = observation["type"]
        event_date = observation["date"]

        # Map event category
        event_category = sanitize_path_component(event_category_mapping.get(event_type.upper(), "Other"))
        formatted_date = sanitize_path_component(event_date.replace("-", "_"))

        # Construct path
        date_dir = parsed_reports_dir / event_category / formatted_date

        # Avoid redundant nesting
        if not date_dir.exists():
            try:
                date_dir.mkdir(parents=True, exist_ok=True)
                logging.info(f"Directory created: {date_dir}")
            except Exception as e:
                logging.error(f"Failed to create directory {date_dir}: {e}")

        # Save observations by type
        csv_file_path = date_dir / f"{event_type.lower()}_observations.csv"
        try:
            if csv_file_path.is_file():
                pd.DataFrame([observation]).to_csv(csv_file_path, mode="a", header=False, index=False)
            else:
                pd.DataFrame([observation]).to_csv(csv_file_path, index=False)
            logging.info(f"Saved observation to: {csv_file_path}")
        except Exception as e:
            logging.error(f"Failed to save observation to {csv_file_path}: {e}")

    # Save metadata
    metadata_file_path = parsed_reports_dir / "metadata.csv"
    try:
        if metadata:
            pd.DataFrame([metadata]).to_csv(metadata_file_path, index=False)
            logging.info(f"Saved metadata to: {metadata_file_path}")
        else:
            logging.warning("No metadata available to save.")
    except Exception as e:
        logging.error(f"Failed to save metadata file: {e}")


if __name__ == "__main__":
    try:
        setup_logging()
        main("OKX")  # Replace with your field office code
    except Exception as e:
        logging.critical(f"Critical error during processing: {e}")
