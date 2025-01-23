"""
PNS Metadata Scraper

This script fetches Public Information Statement (PNS) data from the National Weather Service (NWS) webpage,
parses the HTML to extract relevant metadata and its header, and saves the data to a CSV file for analysis.
It also saves logs into a dedicated directory and creates a backup of the fetched HTML.

Key Features:
1. Fetches the PNS webpage data using the `requests` library.
2. Parses the HTML content to extract key data using `BeautifulSoup`.
3. Saves extracted metadata to a CSV file in `/raw_metadata` directory.
4. Saves a backup of the raw HTML to `/backup` directory.
5. Logs all actions and errors into `/logs/pns_scraper.log`.

Note:
Run this script from the `modules/` directory to ensure relative paths are properly resolved.
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
BASE_URL = "https://forecast.weather.gov/product.php?site=NWS&product=PNS&issuedby=OKX"

# Directories and file paths
LOGS_DIR = "../logs/"  # Logs directory
RAW_METADATA_DIR = "../data/raw_metadata/"  # New directory for raw metadata (CSV files)
BACKUP_DIR = "../data/backup/"  # Directory for raw HTML backups

LOG_FILE = os.path.join(LOGS_DIR, "pns_scraper.log")  # Log file path
BACKUP_HTML = os.path.join(BACKUP_DIR, "pns_backup.html")  # Backup HTML file path
DATA_FILE = os.path.join(RAW_METADATA_DIR, "pns_metadata.csv")  # Metadata CSV file path

# Ensure all required directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(RAW_METADATA_DIR, exist_ok=True)  # Ensure /raw_metadata directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

# --------------------------------------------------------
# Logging Setup
# --------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Save log messages to a file
        logging.StreamHandler()  # Also display log messages on the console
    ]
)


# --------------------------------------------------------
# Functions
# --------------------------------------------------------

def fetch_page(url):
    """
    Fetch the HTML content from the given URL.

    Args:
        url (str): The URL to fetch data from.

    Returns:
        str: The raw HTML content of the page.

    Raises:
        requests.exceptions.RequestException: If there's an issue with the HTTP request.
    """
    try:
        logging.info(f"Fetching page content from: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad HTTP status codes (4xx/5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch page content: {e}")
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


def save_metadata_to_csv(header, metadata, file_path):
    """
    Save the extracted metadata and header into a CSV file.

    Args:
        header (str): The metadata header (e.g., '**METADATA**').
        metadata (list): A list of metadata strings extracted from the page.
        file_path (str): The path where the CSV file should be saved.

    Returns:
        None
    """
    # Create a DataFrame by splitting metadata lines into fields
    data_rows = [row.split(",") for row in metadata]
    df = pd.DataFrame(data_rows)

    # Auto-generate column headers based on the number of columns
    df.columns = [f"Column {i + 1}" for i in range(len(df.columns))]

    # Save header and metadata rows to the CSV file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"{header}\n")  # Write the header at the top of the file
    df.to_csv(file_path, index=False, mode="a")  # Append metadata rows in CSV mode
    logging.info(f"Metadata saved to: {file_path}")


def save_html_backup(html, file_path):
    """
    Save a backup of the fetched HTML content to the specified file.

    Args:
        html (str): The raw HTML content.
        file_path (str): The file path where the backup HTML should be saved.

    Returns:
        None
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    logging.info(f"Backup HTML saved to: {file_path}")


# --------------------------------------------------------
# Main Execution
# --------------------------------------------------------

def main():
    """
    Main function to fetch, parse, and save PNS metadata.
    """
    try:
        # Step 1: Fetch the PNS page HTML content
        html = fetch_page(BASE_URL)

        # Step 2: Save a backup of the raw HTML
        save_html_backup(html, BACKUP_HTML)

        # Step 3: Parse the metadata and header from the HTML
        header, metadata = parse_metadata(html)

        if not metadata:
            logging.warning("No metadata found in the PNS report. Exiting...")
            return

        # Step 4: Save the metadata to a CSV file in /raw_metadata
        save_metadata_to_csv(header, metadata, DATA_FILE)
        logging.info("Metadata extraction and saving completed successfully!")

    except Exception as e:
        logging.error(f"An error occurred during the process: {e}")


if __name__ == "__main__":
    main()
