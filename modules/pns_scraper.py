"""
PNS Metadata Scraper

This script fetches Public Information Statement (PNS) data from the National Weather Service (NWS) webpage,
parses the HTML to extract relevant metadata and its header, and saves the data to a CSV file for analysis.
It also saves logs into a dedicated directory and creates a backup of the fetched HTML.
"""

import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging

# --------------------------------------------------------
# Configuration Section
# --------------------------------------------------------

# Base URL for fetching PNS (Public Information Statement) data
BASE_URL = "https://forecast.weather.gov/product.php?site=NWS&product=PNS&issuedby={field_office}"  # NWS URL template
DEFAULT_FIELD_OFFICE = "OKX"  # Default field office (New York City)
FIELD_OFFICES = ["OKX", "ALY", "BOX", "BTV", "BUF", "CAR", "CXX", "GYX",
                 "OKX"]  # Add full list of field offices as needed

# Directories and file paths
LOGS_DIR = "../logs/"  # Logs directory
DATA_DIR = "../data/"  # Base data directory

BACKUP_HTML_TEMPLATE = os.path.join(DATA_DIR, "{field_office}/backup/pns_backup.html")  # Backup HTML file template
DATA_FILE_TEMPLATE = os.path.join(DATA_DIR,
                                  "{field_office}/raw_metadata/pns_metadata.csv")  # Metadata CSV file template

# Ensure all required directories exist
os.makedirs(LOGS_DIR, exist_ok=True)

# --------------------------------------------------------
# Logging Setup
# --------------------------------------------------------

# Define the LOG_FILE variable for the log file path
LOG_FILE = os.path.join(LOGS_DIR, "pns_scraper.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Save log messages to a file
        logging.StreamHandler()  # Also display log messages on the console
    ]
)


# --------------------------------------------------------
# Helper Functions
# --------------------------------------------------------

def get_user_configured_offices():
    """
    Prompt the user for field office configuration and return the list of selected offices.
    Allows hitting enter to select the default office.
    Returns:
        list: List of field office codes to scrape.
    """
    print(f"Default field office is '{DEFAULT_FIELD_OFFICE}'.")
    user_input = input(
        "Enter a field office code (or 'ALL' for all offices, or press Enter for default): ").strip().upper() or DEFAULT_FIELD_OFFICE
    if user_input == "ALL":
        print("Warning: Scraping all field offices may take a significant amount of time.")
        return FIELD_OFFICES
    if user_input not in FIELD_OFFICES:
        print(f"Invalid field office code. Defaulting to '{DEFAULT_FIELD_OFFICE}'.")
        return [DEFAULT_FIELD_OFFICE]
    return [user_input]


def fetch_page(url, field_office):
    """
    Fetch the HTML content from the given URL for the specified field office.

    Args:
        url (str): The URL template to fetch data from.
        field_office (str): The field office code to replace in the URL.

    Returns:
        str: The raw HTML content of the page.

    Raises:
        Exception: If the page cannot be fetched.
    """
    formatted_url = url.format(field_office=field_office)
    try:
        logging.info(f"Fetching page content from: {formatted_url}")
        response = requests.get(formatted_url, timeout=10)
        response.raise_for_status()  # Raise an error for bad HTTP status codes (4xx/5xx)
        return response.text
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            logging.error(
                f"404 Error: The URL {formatted_url} was not found. Please verify the field office code and URL.")
        else:
            logging.error(f"HTTP Error occurred while fetching data: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch page content for '{field_office}': {e}")
        raise


def parse_metadata(html):
    """
    Parse the PNS metadata and header from the HTML content.

    Args:
        html (str): The raw HTML content fetched from the PNS page.

    Returns:
        tuple: A tuple containing the following:
            - header (str): The metadata header text.
            - metadata (list): A list of metadata lines extracted from the page.

    Raises:
        ValueError: If the expected `<pre>` tag or metadata is not found in the HTML.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Locate the <pre> tag with the class 'glossaryProduct'
    pre_tag = soup.find("pre", {"class": "glossaryProduct"})
    if not pre_tag:
        raise ValueError("No <pre> tag with class 'glossaryProduct' found on the page.")

    logging.info("Found <pre> tag with class 'glossaryProduct'. Extracting metadata...")
    lines = pre_tag.get_text(strip=True).splitlines()  # Extract and split lines of text

    # Extract the header ('**METADATA**') and individual metadata lines (starting with ':')
    header = None
    metadata = []
    for line in lines:
        if "**METADATA**" in line:  # Detect the header
            header = line.strip("**")  # Strip surrounding asterisks
        elif line.startswith(":"):  # Metadata lines start with ':'
            metadata.append(line.strip(":"))  # Remove leading colon for clean formatting

    if not header or not metadata:
        raise ValueError("Failed to find metadata or header in the HTML content.")

    return header, metadata


def save_metadata_to_csv(header, metadata, field_office):
    """
    Save the extracted metadata and header into a CSV file for the specified field office.

    Args:
        header (str): The metadata header (e.g., '**METADATA**').
        metadata (list): A list of metadata strings extracted from the page.
        field_office (str): The field office for the metadata directory.
    """
    file_path = DATA_FILE_TEMPLATE.format(field_office=field_office)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    data_rows = [row.split(",") for row in metadata]
    df = pd.DataFrame(data_rows)
    df.columns = [f"Column {i + 1}" for i in range(len(df.columns))]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"{header}\n")
    df.to_csv(file_path, index=False, mode="a")
    logging.info(f"Metadata saved to: {file_path}")


def save_html_backup(html, field_office):
    """
    Save a backup of the fetched HTML content for the specified field office.

    Args:
        html (str): The raw HTML content.
        field_office (str): The field office for the backup directory.
    """
    file_path = BACKUP_HTML_TEMPLATE.format(field_office=field_office)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    logging.info(f"Backup HTML saved to: {file_path}")


# --------------------------------------------------------
# Main Execution
# --------------------------------------------------------

def main():
    """
    Main function to fetch, parse, and save PNS metadata for user-specified field offices.
    """
    field_offices = get_user_configured_offices()
    for field_office in field_offices:
        try:
            logging.info(f"Processing field office: {field_office}")

            # Step 1: Fetch the field office page HTML content
            html = fetch_page(BASE_URL, field_office)

            # Step 2: Save the raw HTML backup for the field office
            save_html_backup(html, field_office)

            # Step 3: Parse metadata and the header from the HTML
            header, metadata = parse_metadata(html)

            if not metadata:
                logging.warning(f"No metadata found for field office '{field_office}'. Skipping...")
                continue

            # Step 4: Save metadata to a CSV file for the field office
            save_metadata_to_csv(header, metadata, field_office)
            logging.info(f"Completed processing for field office: {field_office}")

        except Exception as e:
            logging.error(f"An error occurred for field office '{field_office}': {e}")
            logging.info(f"Skipping field office: {field_office}")
            continue


if __name__ == "__main__":
    main()
