import os
import json
import re
import yaml
import requests
import jsonschema
from urllib.parse import urlparse

# --- Configuration ---
DATA_RAW_DIR = 'data/raw/datasets'
RULES_FILE = 'automation/quality_rules.yml'
REPORT_FILE = 'data/processed/quality_report.json'


def load_config_file(file_path, loader):
    """Generic function to load a configuration file (YAML or JSON)."""
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
            # Handle lists of objects, e.g., dcat:distribution
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
        # Format the error message for better readability
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
        # Handle mailto scheme as a special case
        if result.scheme == 'mailto':
            email_error = validate_email(result.path)
            if email_error:
                return f"Format Error: Invalid email in mailto: URL '{url}'"
            return None  # Valid mailto format, skip reachability check

        # For other schemes, we expect a scheme and a network location.
        if not all([result.scheme, result.netloc]):
            return f"Format Error: Invalid URL format for '{url}'"
    except ValueError:
        return f"Format Error: Invalid URL format for '{url}'"

    if url.startswith('mailto:'): # Skip reachability for mailto links
        return None

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

def check_dataset_quality(dataset_path, rules, schema):
    """Runs all quality checks for a single dataset file."""
    report = {'file': os.path.basename(dataset_path), 'errors': []}
    data = load_config_file(dataset_path, json.load)
    if data is None:
        report['errors'].append("Critical: Could not read or parse JSON file.")
        return report

    # 1. JSON Schema validation (most critical first step)
    if schema:
        schema_errors = validate_json_schema(data, schema)
        report['errors'].extend(schema_errors)
        if schema_errors: # If schema is invalid, further checks might be unreliable
            return report

    # 2. Custom rule checks
    for rule_type, rule_values in rules.items():
        if rule_type == 'required_fields':
            report['errors'].extend(validate_required_fields(data, rule_values))
        elif rule_type == 'url_fields':
            for field_path in rule_values:
                urls = get_nested_value(data, field_path)
                if urls:
                    for url in urls if isinstance(urls, list) else [urls]:
                        if (error := validate_url(url)):
                            report['errors'].append(f"Field '{field_path}': {error}")
        elif rule_type == 'email_fields':
            for field_path in rule_values:
                emails = get_nested_value(data, field_path)
                if emails:
                    for email in emails if isinstance(emails, list) else [emails]:
                        if (error := validate_email(email)):
                            report['errors'].append(f"Field '{field_path}': {error}")
        elif rule_type == 'enum_fields':
            for field_path, allowed in rule_values.items():
                values = get_nested_value(data, field_path)
                if values:
                    for value in values if isinstance(values, list) else [values]:
                        if value not in allowed:
                            report['errors'].append(f"Consistency Error: Field '{field_path}' has invalid value '{value}'. Allowed: {allowed}")

    return report

def main():
    """Main function to execute the quality checks."""
    rules = load_config_file(RULES_FILE, yaml.safe_load)
    if not rules:
        return

    schema_path = rules.get('json_schema_path')
    schema = load_config_file(schema_path, json.load) if schema_path else None
    
    all_reports = []
    for filename in sorted(os.listdir(DATA_RAW_DIR)):
        if filename.endswith('.json'):
            dataset_path = os.path.join(DATA_RAW_DIR, filename)
            report = check_dataset_quality(dataset_path, rules, schema)
            if report['errors']: # Only include files with errors in the report
                all_reports.append(report)

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)

    print(f"Quality report generated at {REPORT_FILE}")
    print(f"Found issues in {len(all_reports)} dataset(s).")

if __name__ == '__main__':
    main()
