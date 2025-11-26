import math
from typing import List, Any
from src.models import DatasetInput
from src.config import settings

NON_PROPRIETARY_FORMATS = {"CSV", "JSON", "XML", "RDF", "TTL", "GeoJSON", "TXT", "HTML", "ODS"}
MACHINE_READABLE_FORMATS = {"CSV", "JSON", "XML", "RDF", "TTL", "GeoJSON", "XLSX", "XLS"}
LICENSE_VOCABULARY = {"terms_open", "terms_by", "terms_ask", "terms_by_ask", "cc-zero", "cc-by/4.0", "cc-by-sa/4.0"}
ACCESS_RIGHTS_VOCABULARY = {"CONFIDENTIAL", "NON_PUBLIC", "PUBLIC", "RESTRICTED", "SENSITIVE"}

class QualityScorer:
    def compute_scores(self, dataset: DatasetInput) -> dict:
        f = self._score_findability(dataset)
        a = self._score_accessibility(dataset)
        i = self._score_interoperability(dataset)
        r = self._score_reusability(dataset)
        c = self._score_contextuality(dataset)
        return {
            "swiss_score": f + a + i + r + c,
            "findability_score": f,
            "accessibility_score": a,
            "interoperability_score": i,
            "reusability_score": r,
            "contextuality_score": c
        }

    def _score_findability(self, ds: DatasetInput) -> int:
        score = 0.0
        if ds.keywords: score += settings.WEIGHT_FINDABILITY_KEYWORDS
        if ds.themes: score += settings.WEIGHT_FINDABILITY_CATEGORIES
        if getattr(ds, "spatial", None): score += settings.WEIGHT_FINDABILITY_GEO_SEARCH
        if getattr(ds, "temporal", None): score += settings.WEIGHT_FINDABILITY_TIME_SEARCH
        return math.floor(score)

    def _score_accessibility(self, ds: DatasetInput) -> int:
        dists = ds.distributions
        if not dists: return 0
        count = len(dists)
        valid_acc = sum(1 for d in dists if self._is_http_success(d.access_url_status))
        has_dl = sum(1 for d in dists if d.download_url)
        valid_dl = sum(1 for d in dists if d.download_url and self._is_http_success(d.download_url_status))
        
        score = 0.0
        score += settings.WEIGHT_ACCESSIBILITY_ACCESS_URL * (valid_acc / count)
        score += settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL * (has_dl / count)
        score += settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID * (valid_dl / count)
        return math.floor(score)

    def _score_interoperability(self, ds: DatasetInput) -> int:
        if not ds.distributions: return 0
        best = 0.0
        for d in ds.distributions:
            curr = 0.0
            if d.format_type: curr += settings.WEIGHT_INTEROP_FORMAT
            if d.media_type: curr += settings.WEIGHT_INTEROP_MEDIA_TYPE
            if d.format_type and d.media_type: curr += settings.WEIGHT_INTEROP_VOCABULARY
            
            if d.format_type:
                fmt = d.format_type.upper()
                if fmt in NON_PROPRIETARY_FORMATS: curr += settings.WEIGHT_INTEROP_NON_PROPRIETARY
                if fmt in MACHINE_READABLE_FORMATS: curr += settings.WEIGHT_INTEROP_MACHINE_READABLE
            
            curr += settings.WEIGHT_INTEROP_DCAT_AP
            if curr > best: best = curr
        return math.floor(best)

    def _score_reusability(self, ds: DatasetInput) -> int:
        score = 0.0
        dists = ds.distributions
        if dists:
            cnt = len(dists)
            has_lic = sum(1 for d in dists if d.license_id)
            vocab_lic = sum(1 for d in dists if d.license_id in LICENSE_VOCABULARY)
            score += settings.WEIGHT_REUSE_LICENSE * (has_lic / cnt)
            score += settings.WEIGHT_REUSE_LICENSE_VOCAB * (vocab_lic / cnt)
        
        if ds.access_rights:
            score += settings.WEIGHT_REUSE_ACCESS_RESTRICTION
            if ds.access_rights in ACCESS_RIGHTS_VOCABULARY:
                score += settings.WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB
        
        if ds.contact_point and (ds.contact_point.get("schema:name") or ds.contact_point.get("schema:email")):
            score += settings.WEIGHT_REUSE_CONTACT_POINT
            
        if ds.publisher:
            score += settings.WEIGHT_REUSE_PUBLISHER
            
        return math.floor(score)

    def _score_contextuality(self, ds: DatasetInput) -> int:
        score = 0.0
        dists = ds.distributions
        if dists:
            cnt = len(dists)
            has_rights = sum(1 for d in dists if d.rights)
            has_size = sum(1 for d in dists if d.byte_size is not None)
            score += settings.WEIGHT_CONTEXT_RIGHTS * (has_rights / cnt)
            score += settings.WEIGHT_CONTEXT_FILE_SIZE * (has_size / cnt)
            
        if ds.issued: score += settings.WEIGHT_CONTEXT_ISSUE_DATE
        if ds.modified: score += settings.WEIGHT_CONTEXT_MODIFICATION_DATE
        return math.floor(score)

    def analyze_scoring_gaps(self, ds: DatasetInput) -> List[dict]:
        gaps = []
        
        # --- 1. Findability ---
        # Logic: Simple presence checks (matches scoring exactly)
        if not ds.keywords: gaps.append({"msg_key": "msg_missing_keywords", "points": settings.WEIGHT_FINDABILITY_KEYWORDS, "dim": "Findability"})
        if not ds.themes: gaps.append({"msg_key": "msg_missing_themes", "points": settings.WEIGHT_FINDABILITY_CATEGORIES, "dim": "Findability"})
        if not getattr(ds, "spatial", None): gaps.append({"msg_key": "msg_missing_geo", "points": settings.WEIGHT_FINDABILITY_GEO_SEARCH, "dim": "Findability"})
        if not getattr(ds, "temporal", None): gaps.append({"msg_key": "msg_missing_time", "points": settings.WEIGHT_FINDABILITY_TIME_SEARCH, "dim": "Findability"})
        
        # --- 2. Accessibility ---
        # Logic: Algebraic Difference (Max - Current). Reliable.
        current_acc = self._score_accessibility(ds)
        max_acc = (settings.WEIGHT_ACCESSIBILITY_ACCESS_URL + 
                   settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL + 
                   settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID)
        
        if current_acc < max_acc:
            points_lost = max_acc - current_acc
            gaps.append({"msg_key": "msg_broken_links", "points": int(points_lost), "dim": "Accessibility"})
        
        # --- 3. Interoperability ---
        # Logic: Algebraic Difference. Reliable.
        curr_interop = self._score_interoperability(ds)
        max_interop = (settings.WEIGHT_INTEROP_FORMAT + settings.WEIGHT_INTEROP_MEDIA_TYPE + settings.WEIGHT_INTEROP_VOCABULARY + settings.WEIGHT_INTEROP_NON_PROPRIETARY + settings.WEIGHT_INTEROP_MACHINE_READABLE + settings.WEIGHT_INTEROP_DCAT_AP)
        if curr_interop < max_interop:
            gaps.append({"msg_key": "msg_formats", "points": int(max_interop - curr_interop), "dim": "Interoperability"})
            
        # --- 4. Reusability ---
        # Logic: STRICT checks for Vocabulary compliance
        
        # A. License Existence
        if not ds.distributions or not any(d.license_id for d in ds.distributions):
            gaps.append({"msg_key": "msg_license", "points": settings.WEIGHT_REUSE_LICENSE, "dim": "Reusability"})
        else:
            # B. License Vocabulary (Invisible point loss fixed here)
            # Check if at least one distribution has a STANDARD license
            has_std_license = any(d.license_id in LICENSE_VOCABULARY for d in ds.distributions)
            if not has_std_license:
                gaps.append({"msg_key": "msg_license_vocab", "points": settings.WEIGHT_REUSE_LICENSE_VOCAB, "dim": "Reusability"})
        
        # C. Contact Point
        if not (ds.contact_point and (ds.contact_point.get("schema:name") or ds.contact_point.get("schema:email"))):
            gaps.append({"msg_key": "msg_contact", "points": settings.WEIGHT_REUSE_CONTACT_POINT, "dim": "Reusability"})
            
        # D. Publisher
        if not ds.publisher:
             gaps.append({"msg_key": "msg_publisher", "points": settings.WEIGHT_REUSE_PUBLISHER, "dim": "Reusability"})
             
        # E. Access Rights Existence
        if not ds.access_rights:
             gaps.append({"msg_key": "msg_access_rights", "points": settings.WEIGHT_REUSE_ACCESS_RESTRICTION, "dim": "Reusability"})
        else:
             # F. Access Rights Vocabulary (Invisible point loss fixed here)
             if ds.access_rights not in ACCESS_RIGHTS_VOCABULARY:
                 gaps.append({"msg_key": "msg_access_rights_vocab", "points": settings.WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB, "dim": "Reusability"})

        # --- 5. Contextuality ---
        # Logic: Split checks for Issued vs Modified
        
        if not ds.issued:
            gaps.append({"msg_key": "msg_date_issued", "points": settings.WEIGHT_CONTEXT_ISSUE_DATE, "dim": "Contextuality"})
        
        if not ds.modified:
            gaps.append({"msg_key": "msg_date_modified", "points": settings.WEIGHT_CONTEXT_MODIFICATION_DATE, "dim": "Contextuality"})
            
        # Rights & ByteSize
        if ds.distributions:
            has_rights = any(d.rights for d in ds.distributions)
            if not has_rights:
                gaps.append({"msg_key": "msg_rights", "points": settings.WEIGHT_CONTEXT_RIGHTS, "dim": "Contextuality"})
            
            has_size = any(d.byte_size is not None for d in ds.distributions)
            if not has_size:
                gaps.append({"msg_key": "msg_byte_size", "points": settings.WEIGHT_CONTEXT_FILE_SIZE, "dim": "Contextuality"})

        return gaps

    def _is_http_success(self, status: Any) -> bool:
        return isinstance(status, int) and 200 <= status < 400