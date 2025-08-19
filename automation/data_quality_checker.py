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

def check_dataset_quality(dataset_path, rules, schema, error_weights):
    """Runs all quality checks for a single dataset and calculates a score."""
    report = {
        'file': os.path.basename(dataset_path),
        'errors': [],
        'quality_score': 100
    }

    def add_error(message, category):
        report['errors'].append(message)
        report['quality_score'] -= error_weights.get(category, 1)

    data = load_config_file(dataset_path, json.load)
    if data is None:
        add_error("Critical: Could not read or parse JSON file.", 'critical')
        report['quality_score'] = 0
        return report

    if schema:
        for error in validate_json_schema(data, schema):
            add_error(error, 'schema')

    for rule_type, rule_values in rules.items():
        if rule_type == 'required_fields':
            for error in validate_required_fields(data, rule_values):
                add_error(error, 'required_field')
        elif rule_type == 'url_fields':
            for field_path in rule_values:
                urls = get_nested_value(data, field_path)
                if urls:
                    for url in urls if isinstance(urls, list) else [urls]:
                        if (error := validate_url(url)):
                            add_error(f"Field '{field_path}': {error}", 'url')
        elif rule_type == 'email_fields':
            for field_path in rule_values:
                emails = get_nested_value(data, field_path)
                if emails:
                    for email in emails if isinstance(emails, list) else [emails]:
                        if (error := validate_email(email)):
                            add_error(f"Field '{field_path}': {error}", 'email')
        elif rule_type == 'enum_fields':
            for field_path, allowed in rule_values.items():
                values = get_nested_value(data, field_path)
                if values:
                    for value in values if isinstance(values, list) else [values]:
                        if value not in allowed:
                            msg = f"Consistency Error: Field '{field_path}' has invalid value '{value}'. Allowed: {allowed}"
                            add_error(msg, 'enum')
    
    if report['quality_score'] < 0:
        report['quality_score'] = 0
        
    return report

@click.command()
@click.option(
    '--config', 'config_path',
    default=None,
    help='Path to the config.yml file.'
)

def main(config_path):
    """
    Main function to execute the quality checks.
    It dynamically finds the config.yml file.
    """
    # Step 1: Determine the path to the configuration file
    if config_path is None:
        # If no path was provided via --config, search next to the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.yml')
        print(f"No config path provided. Defaulting to: {config_path}")

    # Step 2: Load the main configuration
    config = load_config_file(config_path, yaml.safe_load)
    if not config:
        print("Could not load main configuration. Exiting.")
        return

    data_raw_dir = config.get('paths', {}).get('data_directory')
    rules_file = config.get('paths', {}).get('rules_file')
    report_dir = config.get('paths', {}).get('report_directory')
    error_weights = config.get('scoring', {}).get('weights', {})

    if not all([data_raw_dir, rules_file, report_dir, error_weights]):
        print("Error: One or more required keys are missing in config.yml.")
        return

    rules = load_config_file(rules_file, yaml.safe_load)
    if not rules:
        return

    schema_path = rules.get('json_schema_path')
    schema = load_config_file(schema_path, json.load) if schema_path else None
    
    all_reports = []
    dataset_files = [f for f in os.listdir(data_raw_dir) if f.endswith('.json')]
    
    for filename in sorted(dataset_files):
        dataset_path = os.path.join(data_raw_dir, filename)
        report = check_dataset_quality(dataset_path, rules, schema, error_weights)
        all_reports.append(report)

    all_reports.sort(key=lambda r: r.get('quality_score', 100))

    report_file_path = os.path.join(report_dir, 'quality_report.json')
    os.makedirs(os.path.dirname(report_file_path), exist_ok=True)
    with open(report_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)

    print(f"Quality report generated for {len(all_reports)} dataset(s) at {report_file_path}")

if __name__ == '__main__':
    main()