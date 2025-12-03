import asyncio
import logging
import requests
import warnings

from collections import Counter
from functools import cache
from urllib.parse import urlparse

from data_loader.api.opendata_catalog_jsonld.query import VERIFY, PROXY, TIMEOUT, HEADERS
from data_loader.audit.utils import get_distributions

logger = logging.getLogger(__name__)

# dcat:Distribution properties.
ID = "@id"
ACCESS_URL = "http://www.w3.org/ns/dcat#accessURL"
DOWNLOAD_URL = "http://www.w3.org/ns/dcat#downloadURL"

# Htts status codes.
HTTP_OTHER_ERROR = 400
HTTP_PROXY_ERROR = 502
HTTP_TIMEOUT = 408
HTTP_SSL_CERTIFICATE_ERROR = 495
HTTP_CONNECTION_ERROR = 503
HTTP_VALID_START, HTTP_VALID_END = 200, 400

# We send N queries at a time per domain, to not trigger DoS protections.
# Semaphores in known_domains controle the number of concurent queries per domain.
ASYNC_PER_DOMAIN = 1
known_domains = dict()


async def audit_accessibility(dataset, debug=False):
    if debug:
        return init_empty()

    distributions = get_distributions(dataset)
    access_urls = get_urls(distributions, ACCESS_URL)
    download_urls = get_urls(distributions, DOWNLOAD_URL)

    # The slowest part of our program. Each query is at least > 200ms.
    access_status = await asyncio.gather(*[test_url(url) for url in access_urls])
    download_status = await asyncio.gather(*[test_url(url) for url in download_urls])

    return {
        "download_url": sum([(url is not None) for url in download_urls]),
        "access_url_status_frequency": Counter(s for s in access_status),
        "download_url_status_frequency": Counter(s for s in download_status),
        "access_url_valid": sum([is_success(s) for s in access_status]),
        "download_url_valid": sum([is_success(s) for s in download_status]),
    }


def get_urls(distributions, property):
    return [
        url
        for dist in distributions
        if (property in dist) and ((url := dist[property][0][ID]) is not None)
    ]


def is_success(status):
    """Return True for HTTP request status indicating a successful connection."""
    return (status is not None) and HTTP_VALID_START <= status < HTTP_VALID_END


run, done = 0, 0


async def test_url(url):
    global run, done
    domain = urlparsed if (urlparsed := urlparse(url).netloc) else url
    if domain not in known_domains:
        # Only N queries per domain can be sent at a time.
        known_domains[domain] = asyncio.Semaphore(ASYNC_PER_DOMAIN)

    async with known_domains[domain]:
        run += 1
        loop = asyncio.get_event_loop()
        status = await loop.run_in_executor(None, get_url_status, url)
        run -= 1
        done += 1
        if done == 50 or done % 400 == 0:
            logger.info(f"  Running({run:0>3}) Done({done:0>5}) LastDone(HTTP_{status}, {domain})")

    return status


@cache
def get_url_status(url):
    """
    Try to connect to the URL with the HTTP-HEAD method.
    Return the HTTP status of the request.
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            return requests.head(
                url, verify=VERIFY, proxies=PROXY, timeout=TIMEOUT, headers=HEADERS
            ).status_code
    except requests.exceptions.ProxyError:
        return HTTP_PROXY_ERROR
    except requests.exceptions.SSLError:
        return HTTP_SSL_CERTIFICATE_ERROR
    except requests.exceptions.Timeout:
        return HTTP_TIMEOUT
    except requests.exceptions.ConnectionError:
        return HTTP_CONNECTION_ERROR
    except requests.exceptions.RequestException:
        return HTTP_OTHER_ERROR


def init_empty():
    return {
        "download_url": 0,
        "access_url_status_frequency": {},
        "download_url_status_frequency": {},
        "access_url_valid": 0,
        "download_url_valid": 0,
    }
