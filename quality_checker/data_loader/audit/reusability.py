import data_loader.audit.utils as au
import data_loader.config as c
import data_loader.vocabulary.dcat_ap_ch as dcat
import data_loader.vocabulary.eu_vocab_access_rights as access_rights
from data_loader.utils import load_json

ACCESS_RAW = 'access-right-skos.rdf'
ACCESS_PREPROCESSED = 'access-rights_preprocessed.json'

# Load vocabulary lists.
LICENSE_VOCABULARY = dcat.VOCABULARY
ACCESS_RIGHT_VOCABULARY =  load_json(c.ACCESS_RIGHTS)

# dcat:Distribution properties.
MEDIA_TYPE = 'http://www.w3.org/ns/dcat#mediaType'

# dcat:Resource properties.
CONTACT_POINT = 'http://www.w3.org/ns/dcat#contactPoint'
LICENSE = 'http://purl.org/dc/terms/license'
PUBLISHER = 'http://purl.org/dc/terms/publisher'

# dcat:Distribution & dcat:Resource properties.
ACCESS_RIGHT = 'http://purl.org/dc/terms/accessRights'


def audit_reusability(dataset):
    distributions = au.get_distributions(dataset)
    return {
        "license": au.count_defined(distributions, LICENSE),
        "license_vocabulary": au.count_vocabulary_use(distributions, LICENSE, LICENSE_VOCABULARY),
        # Opendata.swiss data structure has no access restriction. OGD team asked the value to be 100% by default.
        "access_restriction": True,
        "access_restriction_vocabulary": True,
        "contact_point": au.is_defined(dataset, CONTACT_POINT),
        "publisher": au.is_defined(dataset, PUBLISHER)
    }