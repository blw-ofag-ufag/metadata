import logging
import os
import queue
import random
import requests
import time
import warnings

from typing import List

from data_loader.config import ENV_AUDIT_HTTP_PROXY, ENV_AUDIT_HTTPS_PROXY

logger = logging.getLogger(__name__)


# HTTP Connection.
VERIFY = False
TIMEOUT = 1
TIMEOUT_LONG = 60
HEADERS = {"User-Agent": "OGDLinkVerifier/1.0 (+https://dashboard.opendata.swiss/)"}   
PROXY = {
    "http": os.environ.get(ENV_AUDIT_HTTP_PROXY, None),
    "https": os.environ.get(ENV_AUDIT_HTTPS_PROXY, None),
}

# API get.
CATALOG_QUERY = "https://ckan.opendata.swiss/catalog.jsonld"
RETRY_WAIT = 5
RETRY_RANDOM_WAIT = 3
OVERREAD = 2

# STRUCTURE: catalog.jsonld
ID = "@id"
TYPE = "@type"
VALUE = "@value"
DATASET = "http://www.w3.org/ns/dcat#dataset"

# Item Type.
PAGED_COLLECTION = "http://www.w3.org/ns/hydra/core#PagedCollection"

# Paged-collection key.
LAST_PAGE = "http://www.w3.org/ns/hydra/core#lastPage"


def request_all_pages() -> List[requests.Request]:
    """
    Gather every page from opendata.swiss' catalog.jsonld.
    Return the request result for each page, as a list of
    `requests.Request` objects.

    To avoid triggering anti-DDoS mechanisms, it downloads
    one page at a time.

    Warning: Although not observed so far, new datasets might be added to the catalog
    while pages are being gathered. This could shift the pagination and lead to missed
    or duplicated entries. To reduce the risk of such inconsistencies, the catalog is
    intentionally **overread** beyond the reported number of pages.
    """
    output_queue = queue.Queue()
    first_page = request_page_retry(1)
    last_page_number = get_page_count(first_page.json())
    output_queue.put(first_page)
    logger.info("  page  1 downloaded")
    for page in range(2, last_page_number + 1 + OVERREAD):
        output_queue.put(request_page_retry(page))
        if page % 10 == 0:
            logger.info(f"  page {page} downloaded")

    return list(output_queue.queue)


def get_page_count(raw_data: List[dict]) -> int:
    """
    Search for the Paged Collection item within the raw data.
    The Paged Collection inform us about the last page number.
    """
    for item in raw_data:
        if (TYPE in item) and (PAGED_COLLECTION in item[TYPE]):
            return int(item[LAST_PAGE][0][VALUE].split("page=")[1])


def request_page(page: int) -> requests.Request:
    """Request a page by number."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        return requests.get(
            CATALOG_QUERY,
            proxies=PROXY,
            verify=VERIFY,
            headers=HEADERS,
            params=dict(page=page),
        )


def request_page_retry(page: int, maxtry: int = 5) -> None:
    """
    Send a new query until it receive a valid response.
    Upon failure, wait 5 ± 3 seconds and retry.
    """
    response = None
    _try = 0
    while True:
        response = request_page(page)
        if (response is not None) and response.status_code == 200:
            break
        elif _try > maxtry:
            requests.exceptions.RetryError(
                f"Failed to retrive page {page} after {maxtry} attempts."
            )
        else:
            time.sleep(
                RETRY_WAIT + random.randint(-RETRY_RANDOM_WAIT, RETRY_RANDOM_WAIT)
            )
            _try += 1

    return response


def requests_to_json(pages: List[requests.Request]) -> List:
    """Extract the data from request objects and format to json."""
    json_list = [page.json() for page in pages]
    return [entry for entries in json_list for entry in entries]
