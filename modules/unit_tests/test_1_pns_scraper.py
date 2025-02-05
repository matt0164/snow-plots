import pytest
import requests
from unittest.mock import patch, mock_open
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

def test_parse_metadata():
    """Test extracting metadata from sample HTML"""
    header, metadata = parse_metadata(MOCK_HTML)
    assert header == "METADATA"
    assert len(metadata) == 1
    assert metadata[0] == "1/19/2025,1000 PM, CT, Fairfield, Stamford, , , 41.02, -73.56, SNOW_24, 2, Inch, Public, 24 hour snowfall"

@patch("builtins.open", new_callable=mock_open)
def test_save_metadata_to_csv(mock_file):
    """Test saving metadata to a CSV file"""
    metadata = ["1/19/2025,1000 PM, CT, Fairfield, Stamford, , , 41.02, -73.56, SNOW_24, 2, Inch, Public, 24 hour snowfall"]
    save_metadata_to_csv("METADATA", metadata, "OKX")
    mock_file.assert_called_with("../data/OKX/raw_metadata/pns_metadata.csv", "a", encoding="utf-8")
