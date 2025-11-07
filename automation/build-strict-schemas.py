#!/usr/bin/env python
import json
import requests
import sys
import os
import click
from pathlib import Path
from rdflib import Graph, URIRef
from rdflib.namespace import Namespace, SH, RDF


# --- Usage ---
# python automation/build-strict-schemas.py --input-dir data/schemas --output-dir data/schema_strict --prefix strict-ods- --portal ods ## for opendata.swiss
# python automation/build-strict-schemas.py --input-dir data/schemas --output-dir data/schema_strict --prefix strict-i14y- --portal i14y --i14y-map automation/I14Y_dct_map.json ## for I14Y

# --- Configuration ---
SHACL_URL = "https://raw.githubusercontent.com/opendata-swiss/ogdch_checker/main/ogdch.shacl.ttl"

# --- Define Namespaces and Mappings ---
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

NAMESPACES = {
    "dcat": DCAT, 
    "dct": DCT, 
    "sh": SH, 
    "rdfs": RDFS, 
    "foaf": FOAF, 
    "rdf": RDF,
    "skos": SKOS
}


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

# 3. I14Y_TO_DCAT_MAP is loaded from a file

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
            g.bind("rdfs", RDFS)
            g.bind("foaf", FOAF)
            g.bind("rdf", RDF)
            g.bind("skos", SKOS)
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

def get_shacl_shape_rules(g, shape_node, base_properties):
    """
    Parses a specific SHACL NodeShape and returns its rules
    as a JSON Schema properties/required/recommended dict.
    """
    properties = {}
    required = set()
    recommended = set()
    
    for prop_node in g.objects(shape_node, SH.property):
        path_uri = g.value(prop_node, SH.path)
        if not path_uri or path_uri == RDF.type: # Skip rdf:type
            continue
            
        prop_key = shorten_uri(path_uri, NAMESPACES)
        severity = g.value(prop_node, SH.severity, default=SH.Violation)
        min_count = g.value(prop_node, SH.minCount)
        
        message_node = g.value(prop_node, SH.message)
        message = str(message_node) if message_node else ""
        message_lower = message.lower()
        is_deprecated = "deprecated" in message_lower
        
        is_useful_message = (
            message and 
            not is_deprecated and 
            "mandatory" not in message_lower and
            "must be provided" not in message_lower
        )

        is_mandatory = (min_count and int(min_count) >= 1 and severity == SH.Violation)
        is_recommended = (severity == SH.Warning) and (not is_deprecated)
        
        if is_mandatory:
            required.add(prop_key)
        elif is_recommended:
            recommended.add(prop_key)

        properties[prop_key] = {}
        
        if is_useful_message:
            base_desc = base_properties.get(prop_key, {}).get("description", "")
            properties[prop_key]["description"] = f"{base_desc}\n\n**Portal Requirement:** {message}"
        
        enum_list_node = g.value(prop_node, SH["in"])
        if enum_list_node:
            enum_list = [str(item) for item in g.list(enum_list_node)]
            properties[prop_key]["enum"] = [e for e in enum_list if e]
            properties[prop_key]["type"] = "string"

    return {
        "properties": properties, 
        "required": sorted(list(required)),
        "recommended": sorted(list(recommended))
    }


