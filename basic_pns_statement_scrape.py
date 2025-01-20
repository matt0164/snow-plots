import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from pathlib import Path
import logging

# Configuration Class
class Config:
    BASE_PROJECT_DIR = Path("/Users/mattalevy/PycharmProjects/snow-plots")
    CONFIG_FILE = BASE_PROJECT_DIR / "config.txt"
    BASE_URL = "https://forecast.weather.gov/product.php"
    MAX_PAGES = 100  # Arbitrary high value to ensure all versions are captured

    def __init__(self):
        self.base_dir = self.BASE_PROJECT_DIR
        self.data_dir = self.base_dir / "data"
        self.backup_dir = self.data_dir / "backup"
        self.pns_reports_file = self.data_dir / "pns_reports.csv"
        self.log_file = self.base_dir / "logs" / "scraping.log"
        self.setup_directories()

    def setup_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.log_file.parent, exist_ok=True)

# Initialize configuration
config = Config()

# Configure logging
logging.basicConfig(filename=config.log_file, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Functions
def get_total_versions():
    """Determine the total number of versions available on the webpage."""
    params = {
        "site": "OKX",
        "issuedby": "OKX",
        "product": "PNS",
        "format": "CI",
        "version": 1,
        "glossary": "0"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(config.BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the dropdown or links indicating the total number of versions
        version_links = soup.find_all('a', href=True)
        version_numbers = [
            int(link['href'].split('version=')[-1])
            for link in version_links if 'version=' in link['href']
        ]
        if version_numbers:
            return max(version_numbers)
    except Exception as e:
        logging.error(f"Error detecting total versions: {e}")
        print(f"Error detecting total versions: {e}")
    return 0  # Default to 0 if detection fails

def scrape_pns_page(page_number=1):
    """Scrape a single page of PNS reports."""
    params = {
        "site": "OKX",
        "issuedby": "OKX",
        "product": "PNS",
        "format": "CI",
        "version": page_number,
        "glossary": "0"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(config.BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract PNS reports
        reports = []
        for item in soup.find_all('pre'):  # Assuming PNS data is wrapped in <pre> tags
            report_text = item.text.strip()
            reports.append({"report": report_text})
        return reports
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching page {page_number}: {e}")
        print(f"Error fetching page {page_number}: {e}")
        return []  # Return an empty list if there's an error

def load_existing_data():
    """Load existing data from the CSV file, if it exists."""
    if config.pns_reports_file.exists():
        print(f"Loading existing data from {config.pns_reports_file}...")
        return pd.read_csv(config.pns_reports_file)
    else:
        print("No existing data found.")
        return pd.DataFrame(columns=["report"])

def save_to_csv(data, filename):
    """Save data to a CSV file."""
    print(f"Saving data to {filename}...")
    data.to_csv(filename, index=False)
    print(f"Data saved successfully to {filename}")

def scrape_all_pns():
    """Scrape all available versions of PNS reports and preserve new data."""
    total_versions = get_total_versions()
    if total_versions == 0:
        print("No versions detected. Exiting.")
        return

    print(f"Detected {total_versions} versions. Starting scrape...")
    all_reports = []
    existing_data = load_existing_data()

    for version in range(1, total_versions + 1):
        try:
            print(f"Scraping version {version}...")
            reports = scrape_pns_page(version)
            for report in reports:
                if report["report"] not in existing_data["report"].values:
                    all_reports.append(report)
        except Exception as e:
            print(f"Error on version {version}: {e}")
            continue

    # Combine new data with existing data
    if all_reports:
        new_data = pd.DataFrame(all_reports)
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        save_to_csv(combined_data, config.pns_reports_file)
    else:
        print("No new data to save.")

# Main execution
if __name__ == "__main__":
    scrape_all_pns()
