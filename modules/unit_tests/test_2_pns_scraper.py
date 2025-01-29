import pytest
import requests
import os
import logging
from unittest.mock import patch, mock_open, MagicMock
from pns_scraper import fetch_page, parse_metadata, save_metadata_to_csv

# Sample HTML response with metadata
MOCK_HTML = """
<pre class="glossaryProduct">
**METADATA**
:1/19/2025,1000 PM, CT, Fairfield, Stamford, , , 41.02, -73.56, SNOW_24, 2, Inch, Public, 24 hour snowfall
</pre>
"""

@pytest.fixture
def mock_response():
    """Mocks a requests response with sample HTML"""
    mock_resp = requests.models.Response()
    mock_resp.status_code = 200
    mock_resp._content = MOCK_HTML.encode()
    return mock_resp

@patch("requests.get")
def test_fetch_page(mock_get, mock_response):
    """Test fetching a PNS page with a mock response"""
    mock_get.return_value = mock_response
    url = "https://fake.url/{field_office}/page={page}"
    html = fetch_page(url, "OKX", 1)
    assert "**METADATA**" in html

@patch("requests.get")
def test_pagination_handling(mock_get):
    """Test pagination stops when a page is missing (404)"""
    mock_get.return_value.status_code = 404
    html = fetch_page("https://fake.url/{field_office}/page={page}", "OKX", 999)
    assert html is None  # Should return None when page is missing

def test_parse_metadata():
    """Test extracting metadata from sample HTML"""
    header, metadata = parse_metadata(MOCK_HTML)
    assert header == "METADATA"
    assert len(metadata) == 1
    assert metadata[
        0] == "1/19/2025,1000 PM, CT, Fairfield, Stamford, , , 41.02, -73.56, SNOW_24, 2, Inch, Public, 24 hour snowfall"

@patch("builtins.open", new_callable=mock_open)
@patch("os.makedirs")
def test_file_structure(mock_makedirs, mock_file):
    """Test correct file structure for saving"""
    field_office = "OKX"
    event_type = "SNOW"
    event_name = "Snowstorm_012025"
    date = "2025-01-19"

    expected_path = f"../{field_office}/Parsed Reports/{event_type}/{event_name}/{date}/pns_metadata.csv"
    metadata = [
        "1/19/2025,1000 PM, CT, Fairfield, Stamford, , , 41.02, -73.56, SNOW_24, 2, Inch, Public, 24 hour snowfall"
    ]

    save_metadata_to_csv("METADATA", metadata, field_office, event_type, event_name, date)

    mock_makedirs.assert_called_with(os.path.dirname(expected_path), exist_ok=True)
    mock_file.assert_called_with(expected_path, "a", encoding="utf-8")

@patch("logging.warning")
def test_logging_on_failure(mock_log):
    """Test that a warning is logged when metadata parsing fails"""
    parse_metadata("<html></html>")  # No metadata in this HTML
    mock_log.assert_called_with("No <pre> tag with class 'glossaryProduct' found. This page may not contain relevant metadata.")
