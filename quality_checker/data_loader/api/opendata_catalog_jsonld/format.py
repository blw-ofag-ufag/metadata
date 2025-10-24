import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Keys and data types in catalog.jsonld.
# Key.
ID = '@id'
TYPE = '@type'
VALUE = '@values'
DATASETS = 'http://www.w3.org/ns/dcat#dataset'
DISTRIBUTIONS = 'http://www.w3.org/ns/dcat#distribution'
# Paged-collection Key.
LAST_PAGE = 'http://www.w3.org/ns/hydra/core#lastPage'
# Organization key.
NAME = 'http://xmlns.com/foaf/0.1/name'
W3_NAME = 'http://www.w3.org/2006/vcard/ns#fn'

# Type.
PERIOD_OF_TIME = 'http://purl.org/dc/terms/PeriodOfTime'
RIGHTS_STATEMENT = 'http://purl.org/dc/terms/RightsStatement'
ORGANIZATION = 'http://xmlns.com/foaf/0.1/Organization'
W3_ORGANIZATION = 'http://www.w3.org/2006/vcard/ns#Organization'
PUBLISHER = 'http://purl.org/dc/terms/publisher'
CONTACT_POINT = 'http://www.w3.org/ns/dcat#contactPoint'
CATALOG_TYPE = 'http://www.w3.org/ns/dcat#Catalog'
DATASET_TYPE = 'http://www.w3.org/ns/dcat#Dataset'
DISTRIBUTION_TYPE = 'http://www.w3.org/ns/dcat#Distribution'
PAGED_COLLECTION = 'http://www.w3.org/ns/hydra/core#PagedCollection'

# Constants for `extract_items_and_catalog()` tuple.
ITEM_DICTIONARY, CATALOG = 0, 1


def extract_items_and_catalog(raw_data: List[dict]) -> Tuple[dict, set]:
    """ 
        This function does two things at once for performance purposes. 

        1. Extract the necessary items to create the data structure.
        2. Assemble the full catalog; returning it as a list of dataset IDs.
        
        Return a tuple `(item_dictionary, catalog_ids)`.

        Extracted items are stored in a dictionary for O(1) read times.
        
        This function assumes there are no duplicates in `raw_data`. 
        If there are, they will be overwritten.
    """
    item_dictionary = dict()
    catalog = list()
    for item in raw_data:
        if TYPE not in item:
            continue

        _type, _id = item[TYPE], item[ID]
        is_catalog_item = CATALOG_TYPE in _type
        is_structural_item = (
            DATASET_TYPE in _type
            or DISTRIBUTION_TYPE in _type
            # There are two possible keys for organizations.
            or ORGANIZATION in _type
            or W3_ORGANIZATION in _type
        )
        if is_catalog_item and DATASETS in item:
            # Assemble the full catalog (empty pages have no dataset filed.)
            catalog.extend(item[DATASETS])
        elif is_structural_item:
            # Store necessary items to later create the data structure.
            item_dictionary[_id] = item

    # Use a Set() to remove duplicate datasets from the catalog.
    catalog_ids = {dataset[ID] for dataset in catalog}

    return (item_dictionary, catalog_ids)


def format_data(data):
    items, catalog = extract_items_and_catalog(data)
    output = []
    for dataset_id in catalog:
        if dataset_id not in items:
            logger.error(f"Cannot find dataset '{dataset_id}' in the catalog!")
            continue

        dataset = items[dataset_id]
        # Replace a distribution reference with a distribution.
        if DISTRIBUTIONS in dataset:
            dist_ids = [dist[ID] for dist in dataset[DISTRIBUTIONS]]
            dataset[DISTRIBUTIONS] = [items[id] for id in dist_ids]

        # replace a publisher reference with a publisher name.
        if CONTACT_POINT in dataset:
            # The Publisher ID == Organization ID.
            organization_id = dataset[CONTACT_POINT][0][ID]

            # There are two possible keys for organization names.
            org = items[organization_id]
            name_key = NAME if NAME in org else W3_NAME
            if name_key not in org:
                logger.error(f"KeyError: An organisation has no name field! Organisation: {org}")
                continue

            # If multiple names are available, use the longest.
            name = max(org[name_key], key=len)
            dataset[CONTACT_POINT] = [name]
        
        output.append(dataset)

    return output
