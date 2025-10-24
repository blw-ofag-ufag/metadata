from data_loader.audit.utils import is_defined


# dcat:Dataset properties.
GEO_SEARCH = 'http://purl.org/dc/terms/spatial'
TIME_SEARCH = 'http://purl.org/dc/terms/temporal'

# dcat:Resource properties.
KEYWORD = 'http://www.w3.org/ns/dcat#keyword'
CATEGORY = 'http://www.w3.org/ns/dcat#theme'


def audit_findability(dataset: dict) -> dict[str, bool]:
    return {
        'keywords': is_defined(dataset, KEYWORD),
        'categories': is_defined(dataset, CATEGORY),
        'geo_search': is_defined(dataset, GEO_SEARCH),
        'time_search': is_defined(dataset, TIME_SEARCH)
    }
