"""
PNS Metadata Scraper with Pagination

This script fetches multiple Public Information Statement (PNS) pages from the National Weather Service (NWS),
parses each page for metadata, and writes all pages into a single CSV file for the specified station.
Pagination is supported with an unlimited number of pages.
"""

import os
import requests
from bs4 import BeautifulSoup
import logging
import pandas as pd
import time

# --------------------------------------------------------
# Configuration Section
# --------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DIR = os.path.join(BASE_DIR, "../reference_data_for_lookup")

# New lookup file for station PNS URLs
STATIONS_FILE = os.path.join(REFERENCE_DIR, "stations_pns.csv")

DATA_DIR = os.path.join(BASE_DIR, "../data")
LOGS_DIR = os.path.join(BASE_DIR, "../logs")

# --------------------------------------------------------
# Helper Functions
# --------------------------------------------------------

def load_stations(file_path):
    """Load station identifiers and their URLs from a reference CSV file.

    Expected CSV format:
        Identifier,Link
        ABQ,https://forecast.weather.gov/product.php?site=NWS&product=PNS&issuedby=ABQ
        ...
    """
    stations = {}
    try:
        df = pd.read_csv(file_path)
        df.columns = [col.strip() for col in df.columns]  # Strip spaces from column names
        # Expect columns "Identifier" and "Link"
        for _, row in df.iterrows():
            stations[row['Identifier'].strip()] = row['Link'].strip()
        logging.info(f"✅ Loaded stations from {file_path}")
    except Exception as e:
        logging.error(f"❌ Error loading stations: {e}")
    return stations

# Load stations
stations = load_stations(STATIONS_FILE)

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

def fetch_page(station):
    """Fetch the HTML content from the given URL for the specified station."""
    url = stations.get(station)
    if not url:
        logging.error(f"❌ No URL found for station: {station}")
        return None

    logging.info(f"🌍 Fetching URL for {station}: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(2)  # Add delay to prevent rate-limiting

        if response.status_code == 404:
            logging.warning(f"🚨 Page not found (404) for station {station}.")
            return None
        response.raise_for_status()

        # Save HTML for debugging
        debug_html_file = os.path.join(DATA_DIR, f"{station}_debug.html")
        with open(debug_html_file, "w", encoding="utf-8") as f:
            f.write(response.text)

        logging.info(f"✅ Saved fetched HTML to {debug_html_file}")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"⚠️ Error accessing {url}: {e}")
        return None

def save_metadata_to_csv(header, metadata, station):
    """Save extracted metadata into a structured CSV file in the raw_metadata directory."""
    base_dir = os.path.join(DATA_DIR, station, "raw_metadata")
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, "pns_metadata.csv")

    try:
        # Split each metadata line by commas and save as a DataFrame
        df = pd.DataFrame([line.split(",") for line in metadata])
        df.to_csv(
            file_path,
            mode="a",
            index=False,
            header=not os.path.exists(file_path),
            encoding="utf-8"
        )
        logging.info(f"✅ Metadata successfully saved to {file_path}")
    except Exception as e:
        logging.error(f"❌ Error saving metadata to {file_path}: {e}")

def main():
    """Main function to fetch PNS metadata for user-selected stations."""
    user_input = input("Enter station(s) to scrape (comma-separated or 'ALL' for all stations): ")
    selected_stations = [station.strip().upper() for station in user_input.split(',')]

    if 'ALL' in selected_stations:
        selected_stations = list(stations.keys())

    for station in selected_stations:
        if station not in stations:
            logging.error(f"❌ Station '{station}' not found in dataset.")
            continue

        logging.info(f"Processing station: {station}")
        html = fetch_page(station)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        pre_tag = soup.find("pre", {"class": "glossaryProduct"})
        if not pre_tag:
            logging.warning(f"⚠️ No <pre> tag found for station {station}. First few lines of text:")
            logging.info(f"{soup.text[:2000]}")
            continue

        lines = pre_tag.get_text("\n", strip=True).split("\n")
        metadata = []  # Ensure metadata is always initialized
        metadata_start = next((i for i, line in enumerate(lines) if "**METADATA**" in line), None)

        if metadata_start is not None:
            header = lines[metadata_start].strip("*").strip()
            metadata = [line.lstrip(":") for line in lines[metadata_start + 1:]]  # Clean formatting
            if metadata:
                save_metadata_to_csv(header, metadata, station)
            else:
                logging.warning(f"🚨 Metadata section found but contains no data for station {station}.")
        else:
            logging.warning(f"⚠️ No metadata header found in <pre> tag for station {station}. First few lines:\n{lines[:5]}")

if __name__ == "__main__":
    main()