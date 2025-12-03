import data_loader.audit.utils as au


# dcat:CatalogRecord properties.
ISSUE_DATE = 'http://purl.org/dc/terms/issued'

# dcat:CatalogRecord & dcat:Distribution properties.
MODIFY_DATE = 'http://purl.org/dc/terms/modified'

# dcat:Distribution properties.
RIGHTS = 'http://purl.org/dc/terms/rights'
FILE_SIZE = 'http://www.w3.org/ns/dcat#byteSize'


def audit_contextuality(dataset):
    distributions = au.get_distributions(dataset)
    return {
        "rights": au.count_defined(distributions, RIGHTS),
        "file_size": au.count_defined(distributions, FILE_SIZE),
        "issue_date": au.is_defined(dataset, ISSUE_DATE),
        "modification_date": au.is_defined(dataset, MODIFY_DATE)
    }
