import pytest
import requests
import json
from unittest.mock import patch

# --- Import all functions from the script to be tested ---
from data_quality_checker import (
    get_nested_value,
    validate_url,
    validate_email,
    validate_required_fields,
    validate_json_schema,
    check_presence,
    calculate_findability_score,
    calculate_reusability_score,
    calculate_distribution_scores,
    perform_custom_validations,
    check_dataset_mqa
)

# --- Fixtures for test data and configurations ---

@pytest.fixture
def sample_dataset():
    """Provides a comprehensive sample dataset for MQA testing."""
    return {
        "dct:identifier": "test-id-123",
        "dct:title": "Test Dataset",
        "dcat:keyword": ["test", "data"],
        "dcat:theme": ["http://publications.europa.eu/resource/authority/data-theme/ECON"],
        # No dct:spatial, no dct:temporal for testing partial scores
        "dcat:contactPoint": {"schema:email": "good@example.com"},
        "dct:publisher": {"foaf:name": "Test Publisher"},
        "dcat:distribution": [
            {
                # This is the "best" distribution
                "dcat:accessURL": "https://good-url.com/data.csv",
                "dcat:downloadURL": "https://good-url.com/download.csv",
                "dct:format": "CSV",
                "dct:license": "https://creativecommons.org/licenses/by/4.0/",
                "dct:issued": "2024-01-01",
                "dct:modified": "2024-01-02"
            },
            {
                # This is a "worse" distribution
                "dcat:accessURL": "https://bad-url.com",
                # Missing downloadURL, license, etc.
                "dct:format": "JSON"
            }
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

@pytest.fixture
def mqa_metrics_config():
    """Provides a mock of the mqa_metrics section from config.yml."""
    return {
        'findability': {
            'indicators': {
                'keywords': {'path': 'dcat:keyword', 'points': 30},
                'categories': {'path': 'dcat:theme', 'points': 30},
                'spatial': {'path': 'dct:spatial', 'points': 20},
                'temporal': {'path': 'dct:temporal', 'points': 20}
            }
        },
        'accessibility': {
            'indicators': {
                'access_url_accessibility': {'path': 'dcat:accessURL', 'points': 50},
                'download_url_presence': {'path': 'dcat:downloadURL', 'points': 20},
                'download_url_accessibility': {'path': 'dcat:downloadURL', 'points': 30}
            }
        },
        'interoperability': {
            'indicators': {
                'format_presence': {'path': 'dct:format', 'points': 20},
                'dcat_ap_ch_conformity': {'points': 30}
            }
        },
        'reusability': {
            'indicators': {
                'license_presence': {'path': 'dct:license', 'points': 20},
                'contact_point_presence': {'path': 'dcat:contactPoint', 'points': 20},
                'publisher_presence': {'path': 'dct:publisher', 'points': 10},
                'access_rights': {'points': 15}
            }
        },
        'context': {
            'indicators': {
                'issued_date_presence': {'path': 'dct:issued', 'points': 5},
                'modified_date_presence': {'path': 'dct:modified', 'points': 5}
            }
        }
    }

@pytest.fixture
def rating_thresholds_config():
    """Provides a mock of the rating_thresholds from config.yml."""
    return [
        {'rating': 'Excellent', 'min_score': 351},
        {'rating': 'Good', 'min_score': 221},
        {'rating': 'Sufficient', 'min_score': 121},
        {'rating': 'Insufficient', 'min_score': 0}
    ]

@pytest.fixture
def custom_rules_config():
    """Provides a mock of the custom_validations from config.yml."""
    return {
        'email_fields': ['dcat:contactPoint.schema:email']
    }

# --- Tests for get_nested_value (Unchanged) ---

def test_get_nested_value_simple():
    assert get_nested_value({'key': 'value'}, 'key') == 'value'

def test_get_nested_value_nested():
    assert get_nested_value({'a': {'b': 'c'}}, 'a.b') == 'c'

def test_get_nested_value_in_list():
    data = {'items': [{'name': 'A'}, {'name': 'B'}]}
    assert get_nested_value(data, 'items.name') == ['A', 'B']

def test_get_nested_value_missing_key():
    assert get_nested_value({'key': 'value'}, 'missing') is None

# --- Tests for Core Validators (Unchanged) ---

def test_validate_url_valid_and_ok(mocker):
    mocker.patch('requests.head', return_value=mocker.Mock(ok=True))
    assert validate_url("https://www.google.com") is None
    requests.head.assert_called_once_with("https://www.google.com", allow_redirects=True, timeout=5)

def test_validate_url_not_ok(mocker):
    mock_response = mocker.Mock(ok=False, status_code=404)
    mocker.patch('requests.head', return_value=mock_response)
    error = validate_url("https://www.google.com/nonexistent")
    assert "URL not reachable (Status: 404)" in error

def test_validate_email_valid():
    assert validate_email("test.user@example.co.uk") is None

def test_validate_email_invalid():
    assert "Invalid email format" in validate_email("test@example")

def test_validate_required_fields_present(sample_dataset):
    assert validate_required_fields(sample_dataset, ["dct:identifier", "dct:title"]) == []

def test_validate_json_schema_valid(sample_dataset, sample_schema):
    assert validate_json_schema(sample_dataset, sample_schema) == []

# --- NEW Tests for MQA Functions ---

def test_check_presence():
    """Tests the generic presence checker."""
    data = {'a': {'b': 'c'}, 'd': '', 'e': []}
    assert check_presence(data, 'a.b') is True
    assert check_presence(data, 'a.x') is False  # Missing key
    assert check_presence(data, 'd') is False      # Empty string
    assert check_presence(data, 'e') is False      # Empty list

def test_calculate_findability_score(sample_dataset, mqa_metrics_config):
    """Test findability score calculation."""
    # sample_dataset has keyword (30) and theme (30), but not spatial or temporal
    score, details = calculate_findability_score(sample_dataset, mqa_metrics_config['findability'])
    assert score == 60
    assert "OK: Findability/keywords" in details[0]
    assert "FAIL: Findability/spatial" in details[2]

def test_calculate_reusability_score_dataset_level(sample_dataset, mqa_metrics_config):
    """Test dataset-level reusability score calculation."""
    # sample_dataset has contactPoint (20), publisher (10), and gets auto-awarded (15)
    score, details = calculate_reusability_score(sample_dataset, mqa_metrics_config['reusability'])
    assert score == 15 + 20 + 10
    assert "OK: Reusability/access_rights - Auto-awarded" in details[0]
    assert "OK: Reusability/contact_point_presence" in details[1]

def test_calculate_distribution_scores(sample_dataset, mqa_metrics_config, mocker):
    """Test scoring for a single 'best' distribution."""
    # Mock URL validator to always return success (None)
    mocker.patch('data_quality_checker.validate_url', return_value=None)
    
    best_distribution = sample_dataset['dcat:distribution'][0]
    report = calculate_distribution_scores(best_distribution, mqa_metrics_config)
    
    # accessURL (50) + downloadURL presence (20) + downloadURL accessible (30)
    assert report['scores']['accessibility'] == 100
    # format presence (20)
    assert report['scores']['interoperability'] == 20
    # license presence (20)
    assert report['scores']['reusability'] == 20
    # issued (5) + modified (5)
    assert report['scores']['context'] == 10

def test_perform_custom_validations(sample_dataset, custom_rules_config):
    """Test the non-scoring custom validation checks."""
    # Test with good email
    warnings = perform_custom_validations(sample_dataset, custom_rules_config)
    assert len(warnings) == 0

    # Test with bad email
    sample_dataset['dcat:contactPoint']['schema:email'] = "bad-email"
    warnings = perform_custom_validations(sample_dataset, custom_rules_config)
    assert len(warnings) == 1
    assert "EmailFormatWarning" in warnings[0]
    assert "Invalid email format" in warnings[0]

# --- NEW Integration Test for the Core Orchestrator ---

@patch('data_quality_checker.load_config_file')
@patch('data_quality_checker.validate_url')
def test_check_dataset_mqa_full_run(mock_validate_url, mock_load_file, sample_dataset, mqa_metrics_config, rating_thresholds_config, custom_rules_config):
    """
    An integration test for the main check_dataset_mqa function.
    Mocks file loading and URL validation.
    """
    # Simulate file loading by returning our sample dataset
    mock_load_file.return_value = sample_dataset
    
    # Simulate URL checks:
    # 1. Good dist accessURL -> OK
    # 2. Good dist downloadURL -> OK
    # 3. Bad dist accessURL -> Fail
    mock_validate_url.side_effect = [None, None, "Availability Error"]
    
    # --- Execute the function under test ---
    report = check_dataset_mqa(
        'dummy/path.json', 
        mqa_metrics_config, 
        rating_thresholds_config, 
        custom_rules_config
    )

    # --- Assertions ---
    assert report['file'] == 'path.json'
    
    # 1. Findability: keyword (30) + categories (30) = 60
    assert report['scores_by_dimension']['findability'] == 60
    
    # 2. Accessibility (max of distributions): Best dist = 50+20+30=100. Worst dist = 0. Max is 100.
    assert report['scores_by_dimension']['accessibility'] == 100
    
    # 3. Interoperability (max + auto): Best dist = 20. Worst dist = 20. Max is 20. Auto-award = 30. Total = 50.
    assert report['scores_by_dimension']['interoperability'] == 50
    
    # 4. Reusability (dataset + max dist): Dataset = 15+20+10=45. Best dist = 20. Worst = 0. Max is 20. Total = 65.
    assert report['scores_by_dimension']['reusability'] == 65
    
    # 5. Context (max of distributions): Best dist = 5+5=10. Worst = 0. Max is 10.
    assert report['scores_by_dimension']['context'] == 10

    # 6. Total Score and Rating
    expected_total = 60 + 100 + 50 + 65 + 10
    assert report['total_score'] == expected_total # 285
    assert report['rating'] == 'Good' # Because 285 is between 221 and 351

    # 7. Details check
    assert len(report['details']) > 0
    assert "OK: Interoperability/dcat_ap_ch - Auto-awarded 30 points." in report['details']
    assert "FAIL: Accessibility/access_url - URL is not reachable." in report['details'] # From the bad distribution

    # 8. Custom validations
    assert len(report['validation_warnings']) == 0