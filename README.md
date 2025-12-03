[![Combine Datasets](https://github.com/blw-ofag-ufag/metadata/actions/workflows/combine-datasets.yml/badge.svg)](https://github.com/blw-ofag-ufag/metadata/actions/workflows/combine-datasets.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-ND 4.0](https://img.shields.io/badge/License-CC%20BY--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nd/4.0/)
[![GitHub last commit](https://img.shields.io/github/last-commit/blw-ofag-ufag/metadata.svg)](https://github.com/blw-ofag-ufag/metadata/commits)
[![GitHub issues](https://img.shields.io/github/issues/blw-ofag-ufag/metadata.svg)](https://github.com/blw-ofag-ufag/metadata/issues)

Welcome to the **FOAG Metadata** repository! Here, you'll find the metadata files that describe various datasets of ours, the Python automation script responsible for merging and validating our metadata files, as well as the JSON Schemas that ensure each record follows a consistent format. Under `data/processed`, we store the combined metadata ready for use in the FOAG Data Catalog. This setup helps maintain high-quality, well-structured metadata that is compatible with both [I14Y](https://www.i14y.admin.ch/) and [opendata.swiss](https://opendata.swiss).

The metadata you find here is displayed in a more user-friendly way by our [data catalog](https://github.com/blw-ofag-ufag/data-catalog) web application.

---

## Metadata Quality Dashboard

This repository includes a **Quality Assurance Dashboard** built with Streamlit. It allows data stewards to audit datasets against the BLW schema, check for broken links, and calculate a "FAIRC" quality score (Findable, Accessible, Interoperable, Reusable, Contextual).

### 1. Prerequisites & Installation

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

### 2. Initialize the Database

Before running the dashboard for the first time, you must run the audit pipeline. This script processes the raw JSON data, performs asynchronous URL health checks, calculates quality scores, and populates the local SQLite database (`data/qa.db`).

```bash
# Run the audit pipeline from the project root
python -m src.audit
```

### 3. Run the Dashboard

```bash
streamlit run dashboard/app.py
```

### 3b Access the UI via posit workbench

- Go to the PORTS tab in the bottom panel of VS Code/Editor
- Enter Port number indicated in the terminal. For example 8501 for `Local URL: http://localhost:8501`
- Hover over the "Forwarded Address" column
- Click on "Preview in Editor"
