#!/usr/bin/env python
import json
import requests
import sys
import os
import click
import re
import io
import pandas as pd
import markdown
from pathlib import Path
from rdflib import Graph, URIRef
from rdflib.namespace import Namespace, SH, RDF

# --- Usage ---

# For opendata.swiss (ODS):
# python automation/build-strict-schemas.py --input-dir data/schemas --output-dir data/schema_strict --prefix strict-ods- --portal ods
#
# For I14Y:
# python automation/build-strict-schemas.py --input-dir data/schemas --output-dir data/schema_strict --prefix strict-i14y- --portal i14y
# (This will use the default handbook URL. You can override it with --i14y-handbook-url)

# --- Configuration ---
SHACL_URL = "https://raw.githubusercontent.com/opendata-swiss/ogdch_checker/refs/heads/main/ogdch.shacl.ttl"

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


# 1. Mapping for SHACL (ODS)
SCHEMA_TO_SHACL_CLASS = {
    "dataset.json": DCAT.Dataset
}

# 2. Mapping for I14Y Handbook
SCHEMA_TO_I14Y_HEADER = {
    "dataset.json": "## Datensatz",
    "dataService.json": "## Elektronische Schnittstelle (API)"
}

# --- Helper Functions ---

def fetch_rules(url):
    """Fetches a JSON, TTL, or MD file from a URL."""
    print(f"Fetching rules from {url}...")
    try:
        r = requests.get(url)
        r.raise_for_status()
        
        if url.endswith(".json"):
            print("Successfully parsed JSON file.")
            return r.json()
        elif url.endswith(".md"):
            print("Successfully parsed Markdown file.")
            return r.text # Return raw markdown text
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

# --- ODS (SHACL) Parser Functions ---

def get_shacl_shape_rules(g, shape_node, base_properties):
    """
    Parses a specific SHACL NodeShape and returns its rules
    as a JSON Schema properties/required/recommended dict.
    """
    properties = {}
    required = set()
    recommended = set()
    
    IGNORE_PATHS = {RDF.type, SKOS.inScheme}
    
    for prop_node in g.objects(shape_node, SH.property):
        path_uri = g.value(prop_node, SH.path)
        
        if not path_uri or path_uri in IGNORE_PATHS:
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

        if prop_key.startswith("http"):
             print(f"       -> Warning: Skipping unknown IRI property {prop_key}")
             continue

        # Only update properties that are *already* in the base schema
        if prop_key in base_properties:
            properties[prop_key] = {}
            if is_useful_message:
                base_desc = base_properties.get(prop_key, {}).get("description", "")
                if base_desc:
                        properties[prop_key]["description"] = f"{base_desc}\n\n**Portal Requirement:** {message}"
                else:
                        properties[prop_key]["description"] = f"**Portal Requirement:** {message}"
                
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


