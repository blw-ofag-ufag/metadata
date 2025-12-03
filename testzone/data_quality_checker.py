import os
import json
import re
import yaml
import requests
import jsonschema
import click
from urllib.parse import urlparse
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import warnings
from collections import defaultdict

# --- User-Agent Header ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}
warnings.filterwarnings("ignore", category=InsecureRequestWarning)
# ----------------

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
        response = requests.head(
            url, 
            allow_redirects=True, 
            timeout=10,
            headers=HEADERS
        )
        if response.ok:
            return None # Success
    except requests.RequestException:
        pass  # Fallback to GET

    try:
        response = requests.get(
            url, 
            allow_redirects=True, 
            timeout=15,
            stream=True,
            headers=HEADERS
        )
        if not response.ok:
            return f"Availability Error: Fallback GET failed (Status: {response.status_code}) for '{url}'"
    except requests.RequestException as e:
        return f"Availability Error: Fallback GET failed ({type(e).__name__}) for '{url}'"
    
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

def calculate_reusability_score(data, rules, vocab_rules):
    """Calculates the score for the Dataset-level parts of Reusability."""
    score = 0
    details = []
    
    # Dataset-level Access Rights (combines presence and vocabulary)
    if 'access_rights' in rules['indicators']:
        indicator = rules['indicators']['access_rights']
        path = indicator['path'] # Assuming you add this to config, e.g., 'dct:accessRights'
        vocab_key = vocab_rules.get(path)
        
        if check_presence(data, path) and vocab_key:
            value = get_nested_value(data, path)
            allowed_values = vocab_rules.get(vocab_key, set())
            if value in allowed_values:
                score += indicator['points'] # Full points for valid vocab
                details.append(f"OK: Reusability/access_rights - Field '{path}' is present and in vocabulary.")
            else:
                # You might give partial points for presence, e.g., indicator['points'] / 2
                details.append(f"FAIL: Reusability/access_rights - Field '{path}' is present but value '{value}' is not in vocabulary.")
        elif check_presence(data, path):
             # Present but no vocab check defined
             score += indicator.get('points', 0) 
             details.append(f"OK: Reusability/access_rights - Field '{path}' is present.")
        else:
            details.append(f"FAIL: Reusability/access_rights - Field '{path}' is missing.")

    # Contact Point and Publisher checks
    for name in ['contact_point_presence', 'publisher_presence']:
        if name in rules['indicators']:
            indicator = rules['indicators'][name]
            if check_presence(data, indicator['path']):
                score += indicator['points']
                details.append(f"OK: Reusability/{name} - Field '{indicator['path']}' is present.")
            else:
                details.append(f"FAIL: Reusability/{name} - Field '{indicator['path']}' is missing.")
    return score, details

