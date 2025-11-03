#!/usr/bin/env python
import json
import requests
import sys
import os
import click  # Import the click library
from pathlib import Path  # Use pathlib for modern path handling
from rdflib import Graph, URIRef
from rdflib.namespace import Namespace, SH, RDF, XSD

# --- Configuration ---
SHACL_URL = "https://raw.githubusercontent.com/opendata-swiss/ogdch_checker/main/ogdch.shacl.ttl"

# Define namespaces
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
NAMESPACES = {"dcat": DCAT, "dct": DCT, "sh": SH}

# Map base filenames to their corresponding DCAT-AP CH Class
SCHEMA_TO_CLASS = {
    "dataset.json": DCAT.Dataset,
    "dataService.json": DCAT.DataService,
    "catalog.json": DCAT.Catalog
}

# --- SHACL Helper Functions ---

def fetch_shacl_graph():
    """Fetches the SHACL file and parses it into an RDF graph."""
    print(f"Fetching SHACL rules from {SHACL_URL}...")
    try:
        r = requests.get(SHACL_URL)
        r.raise_for_status()
        g = Graph()
        g.parse(data=r.text, format="turtle")
        g.bind("dcat", DCAT)
        g.bind("dct", DCT)
        g.bind("sh", SH)
        print("Successfully parsed SHACL file.")
        return g
    except Exception as e:
        print(f"FATAL: Could not fetch or parse SHACL file: {e}", file=sys.stderr)
        sys.exit(1)

def shorten_uri(uri, ns_map):
    """Turns a URIRef into a 'prefix:name' string."""
    for prefix, namespace in ns_map.items():
        if str(uri).startswith(str(namespace)):
            return f"{prefix}:{str(uri).replace(str(namespace), '')}"
    return str(uri)

def get_shape_rules(g, shape_node):
    """
    Parses a specific SHACL NodeShape and returns its rules
    as a JSON Schema properties/required dict.
    This is the "smart" sub-parser.
    """
    properties = {}
    required = set()
    
    for prop_node in g.objects(shape_node, SH.property):
        path_uri = g.value(prop_node, SH.path)
        if not path_uri:
            continue
            
        prop_key = shorten_uri(path_uri, NAMESPACES)
        severity = g.value(prop_node, SH.severity, default=SH.Violation)
        min_count = g.value(prop_node, SH.minCount)
        
        is_mandatory = (min_count and int(min_count) >= 1 and severity == SH.Violation)
        if is_mandatory:
            required.add(prop_key)

        properties[prop_key] = {}
        
        # Handle Enums (like dct:license)
        enum_list_node = g.value(prop_node, SH["in"])
        if enum_list_node:
            enum_list = [str(item) for item in g.list(enum_list_node)]
            properties[prop_key]["enum"] = [e for e in enum_list if e]
            properties[prop_key]["type"] = "string"

    return {"properties": properties, "required": sorted(list(required))}


def merge_shacl_rules(g, base_schema, target_class_uri):
    """
    Merges top-level SHACL rules into a base JSON schema.
    It adds Mandatory fields to 'required' and makes enums strict.
    It also recursively finds nested shape rules (like for Distribution).
    """
    
    main_shape = g.value(subject=None, predicate=SH.targetClass, object=target_class_uri)
    if not main_shape:
        print(f"    -> Warning: No sh:NodeShape found for {target_class_uri}. Skipping SHACL merge.", file=sys.stderr)
        return base_schema

    required_set = set(base_schema.get("required", []))

    for prop_node in g.objects(main_shape, SH.property):
        path_uri = g.value(prop_node, SH.path)
        if not path_uri:
            continue
            
        prop_key = shorten_uri(path_uri, NAMESPACES)
        
        # --- 1. Handle top-level 'required' logic ---
        severity = g.value(prop_node, SH.severity, default=SH.Violation)
        min_count = g.value(prop_node, SH.minCount)
        is_mandatory = (min_count and int(min_count) >= 1 and severity == SH.Violation)
        
        if is_mandatory:
            required_set.add(prop_key)

        # --- 2. Handle top-level 'enum' logic ---
        enum_list_node = g.value(prop_node, SH["in"])
        if enum_list_node:
            enum_list = [str(item) for item in g.list(enum_list_node)]
            strict_enum = [e for e in enum_list if e]
            if prop_key in base_schema.get("properties", {}):
                base_schema["properties"][prop_key]["enum"] = strict_enum
        
        # --- 3. Handle NESTED rules (the "smart" part) ---
        nested_shape_node = g.value(prop_node, SH.node)
        if nested_shape_node:
            print(f"    -> Found nested shape for '{prop_key}'. Parsing...")
            # This property points to another shape (e.g., dcat:distribution)
            # Go parse that shape's rules.
            nested_rules = get_shape_rules(g, nested_shape_node)
            
            # Ensure the base schema is prepared to receive these rules
            if prop_key not in base_schema.get("properties", {}):
                base_schema["properties"][prop_key] = {}
            
            if "items" not in base_schema["properties"][prop_key]:
                base_schema["properties"][prop_key]["items"] = {}
                
            # Merge the nested rules into the 'items' section
            # This will add {"required": ["dcat:accessURL", "dct:license"], ...}
            # to the 'items' of 'dcat:distribution'.
            base_schema["properties"][prop_key]["items"].update(nested_rules)
            print(f"    -> Successfully merged rules for '{prop_key}'.")


    base_schema["required"] = sorted(list(required_set))
    return base_schema

# --- Click Command ---

@click.command()
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
def build_strict_schemas(input_dir, output_dir, prefix):
    """
    Generates 'strict' JSON schemas for portal validation.
    
    This script reads your internal base schemas from --input-dir,
    fetches the official DCAT-AP CH SHACL rules, and merges them
    to create 'strict' schemas in --output-dir.
    
    It automatically skips any filenames in --input-dir that
    contain the word 'strict'.
    """
    
    g = fetch_shacl_graph()
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create the output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n--- Scanning '{input_path}' for base schemas ---")
    
    processed_count = 0
    
    for f in input_path.glob("*.json"):
        
        if "strict" in f.name:
            print(f"Skipping '{f.name}' (contains 'strict').")
            continue
            
        if f.name not in SCHEMA_TO_CLASS:
            print(f"Skipping '{f.name}' (not a recognized DCAT type).")
            continue
        
        print(f"Processing '{f.name}'...")
        shacl_class_uri = SCHEMA_TO_CLASS[f.name]
        
        with f.open('r', encoding='utf-8') as file:
            base_schema = json.load(file)
        
        strict_schema = merge_shacl_rules(g, base_schema, shacl_class_uri)
        
        output_name = f"{prefix}{f.name}"
        output_file_path = output_path / output_name
        
        try:
            with output_file_path.open('w', encoding='utf-8') as file:
                json.dump(strict_schema, file, indent=4)
            print(f"Successfully generated {output_file_path}\n")
            processed_count += 1
        except Exception as e:
            print(f"Error saving schema file {output_file_path}: {e}", file=sys.stderr)

    print(f"Schema generation complete. Processed {processed_count} files.")

if __name__ == "__main__":
    build_strict_schemas()