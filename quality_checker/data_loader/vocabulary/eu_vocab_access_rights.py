from xml.etree import ElementTree as ET
from data_loader.utils import save_json


TAG = r"{http://www.w3.org/2004/02/skos/core#}Concept"
IDENTIFIER = r"{http://purl.org/dc/elements/1.1/}identifier"


def extract_concept_identifiers(in_filepath, out_filepath):
    """
    Extract concept identifiers from a SKOS XML file and save them as a flat JSON list.

    This is a one-time utility function used to convert vocabulary terms (identified by 
    <skos:Concept> and their <dc:identifier>) from an RDF/XML format to JSON. The output 
    is saved to the specified location, typically in `data/vocabulary/`.

    Args:
        in_filepath (str or Path): Path to the input SKOS XML file.
        out_filepath (str or Path): Path where the resulting JSON file will be saved.
    """
    tree = ET.parse(in_filepath)
    root = tree.getroot()
    vocabulary = [concept.find(IDENTIFIER).text for concept in root.findall(TAG)]
    save_json(out_filepath, vocabulary, indent=0)

