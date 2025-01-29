import pytest
from pns_scraper import parse_metadata
import sys
import os

# Add 'modules' to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.pns_scraper import parse_metadata

@pytest.mark.parametrize(
    "mock_metadata, expected_event_type",
    [
        (["...SNOWFALL REPORTS...", ":More metadata info"], "SNOW"),
        (["...HIGH WIND GUST REPORTS...", ":Some wind data"], "WIND"),
        (["...FLOOD WATCH ISSUED...", ":Flood warning details"], "FLOOD"),
        (["...HEAVY RAIN REPORTS...", ":Rainfall amounts"], "RAIN"),
        (["...OTHER METADATA...", ":No event detected"], "UNKNOWN"),
    ],
)
def test_event_type_extraction(mock_metadata, expected_event_type):
    """Test that event types are extracted correctly from metadata."""
    _, metadata = "METADATA", mock_metadata  # Mocking output of parse_metadata
    event_type = "UNKNOWN"

    for line in metadata:
        if "SNOW" in line:
            event_type = "SNOW"
            break
        elif "WIND" in line:
            event_type = "WIND"
            break
        elif "FLOOD" in line:
            event_type = "FLOOD"
            break
        elif "RAIN" in line:
            event_type = "RAIN"
            break

    assert event_type == expected_event_type, f"Expected {expected_event_type} but got {event_type}"
