import requests
from bs4 import BeautifulSoup
import pandas as pd
from settings import Config

# Initialize configuration
config = Config()

def scrape_pns_page(page_number=1):
    """Scrape a single page of PNS reports."""
    params = {
        "page": page_number  # Pagination for multiple PNS pages
    }
    response = requests.get(config.BASE_URL, params=params)
    response.raise_for_status()  # Ensure the request was successful
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract PNS metadata (e.g., title, timestamp, and content)
    reports = []
    for item in soup.find_all('pre'):  # Assuming PNS data is wrapped in <pre> tags
        report_text = item.text
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

def scrape_all_pns(max_pages=5):
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
