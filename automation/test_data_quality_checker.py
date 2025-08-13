import pytest
import requests

from automation.data_quality_checker import (
    get_nested_value,
    validate_url,
    validate_email,
    validate_required_fields,
    validate_json_schema
)

# --- Fixtures for test data ---

@pytest.fixture
def sample_dataset():
    """Provides a sample dataset that is mostly valid for testing."""
    return {
        "dct:identifier": "test-id-123",
        "dct:title": "Test Dataset",
        "dcat:contactPoint": {
            "schema:email": "test@example.com"
        },
        "dcat:distribution": [
            {"dcat:accessURL": "https://www.example.com/data.csv"}
        ]
    }

@pytest.fixture
def sample_schema():
    """Provides a minimal schema for validation testing."""
    return {
        "type": "object",
        "required": ["dct:identifier", "dct:title"],
        "properties": {
            "dct:identifier": {"type": "string"},
            "dct:title": {"type": "string"},
        }
    }

# --- Tests for get_nested_value ---

def test_get_nested_value_simple():
    assert get_nested_value({'key': 'value'}, 'key') == 'value'

def test_get_nested_value_nested():
    assert get_nested_value({'a': {'b': 'c'}}, 'a.b') == 'c'

def test_get_nested_value_in_list():
    data = {'items': [{'name': 'A'}, {'name': 'B'}]}
    assert get_nested_value(data, 'items.name') == ['A', 'B']

def test_get_nested_value_missing_key():
    assert get_nested_value({'key': 'value'}, 'missing') is None

# --- Tests for Validators ---

def test_validate_url_valid_and_ok(mocker):
    """Test a valid, reachable URL. `mocker` simulates the web request."""
    mocker.patch('requests.head', return_value=mocker.Mock(ok=True))
    assert validate_url("https://www.google.com") is None
    requests.head.assert_called_once_with("https://www.google.com", allow_redirects=True, timeout=5)

def test_validate_url_not_ok(mocker):
    """Test a valid URL that returns an error status like 404 Not Found."""
    mock_response = mocker.Mock(ok=False, status_code=404)
    mocker.patch('requests.head', return_value=mock_response)
    error = validate_url("https://www.google.com/nonexistent")
    assert "URL not reachable (Status: 404)" in error

def test_validate_url_request_exception(mocker):
    """Test a URL that fails to connect."""
    mocker.patch('requests.head', side_effect=requests.exceptions.ConnectionError("Failed to connect"))
    error = validate_url("https://nonexistent.domain")
    assert "URL check failed (ConnectionError)" in error

def test_validate_url_invalid_format():
    assert "Invalid URL format" in validate_url("not-a-url")

def test_validate_url_mailto():
    """Mailto links should be considered valid without a network check."""
    assert validate_url("mailto:test@example.com") is None

def test_validate_email_valid():
    assert validate_email("test.user@example.co.uk") is None

def test_validate_email_invalid():
    assert "Invalid email format" in validate_email("test@example")

def test_validate_required_fields_present(sample_dataset):
    fields = ["dct:identifier", "dct:title"]
    assert validate_required_fields(sample_dataset, fields) == []

def test_validate_required_fields_missing(sample_dataset):
    fields = ["dct:identifier", "dct:description"]
    errors = validate_required_fields(sample_dataset, fields)
    assert len(errors) == 1
    assert "Required field 'dct:description' is missing" in errors[0]

def test_validate_json_schema_valid(sample_dataset, sample_schema):
    assert validate_json_schema(sample_dataset, sample_schema) == []

def test_validate_json_schema_invalid(sample_dataset, sample_schema):
    del sample_dataset["dct:title"] # Make the data invalid
    errors = validate_json_schema(sample_dataset, sample_schema)
    assert len(errors) == 1
    assert "Schema Error at 'root': 'dct:title' is a required property" in errors[0]

