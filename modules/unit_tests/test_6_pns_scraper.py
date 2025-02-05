import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
from modules import (
    load_event_codes,
    classify_event,
    load_field_offices,
    parse_metadata,
    save_metadata_to_csv,
    fetch_page,
)

# Define test file paths
TEST_EVENT_CODES_FILE = "../reference_data_for_lookup/event_codes.csv"
TEST_FIELD_OFFICES_FILE = "../reference_data_for_lookup/field_offices.csv"


class TestPNSScraper(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open,
           read_data="EventCode,EventType\nSNOW_24,Snowfall\nPKGUST,Wind Gust\nFLOOD,Flood\nRAIN,Rainfall\n")
    def test_load_event_codes(self, mock_file):
        """Test that event codes are loaded properly from CSV"""
        event_mapping = load_event_codes(TEST_EVENT_CODES_FILE)
        self.assertEqual(event_mapping.get("SNOW_24"), "Snowfall")
        self.assertEqual(event_mapping.get("PKGUST"), "Wind Gust")
        self.assertEqual(event_mapping.get("FLOOD"), "Flood")
        self.assertEqual(event_mapping.get("RAIN"), "Rainfall")
        self.assertEqual(classify_event("UNKNOWN", event_mapping), "Unknown")

    @patch("builtins.open", new_callable=mock_open,
           read_data="FieldOffice,Identifier\nOKX,New York-Upton\nALY,Albany\nBOX,Boston-Norton\n")
    def test_load_field_offices(self, mock_file):
        """Test that field offices are loaded properly from CSV"""
        field_offices = load_field_offices(TEST_FIELD_OFFICES_FILE)
        self.assertIn("OKX", field_offices)
        self.assertIn("ALY", field_offices)
        self.assertIn("BOX", field_offices)

    def test_classify_event(self):
        """Test classification of events using the event mapping"""
        event_mapping = {"SNOW_24": "Snowfall", "PKGUST": "Wind Gust"}
        self.assertEqual(classify_event("SNOW_24", event_mapping), "Snowfall")
        self.assertEqual(classify_event("PKGUST", event_mapping), "Wind Gust")
        self.assertEqual(classify_event("UNKNOWN", event_mapping), "Unknown")

    @patch("requests.get")
    def test_fetch_page(self, mock_get):
        """Test fetching page content from NWS"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<pre class='glossaryProduct'>Some PNS Data</pre>"
        mock_get.return_value = mock_response
        response = fetch_page("OKX", 1)
        self.assertIn("Some PNS Data", response)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_save_metadata_to_csv(self, mock_makedirs, mock_file):
        """Test that metadata is saved to the correct directory"""
        metadata = ["1/28/2025,1240 PM, CT, Fairfield, Bridgeport Airport, 41.16, -73.13, SNOW_24, 3, Inch"]
        save_metadata_to_csv("Header", metadata, "OKX", "Snowfall", "2025-01-28")

        # Ensure directory was created correctly
        expected_path = os.path.abspath("../data/OKX/Parsed Reports/Snowfall/2025-01-28")
        mock_makedirs.assert_called()

        # Ensure metadata is being written correctly
        expected_file_path = os.path.join(expected_path, "pns_metadata.csv")
        mock_file.assert_called()

    def test_parse_metadata(self):
        """Test parsing metadata from HTML content"""
        html_content = """
        <html>
            <pre class='glossaryProduct'>
**METADATA**
1/28/2025,1240 PM, CT, Fairfield, Bridgeport Airport, 41.16, -73.13, SNOW_24, 3, Inch
            </pre>
        </html>
        """
        header, metadata = parse_metadata(html_content.strip())
        pre_content = html_content.split("<pre class='glossaryProduct'>")[1].split("</pre>")[0].strip()
        print("Extracted <pre> content:", pre_content)  # Debugging output

        # Extract header and metadata correctly
        lines = pre_content.split("\n", 1)
        extracted_header = lines[0].strip() if len(lines) > 0 else ""
        extracted_metadata = lines[1].strip() if len(lines) > 1 else ""

        print("Extracted Header:", extracted_header)
        print("Extracted Metadata:", extracted_metadata)

        self.assertEqual(extracted_header, "**METADATA**")
        self.assertIsNotNone(extracted_metadata, "Metadata should not be None")
        self.assertGreaterEqual(len(extracted_metadata), 1, "Metadata should not be empty")
        self.assertIn("1/28/2025,1240 PM, CT, Fairfield, Bridgeport Airport, 41.16, -73.13, SNOW_24, 3, Inch",
                      extracted_metadata)


if __name__ == "__main__":
    unittest.main()
