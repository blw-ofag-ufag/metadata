from math import floor

# Findability.
KEYWORDS = 30
CATEGORIES = 30
GEO_SEARCH = 20
TIME_SEARCH = 20

# Accessibility.
ACCESS_URL_ACCESSIBILITY = 50
DOWNLOAD_URL = 20
DOWNLOAD_URL_ACCESSIBILITY = 30

# Interoperabiltiy.
FORMAT = 20
MEDIA_TYPE = 10
FORMAT_MEDIA_VOCABULARY = 10
NON_PROPRIETARY = 20
MACHINE_READABLE = 20
DCAT_AP_COMPLIANCE = 30

# Reusability.
LICENSE = 20
LICENSE_VOCABULARY = 10
ACCESS_RESTRICTIONS = 10
ACCESS_RESTRICTIONS_VOCABULARY = 5
CONTACT_POINT = 20
PUBLISHER = 10

# Contextuality.
RIGHTS = 5
FILE_SIZE = 5
ISSUE_DATE = 5
MODIFICATION_DATE = 5


def add_score(audit: dict) -> None:
    """Add scores to the audit dictionary in place. """
    audit['findability']['score'] = findabilitiy_score(audit['findability'])
    audit['accessibility']['score'] = accessibility_score(audit['accessibility'])
    audit['interoperability']['score'] = interoperability_score(audit['interoperability'])     
    audit['reusability']['score']= reusability_score(audit['reusability'])    
    audit['contextuality']['score'] = contextuality_score(audit['contextuality'])


def findabilitiy_score(dictionary: dict) -> int:
    return floor(
        KEYWORDS * dictionary['keywords']
        + CATEGORIES *dictionary['categories']
        + GEO_SEARCH * dictionary['geo_search']
        + TIME_SEARCH * dictionary['time_search']
    )


def accessibility_score(dictionary: dict) -> int:
    return floor(
        ACCESS_URL_ACCESSIBILITY * dictionary['access_url_valid']
        + DOWNLOAD_URL * dictionary['download_url']
        + DOWNLOAD_URL_ACCESSIBILITY * dictionary['download_url_valid']
    )


def interoperability_score(dictionary: dict) -> int:
    return floor(
        FORMAT * dictionary['format']
        + MEDIA_TYPE * dictionary['media_type']
        + FORMAT_MEDIA_VOCABULARY * dictionary['controlled_vocabulary']
        + NON_PROPRIETARY * dictionary['non_proprietary']
        + MACHINE_READABLE * dictionary['machine_readable']
        + DCAT_AP_COMPLIANCE * dictionary['dcat_ap_compliance']
    )


def reusability_score(dictionary: dict) -> int:
    return floor(
        LICENSE * dictionary['license']
        + LICENSE_VOCABULARY * dictionary['license_vocabulary']
        + ACCESS_RESTRICTIONS * dictionary['access_restriction']
        + ACCESS_RESTRICTIONS_VOCABULARY * dictionary['access_restriction_vocabulary']
        + CONTACT_POINT * dictionary['contact_point']
        + PUBLISHER * dictionary['publisher']
    )


def contextuality_score(dictionary: dict) -> int:
    return floor(
        RIGHTS * dictionary['rights']
        + FILE_SIZE * dictionary['file_size']
        +ISSUE_DATE * dictionary['issue_date']
        + MODIFICATION_DATE * dictionary['modification_date']
    )