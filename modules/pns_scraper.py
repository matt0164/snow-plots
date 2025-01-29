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

BASE_URL = "https://forecast.weather.gov/product.php?site=NWS&product=PNS&issuedby={station_id}&page={page}"

MAX_PAGES = 18  # Max number of pages to scrape


# --------------------------------------------------------
# Helper Functions
# --------------------------------------------------------

def load_field_offices(file_path):
    """Load field offices and their station identifiers from a reference CSV file."""
    field_offices = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                field_offices[row['FieldOffice']] = row['Identifier']  # Store proper station ID
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
    station_id = field_offices.get(field_office, None)
    if not station_id:
        logging.error(f"❌ No station ID found for field office: {field_office}")
        return None

    formatted_url = BASE_URL.format(station_id=station_id, page=page)
    try:
        logging.info(f"Fetching page content from: {formatted_url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(formatted_url, headers=headers, timeout=10)
        if response.status_code == 404:
            logging.warning(f"Page {page} does not exist for field office {field_office}. Stopping pagination.")
            return None
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing page {page} for field office {field_office}: {e}")
        return None


def main():
    """Main function to fetch PNS metadata for all field offices."""
    for field_office in field_offices.keys():
        for page in range(1, MAX_PAGES + 1):
            logging.info(f"Processing field office: {field_office} ({field_offices[field_office]}), page: {page}")
            html = fetch_page(field_office, page)
            if not html:
                break


if __name__ == "__main__":
    main()
