import math
from typing import List, Any, Optional, Tuple
from src.models import DatasetInput, DistributionInput
from src.config import settings

# ==============================================================================
# CONSTANTS
# ==============================================================================
NON_PROPRIETARY_FORMATS = {"CSV", "JSON", "XML", "RDF", "TTL", "GEOJSON", "TXT", "HTML", "ODS"}
MACHINE_READABLE_FORMATS = {"CSV", "JSON", "XML", "RDF", "TTL", "GEOJSON", "XLSX", "XLS"}
LICENSE_VOCABULARY = {"terms_open", "terms_by", "terms_ask", "terms_by_ask", "cc-zero", "cc-by/4.0", "cc-by-sa/4.0"}
ACCESS_RIGHTS_VOCABULARY = {"CONFIDENTIAL", "NON_PUBLIC", "PUBLIC", "RESTRICTED", "SENSITIVE"}

class QualityScorer:
    """
    Calculates FAIRC scores and generates Improvement Suggestions based on the gap
    between the Earned Score and the Max Weight.
    """

    def analyze_quality(self, dataset: DatasetInput) -> dict:
        """
        Main Entry Point: Computes scores AND suggestions.
        Returns dictionary for DB update.
        """
        suggestions = []

        # 1. Calculate components
        findability, s_find = self._score_findability(dataset)
        accessibility, s_acc = self._score_accessibility(dataset)
        interoperability, s_int = self._score_interoperability(dataset)
        reusability, s_reu = self._score_reusability(dataset)
        contextuality, s_con = self._score_contextuality(dataset)

        # 2. Aggregate
        suggestions.extend(s_find)
        suggestions.extend(s_acc)
        suggestions.extend(s_int)
        suggestions.extend(s_reu)
        suggestions.extend(s_con)

        total_score = math.floor(findability + accessibility + interoperability + reusability + contextuality)

        return {
            "swiss_score": total_score,
            "findability_score": math.floor(findability),
            "accessibility_score": math.floor(accessibility),
            "interoperability_score": math.floor(interoperability),
            "reusability_score": math.floor(reusability),
            "contextuality_score": math.floor(contextuality),
            "quality_suggestions": suggestions
        }

    # --- HELPER: Suggestion Generator ---
    def _add_suggestion(self, dimension: str, key: str, max_pts: int, earned_pts: float, list_ref: list):
        """
        Calculates the gap. If gap > 0, adds a suggestion.
        """
        gap = max_pts - earned_pts
        if gap > 0:
            # Round to avoid floating point weirdness (e.g., 19.99999)
            gap_rounded = round(gap)
            if gap_rounded > 0:
                list_ref.append({
                    "dimension": dimension,
                    "key": key,         # Translation key
                    "points": gap_rounded
                })

    # --- SCORING LOGIC ---

    def _score_findability(self, ds: DatasetInput) -> Tuple[float, list]:
        score = 0.0
        sug = []
        dim = "Findability"

        # Keywords
        w = settings.WEIGHT_FINDABILITY_KEYWORDS
        pts = w if (ds.keywords and len(ds.keywords) > 0) else 0
        score += pts
        self._add_suggestion(dim, "crit_keywords", w, pts, sug)

        # Categories
        w = settings.WEIGHT_FINDABILITY_CATEGORIES
        pts = w if (ds.themes and len(ds.themes) > 0) else 0
        score += pts
        self._add_suggestion(dim, "crit_themes", w, pts, sug)

        # Geo
        w = settings.WEIGHT_FINDABILITY_GEO_SEARCH
        pts = w if (getattr(ds, "spatial", None)) else 0
        score += pts
        self._add_suggestion(dim, "crit_geo", w, pts, sug)

        # Time
        w = settings.WEIGHT_FINDABILITY_TIME_SEARCH
        pts = w if (getattr(ds, "temporal", None)) else 0
        score += pts
        self._add_suggestion(dim, "crit_time", w, pts, sug)

        return score, sug

    def _score_accessibility(self, ds: DatasetInput) -> Tuple[float, list]:
        score = 0.0
        sug = []
        dim = "Accessibility"
        dists = ds.distributions
        
        if not dists:
            # If no distributions, all points are lost
            self._add_suggestion(dim, "crit_access", settings.WEIGHT_ACCESSIBILITY_ACCESS_URL, 0, sug)
            self._add_suggestion(dim, "crit_download", settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL, 0, sug)
            self._add_suggestion(dim, "crit_download_valid", settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID, 0, sug)
            return 0.0, sug

        count = len(dists)
        
        # Access URL Valid (Weighted Average)
        w = settings.WEIGHT_ACCESSIBILITY_ACCESS_URL
        valid_access = sum(1 for d in dists if self._is_http_success(d.access_url_status))
        earned_access = w * (valid_access / count)
        score += earned_access
        self._add_suggestion(dim, "crit_access", w, earned_access, sug)

        # Download URL Provided (Weighted Average)
        w = settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL
        has_dl = sum(1 for d in dists if d.download_url)
        earned_dl = w * (has_dl / count)
        score += earned_dl
        self._add_suggestion(dim, "crit_download", w, earned_dl, sug)

        # Download URL Valid (Weighted Average)
        w = settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID
        valid_dl = sum(1 for d in dists if d.download_url and self._is_http_success(d.download_url_status))
        earned_dl_valid = w * (valid_dl / count)
        score += earned_dl_valid
        self._add_suggestion(dim, "crit_download_valid", w, earned_dl_valid, sug)

        return score, sug

    def _score_interoperability(self, ds: DatasetInput) -> Tuple[float, list]:
        # Logic: Score is based on the BEST distribution.
        sug = []
        dim = "Interoperability"
        
        if not ds.distributions:
            # Fail all
            self._add_suggestion(dim, "crit_format", settings.WEIGHT_INTEROP_FORMAT, 0, sug)
            self._add_suggestion(dim, "crit_media", settings.WEIGHT_INTEROP_MEDIA_TYPE, 0, sug)
            self._add_suggestion(dim, "crit_vocab", settings.WEIGHT_INTEROP_VOCABULARY, 0, sug)
            self._add_suggestion(dim, "crit_openfmt", settings.WEIGHT_INTEROP_NON_PROPRIETARY, 0, sug)
            self._add_suggestion(dim, "crit_machine", settings.WEIGHT_INTEROP_MACHINE_READABLE, 0, sug)
            self._add_suggestion(dim, "crit_dcat", settings.WEIGHT_INTEROP_DCAT_AP, 0, sug)
            return 0.0, sug

        # Calculate score for every distribution, keep the best one
        best_score = -1.0
        best_breakdown = {}

        for d in ds.distributions:
            current_score = 0.0
            breakdown = {}
            
            # Format
            w = settings.WEIGHT_INTEROP_FORMAT
            p = w if d.format_type else 0
            current_score += p
            breakdown['crit_format'] = p

            # Media
            w = settings.WEIGHT_INTEROP_MEDIA_TYPE
            p = w if d.media_type else 0
            current_score += p
            breakdown['crit_media'] = p

            # Vocab
            w = settings.WEIGHT_INTEROP_VOCABULARY
            p = w if (d.format_type and d.media_type) else 0 # Simplified vocab check
            current_score += p
            breakdown['crit_vocab'] = p

            # Non-Proprietary
            w = settings.WEIGHT_INTEROP_NON_PROPRIETARY
            fmt = d.format_type.upper() if d.format_type else ""
            p = w if fmt in NON_PROPRIETARY_FORMATS else 0
            current_score += p
            breakdown['crit_openfmt'] = p

            # Machine Readable
            w = settings.WEIGHT_INTEROP_MACHINE_READABLE
            p = w if fmt in MACHINE_READABLE_FORMATS else 0
            current_score += p
            breakdown['crit_machine'] = p

            # DCAT-AP
            w = settings.WEIGHT_INTEROP_DCAT_AP
            p = w # Assumed True
            current_score += p
            breakdown['crit_dcat'] = p

            if current_score > best_score:
                best_score = current_score
                best_breakdown = breakdown

        # Generate suggestions based on the BEST distribution's missing points
        self._add_suggestion(dim, "crit_format", settings.WEIGHT_INTEROP_FORMAT, best_breakdown['crit_format'], sug)
        self._add_suggestion(dim, "crit_media", settings.WEIGHT_INTEROP_MEDIA_TYPE, best_breakdown['crit_media'], sug)
        self._add_suggestion(dim, "crit_vocab", settings.WEIGHT_INTEROP_VOCABULARY, best_breakdown['crit_vocab'], sug)
        self._add_suggestion(dim, "crit_openfmt", settings.WEIGHT_INTEROP_NON_PROPRIETARY, best_breakdown['crit_openfmt'], sug)
        self._add_suggestion(dim, "crit_machine", settings.WEIGHT_INTEROP_MACHINE_READABLE, best_breakdown['crit_machine'], sug)
        self._add_suggestion(dim, "crit_dcat", settings.WEIGHT_INTEROP_DCAT_AP, best_breakdown['crit_dcat'], sug)

        return best_score, sug

    def _score_reusability(self, ds: DatasetInput) -> Tuple[float, list]:
        score = 0.0
        sug = []
        dim = "Reusability"
        dists = ds.distributions
        count = len(dists) if dists else 0

        # License (Average)
        w = settings.WEIGHT_REUSE_LICENSE
        earned = 0
        if count > 0:
            valid = sum(1 for d in dists if d.license_id)
            earned = w * (valid / count)
        score += earned
        self._add_suggestion(dim, "crit_license", w, earned, sug)

        # License Vocab (Average)
        w = settings.WEIGHT_REUSE_LICENSE_VOCAB
        earned = 0
        if count > 0:
            valid = sum(1 for d in dists if d.license_id in LICENSE_VOCABULARY)
            earned = w * (valid / count)
        score += earned
        self._add_suggestion(dim, "crit_lic_vocab", w, earned, sug)

        # Access Rights
        w = settings.WEIGHT_REUSE_ACCESS_RESTRICTION
        pts = w if ds.access_rights else 0
        score += pts
        self._add_suggestion(dim, "crit_access_res", w, pts, sug)

        # Access Vocab
        w = settings.WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB
        pts = w if ds.access_rights in ACCESS_RIGHTS_VOCABULARY else 0
        score += pts
        self._add_suggestion(dim, "crit_access_vocab", w, pts, sug)

        # Contact
        w = settings.WEIGHT_REUSE_CONTACT_POINT
        has_contact = ds.contact_point and (ds.contact_point.get("schema:name") or ds.contact_point.get("schema:email"))
        pts = w if has_contact else 0
        score += pts
        self._add_suggestion(dim, "crit_contact", w, pts, sug)

        # Publisher
        w = settings.WEIGHT_REUSE_PUBLISHER
        pts = w if ds.publisher else 0
        score += pts
        self._add_suggestion(dim, "crit_publisher", w, pts, sug)

        return score, sug

    def _score_contextuality(self, ds: DatasetInput) -> Tuple[float, list]:
        score = 0.0
        sug = []
        dim = "Contextuality"
        dists = ds.distributions
        count = len(dists) if dists else 0

        # Rights (Average)
        w = settings.WEIGHT_CONTEXT_RIGHTS
        earned = 0
        if count > 0:
            valid = sum(1 for d in dists if d.rights)
            earned = w * (valid / count)
        score += earned
        self._add_suggestion(dim, "crit_rights", w, earned, sug)

        # File Size (Average)
        w = settings.WEIGHT_CONTEXT_FILE_SIZE
        earned = 0
        if count > 0:
            valid = sum(1 for d in dists if d.byte_size is not None)
            earned = w * (valid / count)
        score += earned
        self._add_suggestion(dim, "crit_filesize", w, earned, sug)

        # Issue Date
        w = settings.WEIGHT_CONTEXT_ISSUE_DATE
        pts = w if ds.issued else 0
        score += pts
        self._add_suggestion(dim, "crit_issue", w, pts, sug)

        # Mod Date
        w = settings.WEIGHT_CONTEXT_MODIFICATION_DATE
        pts = w if ds.modified else 0
        score += pts
        self._add_suggestion(dim, "crit_mod", w, pts, sug)

        return score, sug

    def _is_http_success(self, status_code: Any) -> bool:
        if isinstance(status_code, int):
            return 200 <= status_code < 400
        return False