def audit_distribution(dist_data, mqa_metrics, vocab_rules, format_char_rules):
    """
    Audits a single distribution and returns a report of boolean checks.
    """
    check_report = {
        'access_url_ok': False,
        'download_url_present': False,
        'download_url_ok': False,
        'format_present': False,
        'format_in_vocab': False,
        'media_type_present': False,
        'format_is_non_proprietary': False,
        'format_is_machine_readable': False,
        'license_present': False,
        'license_in_vocab': False,
        'rights_present': False,
        'bytesize_present': False,
        'issued_present': False,
        'modified_present': False
    }
    details = []
    
    acc_rules = mqa_metrics['accessibility']['indicators']
    interop_rules = mqa_metrics['interoperability']['indicators']
    reuse_rules = mqa_metrics['reusability']['indicators']
    context_rules = mqa_metrics['context']['indicators']

    # --- Accessibility ---
    access_url = get_nested_value(dist_data, acc_rules['access_url_accessibility']['path'])
    if access_url:
        url_error = validate_url(access_url)
        if url_error is None:
            check_report['access_url_ok'] = True
            details.append("OK: Accessibility/access_url - URL is reachable.")
        else:
            details.append(f"FAIL: Accessibility/access_url - {url_error}")
    else:
        details.append("FAIL: Accessibility/access_url - Field is missing.")
        
    download_url = get_nested_value(dist_data, acc_rules['download_url_presence']['path'])
    if download_url:
        check_report['download_url_present'] = True
        details.append("OK: Accessibility/download_url_presence - Field is present.")
        url_error = validate_url(download_url)
        if url_error is None:
            check_report['download_url_ok'] = True
            details.append("OK: Accessibility/download_url_accessibility - URL is reachable.")
        else:
            details.append(f"FAIL: Accessibility/download_url_accessibility - {url_error}")
    else:
        details.append("FAIL: Accessibility/download_url_presence - Field is missing.")
        
    # --- Interoperability ---
    format_path = interop_rules['format_presence']['path']
    format_value = get_nested_value(dist_data, format_path)
    if format_value:
        check_report['format_present'] = True
        details.append("OK: Interoperability/format_presence - Field is present.")
        
        # Check vocabularies
        vocab_key = vocab_rules.get(format_path)
        if vocab_key and format_value in vocab_rules.get(vocab_key, set()):
            check_report['format_in_vocab'] = True
            details.append(f"OK: Interoperability/format_from_vocabulary - Format '{format_value}' is in vocabulary.")
        
        # Check characteristics
        if format_value in format_char_rules.get('non_proprietary', set()):
            check_report['format_is_non_proprietary'] = True
            details.append(f"OK: Interoperability/non_proprietary - Format '{format_value}' is non-proprietary.")
        
        if format_value in format_char_rules.get('machine_readable', set()):
            check_report['format_is_machine_readable'] = True
            details.append(f"OK: Interoperability/machine_readable - Format '{format_value}' is machine-readable.")
    else:
        details.append("FAIL: Interoperability/format_presence - Field is missing.")
    
    if check_presence(dist_data, interop_rules['media_type_presence']['path']):
        check_report['media_type_present'] = True
        details.append("OK: Interoperability/media_type_presence - Field is present.")
    else:
        details.append("FAIL: Interoperability/media_type_presence - Field is missing.")

    # --- Reusability ---
    license_path = reuse_rules['license_presence']['path']
    license_value = get_nested_value(dist_data, license_path)
    if license_value:
        check_report['license_present'] = True
        details.append("OK: Reusability/license_presence - Field is present.")
        
        vocab_key = vocab_rules.get(license_path)
        if vocab_key and license_value in vocab_rules.get(vocab_key, set()):
            check_report['license_in_vocab'] = True
            details.append(f"OK: Reusability/license_from_vocabulary - License '{license_value}' is in vocabulary.")
    else:
        details.append("FAIL: Reusability/license_presence - Field is missing.")
        
    # --- Contextuality ---
    if check_presence(dist_data, context_rules['rights_presence']['path']):
        check_report['rights_present'] = True
    if check_presence(dist_data, context_rules['bytesize_presence']['path']):
        check_report['bytesize_present'] = True
    if check_presence(dist_data, context_rules['issued_date_presence']['path']):
        check_report['issued_present'] = True
    if check_presence(dist_data, context_rules['modified_date_presence']['path']):
        check_report['modified_present'] = True

    return check_report, details

def perform_custom_validations(data, rules):
    """Performs a series of non-scoring, best-practice validations."""
    warnings = []
    email_fields_to_check = rules.get('email_fields', [])
    for field_path in email_fields_to_check:
        emails = get_nested_value(data, field_path)
        if emails:
            email_list = emails if isinstance(emails, list) else [emails]
            for email in email_list:
                error = validate_email(email)
                if error:
                    warnings.append(f"EmailFormatWarning: Field '{field_path}' - {error}")
    return warnings

# --- CORE ORCHESTRATOR FUNCTION (NEW LOGIC) ---

