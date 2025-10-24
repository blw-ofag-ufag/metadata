import asyncio
from typing import Any, Union

from data_loader.audit.findability import audit_findability
from data_loader.audit.accessibility import audit_accessibility
from data_loader.audit.reusability import audit_reusability
from data_loader.audit.contextuality import audit_contextuality
from data_loader.audit.interoperability import audit_interoperability
from data_loader.audit.utils import get_distributions
from data_loader.audit.scoring import add_score

VALUE = "@value"
IDENTIFIER = "http://purl.org/dc/terms/identifier"


async def audit_datasets(catalog: list[dict], debug: bool=False) -> dict[str, Any]:
    """Return the raw audit results for each dataset in the catalog.

    In debug mode, URL audits are skipped to **drastically** speed up execution.
    """
    return await asyncio.gather(*[audit_dataset(dataset, debug=debug) for dataset in catalog])


async def audit_dataset(dataset: dict, debug: bool=False) -> list[dict[str, Any]]:
    """Return the raw audit of a single dataset. Count the number of valid properties (YES) given.

    The raw audit contain the total count of positive (YES) values along with `distribution_count` and `organisation_name`.    
    """
    return {
        "identifyer": get_identifyer(dataset),
        "organisation_name": get_organisation_name(dataset),
        "distribution_count": len(get_distributions(dataset)),
        "findability": audit_findability(dataset),
        "accessibility": await audit_accessibility(dataset, debug=debug),
        "reusability": audit_reusability(dataset),
        "contextuality": audit_contextuality(dataset),
        "interoperability": audit_interoperability(dataset),
    }


def score_datasets(audits: list[dict]) -> dict[str, dict]:
    """Compute scores by dataset (one dataset per group)."""
    return score(
        {name: aggregate(group) for name, group in group_by_dataset(audits).items()}
    )


def score_organisations(audits: list[dict]) -> dict[str, dict]:
    """Compute scores by organisation."""
    return score(
        {name: aggregate(group) for name, group in group_by_org(audits).items()}
    )


def score_total(audits: list[dict]) -> dict[str, dict]:
    """Compute a single overall score for all metadatasets on opendata.swiss."""
    return score({"opendata.swiss": aggregate(audits)})


def score(audit_groups: dict[str, list[dict]]) -> dict[str, dict]:
    """Compute a score for each group of audited metadata, in place"""
    for audit in audit_groups.values():
        to_percent(audit)
        add_score(audit)
        remove_keys(audit)

    return audit_groups


def group_by_dataset(audits: list[dict]) -> dict[str, list[dict]]:
    """Group audits by dataset identifier (one dataset per group)."""
    return {audit["identifyer"]: [audit] for audit in audits}


def group_by_org(audits: list[dict]) -> dict[str, list[dict]]:
    """Group audits by organisation name."""
    organisations = dict()
    for audit in audits:
        org_name = audit["organisation_name"]
        if org_name not in organisations:
            organisations[org_name] = [audit]
        else:
            organisations[org_name].append(audit)

    return organisations


def get_identifyer(dataset: dict) -> str:
    """Return a dataset's identifyer."""
    return dataset[IDENTIFIER][0][VALUE]


def get_organisation_name(dataset: dict) -> str:
    return get_identifyer(dataset).split("@")[1]


def aggregate(audits: list[dict]) -> dict[str, Union[int, dict]]:
    """Aggregate all audit dictionaries as one."""
    # Initialize first entry.
    dictionary = initialize_empty()
    dictionary["dataset_count"] = len(audits)
    for audit in audits:
        dictionary["distribution_count"] += audit["distribution_count"]
        aggregate_dict(dictionary["findability"], audit["findability"])
        aggregate_dict(dictionary["reusability"], audit["reusability"])
        aggregate_dict(dictionary["contextuality"], audit["contextuality"])
        aggregate_dict(dictionary["interoperability"], audit["interoperability"])

        # Accessibility properties are handled differently.
        access_dict, access_audit = dictionary["accessibility"], audit["accessibility"]
        access_dict["download_url"] += access_audit["download_url"]
        access_dict["access_url_valid"] += access_audit["access_url_valid"]
        access_dict["download_url_valid"] += access_audit["download_url_valid"]
        aggregate_dict(access_dict["access_url_status_frequency"], access_audit["access_url_status_frequency"])  # fmt: skip
        aggregate_dict(access_dict["download_url_status_frequency"], access_audit["download_url_status_frequency"])  # fmt: skip

    return dictionary


