import requests
from bs4 import BeautifulSoup
import pandas as pd
from settings import Config
import logging

# Initialize configuration
config = Config()

# Configure logging
logging.basicConfig(filename=config.log_file, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_pns_page(page_number=1):
    """Scrape a single page of PNS reports."""
    # Include all required parameters for the request
    params = {
        "site": "OKX",               # Specific site
        "issuedby": "OKX",           # Issued by the OKX office
        "product": "PNS",            # Public Information Statement
        "format": "CI",              # Compact format
        "version": page_number,      # Page/version number
        "glossary": "0"              # No glossary
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Send the GET request with correct parameters
        response = requests.get(config.BASE_URL, params=params, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching page {page_number}: {e}")
        print(f"Error fetching page {page_number}: {e}")
        return []  # Return an empty list if there's an error

    # Parse the response content
    soup = BeautifulSoup(response.text, 'html.parser')
    reports = []
    for item in soup.find_all('pre'):  # Assuming PNS data is wrapped in <pre> tags
        report_text = item.text.strip()
        reports.append({"report": report_text})
    return reports

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

def scrape_all_pns(max_pages=config.MAX_PAGES):
    """Scrape multiple pages of PNS reports and preserve new data."""
    all_reports = []
    existing_data = load_existing_data()

    for page in range(1, max_pages + 1):
        try:
            print(f"Scraping page {page}...")
            reports = scrape_pns_page(page)
            for report in reports:
                if report["report"] not in existing_data["report"].values:
                    all_reports.append(report)
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    # Combine new data with existing data
    if all_reports:
        new_data = pd.DataFrame(all_reports)
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        save_to_csv(combined_data, config.pns_reports_file)
    else:
        print("No new data to save.")

# Main execution
if __name__ == "__main__":
    scrape_all_pns(max_pages=config.MAX_PAGES)