def check_dataset_mqa(dataset_path, mqa_metrics, rating_thresholds, custom_rules, vocab_rules, format_char_rules):
    """Runs all MQA checks and custom validations for a single dataset."""
    data = load_config_file(dataset_path, json.load)
    if data is None:
        return {
            'file': os.path.basename(dataset_path),
            'scores_by_dimension': {},
            'total_score': 0,
            'rating': 'Insufficient',
            'details': [f"FAIL: Core - Could not load or parse file."],
            'validation_warnings': []
        }

    scores = {}
    details = []

    # --- 1. Dataset-level checks (Findability, partial Reusability) ---
    scores['findability'], find_details = calculate_findability_score(data, mqa_metrics['findability'])
    details.extend(find_details)
    
    # Pass vocab_rules to the reusability score function
    scores['reusability'], reuse_details = calculate_reusability_score(
        data, mqa_metrics['reusability'], vocab_rules
    )
    details.extend(reuse_details)

    # --- 2. Distribution-level checks (Aggregation) ---
    dist_agg_results = defaultdict(int)
    dist_details = []
    
    distributions = get_nested_value(data, 'dcat:distribution')
    num_dists = 0
    
    if distributions and isinstance(distributions, list):
        num_dists = len(distributions)
        for i, dist_data in enumerate(distributions):
            dist_report, single_dist_details = audit_distribution(
                dist_data, mqa_metrics, vocab_rules, format_char_rules
            )
            dist_details.extend([f"[Dist {i+1}] {d}" for d in single_dist_details])
            
            for check_name, is_ok in dist_report.items():
                if is_ok:
                    dist_agg_results[check_name] += 1
    
    # --- 3. Calculate Scores from Aggregates ---
    scores['accessibility'] = 0
    scores['interoperability'] = 0
    scores['context'] = 0
    
    if num_dists > 0:
        # Calculate percentages (0.0 to 1.0)
        access_url_ok_pct = dist_agg_results['access_url_ok'] / num_dists
        download_url_present_pct = dist_agg_results['download_url_present'] / num_dists
        download_url_ok_pct = dist_agg_results['download_url_ok'] / num_dists
        format_present_pct = dist_agg_results['format_present'] / num_dists
        format_in_vocab_pct = dist_agg_results['format_in_vocab'] / num_dists
        media_type_present_pct = dist_agg_results['media_type_present'] / num_dists
        non_proprietary_pct = dist_agg_results['format_is_non_proprietary'] / num_dists
        machine_readable_pct = dist_agg_results['format_is_machine_readable'] / num_dists
        license_present_pct = dist_agg_results['license_present'] / num_dists
        license_in_vocab_pct = dist_agg_results['license_in_vocab'] / num_dists
        rights_present_pct = dist_agg_results['rights_present'] / num_dists
        bytesize_present_pct = dist_agg_results['bytesize_present'] / num_dists
        issued_present_pct = dist_agg_results['issued_present'] / num_dists
        modified_present_pct = dist_agg_results['modified_present'] / num_dists

        # Get point rules from config
        acc_rules = mqa_metrics['accessibility']['indicators']
        interop_rules = mqa_metrics['interoperability']['indicators']
        reuse_rules = mqa_metrics['reusability']['indicators']
        context_rules = mqa_metrics['context']['indicators']

        # Calculate final scores based on average success
        scores['accessibility'] = (
            (access_url_ok_pct * acc_rules['access_url_accessibility']['points']) +
            (download_url_present_pct * acc_rules['download_url_presence']['points']) +
            (download_url_ok_pct * acc_rules['download_url_accessibility']['points'])
        )
        
        scores['interoperability'] = (
            (format_present_pct * interop_rules['format_presence']['points']) +
            (media_type_present_pct * interop_rules['media_type_presence']['points']) +
            (format_in_vocab_pct * interop_rules['format_from_vocabulary']['points']) + # Assuming vocab check is for format
            (non_proprietary_pct * interop_rules['non_proprietary']['points']) +
            (machine_readable_pct * interop_rules['machine_readable']['points'])
        )
        
        scores['reusability'] += (
            (license_present_pct * reuse_rules['license_presence']['points']) +
            (license_in_vocab_pct * reuse_rules['license_from_vocabulary']['points'])
        )
        
        scores['context'] = (
            (rights_present_pct * context_rules['rights_presence']['points']) +
            (bytesize_present_pct * context_rules['bytesize_presence']['points']) +
            (issued_present_pct * context_rules['issued_date_presence']['points']) +
            (modified_present_pct * context_rules['modified_date_presence']['points'])
        )
        
        # Add summary details
        details.append(f"--- Distribution Summary (Total: {num_dists}) ---")
        details.append(f"Access URLs reachable: {dist_agg_results['access_url_ok']}/{num_dists}")
        details.append(f"Download URLs present: {dist_agg_results['download_url_present']}/{num_dists}")
        details.append(f"Download URLs reachable: {dist_agg_results['download_url_ok']}/{num_dists}")
        details.append(f"Licenses present: {dist_agg_results['license_present']}/{num_dists} (In vocab: {dist_agg_results['license_in_vocab']})")
        details.append(f"Formats present: {dist_agg_results['format_present']}/{num_dists} (In vocab: {dist_agg_results['format_in_vocab']})")
        details.append(f"Media Types present: {dist_agg_results['media_type_present']}/{num_dists}")
        details.append(f"Machine-Readable: {dist_agg_results['format_is_machine_readable']}/{num_dists}")
        details.append(f"Non-Proprietary: {dist_agg_results['format_is_non_proprietary']}/{num_dists}")
        
        # Optional: Uncomment to see full per-distribution logs
        # details.extend(dist_details) 
        
    else:
        details.append("FAIL: Core - No distributions found in the dataset.")

    # --- 4. Final static scores and warnings ---
    scores['interoperability'] += mqa_metrics['interoperability']['indicators']['dcat_ap_ch_conformity']['points']
    details.append(f"OK: Interoperability/dcat_ap_ch - Auto-awarded {mqa_metrics['interoperability']['indicators']['dcat_ap_ch_conformity']['points']} points.")

    # Round all scores for clean reporting
    for dim in scores:
        scores[dim] = round(scores[dim])

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

    # Load configuration sections
    data_raw_dir = config.get('paths', {}).get('data_directory')
    base_report_dir = config.get('paths', {}).get('report_directory') 
    mqa_metrics = config.get('mqa_metrics', {})
    rating_thresholds = config.get('rating_thresholds', {})
    custom_rules = config.get('custom_validations', {})
    
    # Load new vocabulary and format rules
    vocab_rules = config.get('vocabularies', {})
    format_char_rules = config.get('format_characteristics', {})

    if not all([data_raw_dir, base_report_dir, mqa_metrics, rating_thresholds]):
        print("Error: One or more required keys are missing in config.yml.")
        return
    
    # Create the new specific directory path for quality reports
    report_dir = os.path.join(base_report_dir, 'quality_reports')
    
    all_reports = []
    
    if not os.path.isdir(data_raw_dir):
        print(f"Error: data_directory not found at {data_raw_dir}")
        return
        
    dataset_files = [f for f in os.listdir(data_raw_dir) if f.endswith('.json')]
    
    if not dataset_files:
        print(f"No .json files found in {data_raw_dir}")
        return
    
    print(f"Starting quality check on {len(dataset_files)} files...")
    for filename in sorted(dataset_files):
        print(f"Checking {filename}...") 
        dataset_path = os.path.join(data_raw_dir, filename)
        report = check_dataset_mqa(
            dataset_path, mqa_metrics, rating_thresholds, 
            custom_rules, vocab_rules, format_char_rules
        )
        all_reports.append(report)

    all_reports.sort(key=lambda r: r.get('total_score', 0), reverse=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"quality_report_mqa_{timestamp}.json"
    report_file_path = os.path.join(report_dir, report_filename)

    os.makedirs(os.path.dirname(report_file_path), exist_ok=True)
    with open(report_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)

    print(f"\nReport complete.")
    print(f"MQA Quality report generated for {len(all_reports)} dataset(s) at {report_file_path}")

if __name__ == '__main__':
    main()