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
import time

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

BASE_URL_1 = "https://forecast.weather.gov/product.php?site=NWS&product=PNS&issuedby={station_id}&page={page}"
BASE_URL_2 = "https://www.weather.gov/{station_id}/pns"

MAX_PAGES = 30  # Max number of pages to scrape

# --------------------------------------------------------
# Helper Functions
# --------------------------------------------------------

def load_field_offices(file_path):
    """Load field offices with their station identifiers and HTML formats from a reference CSV file."""
    field_offices = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                field_offices[row['FieldOffice']] = {
                    "station_id": row['Identifier'],
                    "html_format": int(row['HTMLFormat'])  # Ensure html_format is an integer
                }
        logging.info(f"✅ Loaded field offices from {file_path}")
    except Exception as e:
        logging.error(f"❌ Error loading field offices: {e}")
    return field_offices

# Load field offices
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
    field_office_data = field_offices.get(field_office, None)
    if not field_office_data:
        logging.error(f"❌ No data found for field office: {field_office}")
        return None

    station_id = field_office_data["station_id"]
    html_format = field_office_data["html_format"]

    # Select the appropriate BASE_URL based on html_format
    if html_format == 1:
        base_url = BASE_URL_1
    elif html_format == 2:
        base_url = BASE_URL_2
    else:
        logging.error(f"❌ Unknown HTML format {html_format} for field office: {field_office}")
        return None

    formatted_url = base_url.format(station_id=station_id, page=page)
    try:
        logging.info(f"Fetching page content from: {formatted_url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(formatted_url, headers=headers, timeout=10)
        time.sleep(2)  # Add delay to prevent rate-limiting

        if response.status_code == 404:
            logging.warning(f"Page {page} does not exist for field office {field_office}. Stopping pagination.")
            return None
        response.raise_for_status()

        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing page {page} for field office {field_office}: {e}")
        return None


def save_metadata_to_csv(header, metadata, field_office):
    """Save extracted metadata into a structured CSV file in raw_metadata directory."""
    base_dir = os.path.join(DATA_DIR, field_office, "raw_metadata")
    os.makedirs(base_dir, exist_ok=True)

    file_path = os.path.join(base_dir, "pns_metadata.csv")

    try:
        with open(file_path, "a", encoding="utf-8") as f:
            if os.stat(file_path).st_size == 0:
                f.write(f"{header}\n")  # Write header if file is new
            for row in metadata:
                f.write(row + "\n")  # Ensure proper CSV formatting

        logging.info(f"✅ Metadata successfully saved to {file_path}")
    except Exception as e:
        logging.error(f"❌ Error saving metadata to {file_path}: {e}")

def main():
    """Main function to fetch PNS metadata for all field offices."""
    for field_office in field_offices.keys():
        all_metadata = []
        header = ""
        first_failure_logged = False

        for page in range(1, MAX_PAGES + 1):
            logging.info(f"Processing field office: {field_office} ({field_offices[field_office]}), page: {page}")
            html = fetch_page(field_office, page)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            pre_tag = soup.find("pre", {"class": "glossaryProduct"})

            if not pre_tag:
                logging.warning(f"No <pre> tag found on page {page}.")
                if not first_failure_logged:
                    logging.info(f"Full HTML Response for {field_office}:{html[:2000]}")
                    first_failure_logged = True
                continue

            lines = pre_tag.get_text("\n", strip=True).split("\n")
            if "**METADATA**" in lines[0]:
                header = lines[0].strip("*").strip()
                metadata = lines[1:]
                all_metadata.extend(metadata)
            else:
                logging.warning(f"No metadata header found on page {page}. Extracted text:")
                logging.info(f"Extracted text:{pre_tag.get_text()}")

        if all_metadata:
            save_metadata_to_csv(header, all_metadata, field_office)
        else:
            logging.warning(f"No metadata found for field office {field_office}.")


if __name__ == "__main__":
    main()
