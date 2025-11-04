#!/usr/bin/env python
import json
import requests
import sys
import os
import click
from pathlib import Path
from rdflib import Graph, URIRef
from rdflib.namespace import Namespace, SH, RDF

# --- Usage Example ---
# python automation/build-strict-schemas.py --input-dir data/schemas --output-dir data/schema_strict --prefix strict-ods- --portal ods
# python automation/build-strict-schemas.py --help

# --- Configuration ---
SHACL_URL = "https://raw.githubusercontent.com/opendata-swiss/ogdch_checker/main/ogdch.shacl.ttl"
I14Y_URL = "https://apiconsole.i14y.admin.ch/partner/v1/Release.json"

# --- Define Namespaces and Mappings ---
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
NAMESPACES = {"dcat": DCAT, "dct": DCT, "sh": SH}

# 1. Mapping for SHACL (ODS & Base for I14Y)
SCHEMA_TO_SHACL_CLASS = {
    "dataset.json": DCAT.Dataset,
    "dataService.json": DCAT.DataService,
    "catalog.json": DCAT.Catalog
}

# 2. Mapping for I14Y OpenAPI (Release.json)
SCHEMA_TO_I14Y_MODEL = {
    "dataset.json": "DcatDatasetInputModel",
    "dataService.json": "DataServiceInputModel"
}

# --- Helper Functions ---

def fetch_rules(url):
    """Fetches a JSON or TTL file from a URL."""
    print(f"Fetching rules from {url}...")
    try:
        r = requests.get(url)
        r.raise_for_status()
        if url.endswith(".json"):
            print("Successfully parsed JSON file.")
            return r.json()
        else:
            g = Graph()
            g.parse(data=r.text, format="turtle")
            g.bind("dcat", DCAT)
            g.bind("dct", DCT)
            g.bind("sh", SH)
            print("Successfully parsed SHACL (Turtle) file.")
            return g
    except Exception as e:
        print(f"FATAL: Could not fetch or parse rules from {url}: {e}", file=sys.stderr)
        sys.exit(1)

def shorten_uri(uri, ns_map):
    """Turns a URIRef into a 'prefix:name' string."""
    for prefix, namespace in ns_map.items():
        if str(uri).startswith(str(namespace)):
            return f"{prefix}:{str(uri).replace(str(namespace), '')}"
    return str(uri)

def get_shacl_shape_rules(g, shape_node):
    """
    Parses a specific SHACL NodeShape and returns its rules
    as a JSON Schema properties/required dict.
    """
    properties = {}
    required = set()
    
    for prop_node in g.objects(shape_node, SH.property):
        path_uri = g.value(prop_node, SH.path)
        if not path_uri: continue
            
        prop_key = shorten_uri(path_uri, NAMESPACES)
        severity = g.value(prop_node, SH.severity, default=SH.Violation)
        min_count = g.value(prop_node, SH.minCount)
        
        is_mandatory = (min_count and int(min_count) >= 1 and severity == SH.Violation)
        if is_mandatory:
            required.add(prop_key)

        properties[prop_key] = {}
        
        enum_list_node = g.value(prop_node, SH["in"])
        if enum_list_node:
            enum_list = [str(item) for item in g.list(enum_list_node)]
            properties[prop_key]["enum"] = [e for e in enum_list if e]
            properties[prop_key]["type"] = "string"

    return {"properties": properties, "required": sorted(list(required))}


