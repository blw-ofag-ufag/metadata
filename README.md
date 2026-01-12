[![Combine Datasets](https://github.com/blw-ofag-ufag/metadata/actions/workflows/combine-datasets.yml/badge.svg)](https://github.com/blw-ofag-ufag/metadata/actions/workflows/combine-datasets.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-ND 4.0](https://img.shields.io/badge/License-CC%20BY--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nd/4.0/)
[![GitHub last commit](https://img.shields.io/github/last-commit/blw-ofag-ufag/metadata.svg)](https://github.com/blw-ofag-ufag/metadata/commits)
[![GitHub issues](https://img.shields.io/github/issues/blw-ofag-ufag/metadata.svg)](https://github.com/blw-ofag-ufag/metadata/issues)

Welcome to the **FOAG Metadata** repository! Here, you'll find the metadata files that describe various datasets of ours, the Python automation script responsible for merging and validating our metadata files, as well as the JSON Schemas that ensure each record follows a consistent format. Under `data/processed`, we store the combined metadata ready for use in the FOAG Data Catalog. This setup helps maintain high-quality, well-structured metadata that is compatible with both [I14Y](https://www.i14y.admin.ch/) and [opendata.swiss](https://opendata.swiss).

The metadata you find here is displayed in a more user-friendly way by our [data catalog](https://github.com/blw-ofag-ufag/data-catalog) web application.

---

## 🏆 Metadata Quality Dashboard

This repository includes a **Quality Assurance Dashboard** built with Streamlit and deployed statically via **Stlite** (Python in the browser). It allows data stewards to audit datasets against the `dataset.json` schema, check for broken links, and calculate a "FAIRC" quality score.

👉 **[View the Live Dashboard](https://blw-ofag-ufag.github.io/metadata/dashboard/)**

### Architecture
The dashboard runs entirely in the client's browser (Serverless).
1.  **Builder:** GitHub Actions runs `src/audit.py` to validate links and calculate scores.
2.  **Snapshot:** The results are saved to `dashboard/data_snapshot.json`.
3.  **Viewer:** The `dashboard/` folder is published to GitHub Pages. `index.html` loads the Stlite engine, which executes `app.py` using the JSON snapshot.

### 1. Prerequisites & Installation locally

Ensure you have **Python 3.12+** installed.

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
# Generates: dashboard/data_snapshot.json
python -m src.audit
```

### 3. Run the Dashboard

```bash
streamlit run dashboard/app.py
```
