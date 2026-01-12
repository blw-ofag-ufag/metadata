from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from sqlalchemy import String, Float, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ==========================================
# 1. Pydantic Parsing Models (Input Layer)
# ==========================================

class MultilingualText(BaseModel):
    """Handles dictionary structures like {'de': '...', 'fr': '...'}"""
    de: Optional[str] = None
    fr: Optional[str] = None
    it: Optional[str] = None
    en: Optional[str] = None

class DistributionInput(BaseModel):
    """Parses a single distribution object from the raw JSON list."""
    model_config = ConfigDict(populate_by_name=True)

    identifier: Optional[str] = Field(alias="dct:identifier", default=None)
    title: Optional[MultilingualText] = Field(alias="dct:title", default=None)
    description: Optional[MultilingualText] = Field(alias="dct:description", default=None)
    access_url: Optional[str] = Field(alias="dcat:accessURL", default=None)
    download_url: Optional[str] = Field(alias="dcat:downloadURL", default=None)
    internal_path: Optional[str] = Field(alias="bv:internalPath", default=None)
    format_type: Optional[str] = Field(alias="dct:format", default=None)
    media_type: Optional[str] = Field(alias="dcat:mediaType", default=None)
    license_id: Optional[str] = Field(alias="dct:license", default=None)
    rights: Optional[str] = Field(alias="dct:rights", default=None)
    byte_size: Optional[int] = Field(alias="dcat:byteSize", default=None)
    modified: Optional[str] = Field(alias="dct:modified", default=None)
    
    # Helper to hold audit results temporarily (not in raw JSON)
    access_url_status: Optional[int] = None
    download_url_status: Optional[int] = None

    @model_validator(mode='after')
    def check_exclusivity(self):
        # We access the values directly from the model instance (self)
        url = self.access_url
        path = self.internal_path
        
        if url and path:
            raise ValueError(f"Distribution '{self.identifier or 'unknown'}' cannot have both an Access URL and an Internal Path. Please choose one.")
        return self

class DatasetInput(BaseModel):
    """
    The Master Parser.
    Maps JSON-LD fields (dct:...) to Pythonic names.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identity
    id: str = Field(alias="dct:identifier")
    rdf_type: str = Field(alias="rdf:type", default="dcat:Dataset")
    
    # Content
    title: MultilingualText = Field(alias="dct:title")
    description: Optional[MultilingualText] = Field(alias="dct:description", default=None)
    keywords: Optional[List[str]] = Field(alias="dcat:keyword", default_factory=list)
    themes: Optional[List[str]] = Field(alias="dcat:theme", default_factory=list)
    
    # Responsible Parties
    publisher: Optional[str] = Field(alias="dct:publisher", default=None)
    contact_point: Optional[Dict[str, Any]] = Field(alias="dcat:contactPoint", default=None)
    business_owner: Optional[str] = Field(alias="dataOwner", default=None)

    # Dates & Legal
    issued: Optional[str] = Field(alias="dct:issued", default=None)
    modified: Optional[str] = Field(alias="dct:modified", default=None)
    accrual_periodicity: Optional[str] = Field(alias="dct:accrualPeriodicity", default=None)
    access_rights: Optional[str] = Field(alias="dct:accessRights", default=None)
    
    # Spatial / Temporal
    spatial: Optional[Any] = Field(alias="dct:spatial", default=None)
    temporal: Optional[Any] = Field(alias="dct:temporal", default=None)

    # Structure
    distributions: Optional[List[DistributionInput]] = Field(alias="dcat:distribution", default_factory=list)

    # Injected Metrics
    schema_violations_count: int = Field(alias="schemaViolations", default=0)
    schema_violation_messages: List[str] = Field(alias="schemaViolationMessages", default_factory=list)
    input_quality_score: float = Field(alias="quality", default=0.0)

    @field_validator('distributions', mode='before')
    @classmethod
    def handle_null_distributions(cls, v):
        return v or []

    @field_validator('keywords', 'themes', mode='before')
    @classmethod
    def coerce_to_list(cls, v):
        """
        Fixes cases where a single string is provided instead of a list.
        Also handles dictionary structures (schema change) by flattening values.
        Example: "agriculture" -> ["agriculture"]
        Example: {"k1": {"de": "A"}, "k2": {"en": "B"}} -> ["A", "B"]
        """
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, dict):
            # [cite_start]Flatten dictionary values into a list of strings [cite: 1]
            flat_list = []
            for item in v.values():
                if isinstance(item, dict):
                    # Extract multilingual values
                    flat_list.extend(item.values())
                elif isinstance(item, str):
                    flat_list.append(item)
                elif isinstance(item, list):
                    flat_list.extend(item)
            # Remove None/Empty and duplicates
            return list(set(filter(None, flat_list)))
        return v

# ==========================================
# 2. SQLAlchemy Database Models (Storage Layer)
# ==========================================

class Base(DeclarativeBase):
    pass

class Dataset(Base):
    __tablename__ = "datasets"

    # Identity
    id: Mapped[str] = mapped_column(String, primary_key=True)
    rdf_type: Mapped[str] = mapped_column(String, nullable=True)
    
    # Content
    title: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    description: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    keywords: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    themes: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    
    # Responsibility
    publisher: Mapped[str] = mapped_column(String, nullable=True)
    contact_point: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    business_owner: Mapped[str] = mapped_column(String, nullable=True)

    # Metadata
    issued: Mapped[str] = mapped_column(String, nullable=True)
    modified: Mapped[str] = mapped_column(String, nullable=True)
    access_rights: Mapped[str] = mapped_column(String, nullable=True)

    # --- UNIFIED QUALITY METRICS ---
    schema_violations_count: Mapped[int] = mapped_column(Integer, default=0)
    schema_violation_messages: Mapped[List[str]] = mapped_column(JSON, default=list)
    input_quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Computed Scores
    swiss_score: Mapped[float] = mapped_column(Float, default=0.0, comment="Computed Deep Quality Score")
    findability_score: Mapped[int] = mapped_column(Integer, default=0)
    accessibility_score: Mapped[int] = mapped_column(Integer, default=0)
    interoperability_score: Mapped[int] = mapped_column(Integer, default=0)
    reusability_score: Mapped[int] = mapped_column(Integer, default=0)
    contextuality_score: Mapped[int] = mapped_column(Integer, default=0)

    # Computed Suggestions (NEW FIELD)
    # Stores list of dicts: [{"dimension": "Findability", "key": "crit_geo", "points": 20}]
    quality_suggestions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

    # Relationships
    distributions: Mapped[List["Distribution"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )
    violations: Mapped[List["QualityViolation"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )

class Distribution(Base):
    __tablename__ = "distributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    
    identifier: Mapped[str] = mapped_column(String, nullable=True)
    access_url: Mapped[str] = mapped_column(String, nullable=True)
    download_url: Mapped[str] = mapped_column(String, nullable=True)
    format_type: Mapped[str] = mapped_column(String, nullable=True)
    media_type: Mapped[str] = mapped_column(String, nullable=True)
    license_id: Mapped[str] = mapped_column(String, nullable=True)
    
    rights: Mapped[str] = mapped_column(String, nullable=True)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=True)


    access_url_status: Mapped[int] = mapped_column(Integer, nullable=True)
    download_url_status: Mapped[int] = mapped_column(Integer, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="distributions")

class QualityViolation(Base):
    __tablename__ = "quality_violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    dimension: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String, default="warning")

    dataset: Mapped["Dataset"] = relationship(back_populates="violations")