def merge_shacl_rules(g, base_schema, target_class_uri):
    """
    Merges top-level SHACL rules into a base JSON schema.
    Returns the modified schema, and the sets of required/recommended fields.
    """
    main_shape = g.value(subject=None, predicate=SH.targetClass, object=target_class_uri)
    if not main_shape:
        print(f"    -> Warning: No sh:NodeShape found for {target_class_uri}. Skipping SHACL merge.", file=sys.stderr)
        return base_schema, set(), set()

    shacl_required = set()
    shacl_recommended = set()
    base_properties = base_schema.get("properties", {})

    for prop_node in g.objects(main_shape, SH.property):
        path_uri = g.value(prop_node, SH.path)
        if not path_uri or path_uri == RDF.type: # Skip rdf:type
            continue
            
        prop_key = shorten_uri(path_uri, NAMESPACES)
        
        # 1. Handle 'required' & 'recommended' logic
        severity = g.value(prop_node, SH.severity, default=SH.Violation)
        min_count = g.value(prop_node, SH.minCount)
        
        message_node = g.value(prop_node, SH.message)
        message = str(message_node) if message_node else ""
        message_lower = message.lower()
        is_deprecated = "deprecated" in message_lower
        
        is_useful_message = (
            message and 
            not is_deprecated and 
            "mandatory" not in message_lower and
            "must be provided" not in message_lower
        )
        
        is_mandatory = (min_count and int(min_count) >= 1 and severity == SH.Violation)
        is_recommended = (severity == SH.Warning) and (not is_deprecated)
        
        if is_mandatory:
            shacl_required.add(prop_key)
        elif is_recommended:
            shacl_recommended.add(prop_key)

        # Append Description Logic
        if is_useful_message and prop_key in base_properties:
            base_desc = base_properties[prop_key].get("description", "")
            base_schema["properties"][prop_key]["description"] = f"{base_desc}\n\n**Portal Requirement:** {message}"

        # 2. Handle 'enum' logic
        enum_list_node = g.value(prop_node, SH["in"])
        if enum_list_node:
            enum_list = [str(item) for item in g.list(enum_list_node)]
            strict_enum = [e for e in enum_list if e]
            if prop_key in base_properties:
                base_schema["properties"][prop_key]["enum"] = strict_enum
        
        # 3. Handle NESTED rules (for Distribution)
        nested_shape_node = g.value(prop_node, SH.node)
        
        
        base_prop = base_properties.get(prop_key, {})
        prop_type = base_prop.get("type", "string")
        is_array = "array" in prop_type if isinstance(prop_type, list) else prop_type == "array"

        if nested_shape_node and is_array:
            print(f"    -> Found nested SHACL shape for array property '{prop_key}'. Parsing...")
            
            nested_base_props = base_prop.get("items", {}).get("properties", {})
            nested_rules = get_shacl_shape_rules(g, nested_shape_node, nested_base_props)
            
            if "items" not in base_schema["properties"][prop_key]:
                base_schema["properties"][prop_key]["items"] = {}
                
            base_schema["properties"][prop_key]["items"].update(nested_rules)
            
            if "properties" in nested_rules:
                for nested_key, nested_prop in nested_rules["properties"].items():
                    if "description" in nested_prop and nested_key in nested_base_props:
                        base_schema["properties"][prop_key]["items"]["properties"][nested_key]["description"] = nested_prop["description"]

            print(f"    -> Successfully merged SHACL rules for '{prop_key}'.")
        
        elif nested_shape_node and not is_array:
             print(f"    -> Found nested SHACL shape for non-array property '{prop_key}'. Appending message only.")
             # This is a validation rule *on* the property (e.g., must be in a scheme)
             pass

    return base_schema, shacl_required, shacl_recommended


