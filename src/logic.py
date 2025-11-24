import math
from typing import List, Any, Optional
from src.models import DatasetInput, DistributionInput
from src.config import settings

# ==============================================================================
# 1. SCORING CONSTANTS & VOCABULARIES
# ==============================================================================

# --- INTEROPERABILITY CONSTANTS ---
# Used to determine if the file format is open and usable by machines.
# Source: interoperability.py from opendata.swiss
NON_PROPRIETARY_FORMATS = {
    "CSV", "JSON", "XML", "RDF", "TTL", "GeoJSON", "TXT", "HTML", "ODS"
}

MACHINE_READABLE_FORMATS = {
    "CSV", "JSON", "XML", "RDF", "TTL", "GeoJSON", "XLSX", "XLS"
}

# --- REUSABILITY CONSTANTS ---
# Used to ensure legal clarity (License) and access permissions (Rights).
# Source: reusability.py from opendata.swiss and internal schema
LICENSE_VOCABULARY = {
    "terms_open", "terms_by", "terms_ask", "terms_by_ask", 
    "cc-zero", "cc-by/4.0", "cc-by-sa/4.0"
}

ACCESS_RIGHTS_VOCABULARY = {
    "CONFIDENTIAL", "NON_PUBLIC", "PUBLIC", "RESTRICTED", "SENSITIVE"
}


