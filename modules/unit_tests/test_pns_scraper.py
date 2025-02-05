import requests
from modules import fetch_page
from unittest.mock import patch, Mock


@patch("requests.get")
def test_fetch_page_success_car(mock_get):
    """Test successful fetching of a page for field office CAR"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html>Valid HTML Content</html>"
    mock_get.return_value = mock_response

    field_office = "CAR"
    page = 1

    result = fetch_page(field_office, page)
    assert result == "<html>Valid HTML Content</html>"
    mock_get.assert_called_once()


@patch("requests.get")
def test_fetch_page_404_car(mock_get):
    """Test fetching a non-existent page (404 error) for field office CAR"""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    field_office = "CAR"
    page = 2

    result = fetch_page(field_office, page)
    assert result is None
    mock_get.assert_called_once()


@patch("requests.get")
def test_fetch_page_no_station_id_for_car(mock_get):
    """Test fetching a page with an invalid field office instead of CAR"""
    field_office = "INVALID"
    page = 1

    result = fetch_page(field_office, page)
    assert result is None
    mock_get.assert_not_called()


@patch("requests.get")
def test_fetch_page_request_exception_car(mock_get):
    """Test handling of a request exception when fetching a page for field office CAR"""
    mock_get.side_effect = Exception("Request failed")

    field_office = "CAR"
    page = 1

    result = fetch_page(field_office, page)
    assert result is None
    mock_get.assert_called_once()


@patch("requests.get")
def test_fetch_page_timeout_car(mock_get):
    """Test timeout handling when fetching a page for field office CAR"""
    mock_get.side_effect = requests.exceptions.Timeout

    field_office = "CAR"
    page = 1

    result = fetch_page(field_office, page)
    assert result is None
    mock_get.assert_called_once()
