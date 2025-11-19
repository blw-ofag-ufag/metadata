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

# --- Configuration ---
SHACL_URL = "https://raw.githubusercontent.com/opendata-swiss/ogdch_checker/refs/heads/main/ogdch.shacl.ttl"

# --- Namespaces ---
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

NAMESPACES = {
    "dcat": DCAT, "dct": DCT, "sh": SH, "rdfs": RDFS, 
    "foaf": FOAF, "rdf": RDF, "skos": SKOS
}

# Mappings
SCHEMA_TO_SHACL_CLASS = {
    "dataset.json": DCAT.Dataset,
    "distribution.json": DCAT.Distribution, 
}

SCHEMA_TO_I14Y_HEADER = {
    "dataset.json": "## Datensatz",
    "dataService.json": "## Elektronische Schnittstelle (API)",
    "distribution.json": "### Distribution"
}

# --- Helper Functions ---

def fetch_rules(url):
    print(f"Fetching rules from {url}...")
    try:
        r = requests.get(url)
        r.raise_for_status()
        if url.endswith(".json"): return r.json()
        elif url.endswith(".md"): return r.text 
        else:
            g = Graph()
            g.parse(data=r.text, format="turtle")
            g.bind("dcat", DCAT)
            g.bind("dct", DCT)
            g.bind("sh", SH)
            return g
    except Exception as e:
        print(f"FATAL: Could not fetch rules: {e}", file=sys.stderr)
        sys.exit(1)

def shorten_uri(uri, ns_map):
    for prefix, namespace in ns_map.items():
        if str(uri).startswith(str(namespace)):
            return f"{prefix}:{str(uri).replace(str(namespace), '')}"
    return str(uri)

# --- SHACL Logic ---

def merge_shacl_rules(g, base_schema, target_class_uri, update_descriptions=True):
    # 1. Find the correct NodeShape
    if target_class_uri == DCAT.Distribution:
        main_shape = g.value(predicate=SH.targetClass, object=DCAT.Distribution)
    else:
        main_shape = g.value(subject=None, predicate=SH.targetClass, object=target_class_uri)
        
    if not main_shape:
        print(f"       -> Warning: No sh:NodeShape found for {target_class_uri}.")
        return base_schema, set(), set()

    shacl_required = set()
    shacl_recommended = set()
    base_properties = base_schema.get("properties", {})
    
    IGNORE_PATHS = {RDF.type, SKOS.inScheme}

    for prop_node in g.objects(main_shape, SH.property):
        path_uri = g.value(prop_node, SH.path)
        if not path_uri or path_uri in IGNORE_PATHS: continue
        
        prop_key = shorten_uri(path_uri, NAMESPACES)
        
        severity = g.value(prop_node, SH.severity, default=SH.Violation)
        min_count = g.value(prop_node, SH.minCount)
        message = str(g.value(prop_node, SH.message) or "")
        
        # Normalize whitespace for reliable matching
        msg_lower = " ".join(message.lower().split())
        
        # --- REVISED LOGIC ---
        
        # 1. Deprecated? (Exclude from Recommended)
        is_deprecated = "deprecated" in msg_lower or "exceptional use" in msg_lower or "should now be provided under" in msg_lower

        # 2. Strictly Mandatory (minCount >= 1 + Violation)
        is_strictly_mandatory = (min_count and int(min_count) >= 1 and severity == SH.Violation)
        
        # 3. Implicitly Mandatory (Violation + "Please provide" or "Must be chosen")
        # This catches dct:license in ODS which is missing minCount but is required.
        # We do NOT use just "must" because "must be a Literal" applies to optional fields too.
        text_implies_mandatory = ("please provide" in msg_lower or "must be chosen" in msg_lower)
        is_implicitly_mandatory = (severity == SH.Violation and text_implies_mandatory)

        # Final Decision
        if (is_strictly_mandatory or is_implicitly_mandatory) and not is_deprecated:
            shacl_required.add(prop_key)
        elif severity == SH.Warning and not is_deprecated:
            shacl_recommended.add(prop_key)

        # ---------------------

        if update_descriptions and message and not is_deprecated and prop_key in base_properties:
             base_desc = base_properties[prop_key].get("description", "")
             if "**Portal Requirement:**" not in base_desc:
                prefix = f"{base_desc}\n\n" if base_desc else ""
                base_schema["properties"][prop_key]["description"] = f"{prefix}**Portal Requirement:** {message}"

        enum_node = g.value(prop_node, SH["in"])
        if enum_node and prop_key in base_properties:
            enums = [str(item) for item in g.list(enum_node) if item]
            base_schema["properties"][prop_key]["enum"] = enums

    return base_schema, shacl_required, shacl_recommended

# --- I14Y Logic ---

def parse_md_table(table_md):
    required = set()
    recommended = set()
    key_regex = re.compile(r'\[([a-zA-Z0-9]+:\w+)\]')
    key_regex_plain = re.compile(r'([a-zA-Z0-9]+:\w+)')

    try:
        html = markdown.markdown(table_md, extensions=['tables'])
        df = pd.read_html(io.StringIO(html))[0]
    except Exception:
        return set(), set()

    if "URI" not in df.columns or "Anmerkung" not in df.columns: return set(), set()

    for _, row in df.iterrows():
        uri = str(row["URI"])
        note = str(row["Anmerkung"]).lower()
        
        match = key_regex.search(uri)
        if not match: match = key_regex_plain.search(uri)
        
        if match:
            key = match.group(1)
            if "obligatorisch" in note: required.add(key)
            elif "erwünscht" in note: recommended.add(key)
            
    return required, recommended

