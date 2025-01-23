from pathlib import Path
import pandas as pd
import logging
import os


def extract_metadata(lines):
    # Placeholder logic for metadata extraction
    return {}


def extract_observations(lines):
    # Placeholder logic for observation extraction
    return []


def save_dataframes(metadata, observations, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_file = output_dir / "metadata.csv"
    pd.DataFrame([metadata]).to_csv(metadata_file, index=False)
    observations_file = output_dir / "observations.csv"
    pd.DataFrame(observations).to_csv(observations_file, index=False)


def main(field_office_code):
    # Setup logger
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Define base directory and input/output paths
    base_dir = Path(__file__).resolve().parent.parent  # Base directory for project
    input_file = base_dir / f"data/{field_office_code}/raw_metadata/pns_metadata.csv"
    output_dir = base_dir / f"data/{field_office_code}/parsed_reports"

    logging.info(f"Base directory: {base_dir}")
    logging.info(f"Input file path: {input_file}")
    logging.info(f"Output directory path: {output_dir}")

    if not input_file.is_file():
        raw_metadata_dir = input_file.parent
        logging.error(
            f"Input file not found. Directory contents: {list(raw_metadata_dir.iterdir()) if raw_metadata_dir.exists() else 'Directory does not exist'}")
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    # Process metadata file
    with input_file.open("r") as f:
        lines = f.readlines()

    metadata = extract_metadata(lines)
    observations = extract_observations(lines)

    # Save dataframes
    save_dataframes(metadata, observations, output_dir)


if __name__ == "__main__":
    main("OKX")
