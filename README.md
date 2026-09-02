# FOAG Metadata

[![Combine Datasets](https://github.com/blw-ofag-ufag/metadata/actions/workflows/combine-datasets.yml/badge.svg)](https://github.com/blw-ofag-ufag/metadata/actions/workflows/combine-datasets.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-ND 4.0](https://img.shields.io/badge/License-CC%20BY--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nd/4.0/)
[![GitHub last commit](https://img.shields.io/github/last-commit/blw-ofag-ufag/metadata.svg)](https://github.com/blw-ofag-ufag/metadata/commits)
[![GitHub issues](https://img.shields.io/github/issues/blw-ofag-ufag/metadata.svg)](https://github.com/blw-ofag-ufag/metadata/issues)

Welcome to the **FOAG Metadata** repository. This repository contains the canonical metadata definitions, JSON schema artifacts, the dataset validation/audit automation and a client-side Quality Dashboard used by data stewards to validate and monitor dataset metadata quality.

## Repository tree (high-level)

Trimmed repository layout

```
.
├── .github/                     # CI/workflows and GitHub actions
├── .gitignore
├── LICENSE
├── README.md                    # <-- this file
├── automation/                  # Automation scripts for building / publishing
├── dashboard/                   # Static Streamlit (stlite) dashboard (viewer)
│   ├── index.html
│   ├── app.py
│   ├── translations.py
│   └── style.css
├── data/
│   ├── raw/                     # Raw metadata exports (source)
│   ├── processed/               # Processed/normalized dataset files (generated)
│   ├── schemas/                 # Catalog & working JSON Schemas (more permissive)
│   │   ├── Readme.md
│   │   ├── catalog.json
│   │   ├── dataService.json
│   │   ├── dataset.json
│   │   ├── datasetSeries.json
│   │   ├── dimensions.json
│   │   ├── keywords.json
│   │   └── roles.json
│   └── schema_strict/           # Strict/portal-enforced JSON Schemas (stricter)
│       ├── strict-dataService.json
│       ├── strict-dataset.json
│       ├── strict-distribution.json
│       ├── strict-i14y-dataService.json
│       ├── strict-i14y-dataset.json
│       ├── strict-i14y-distribution.json
│       ├── strict-ods-dataset.json
│       └── strict-ods-distribution.json
├── requirements.txt
├── src/                         # Builder / audit scripts (validation & snapshot generation)
│   └── audit.py                 # pipeline to validate, check links and create dashboard snapshot
└── tests/
```

How it fits together (runtime shape)
- The audit pipeline in `src/` reads raw metadata (`data/raw`), validates it against schemas (`data/schemas` or `data/schema_strict` depending on target), runs link-health checks and scoring, and writes a static snapshot consumed by the dashboard.
- The dashboard in `dashboard/` is a static stlite (Streamlit-in-the-browser) viewer that loads a JSON snapshot and renders an interactive QA UI entirely client-side.

---

## Short overview of the schemas

The schemas contain two related sets of JSON Schema artifacts used at different stages of the pipeline:

- `data/schemas/` — the working/authoring schema set. These schemas capture the expected metadata model for datasets, distributions and services, but are designed to be practical for contributors and transformations. They include `dataset.json`, `dataService.json`, `datasetSeries.json`, `catalog.json` and lookups such as `keywords.json` and `roles.json`.

- `data/schema_strict/` — the stricter schema set used to validate if a dataproduct meets the requirements for publishing to external portals (e.g., opendata.swiss, i14y). These are intended for final validation prior to submitting. They include `strict-dataset.json`, `strict-distribution.json`, `strict-dataService.json` and portal-specific specializations (e.g., `strict-i14y-*`, `strict-ods-*`).

Guidance:
- Use `data/schemas/` for local authoring, CI checks and transformations where some fields may be optional.
- Use `data/schema_strict/` for a pre-publication gate to ensure portal-level constraints are satisfied (license present, multilingual titles, access rights declared, distribution metadata complete, etc.).

---

## Metadata Quality Dashboard

This repository includes a **Quality Assurance Dashboard** built with Streamlit and deployed statically via **Stlite** (Python in the browser). It allows data stewards to audit datasets against the metadata model, run link health checks and inspect suggestions for improvement.

👉 **[View the Live Dashboard](https://blw-ofag-ufag.github.io/metadata/)**

### Architecture
The dashboard runs entirely in the client's browser (Serverless).
1.  **Builder:** GitHub Actions runs `src/audit.py` to validate links and calculate scores.
2.  **Snapshot:** The results are saved to `dashboard/data_summary.json` and `dashboard/data_details.json`.
3.  **Viewer:** The `dashboard/` folder is published to GitHub Pages. `index.html` loads the Stlite engine, which executes `app.py` using the JSON snapshot.

### 1. Prerequisites & Installation locally

Ensure you have **Python 3.9+** installed.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/blw-ofag-ufag/metadata.git
    cd metadata
    ```

2.  **Install dependencies:**
    It is highly recommended to use a virtual environment.
    ```bash
    # Create virtual env (optional but recommended)
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate

    # Install packages
    pip install -r requirements.txt
    ```

### 2. Generate Data Snapshot (The "Builder")

Before running the dashboard, you must generate the data. This script processes raw JSON, performs async URL health checks, and creates the static JSON snapshot.

```bash
# Run the audit pipeline from the project root
# Generates: dashboard/data_summary.json & dashboard/data_details.json 
python -m src.audit
```

### 3. Run the Dashboard

```bash
streamlit run dashboard/app.py
```

---

## Schema description: data/schemas vs data/schema_strict

Below are the main schema files and the notable differences between the regular (`data/schemas`) and strict (`data/schema_strict`) variants. These points reference the concrete files present in the repository.

Main schema files:
- data/schemas/dataset.json — canonical dataset schema used for authoring / validation
- data/schemas/dataService.json — service-level schema
- data/schemas/datasetSeries.json — series collection schema
- data/schemas/* (keywords.json, roles.json, catalog.json) — lookups and supporting assets

Strict schema variants:
- data/schema_strict/strict-dataset.json
- data/schema_strict/strict-distribution.json
- data/schema_strict/strict-dataService.json
- portal specializations: strict-i14y-*, strict-ods-* (tuned to target portals)

Main differences:

1. dct:accessRights is required in strict mode (line 10 in strict-dataset) but only recommended in regular mode (line 17 in dataset.json).

2. Distribution model divergence:

- Regular schema embeds distribution properties inline in the dataset
- Strict schema uses a $ref to strict-distribution.json

3. Distribution requirements:

- Regular: only requires dcat:accessURL, adms:status, dct:format
- Strict: requires those plus dct:title, dct:description, dct:license

4. `additionalProperties: false` in strict-distribution.json restricts extra properties.

5. Portal requirement annotations in descriptions (e.g., "Portal Requirement:...") appear only in strict schemas.

Practical implications for pipeline users
- Authoring & CI: Use `data/schemas/` for local schema validation during editing and transformations where a lighter-touch model helps contributors iterate.
- Pre-publication gate: Use `data/schema_strict/` to catch portal-level requirements (missing license, missing access rights, insufficient multilingual titles/descriptions, missing distribution metadata).
- The audit pipeline uses these schema families to decide “publishable” vs “needs changes” and the Dashboard surfaces the results to data stewards.

---

## Developer pointers
- `data/schemas/` — working schema set (authoring).
- `data/schema_strict/` — strict schema set (pre-publication / portal compliance).
- `src/audit.py` — pipeline that validates metadata files, checks link health, and generates the dashboard snapshot.
- `dashboard/app.py` and `dashboard/index.html` — the client-side viewer (stlite) that consumes the snapshot and shows scores / validation results.