def merge_shacl_rules(g, base_schema, target_class_uri, update_descriptions=True):
    """
    Merges top-level SHACL rules into a base JSON schema.
    Returns the modified schema, and the sets of required/recommended fields.
    """
    main_shape = g.value(subject=None, predicate=SH.targetClass, object=target_class_uri)
    if not main_shape:
        print(f"       -> Warning: No sh:NodeShape found for {target_class_uri}. Skipping SHACL merge.", file=sys.stderr)
        return base_schema, set(), set()

    shacl_required = set()
    shacl_recommended = set()
    base_properties = base_schema.get("properties", {})
    
    IGNORE_PATHS = {RDF.type, SKOS.inScheme}

    for prop_node in g.objects(main_shape, SH.property):
        path_uri = g.value(prop_node, SH.path)

        if not path_uri or path_uri in IGNORE_PATHS:
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
            shacl_required.add(prop_key)
        elif is_recommended:
            shacl_recommended.add(prop_key)

        if update_descriptions and is_useful_message and prop_key in base_properties:
            base_desc = base_properties[prop_key].get("description", "")
            if base_desc:
                base_schema["properties"][prop_key]["description"] = f"{base_desc}\n\n**Portal Requirement:** {message}"
            else:
                base_schema["properties"][prop_key]["description"] = f"**Portal Requirement:** {message}"

        enum_list_node = g.value(prop_node, SH["in"])
        if enum_list_node:
            enum_list = [str(item) for item in g.list(enum_list_node)]
            strict_enum = [e for e in enum_list if e]
            if prop_key in base_properties:
                base_schema["properties"][prop_key]["enum"] = strict_enum
        
        nested_shape_node = g.value(prop_node, SH.node)
        
        base_prop = base_properties.get(prop_key, {})
        prop_type = base_prop.get("type", "string")
        is_array = "array" in prop_type if isinstance(prop_type, list) else prop_type == "array"

        if nested_shape_node and is_array:
            print(f"       -> Found nested SHACL shape for array property '{prop_key}'. Parsing...")
            
            nested_base_props = base_prop.get("items", {}).get("properties", {})
            nested_rules = get_shacl_shape_rules(g, nested_shape_node, nested_base_props)
            
            if "items" not in base_schema["properties"][prop_key]:
                base_schema["properties"][prop_key]["items"] = {}
                
            base_items_req = set(base_schema["properties"][prop_key]["items"].get("required", []))
            base_items_rec = set(base_schema["properties"][prop_key]["items"].get("recommended", []))

            new_req = base_items_req.union(nested_rules.get("required", []))
            new_rec = (base_items_rec.union(nested_rules.get("recommended", []))) - new_req

            base_schema["properties"][prop_key]["items"]["required"] = sorted(list(new_req))
            base_schema["properties"][prop_key]["items"]["recommended"] = sorted(list(new_rec))
            
            if update_descriptions and "properties" in nested_rules:
                for nested_key, nested_prop in nested_rules["properties"].items():
                    if "description" in nested_prop and nested_key in nested_base_props:
                        base_schema["properties"][prop_key]["items"]["properties"][nested_key]["description"] = nested_prop["description"]

            print(f"       -> Successfully merged SHACL rules for '{prop_key}'.")
        
        elif nested_shape_node and not is_array:
             print(f"       -> Found nested SHACL shape for non-array property '{prop_key}'. Appending message only.")
             pass

    return base_schema, shacl_required, shacl_recommended


# --- I14Y (Markdown) PARSER Functions ---

def parse_md_table(table_md):
    """Parses a single Markdown table and extracts rules."""
    required = set()
    recommended = set()
    
    # This regex finds prefix:key (like 'dct:title' or 'dcat:landingPage')
    # It will find the *first* match in the string, which works for
    # 'dct:title' and 'Teil von dcat:contactPoint'
    key_regex = re.compile(r'([a-zA-Z0-9]+:\w+)')
    
    try:
        html = markdown.markdown(table_md, extensions=['tables'])
        df = pd.read_html(io.StringIO(html))[0]
    except Exception as e:
        print(f"     -> Warning: Could not parse Markdown table. {e}", file=sys.stderr)
        return set(), set()

    if "URI" not in df.columns or "Anmerkung" not in df.columns:
        print(f"     -> Warning: Table missing 'URI' or 'Anmerkung' column. Skipping.")
        return set(), set()

    for _, row in df.iterrows():
        uri = str(row["URI"])
        note = str(row["Anmerkung"]).lower()
        
        # Find the first 'prefix:key' match. ---
        key = None
        match = key_regex.search(uri)
        if match:
            key = match.group(1) # Get the matched key, e.g., "dct:title"
        else:
            continue
            
        # Check the requirement level
        if "obligatorisch" in note:
            required.add(key)
        elif "erwünscht" in note:
            recommended.add(key)
            
    return required, recommended

