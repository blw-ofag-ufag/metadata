# Metadata Schemas

This directory contains the core JSON schemas for our internal data catalog.

They are intentionally "loose" to allow users to save work-in-progress (e.g., they permit empty strings `""` in enums).

These "base" schemas are used for internal validation. They serve as the foundation for a script (`automation/build-strict-schemas.py`) that generates separate "strict" schemas. Those strict schemas are required for metadata to be published on external portals like 
[opendata.swiss](https://opendata.swiss/en) and [I14Y](https://www.i14y.admin.ch/en/home).

---

## Schema Definitions

This directory contains the schemas for the following metadata objects:

* **`catalog.json`:** Defines the metadata for a **Data Catalog** (a collection of datasets).
* **`dataset.json`:** Defines the metadata for a single **Dataset**. This is the primary object for publication.
* **`dataService.json`:** Defines the metadata for a **Data Service** (e.g., an API).
* **`datasetSeries.json`:** A custom, internal schema for grouping related datasets into a series.
* **`roles.json`:** An internal schema defining user roles and permissions within the catalog.
