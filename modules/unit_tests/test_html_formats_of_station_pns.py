import requests
import pandas as pd
import time
import os

# Load field offices CSV file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
file_path = os.path.join(PROJECT_ROOT, "reference_data_for_lookup/field_offices.csv")
field_offices_df = pd.read_csv(file_path)

# Define the base URL for checking formats
BASE_URL_1 = "https://forecast.weather.gov/product.php?site=NWS&product=PNS&issuedby={station_id}&page=1"


# Function to check if a URL is valid and determine format type
def check_html_format(station_id):
    url_1 = BASE_URL_1.format(station_id=station_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response_1 = requests.get(url_1, headers=headers, timeout=10)
        if response_1.status_code == 200:
            return "Pass"  # URL works
    except requests.exceptions.RequestException:
        pass  # Ignore request errors

    return "Fail"  # URL fails


# Check HTML format for each field office
for index, row in field_offices_df.iterrows():
    station_id = row["Identifier"]
    field_offices_df.at[index, "Detected_HTML_Format_1"] = check_html_format(station_id)
    print(f"Checked {station_id}, format: {field_offices_df.at[index, 'Detected_HTML_Format_1']}")
    time.sleep(2)  # Sleep to prevent rate-limiting

# Save updated CSV file
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
output_path = os.path.join(LOGS_DIR, "detected_html_format_1.csv")
field_offices_df.to_csv(output_path, index=False)
print(f"Updated file saved as {output_path}")
