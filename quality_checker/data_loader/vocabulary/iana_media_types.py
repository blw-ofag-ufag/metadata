# Source: https://www.iana.org/assignments/media-types/media-types.xhtml

from xml.etree import ElementTree as ET
from data_loader.config import MEDIATYPE


IANA_MEDIA_TYPE = "http://www.iana.org/assignments/media-types"
REGISTRY = r"{http://www.iana.org/assignments}registry"
RECORD = r"{http://www.iana.org/assignments}record"
FILE = r"{http://www.iana.org/assignments}file"

tree = ET.parse(MEDIATYPE)
root = tree.getroot()
# A template is composed of a context and a data type.
# Example of a template: [context]/[type] -> application/csv.
templates = {
    file.text
    for registry in root.findall(REGISTRY)
    for record in registry.findall(RECORD)
    if (file := record.find(FILE)) is not None
}

MEDIA_TYPE_VOCABULARY = {f"{IANA_MEDIA_TYPE}/{template}" for template in templates}
