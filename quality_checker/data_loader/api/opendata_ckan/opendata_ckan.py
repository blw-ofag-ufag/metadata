import requests
import warnings

from data_loader.audit.utils import DATASET


# TODO setup the authentification (verify=Very.certificates(url...))
VERIFY = False
TIMEOUT = 3
TIMEOUT_LONG = 60
""" We need a longer timeout when querying >2k packages from an organiztion; It takes ~20s. """

PROXY = {'http': 'http://proxy-bvcol.admin.ch:8080',
           'https': 'http://proxy-bvcol.admin.ch:8080'}

ROWS_PER_QUERY = 1_000
""" The maximum number of Packages provided in one query.
    It is a Server-side configuration; It cannot be modified on our end. 
"""

# API actions.
query_package_search = 'https://ckan.opendata.swiss/api/3/action/package_search'
query_package_show = 'https://ckan.opendata.swiss/api/3/action/package_show'
query_package_list = 'https://ckan.opendata.swiss/api/3/action/package_list'
query_package_list_with_resources = 'https://ckan.opendata.swiss/api/3/action/current_package_list_with_resources'
query_organisation_list = 'https://ckan.opendata.swiss/api/3/action/organization_list'
query_group_list = 'https://ckan.opendata.swiss/api/3/action/group_list'


def get(query, **kwargs):
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')

        response = requests.get(
            query,
            params=kwargs,
            verify=VERIFY,
            proxies=PROXY,
            timeout=TIMEOUT_LONG)

    if resp := response.json()['success'] == False:
        return resp # TODO: Handle the error case.
    else:
        return resp['result']


def get_package(id):
    """ Return the package with the provided id. """
    return get(query_package_show, **dict(id=id))


def get_organisation_packages(org_name):
    """ Return all packages created by an organisation. """
    params = dict(
        fq=f'organization:{org_name}', 
        rows=0)
    total_rows = get(query_package_search, **params)['count']

    div, mod = divmod(total_rows, ROWS_PER_QUERY)
    packages = []
    for i in range(div):
        params = dict(
            fq=f'organization:{org_name}',
            rows=ROWS_PER_QUERY, 
            start=ROWS_PER_QUERY*i)
        packages.extend(get(query_package_search, **params)[DATASET])

    if mod > 0:
        params = dict(
            fq=f'organization:{org_name}',
            rows=mod, 
            start=ROWS_PER_QUERY*div)
        packages.extend(get(query_package_search, **params)[DATASET])

    return dict(count=total_rows, results=packages)


def get_group_list():
    """ Return all available groups/categories referenced by opendata.swiss """
    return get(query_group_list)


def get_package_list():
    """ Return all packages referenced by opendata.swiss """
    return get(query_package_list)


def get_organisation_list():
    """ return all organisations referenced by opendata.swiss """
    return get(query_organisation_list)


def get_all_packages():
    all_datasets = []
    for org in get_organisation_list():
        all_datasets += get_organisation_packages(org)[DATASET]

    return all_datasets

def fix(dictionary, property):
    """ The opendata.swiss CKAN API is broken and returns badly formated results.
        This function formats those base ends and will not break once the API
        is restored. TODO: remove this func once the issue is solved.

        It is a temporary fix, while waiting for the team to fix the issue.
    """
    if property in dictionary:
        data = dictionary[property]
        dictionary[property] = json.loads(data) if type(data) is str else data

    return dictionary
    