def aggregate_dict(aggregator_dict: dict, source_dict: dict) -> None:
    """Add values from source_dict into aggregator_dict in place.
    
    If the key does not exist in aggregator_dict, it will be initialized with the source_dict value.
    """
    for key in source_dict.keys():
        if key in aggregator_dict:
            aggregator_dict[key] += source_dict[key]
        else:
            aggregator_dict[key] = source_dict[key]


def initialize_empty() -> dict[str, Union[int, dict]]:
    # fmt: off
    return {
        'dataset_count' : 0,
        'distribution_count' : 0,
        'findability' : {'keywords': 0, 'categories': 0, 'geo_search': 0, 'time_search': 0},
        'accessibility' : {'access_url_status_frequency': {}, 'download_url': 0, 'download_url_status_frequency': {}, 'access_url_valid': 0, 'download_url_valid': 0},
        'reusability' : {'license': 0, 'license_vocabulary': 0, 'access_restriction': 0, 'access_restriction_vocabulary': 0, 'contact_point': 0, 'publisher': 0},
        'contextuality' : {'rights': 0, 'file_size': 0, 'issue_date': 0, 'modification_date': 0, 'score': 0},
        'interoperability' : {'format': 0, 'media_type': 0, 'controlled_vocabulary': 0, 'non_proprietary': 0, 'machine_readable': 0, 'dcat_ap_compliance': 0}
    }
    # fmt: on


def to_percent(audit: dict[str, Union[int, dict]]) -> None:
    """Convert raw totals to percentages in place.

    A property may belong to either the dataset itself or its distributions.
    For distribution-level properties, the score is computed as the average across all distributions.
    """
    # fmt: off
    dataset_count = audit["dataset_count"]
    distribution_count = audit["distribution_count"]

    # Findability.
    findability = audit["findability"]
    for key, value in findability.items():
        findability[key] = round(value / dataset_count, 3)

    # Accessibility.
    accessibility = audit["accessibility"]
    accessibility["download_url"] = round(_safediv(accessibility["download_url"], distribution_count), 3)
    accessibility["access_url_valid"] = round(_safediv(accessibility["access_url_valid"], distribution_count), 3)
    accessibility["download_url_valid"] = round(_safediv(accessibility["download_url_valid"], distribution_count), 3)

    access_url = accessibility["access_url_status_frequency"]
    len_acc_url = sum(access_url.values())
    access_url = {key: round(value / len_acc_url, 3) for key, value in access_url.items()}
    accessibility["access_url_status_frequency"] = access_url

    download_url = accessibility["download_url_status_frequency"]
    len_down_url = sum(download_url.values())
    download_url = {key: round(value / len_down_url, 3) for key, value in download_url.items()}
    accessibility["download_url_status_frequency"] = download_url

    # Interoperability.
    interoperability = audit["interoperability"]
    for key, value in interoperability.items():
        interoperability[key] = round(value / dataset_count, 3)

    # Reusability.
    reusability = audit["reusability"]
    reusability["license"] = round(_safediv(reusability["license"], distribution_count), 3)
    reusability["license_vocabulary"] = round(_safediv(reusability["license_vocabulary"], distribution_count), 3)
    reusability["access_restriction"] = round(reusability["access_restriction"] / dataset_count, 3)
    reusability["access_restriction_vocabulary"] = round(reusability["access_restriction_vocabulary"] / dataset_count, 3)
    reusability["contact_point"] = round(reusability["contact_point"] / dataset_count, 3)
    reusability["publisher"] = round(reusability["publisher"] / dataset_count, 3)

    # Contextuality.
    contextuality = audit["contextuality"]
    contextuality["rights"] = round(_safediv(contextuality["rights"], distribution_count), 3)
    contextuality["file_size"] = round(_safediv(contextuality["file_size"], distribution_count), 3)
    contextuality["issue_date"] = round(contextuality["issue_date"] / dataset_count, 3)
    contextuality["modification_date"] = round(contextuality["modification_date"] / dataset_count, 3)
    # fmt: on


def _safediv(dividend: int, divisor: int) -> float:
    """Return zero instead of a ZeroDivisionError."""
    return dividend / divisor if divisor > 0 else 0.


def remove_keys(audit: dict) -> None:
    """Remove temporary items from a dictionary in place."""
    del audit["dataset_count"]
    del audit["distribution_count"]