def merge_i14y_rules(spec, base_schema, model_name, translation_map):
    """
    Merges I14Y OpenAPI 'required' rules into a base JSON schema.
    It *translates* the keys before adding them.
    """
    
    try:
        model_schema = spec["components"]["schemas"][model_name]
    except KeyError:
        print(f"    -> Warning: Model '{model_name}' not found in OpenAPI spec. Skipping.", file=sys.stderr)
        return base_schema, set(), set()
        
    i14y_flat_required = set(model_schema.get("required", []))
    print(f"    -> Found {len(i14y_flat_required)} I14Y-specific fields for '{model_name}'.")

    # --- 1. Translate Required Keys ---
    i14y_dcat_required = set()
    required_translation = translation_map.get(model_name, {}).get("Required", {})
    for flat_key in i14y_flat_required:
        dcat_key = required_translation.get(flat_key)
        if dcat_key:
            i14y_dcat_required.add(dcat_key)
        else:
            print(f"    -> Warning: No DCAT translation for I14Y *required* key '{flat_key}'. Skipping.")

    # --- 2. Translate Recommended Keys (from I14Y map) ---
    i14y_dcat_recommended = set()
    recommended_translation = translation_map.get(model_name, {}).get("Recommended", {})
    for flat_key in recommended_translation:
        dcat_key = recommended_translation.get(flat_key)
        if dcat_key:
            i14y_dcat_recommended.add(dcat_key)
        else:
            print(f"    -> Warning: No DCAT translation for I14Y *recommended* key '{flat_key}'. Skipping.")

    # --- 3. Handle nested Distribution ---
    if model_name == "DcatDatasetInputModel":
        print("    -> Found Dataset, looking for nested I14Y Distribution rules...")
        try:
            dist_model = spec["components"]["schemas"]["DcatDistributionInputModel"]
            dist_map = translation_map.get("DcatDistributionInputModel", {})
            
            # Get and translate required distribution fields
            dist_flat_required = set(dist_model.get("required", []))
            dist_req_translation = dist_map.get("Required", {})
            dist_dcat_required = {dist_req_translation.get(k) for k in dist_flat_required if dist_req_translation.get(k)}
            
            # Get and translate recommended distribution fields
            dist_flat_recommended = set(dist_map.get("Recommended", {}).keys())
            dist_rec_translation = dist_map.get("Recommended", {})
            dist_dcat_recommended = {dist_rec_translation.get(k) for k in dist_flat_recommended if dist_rec_translation.get(k)}

            if "dcat:distribution" not in base_schema["properties"]:
                 base_schema["properties"]["dcat:distribution"] = {}
            if "items" not in base_schema["properties"]["dcat:distribution"]:
                 base_schema["properties"]["dcat:distribution"]["items"] = {}
                 
            dist_prop = base_schema["properties"]["dcat:distribution"]["items"]
            
            dist_prop_req = set(dist_prop.get("required", []))
            dist_prop_rec = set(dist_prop.get("recommended", []))
            
            dist_prop["required"] = sorted(list(dist_prop_req | dist_dcat_required))
            dist_prop["recommended"] = sorted(list((dist_prop_rec | dist_dcat_recommended) - set(dist_prop["required"])))

            print(f"    -> Merged I1Failure: 4Y distribution rules (Req: {dist_dcat_required}, Rec: {dist_dcat_recommended})")
            
        except KeyError:
            print("    -> Warning: Could not find 'DcatDistributionInputModel' in spec.", file=sys.stderr)

    return base_schema, i14y_dcat_required, i14y_dcat_recommended


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
@click.option(
    '--i14y-url',
    type=str,
    default="https://apiconsole.i14y.admin.ch/partner/v1/Release.json",
    show_default=True,
    help="URL to the I14Y 'Release.json' OpenAPI specification."
)
def build_strict_schemas(portal, input_dir, output_dir, prefix, i14y_map, i14y_url):
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
        
        rules_source = fetch_rules(i14y_url)
        shacl_rules = fetch_rules(SHACL_URL)  
        
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
        base_recommended = set(base_schema.get("recommended", []))
        
        portal_required = set()
        portal_recommended = set()
        
        # --- Apply Rules based on Portal ---
        if portal == 'ods':
            shacl_class_uri = SCHEMA_TO_SHACL_CLASS[f.name]
            base_schema, portal_req, portal_rec = merge_shacl_rules(rules_source, base_schema, shacl_class_uri)
            portal_required.update(portal_req)
            portal_recommended.update(portal_rec)

        elif portal == 'i14y':
            # 1. Apply base SHACL rules first
            shacl_class_uri = SCHEMA_TO_SHACL_CLASS[f.name]
            base_schema, shacl_req, shacl_rec = merge_shacl_rules(shacl_rules, base_schema, shacl_class_uri)
            portal_required.update(shacl_req)
            
            # For I14Y, the SHACL recommended fields not added
            portal_recommended.update(set()) # Start with an empty set
            
            # 2. Apply I14Y-specific rules on top
            if f.name in mapping_dict:
                i14y_model_name = mapping_dict[f.name]
                base_schema, i14y_req, i14y_rec = merge_i14y_rules(rules_source, base_schema, i14y_model_name, translation_map)
                portal_required.update(i14y_req)
                portal_recommended.update(i14y_rec)
            else:
                 print(f"    -> Note: '{f.name}' has no I14Y-specific API model. Using base DCAT rules.")
        
        # --- Create Final 'required' and 'recommended' Lists ---
        final_required = base_required | portal_required
        final_recommended = (base_recommended | portal_recommended) - final_required
        
        base_schema["required"] = sorted(list(final_required))
        base_schema["recommended"] = sorted(list(final_recommended))

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