def merge_shacl_rules(g, base_schema, target_class_uri):
    """
    Merges top-level SHACL rules into a base JSON schema.
    """
    main_shape = g.value(subject=None, predicate=SH.targetClass, object=target_class_uri)
    if not main_shape:
        print(f"    -> Warning: No sh:NodeShape found for {target_class_uri}. Skipping SHACL merge.", file=sys.stderr)
        return base_schema, set()

    shacl_required = set()

    for prop_node in g.objects(main_shape, SH.property):
        path_uri = g.value(prop_node, SH.path)
        if not path_uri: continue
            
        prop_key = shorten_uri(path_uri, NAMESPACES)
        
        # 1. Handle 'required' logic
        severity = g.value(prop_node, SH.severity, default=SH.Violation)
        min_count = g.value(prop_node, SH.minCount)
        is_mandatory = (min_count and int(min_count) >= 1 and severity == SH.Violation)
        
        if is_mandatory:
            shacl_required.add(prop_key)

        # 2. Handle 'enum' logic
        enum_list_node = g.value(prop_node, SH["in"])
        if enum_list_node:
            enum_list = [str(item) for item in g.list(enum_list_node)]
            strict_enum = [e for e in enum_list if e]
            if prop_key in base_schema.get("properties", {}):
                base_schema["properties"][prop_key]["enum"] = strict_enum
        
        # 3. Handle NESTED rules (for Distribution)
        nested_shape_node = g.value(prop_node, SH.node)
        if nested_shape_node:
            print(f"    -> Found nested SHACL shape for '{prop_key}'. Parsing...")
            nested_rules = get_shacl_shape_rules(g, nested_shape_node)
            
            if prop_key not in base_schema.get("properties", {}):
                base_schema["properties"][prop_key] = {}
            if "items" not in base_schema["properties"][prop_key]:
                base_schema["properties"][prop_key]["items"] = {}
                
            base_schema["properties"][prop_key]["items"].update(nested_rules)
            print(f"    -> Successfully merged SHACL rules for '{prop_key}'.")

    # Return the *original* base requirements and *new* SHACL requirements separately
    return base_schema, shacl_required


def merge_i14y_rules(spec, base_schema, model_name, translation_map):
    """
    Merges I14Y OpenAPI 'required' rules into a base JSON schema.
    It *translates* the keys before adding them.
    """
    
    try:
        model_schema = spec["components"]["schemas"][model_name]
    except KeyError:
        print(f"    -> Warning: Model '{model_name}' not found in OpenAPI spec. Skipping.", file=sys.stderr)
        return base_schema, set()
        
    i14y_flat_required = set(model_schema.get("required", []))
    print(f"    -> Found {len(i14y_flat_required)} I14Y-specific fields for '{model_name}'.")

    i14y_dcat_required = set()
    model_translation = translation_map.get(model_name, {})
    
    for flat_key in i14y_flat_required:
        dcat_key = model_translation.get(flat_key)
        if dcat_key:
            i14y_dcat_required.add(dcat_key)
        else:
            print(f"    -> Warning: No DCAT translation for I14Y key '{flat_key}'. Skipping.")

    # --- Handle nested Distribution ---
    if model_name == "DcatDatasetInputModel":
        print("    -> Found Dataset, looking for nested I14Y Distribution rules...")
        try:
            dist_model = spec["components"]["schemas"]["DcatDistributionInputModel"]
            dist_flat_required = set(dist_model.get("required", []))
            dist_translation = translation_map.get("DcatDistributionInputModel", {})
            
            dist_dcat_required = set()
            for flat_key in dist_flat_required:
                dcat_key = dist_translation.get(flat_key)
                if dcat_key:
                    dist_dcat_required.add(dcat_key)
            
            if "dcat:distribution" not in base_schema["properties"]:
                 base_schema["properties"]["dcat:distribution"] = {}
            if "items" not in base_schema["properties"]["dcat:distribution"]:
                 base_schema["properties"]["dcat:distribution"]["items"] = {}
                 
            dist_prop = base_schema["properties"]["dcat:distribution"]["items"]
            dist_prop_required = set(dist_prop.get("required", []))
            dist_prop["required"] = sorted(list(dist_prop_required | dist_dcat_required))
            print(f"    -> Merged I14Y distribution rules: {dist_dcat_required}")
            
        except KeyError:
            print("    -> Warning: Could not find 'DcatDistributionInputModel' in spec.", file=sys.stderr)

    return base_schema, i14y_dcat_required


# --- Click Command ---

