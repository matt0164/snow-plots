#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import csv


def extract_station_links(url):
    """
    Fetches the webpage at `url`, parses it, and returns a list of dictionaries,
    each containing:
      - 'station': the station identifier (extracted from the issuedby query parameter)
      - 'link': the absolute URL to the public information statements.

    It looks for links with query parameters that include:
      - product=PNS
      - issuedby=<station identifier>
    """
    response = requests.get(url)
    response.raise_for_status()

    base_url = response.url  # in case of redirects
    soup = BeautifulSoup(response.text, 'html.parser')
    stations = []

    # Iterate over all anchor tags
    for a in soup.find_all('a', href=True):
        # Build absolute URL
        abs_link = urljoin(base_url, a['href'])
        parsed = urlparse(abs_link)
        qs = parse_qs(parsed.query)

        # Look for links with product=PNS and an issuedby parameter.
        if qs.get("product", [""])[0] == "PNS" and "issuedby" in qs:
            station_id = qs["issuedby"][0]
            stations.append({"station": station_id, "link": abs_link})

    return stations


def deduplicate_by_station(station_list):
    """
    Deduplicate the list of station links so that only one (the first encountered)
    link is kept for each station.

    Returns a dictionary mapping station identifiers to their link.
    """
    unique = {}
    for item in station_list:
        station = item["station"]
        if station not in unique:
            unique[station] = item["link"]
    return unique


def write_csv(filename, data):
    """
    Writes a list of dictionaries with keys 'station' and 'link' to a CSV file.
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["station", "link"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def main():
    url = "https://forecast.weather.gov/product_sites.php?site=NWS&product=PNS"
    station_links = extract_station_links(url)
    unique_stations = deduplicate_by_station(station_links)

    # Create a sorted list of stations for CSV output
    table_data = [{"station": st, "link": unique_stations[st]} for st in sorted(unique_stations.keys())]

    # Write the table to a CSV file in the current folder
    csv_filename = "../reference_data_for_lookup/stations_pns.csv"
    write_csv(csv_filename, table_data)
    print(f"CSV file '{csv_filename}' has been written with {len(table_data)} stations.")


if __name__ == '__main__':
    main()