def merge_i14y_rules(md_text, base_schema, header, shacl_graph):
    """
    Finds and parses all I14Y rules from the Markdown text
    for a given schema.
    
    It also uses the SHACL graph to merge enums and descriptions.
    """
    
    # 1. Find the main section for the schema (e.g., "## Datensatz")
    try:
        section_regex = re.compile(rf'^{re.escape(header)}\s*.*?\n(.*?)(?=\n##|\Z)', re.MULTILINE | re.DOTALL)
        section_md = section_regex.search(md_text).group(1)
    except Exception:
        print(f"     -> Warning: Could not find section for '{header}' in handbook. Skipping.", file=sys.stderr)
        return base_schema, set(), set()
    
    # 2. Find all tables within that section
    table_regex = re.compile(r'(\|.*?\n\|\s*-+.*?\n(?:\|.*?\n)+)')
    portal_required = set()
    portal_recommended = set()
    
    for table_match in table_regex.finditer(section_md):
        table_md = table_match.group(1)
        req, rec = parse_md_table(table_md)
        portal_required.update(req)
        portal_recommended.update(rec)

    # 3. Merge SHACL rules for enums/descriptions ---

    if base_schema["title"] == "Dataset Schema":
        base_schema, _, _ = merge_shacl_rules(shacl_graph, base_schema, DCAT.Dataset, update_descriptions=True)
    elif base_schema["title"] == "Data service Schema":
        # Note: ODS SHACL doesn't have DataService, so this will just
        # add enums/descriptions for any properties that overlap with Dataset.
        base_schema, _, _ = merge_shacl_rules(shacl_graph, base_schema, DCAT.Dataset, update_descriptions=True)


    # 4. Specifically find the Distribution table (it's a subsection)
    if header == "## Datensatz":
        try:
            dist_regex = re.compile(r'### Distribution\s*.*?\n(\|.*?\n\|-.*?\n(?:\|.*?\n)+)', re.DOTALL)
            dist_table_md = dist_regex.search(section_md).group(1)
            
            dist_req, dist_rec = parse_md_table(dist_table_md)
            
            if "dcat:distribution" not in base_schema["properties"]:
                 base_schema["properties"]["dcat:distribution"] = {}
            if "items" not in base_schema["properties"]["dcat:distribution"]:
                 base_schema["properties"]["dcat:distribution"]["items"] = {}
            
            dist_prop = base_schema["properties"]["dcat:distribution"]["items"]
            
            dist_prop_req = set(dist_prop.get("required", []))
            dist_prop_rec = set(dist_prop.get("recommended", []))
            
            dist_prop["required"] = sorted(list(dist_prop_req | dist_req))
            dist_prop["recommended"] = sorted(list((dist_prop_rec | dist_rec) - set(dist_prop["required"])))

            print(f"     -> Merged I14Y distribution rules (Req: {dist_req}, Rec: {dist_rec})")
        
        except Exception:
            print(f"     -> Warning: Could not find/parse Distribution table for I14Y.")

    print(f"     -> Found I14Y rules (Req: {portal_required}, Rec: {portal_recommended})")
    return base_schema, portal_required, portal_recommended


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
    '--i14y-handbook-url',
    type=str,
    default="https://raw.githubusercontent.com/I14Y-ch/handbook/refs/heads/main/content/de/anhang/eingabefelder.md",
    show_default=True,
    help="URL to the I14Y handbook's Markdown file."
)
def build_strict_schemas(portal, input_dir, output_dir, prefix, i14y_handbook_url):
    """
    Generates 'strict' JSON schemas for portal validation based on a
    chosen source of truth (ODS SHACL or I14Y Handbook).
    """
    
    # --- 1. Load the correct rules based on --portal flag ---
    rules_source = None
    shacl_rules = None # Only used by I14Y for enums/descriptions
    
    if portal == 'ods':
        rules_source = fetch_rules(SHACL_URL)
        parser_func = merge_shacl_rules
        mapping_dict = SCHEMA_TO_SHACL_CLASS
    
    elif portal == 'i14y':
        rules_source = fetch_rules(i14y_handbook_url) # This is the Markdown text
        shacl_rules = fetch_rules(SHACL_URL) # Also load SHACL for enums/descriptions
        parser_func = merge_i14y_rules
        mapping_dict = SCHEMA_TO_I14Y_HEADER
    
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
            
        # Find the correct key for this file (either a SHACL class or a MD header)
        if portal == 'ods' and f.name not in SCHEMA_TO_SHACL_CLASS:
            print(f"Skipping '{f.name}' (not applicable for {portal.upper()} validation).")
            continue
        elif portal == 'i14y' and f.name not in SCHEMA_TO_I14Y_HEADER:
            print(f"Skipping '{f.name}' (not applicable for {portal.upper()} validation).")
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
            # 1. (Optional) Run SHACL parser *only* to update descriptions/enums
            if f.name in SCHEMA_TO_SHACL_CLASS:
                shacl_class_uri = SCHEMA_TO_SHACL_CLASS[f.name]
                base_schema, _, _ = merge_shacl_rules(shacl_rules, base_schema, shacl_class_uri, update_descriptions=True)
  
            
            # 2. Apply I14Y-specific rules from the Markdown file
            i14y_header = mapping_dict[f.name]

            base_schema, i14y_req, i14y_rec = merge_i14y_rules(rules_source, base_schema, i14y_header, shacl_rules)
            portal_required.update(i14y_req)
            portal_recommended.update(i14y_rec)
        
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