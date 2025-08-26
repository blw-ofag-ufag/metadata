import os
import json
import re
import yaml
import requests
import jsonschema
import click
from urllib.parse import urlparse

def load_config_file(file_path, loader):
    """Function to load yaml-file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return loader(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading or parsing {file_path}: {e}")
        return None


def get_nested_value(data, key_path):
    """
    Retrieves a value from a nested dictionary using a dot-separated path.
    Handles lists by iterating over them and collecting values.
    """
    keys = key_path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list):
            new_value = []
            for item in value:
                if isinstance(item, dict) and key in item:
                    new_value.append(item[key])
            value = new_value if new_value else None
        else:
            return None
    return value

def validate_json_schema(data, schema):
    """Validates the data against the provided JSON schema."""
    errors = []
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        path = ".".join(map(str, e.path)) if e.path else "root"
        errors.append(f"Schema Error at '{path}': {e.message}")
    return errors

def validate_required_fields(data, fields):
    """Checks if all specified required fields are present."""
    errors = []
    for field in fields:
        if get_nested_value(data, field) is None:
            errors.append(f"Completeness Error: Required field '{field}' is missing.")
    return errors

def validate_url(url):
    """Checks if a URL has a valid format and is reachable."""
    if not isinstance(url, str) or not url:
        return "Format Error: URL is not a string or is empty."
    try:
        result = urlparse(url)
        if result.scheme == 'mailto':
            email_error = validate_email(result.path)
            return f"Format Error: Invalid email in mailto: URL '{url}'" if email_error else None
        if not all([result.scheme, result.netloc]):
            return f"Format Error: Invalid URL format for '{url}'"
    except ValueError:
        return f"Format Error: Invalid URL format for '{url}'"
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if not response.ok:
            return f"Availability Error: URL not reachable (Status: {response.status_code}) for '{url}'"
    except requests.RequestException as e:
        return f"Availability Error: URL check failed ({type(e).__name__}) for '{url}'"
    return None

def validate_email(email):
    """Checks if an email has a valid format."""
    if not isinstance(email, str) or not email:
        return "Format Error: Email is not a string or is empty."
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return f"Format Error: Invalid email format for '{email}'"
    return None
    
# --- MQA & CUSTOM VALIDATION FUNCTIONS ---

def check_presence(data, indicator_path):
    """Generic check for the presence and non-emptiness of a value."""
    value = get_nested_value(data, indicator_path)
    if value is None:
        return False
    if isinstance(value, (str, list, dict)) and not value:
        return False
    return True

def calculate_findability_score(data, rules):
    """Calculates the score for the Findability dimension."""
    score = 0
    details = []
    for name, indicator in rules['indicators'].items():
        if check_presence(data, indicator['path']):
            score += indicator['points']
            details.append(f"OK: Findability/{name} - Field '{indicator['path']}' is present.")
        else:
            details.append(f"FAIL: Findability/{name} - Field '{indicator['path']}' is missing.")
    return score, details

def calculate_reusability_score(data, rules):
    """Calculates the score for the Dataset-level parts of Reusability."""
    score = 0
    details = []
    score += rules['indicators']['access_rights']['points']
    details.append(f"OK: Reusability/access_rights - Auto-awarded {rules['indicators']['access_rights']['points']} points.")
    for name in ['contact_point_presence', 'publisher_presence']:
        indicator = rules['indicators'][name]
        if check_presence(data, indicator['path']):
            score += indicator['points']
            details.append(f"OK: Reusability/{name} - Field '{indicator['path']}' is present.")
        else:
            details.append(f"FAIL: Reusability/{name} - Field '{indicator['path']}' is missing.")
    return score, details

def calculate_distribution_scores(dist_data, mqa_metrics):
    """Calculates all MQA scores for a single distribution."""
    scores = {'accessibility': 0, 'interoperability': 0, 'reusability': 0, 'context': 0}
    details = []
    acc_rules = mqa_metrics['accessibility']['indicators']
    access_url = get_nested_value(dist_data, acc_rules['access_url_accessibility']['path'])
    if access_url:
        if validate_url(access_url) is None:
            scores['accessibility'] += acc_rules['access_url_accessibility']['points']
            details.append("OK: Accessibility/access_url - URL is reachable.")
        else:
            details.append("FAIL: Accessibility/access_url - URL is not reachable.")
    else:
        details.append("FAIL: Accessibility/access_url - Field is missing.")
    download_url = get_nested_value(dist_data, acc_rules['download_url_presence']['path'])
    if download_url:
        scores['accessibility'] += acc_rules['download_url_presence']['points']
        details.append("OK: Accessibility/download_url_presence - Field is present.")
        if validate_url(download_url) is None:
            scores['accessibility'] += acc_rules['download_url_accessibility']['points']
            details.append("OK: Accessibility/download_url_accessibility - URL is reachable.")
        else:
            details.append("FAIL: Accessibility/download_url_accessibility - URL is not reachable.")
    else:
        details.append("FAIL: Accessibility/download_url_presence - Field is missing.")
    interop_rules = mqa_metrics['interoperability']['indicators']
    reuse_rules = mqa_metrics['reusability']['indicators']
    if check_presence(dist_data, interop_rules['format_presence']['path']):
        scores['interoperability'] += interop_rules['format_presence']['points']
        details.append("OK: Interoperability/format_presence - Field is present.")
    else:
        details.append("FAIL: Interoperability/format_presence - Field is missing.")
    if check_presence(dist_data, reuse_rules['license_presence']['path']):
        scores['reusability'] += reuse_rules['license_presence']['points']
        details.append("OK: Reusability/license_presence - Field is present.")
    else:
        details.append("FAIL: Reusability/license_presence - Field is missing.")
    context_rules = mqa_metrics['context']['indicators']
    if check_presence(dist_data, context_rules['issued_date_presence']['path']):
        scores['context'] += context_rules['issued_date_presence']['points']
    if check_presence(dist_data, context_rules['modified_date_presence']['path']):
        scores['context'] += context_rules['modified_date_presence']['points']
    return {'scores': scores, 'details': details}

def perform_custom_validations(data, rules):
    """Performs a series of non-scoring, best-practice validations."""
    warnings = []
    email_fields_to_check = rules.get('email_fields',)
    for field_path in email_fields_to_check:
        emails = get_nested_value(data, field_path)
        if emails:
            email_list = emails if isinstance(emails, list) else [emails]
            for email in email_list:
                error = validate_email(email)
                if error:
                    warnings.append(f"EmailFormatWarning: Field '{field_path}' - {error}")
    return warnings

# --- CORE ORCHESTRATOR FUNCTION ---

def check_dataset_mqa(dataset_path, mqa_metrics, rating_thresholds, custom_rules):
    """Runs all MQA checks and custom validations for a single dataset."""
    data = load_config_file(dataset_path, json.load)
    if data is None:
        return {
            'file': os.path.basename(dataset_path),
            'scores_by_dimension': {},
            'total_score': 0,
            'rating': 'Insufficient',
            'details': [],
            'validation_warnings': []
        }

    scores = {}
    details = []

    scores['findability'], find_details = calculate_findability_score(data, mqa_metrics['findability'])
    details.extend(find_details)
    scores['reusability'], reuse_details = calculate_reusability_score(data, mqa_metrics['reusability'])
    details.extend(reuse_details)

    distribution_reports = []
    distributions = get_nested_value(data, 'dcat:distribution')
    if distributions and isinstance(distributions, list):
        for dist_data in distributions:
            dist_report = calculate_distribution_scores(dist_data, mqa_metrics)
            distribution_reports.append(dist_report)
            details.extend(dist_report['details'])

    if distribution_reports:
        scores['accessibility'] = max(r['scores']['accessibility'] for r in distribution_reports)
        scores['interoperability'] = max(r['scores']['interoperability'] for r in distribution_reports)
        scores['reusability'] += max(r['scores']['reusability'] for r in distribution_reports)
        scores['context'] = max(r['scores']['context'] for r in distribution_reports)
    else:
        scores.update({'accessibility': 0, 'interoperability': 0, 'context': 0})
        details.append("FAIL: Core - No distributions found in the dataset.")

    scores['interoperability'] += mqa_metrics['interoperability']['indicators']['dcat_ap_ch_conformity']['points']
    details.append(f"OK: Interoperability/dcat_ap_ch - Auto-awarded {mqa_metrics['interoperability']['indicators']['dcat_ap_ch_conformity']['points']} points.")

    total_score = sum(scores.values())
    rating = 'Insufficient'
    for threshold in rating_thresholds:
        if total_score >= threshold['min_score']:
            rating = threshold['rating']
            break
            
    validation_warnings = perform_custom_validations(data, custom_rules)

    return {
        'file': os.path.basename(dataset_path),
        'scores_by_dimension': scores,
        'total_score': total_score,
        'rating': rating,
        'details': details,
        'validation_warnings': validation_warnings
    }

# --- MAIN EXECUTION ---

@click.command()
@click.option('--config', 'config_path', default=None, help='Path to the config.yml file.')
def main(config_path):
    """Main function to execute the MQA quality checks."""
    if config_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.yml')
        print(f"No config path provided. Defaulting to: {config_path}")

    config = load_config_file(config_path, yaml.safe_load)
    if not config:
        return

    data_raw_dir = config.get('paths', {}).get('data_directory')
    report_dir = config.get('paths', {}).get('report_directory')
    mqa_metrics = config.get('mqa_metrics', {})
    rating_thresholds = config.get('rating_thresholds', {})
    custom_rules = config.get('custom_validations', {})

    if not all([data_raw_dir, report_dir, mqa_metrics, rating_thresholds]):
        print("Error: One or more required keys are missing in config.yml.")
        return
    
    all_reports = []
    dataset_files = [f for f in os.listdir(data_raw_dir) if f.endswith('.json')]
    
    for filename in sorted(dataset_files):
        dataset_path = os.path.join(data_raw_dir, filename)
        report = check_dataset_mqa(dataset_path, mqa_metrics, rating_thresholds, custom_rules)
        all_reports.append(report)

    all_reports.sort(key=lambda r: r.get('total_score', 0), reverse=True)

    report_file_path = os.path.join(report_dir, 'quality_report_mqa.json')
    os.makedirs(os.path.dirname(report_file_path), exist_ok=True)
    with open(report_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)

    print(f"MQA Quality report generated for {len(all_reports)} dataset(s) at {report_file_path}")

if __name__ == '__main__':
    main()