"""
PNS Metadata Scraper with Pagination

This script fetches multiple Public Information Statement (PNS) pages from the National Weather Service (NWS),
parses each page for metadata, and writes all pages into a single CSV file for the specified field office.
Pagination is supported with a defined maximum number of pages.
"""

import os
import requests
from bs4 import BeautifulSoup
import logging
import csv

# --------------------------------------------------------
# Configuration Section
# --------------------------------------------------------

# Paths to reference data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DIR = os.path.join(BASE_DIR, "../reference_data_for_lookup")

EVENT_CODES_FILE = os.path.join(REFERENCE_DIR, "event_codes.csv")
FIELD_OFFICES_FILE = os.path.join(REFERENCE_DIR, "field_offices.csv")

DATA_DIR = os.path.join(BASE_DIR, "../data")
LOGS_DIR = os.path.join(BASE_DIR, "../logs")

BASE_URL = "https://forecast.weather.gov/product.php?site=NWS&product=PNS&issuedby={field_office}&page={page}"

MAX_PAGES = 18  # Max number of pages to scrape


# --------------------------------------------------------
# Helper Functions
# --------------------------------------------------------

def load_event_codes(file_path):
    """Load event codes from a reference CSV file."""
    event_mapping = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                event_mapping[row['EventCode']] = row['EventType']
        logging.info(f"✅ Loaded event codes from {file_path}")
    except Exception as e:
        logging.error(f"❌ Error loading event codes: {e}")
    return event_mapping


def load_field_offices(file_path):
    """Load field offices from a reference CSV file."""
    field_offices = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                field_offices[row['FieldOffice']] = row['Identifier']
        logging.info(f"✅ Loaded field offices from {file_path}")
    except Exception as e:
        logging.error(f"❌ Error loading field offices: {e}")
    return field_offices


def classify_event(event_code, event_mapping):
    """Classify event based on event code using the mapping."""
    event_type = event_mapping.get(event_code, "Unknown")

    # Ensure consistent naming format (use title case)
    return event_type.replace("_", " ").title()

# Load data files
event_mapping = load_event_codes(EVENT_CODES_FILE)
field_offices = load_field_offices(FIELD_OFFICES_FILE)

# --------------------------------------------------------
# Logging Setup
# --------------------------------------------------------

LOG_FILE = os.path.join(LOGS_DIR, "pns_scraper.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)


# --------------------------------------------------------
# Main Functions
# --------------------------------------------------------

def fetch_page(field_office, page):
    """Fetch the HTML content from the given URL for the specified field office and page."""
    formatted_url = BASE_URL.format(field_office=field_office, page=page)
    try:
        logging.info(f"Fetching page content from: {formatted_url}")
        response = requests.get(formatted_url, timeout=10)
        if response.status_code == 404:
            logging.warning(f"Page {page} does not exist for field office {field_office}. Stopping pagination.")
            return None
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing page {page} for field office {field_office}: {e}")
        return None


def parse_metadata(html):
    """
    Parses PNS metadata from raw HTML content.

    Args:
        html (str): Raw HTML content.

    Returns:
        tuple: (header, metadata_list) where metadata_list contains parsed lines.
    """
    soup = BeautifulSoup(html, "html.parser")
    pre_tag = soup.find("pre", {"class": "glossaryProduct"})

    if not pre_tag:
        logging.warning("⚠️ No <pre> tag with class 'glossaryProduct' found.")
        return None, []

    logging.info("✅ Found <pre> tag. Extracting metadata...")

    # Ensure metadata lines are separated properly
    lines = pre_tag.get_text("\n", strip=True).split("\n")

    header = None
    metadata = []

    for line in lines:
        line = line.strip()
        if "**METADATA**" in line:
            header = line.strip("*").strip()
        elif line.startswith(":"):
            metadata.append(line.lstrip(":"))  # Strip leading `:` from metadata entries

    if not metadata:
        logging.warning("⚠️ No metadata extracted.")

    return header, metadata


def save_metadata_to_csv(header, metadata, field_office, event_code, date):
    """Save extracted metadata into structured CSV file with correct classification."""

    event_type = classify_event(event_code, event_mapping)

    # Ensure unknown event types go into "Miscellaneous"
    if event_type == "Unknown":
        logging.warning(f"⚠️ Unrecognized event code '{event_code}'. Saving under 'Miscellaneous'.")
        event_type = "Miscellaneous"

    base_dir = os.path.join(DATA_DIR, field_office, "Parsed Reports", event_type, date)
    os.makedirs(base_dir, exist_ok=True)

    file_path = os.path.join(base_dir, "pns_metadata.csv")

    try:
        with open(file_path, "a", encoding="utf-8") as f:
            if os.stat(file_path).st_size == 0:
                f.write(f"{header}\n")  # Write header if file is new
            for row in metadata:
                f.write(",".join(row.split(",")) + "\n")  # Ensure CSV formatting

        logging.info(f"✅ Metadata successfully saved to {file_path}")
    except Exception as e:
        logging.error(f"❌ Error saving metadata to {file_path}: {e}")


# --------------------------------------------------------
# Main Execution
# --------------------------------------------------------

def main():
    """Main function to fetch, parse, and save PNS metadata for all field offices."""
    for field_office in field_offices.keys():
        for page in range(1, MAX_PAGES + 1):
            logging.info(f"Processing field office: {field_office}, page: {page}")

            html = fetch_page(field_office, page)
            if not html:
                break

            header, metadata = parse_metadata(html)
            if not metadata:
                logging.info(f"No metadata found on page {page}. Stopping pagination for office '{field_office}'.")
                break

            # Extract date and event code
            first_entry = metadata[0].split(",")
            event_code = first_entry[8] if len(first_entry) > 8 else "Unknown"
            date_parts = first_entry[0].split("/")
            date = f"{date_parts[2]}-{date_parts[0].zfill(2)}-{date_parts[1].zfill(2)}" if len(
                date_parts) == 3 else "Unknown"

            save_metadata_to_csv(header, metadata, field_office, event_code, date)


if __name__ == "__main__":
    main()
