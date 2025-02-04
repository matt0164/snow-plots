import pytest
from modules.old_or_not_used.pns_scraper import classify_event, load_event_codes

# Define a mock event codes mapping for testing
event_mapping_mock = {
    "SNOW_24": "Snowfall",
    "PKGUST": "Wind Gust",
    "FLOOD": "Flood",
    "RAIN": "Rainfall",
    "HAIL": "Hail",
    "TORNADO": "Tornado",
    "HEAVY_SNOW": "Heavy Snowfall"
}

@pytest.mark.parametrize("event_code, expected", [
    ("SNOW_24", "Snowfall"),
    ("PKGUST", "Wind Gust"),
    ("FLOOD", "Flood"),
    ("RAIN", "Rainfall"),
    ("HAIL", "Hail"),
    ("TORNADO", "Tornado"),
    ("HEAVY_SNOW", "Heavy Snowfall"),
    ("UNKNOWN_CODE", "Unknown")  # Should return Unknown for unrecognized codes
])
def test_event_type_extraction(event_code, expected):
    """Test event classification against known event types"""
    result = classify_event(event_code, event_mapping_mock)
    assert result == expected, f"Expected {expected} but got {result}"


def test_load_event_codes():
    """Test loading event codes from a CSV file."""
    file_path = "reference_data_for_lookup/event_codes.csv"
    event_mapping = load_event_codes(file_path)

    assert isinstance(event_mapping, dict), "Expected a dictionary mapping"
    assert "SNOW_24" in event_mapping, "SNOW_24 should be in the event mapping"
    assert "PKGUST" in event_mapping, "PKGUST should be in the event mapping"
    assert "FLOOD" in event_mapping, "FLOOD should be in the event mapping"
    assert "RAIN" in event_mapping, "RAIN should be in the event mapping"

