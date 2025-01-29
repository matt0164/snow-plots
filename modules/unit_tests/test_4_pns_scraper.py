import sys
import os
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

# Add the project root to sys.path so pytest can find pns_scraper.py
sys.path.append(str(Path(__file__).resolve().parents[1]))

from pns_scraper import save_metadata_to_csv


@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_directory_creation_and_metadata_saving(mock_file, mock_makedirs):
    """Test that the correct directories are created and metadata is saved."""

    field_office = "OKX"
    event_type = "WIND"
    event_name = "High_Wind_Event"
    date = "2025-01-28"

    expected_dir = f"../{field_office}/Parsed Reports/{event_type}/{event_name}/{date}"
    expected_file_path = os.path.join(expected_dir, "pns_metadata.csv")

    metadata = [
        "1/19/2025,1000 PM, CT, Fairfield, 5.0 inches"
    ]

    # Call function to test directory creation
    save_metadata_to_csv("METADATA", metadata, field_office, event_type, event_name, date)

    # Assert that the correct directory was created
    mock_makedirs.assert_called_with(expected_dir, exist_ok=True)

    # Assert that the correct file path was used
    mock_file.assert_called_with(expected_file_path, "a", encoding="utf-8")