def merge_i14y_rules(md_text, base_schema, header, shacl_graph):
    stop_pattern = r'(?=\n##|\Z)' if header.startswith("## ") else r'(?=\n#|\Z)'
    section_regex = re.compile(rf'^{re.escape(header)}\s*.*?\n(.*?){stop_pattern}', re.MULTILINE | re.DOTALL)
    
    try:
        section_md = section_regex.search(md_text).group(1)
    except AttributeError:
        print(f"     -> Warning: Could not find section '{header}' in handbook.")
        return base_schema, set(), set()
    
    table_regex = re.compile(r'(\|.*?\n\|\s*-+.*?\n(?:\|.*?\n)+)')
    portal_req = set()
    portal_rec = set()

    for table_match in table_regex.finditer(section_md):
        r, rc = parse_md_table(table_match.group(1))
        portal_req.update(r)
        portal_rec.update(rc)

    return base_schema, portal_req, portal_rec

# --- Main Processor ---

def process_single_schema(name, base_schema, portal, rules_source, shacl_graph):
    base_required = set(base_schema.get("required", []))
    base_recommended = set(base_schema.get("recommended", []))
    
    ext_req = set()
    ext_rec = set()

    if portal == 'ods':
        if name in SCHEMA_TO_SHACL_CLASS:
            base_schema, ext_req, ext_rec = merge_shacl_rules(
                rules_source, base_schema, SCHEMA_TO_SHACL_CLASS[name]
            )
    elif portal == 'i14y':
        if name in SCHEMA_TO_SHACL_CLASS: 
             base_schema, _, _ = merge_shacl_rules(
                 shacl_graph, base_schema, SCHEMA_TO_SHACL_CLASS[name], update_descriptions=True
             )
        if name in SCHEMA_TO_I14Y_HEADER:
            base_schema, ext_req, ext_rec = merge_i14y_rules(
                rules_source, base_schema, SCHEMA_TO_I14Y_HEADER[name], shacl_graph
            )

    final_required = base_required | ext_req
    final_recommended = (base_recommended | ext_rec) - final_required

    base_schema["required"] = sorted(list(final_required))
    base_schema["recommended"] = sorted(list(final_recommended))
    
    return base_schema

def save_ordered_json(schema, path):
    key_order = ["$schema", "title", "description", "type", "required", "recommended", "properties"]
    ordered = {}
    for k in key_order:
        if k in schema: ordered[k] = schema[k]
    for k, v in schema.items():
        if k not in ordered: ordered[k] = v
        
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(ordered, f, indent=4)
    print(f"Saved {path}")

@click.command()
@click.option('--portal', type=click.Choice(['ods', 'i14y']), required=True)
@click.option('--input-dir', type=click.Path(exists=True), required=True)
@click.option('--output-dir', type=click.Path(), required=True)
@click.option('--prefix', default='strict-')
@click.option('--i14y-handbook-url', default="https://raw.githubusercontent.com/I14Y-ch/handbook/refs/heads/main/content/de/anhang/eingabefelder.md")
def build_strict_schemas(portal, input_dir, output_dir, prefix, i14y_handbook_url):
    
    if portal == 'ods':
        rules_source = fetch_rules(SHACL_URL)
        shacl_graph = rules_source
    else:
        rules_source = fetch_rules(i14y_handbook_url)
        shacl_graph = fetch_rules(SHACL_URL)

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        with open(input_path / "dataset.json") as f: dataset_schema = json.load(f)
        dist_schema_base = dataset_schema["properties"]["dcat:distribution"]["items"]
        dist_schema_base["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        dist_schema_base["title"] = "Distribution Schema"
        dist_schema_base["type"] = "object"
    except Exception as e:
        print(f"Error loading dataset.json: {e}")
        sys.exit(1)

    print(f"\n--- Building {portal.upper()} Schemas ---")

    print(">> Processing Distribution Rules...")
    strict_dist = process_single_schema(
        "distribution.json", dist_schema_base, portal, rules_source, shacl_graph
    )
    dist_filename = f"{prefix}distribution.json"
    save_ordered_json(strict_dist, output_path / dist_filename)

    print(">> Processing Dataset Rules...")
    strict_dataset = process_single_schema(
        "dataset.json", dataset_schema, portal, rules_source, shacl_graph
    )
    strict_dataset["properties"]["dcat:distribution"]["items"] = {
        "$ref": dist_filename
    }
    save_ordered_json(strict_dataset, output_path / f"{prefix}dataset.json")

    if (input_path / "dataService.json").exists() and portal != 'ods':
        with open(input_path / "dataService.json") as f: svc_schema = json.load(f)
        print(">> Processing DataService Rules...")
        strict_svc = process_single_schema(
            "dataService.json", svc_schema, portal, rules_source, shacl_graph
        )
        save_ordered_json(strict_svc, output_path / f"{prefix}dataService.json")

if __name__ == "__main__":
    build_strict_schemas()