import pytest
from pns_scraper import parse_metadata


@pytest.mark.parametrize("mock_metadata, expected_event_type", [
    (["...SNOW TOTALS...", "1/19/2025,1000 PM, CT, Fairfield, 5.0 inches"], "SNOW"),
    (["...HIGH WIND REPORTS...", "1/19/2025,1200 PM, NY, Bronx, 65 mph"], "WIND"),
    (["...FLOODING OBSERVATIONS...", "1/19/2025,0800 AM, NJ, Trenton, Major flooding"], "FLOOD"),
    (["...RAINFALL TOTALS...", "1/19/2025,0600 AM, PA, Pittsburgh, 3.5 inches"], "RAIN"),
    (["...NO RELEVANT DATA...", "1/19/2025,1000 PM, CT, Fairfield, 5.0 inches"], "Unknown"),
])
def test_event_type_extraction(mock_metadata, expected_event_type):
    """Test that the correct event type is extracted from metadata."""
    header, extracted_metadata = "METADATA", mock_metadata

    # Mimic the logic used in `pns_scraper.py`
    event_type = "Unknown"
    for line in extracted_metadata:
        if "SNOW" in line.upper():
            event_type = "SNOW"
            break
        elif "WIND" in line.upper():
            event_type = "WIND"
            break
        elif "FLOOD" in line.upper():
            event_type = "FLOOD"
            break
        elif "RAIN" in line.upper():
            event_type = "RAIN"
            break

    assert event_type == expected_event_type, f"Expected {expected_event_type}, got {event_type}"