@click.command()
@click.option(
    '--portal',
    type=click.Choice(['ods', 'i14y']),
    required=True,
    help="The target portal: 'ods' (opendata.swiss) or 'i14y'."
)
@click.option(
    '--input-dir',
    type=click.Path(exists=True, file_okay=False, readable=True),
    required=True,
    help="Directory containing the base JSON schemas (e.g., 'dataset.json')."
)
@click.option(
    '--output-dir',
    type=click.Path(file_okay=False, writable=True),
    required=True,
    help="Directory to save the generated strict schemas."
)
@click.option(
    '--prefix',
    type=str,
    default='strict-',
    show_default=True,
    help="Prefix to add to all generated schema files (e.g., 'strict-')."
)
@click.option(
    '--i14y-map',
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the I14Y to DCAT translation map JSON file (required if --portal=i14y)."
)
def build_strict_schemas(portal, input_dir, output_dir, prefix, i14y_map):
    """
    Generates 'strict' JSON schemas for portal validation based on a
    chosen source of truth (ODS SHACL or I14Y OpenAPI).
    """
    
    # --- 1. Load the correct rules based on --portal flag ---
    rules_source = None
    shacl_rules = None
    translation_map = None
    
    if portal == 'ods':
        rules_source = fetch_rules(SHACL_URL)
        parser_func = merge_shacl_rules
        mapping_dict = SCHEMA_TO_SHACL_CLASS
    
    elif portal == 'i14y':
        if not i14y_map:
            print("Error: --portal=i14y requires the --i14y-map flag.", file=sys.stderr)
            sys.exit(1)
        
        rules_source = fetch_rules(I14Y_URL)  # This is the OpenAPI spec
        shacl_rules = fetch_rules(SHACL_URL)  # We also need the base SHACL rules
        
        try:
            with Path(i14y_map).open('r', encoding='utf-8') as f:
                translation_map = json.load(f)
            print(f"Successfully loaded I14Y translation map from {i14y_map}")
        except Exception as e:
            print(f"FATAL: Could not load or parse --i14y-map file '{i14y_map}': {e}", file=sys.stderr)
            sys.exit(1)
            
        parser_func = merge_i14y_rules
        mapping_dict = SCHEMA_TO_I14Y_MODEL
    
    else:
        print(f"Error: Unknown portal '{portal}'", file=sys.stderr)
        sys.exit(1)
        
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n--- Scanning '{input_path}' for base schemas (Mode: {portal.upper()}) ---")
    
    processed_count = 0
    
    # --- 2. Loop through local schemas and apply rules ---
    for f in input_path.glob("*.json"):
        
        if "strict" in f.name:
            print(f"Skipping '{f.name}' (contains 'strict').")
            continue
            
        if f.name not in SCHEMA_TO_SHACL_CLASS:
            print(f"Skipping '{f.name}' (not a recognized DCAT type).")
            continue
        
        print(f"Processing '{f.name}'...")
        
        with f.open('r', encoding='utf-8') as file:
            base_schema = json.load(file)
        
        base_required = set(base_schema.get("required", []))
        portal_required = set()
        
        # --- Apply Rules based on Portal ---
        if portal == 'ods':
            shacl_class_uri = SCHEMA_TO_SHACL_CLASS[f.name]
            base_schema, portal_required = merge_shacl_rules(rules_source, base_schema, shacl_class_uri)

        elif portal == 'i14y':
            # 1. Apply base SHACL rules first
            shacl_class_uri = SCHEMA_TO_SHACL_CLASS[f.name]
            base_schema, shacl_required = merge_shacl_rules(shacl_rules, base_schema, shacl_class_uri)
            portal_required.update(shacl_required)
            
            # 2. Apply I14Y-specific rules on top (if this file has an I14Y model)
            if f.name in mapping_dict:
                i14y_model_name = mapping_dict[f.name]
                base_schema, i14y_required = merge_i14y_rules(rules_source, base_schema, i14y_model_name, translation_map)
                portal_required.update(i14y_required)
            else:
                 print(f"    -> Note: '{f.name}' has no I14Y-specific API model. Using base DCAT rules.")
        
        # --- Create Final 'required' List ---
        final_required = base_required | portal_required
        base_schema["required"] = sorted(list(final_required))

        # 4. Save the new strict schema
        output_name = f"{prefix}{f.name}"
        output_file_path = output_path / output_name
        
        try:
            with output_file_path.open('w', encoding='utf-8') as file:
                json.dump(base_schema, file, indent=4)
            print(f"Successfully generated {output_file_path}\n")
            processed_count += 1
        except Exception as e:
            print(f"Error saving schema file {output_file_path}: {e}", file=sys.stderr)

    print(f"Schema generation complete. Processed {processed_count} files.")

if __name__ == "__main__":
    build_strict_schemas()