class QualityScorer:
    """
    Implements the 'opendata.swiss' metadata quality methodology.
    Calculates scores for Findability, Accessibility, Interoperability,
    Reusability, and Contextuality (FAIRC).
    """

    def compute_scores(self, dataset: DatasetInput) -> dict:
        """
        Main Entry Point: Aggregates all sub-scores into a final Swiss Score.
        Returns a dictionary ready for the database.
        """
        findability = self._score_findability(dataset)
        accessibility = self._score_accessibility(dataset)
        interoperability = self._score_interoperability(dataset)
        reusability = self._score_reusability(dataset)
        contextuality = self._score_contextuality(dataset)

        # Total score is the simple sum of the dimensional scores.
        total_score = (
            findability +
            accessibility +
            interoperability +
            reusability +
            contextuality
        )

        return {
            "swiss_score": total_score,
            "findability_score": findability,
            "accessibility_score": accessibility,
            "interoperability_score": interoperability,
            "reusability_score": reusability,
            "contextuality_score": contextuality
        }

    # ==========================================================================
    # 2. DIMENSION SCORING LOGIC
    # ==========================================================================

    def _score_findability(self, ds: DatasetInput) -> int:
        """
        Dimension: FINDABILITY
        Goal: Ensure the dataset can be found via search (Keywords, Themes, Geo, Time).
        Source: findability.py from opendata.swiss
        """
        score = 0.0

        # Check if keywords exist (dcat:keyword)
        if ds.keywords and len(ds.keywords) > 0:
            score += settings.WEIGHT_FINDABILITY_KEYWORDS

        # Check if themes/categories exist (dcat:theme)
        if ds.themes and len(ds.themes) > 0:
            score += settings.WEIGHT_FINDABILITY_CATEGORIES

        # Check if spatial coverage is defined (dct:spatial)
        if getattr(ds, "spatial", None) or getattr(ds, "dct_spatial", None): 
            score += settings.WEIGHT_FINDABILITY_GEO_SEARCH

        # Check if temporal coverage is defined (dct:temporal)
        if getattr(ds, "temporal", None):
            score += settings.WEIGHT_FINDABILITY_TIME_SEARCH

        return math.floor(score)

    def _score_accessibility(self, ds: DatasetInput) -> int:
        """
        Dimension: ACCESSIBILITY
        Goal: Ensure the links provided actually work (HTTP 200 OK).
        Dependency: Requires 'audit.py' to have already populated status codes.
        Source: accessibility.py from opendata.swiss
        """
        dists = ds.distributions
        if not dists:
            return 0

        count = len(dists)
        valid_access_url_count = 0
        has_download_url_count = 0
        valid_download_url_count = 0

        for d in dists:
            # Score if Access URL is reachable (HTTP 200-399)
            if self._is_http_success(getattr(d, "access_url_status", None)):
                valid_access_url_count += 1

            # Score if Download URL simply exists
            if d.download_url:
                has_download_url_count += 1
                
                # Score bonus if Download URL is also reachable
                if self._is_http_success(getattr(d, "download_url_status", None)):
                    valid_download_url_count += 1

        # Calculate weighted average across all distributions
        score = 0.0
        score += settings.WEIGHT_ACCESSIBILITY_ACCESS_URL * (valid_access_url_count / count)
        score += settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL * (has_download_url_count / count)
        score += settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID * (valid_download_url_count / count)

        return math.floor(score)

    def _score_interoperability(self, ds: DatasetInput) -> int:
        """
        Dimension: INTEROPERABILITY
        Goal: Ensure data formats are open and machine-readable.
        Rule: Score is based on the *single best* distribution, not the average.
        Source: interoperability.py from opendata.swiss
        """
        if not ds.distributions:
            return 0

        best_dist_score = 0.0

        for d in ds.distributions:
            current_score = 0.0
            has_format = bool(d.format_type)
            has_media = bool(d.media_type)
            
            # Basic Format/Media presence
            if has_format: current_score += settings.WEIGHT_INTEROP_FORMAT
            if has_media: current_score += settings.WEIGHT_INTEROP_MEDIA_TYPE

            # Controlled Vocabulary Check (Simplified)
            if has_format and has_media:
                current_score += settings.WEIGHT_INTEROP_VOCABULARY

            # Format Quality Checks (using constants defined at top)
            if has_format:
                fmt = d.format_type.upper()
                if fmt in NON_PROPRIETARY_FORMATS:
                    current_score += settings.WEIGHT_INTEROP_NON_PROPRIETARY
                if fmt in MACHINE_READABLE_FORMATS:
                    current_score += settings.WEIGHT_INTEROP_MACHINE_READABLE

            # DCAT-AP Compliance (Default assumption from legacy script)
            current_score += settings.WEIGHT_INTEROP_DCAT_AP

            # Maximize: We only care about the "best" file provided
            if current_score > best_dist_score:
                best_dist_score = current_score

        return math.floor(best_dist_score)

    def _score_reusability(self, ds: DatasetInput) -> int:
        """
        Dimension: REUSABILITY
        Goal: Ensure legal and administrative metadata is clear.
        Source: reusability.py from opendata.swiss
        """
        score = 0.0
        dists = ds.distributions
        dist_count = len(dists) if dists else 0

        # 1. Licensing (Average across distributions)
        if dist_count > 0:
            # Has any license?
            defined_licenses = sum(1 for d in dists if d.license_id)
            score += settings.WEIGHT_REUSE_LICENSE * (defined_licenses / dist_count)

            # Is it a standard license? (using constants defined at top)
            vocab_licenses = sum(1 for d in dists if d.license_id in LICENSE_VOCABULARY)
            score += settings.WEIGHT_REUSE_LICENSE_VOCAB * (vocab_licenses / dist_count)

        # 2. Access Rights (Dataset Level)
        if ds.access_rights:
            score += settings.WEIGHT_REUSE_ACCESS_RESTRICTION
            # Is it a standard access term?
            if ds.access_rights in ACCESS_RIGHTS_VOCABULARY:
                score += settings.WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB

        # 3. Contact Info Presence
        if ds.contact_point and (ds.contact_point.get("schema:name") or ds.contact_point.get("schema:email")):
            score += settings.WEIGHT_REUSE_CONTACT_POINT

        # 4. Publisher Presence
        if ds.publisher:
            score += settings.WEIGHT_REUSE_PUBLISHER

        return math.floor(score)

    def _score_contextuality(self, ds: DatasetInput) -> int:
        """
        Dimension: CONTEXTUALITY
        Goal: Ensure context (dates, sizes, rights) is provided.
        Source: contextuality.py from opendata.swiss
        """
        score = 0.0
        dists = ds.distributions
        dist_count = len(dists) if dists else 0

        # Distribution-level checks (Average)
        if dist_count > 0:
            # Rights field defined?
            defined_rights = sum(1 for d in dists if d.rights)
            score += settings.WEIGHT_CONTEXT_RIGHTS * (defined_rights / dist_count)

            # File size defined?
            defined_size = sum(1 for d in dists if d.byte_size is not None)
            score += settings.WEIGHT_CONTEXT_FILE_SIZE * (defined_size / dist_count)

        # Dataset-level checks
        if ds.issued:
            score += settings.WEIGHT_CONTEXT_ISSUE_DATE
        if ds.modified:
            score += settings.WEIGHT_CONTEXT_MODIFICATION_DATE

        return math.floor(score)

    # ==========================================================================
    # 3. UTILITIES
    # ==========================================================================

    def _is_http_success(self, status_code: Any) -> bool:
        """Helper: Returns True if status is 200-399."""
        if isinstance(status_code, int):
            return 200 <= status_code < 400
        return False