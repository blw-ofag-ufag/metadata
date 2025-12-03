import requests
from data_loader.api.opendata_catalog_jsonld import VERIFY, PROXY, HEADERS


def generate_detailed_org_list(organization_audits):
    org_list = list(organization_audits.keys())
    org_details = [get_organisation_details(org) for org in org_list]
    keys = {"name", "display_name", "description", "image_display_url", "package_count"}
    filter_keys = lambda org: {key: value for key, value in org.items() if key in keys}
    return [filter_keys(org) for org in org_details]


def get_organisation_details(id):
    return requests.get(
        "https://ckan.opendata.swiss/api/3/action/organization_show",
        verify=VERIFY,
        proxies=PROXY,
        headers=HEADERS,
        params={"id": id},
    ).json()["result"]
