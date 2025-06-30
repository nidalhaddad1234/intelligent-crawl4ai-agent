"""
Core data models for Feature 8: Schema Detection
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class SchemaType(Enum):
    """Types of detected schemas"""
    TABLE = "table"
    LIST = "list"
    FORM = "form"
    ARTICLE = "article"
    PRODUCT = "product"
    CONTACT = "contact"
    NAVIGATION = "navigation"
    PRICING = "pricing"
    REVIEW = "review"
    SEARCH_RESULTS = "search_results"
    DIRECTORY = "directory"
    CALENDAR = "calendar"
    MEDIA_GALLERY = "media_gallery"

class PatternType(Enum):
    """Types of content patterns"""
    REPEATING_ELEMENTS = "repeating_elements"
    PRODUCT_LISTING = "product_listing"
    ARTICLE_CONTENT = "article_content"
    CONTACT_INFO = "contact_info"
    PRICING_DATA = "pricing_data"
    NAVIGATION_MENU = "navigation_menu"
    FORM_FIELDS = "form_fields"
    SOCIAL_LINKS = "social_links"
    BREADCRUMB = "breadcrumb"
    PAGINATION = "pagination"

class ContentType(Enum):
    """Content type classifications"""
    ECOMMERCE_PRODUCT = "ecommerce_product"
    ECOMMERCE_LISTING = "ecommerce_listing"
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    CONTACT_PAGE = "contact_page"
    PRICING_PAGE = "pricing_page"
    SEARCH_RESULTS = "search_results"
    DIRECTORY_LISTING = "directory_listing"
    COMPANY_ABOUT = "company_about"
    PRODUCT_CATALOG = "product_catalog"
    EVENT_LISTING = "event_listing"
    DOCUMENTATION = "documentation"

class DataType(Enum):
    """Data type classifications"""
    TEXT = "text"
    PRICE = "price"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    IMAGE = "image"
    RATING = "rating"
    NUMBER = "number"
    BOOLEAN = "boolean"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    ADDRESS = "address"
    NAME = "name"

@dataclass
class SchemaElement:
    """Individual element within a detected schema"""
    tag_name: str
    css_classes: List[str] = field(default_factory=list)
    element_id: Optional[str] = None
    text_content: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    xpath: str = ""
    css_selector: str = ""
    data_type: DataType = DataType.TEXT
    confidence: float = 0.0
    parent_context: Optional[str] = None

@dataclass
class DetectedSchema:
    """A detected content schema on the webpage"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_type: SchemaType
    confidence: float
    elements: List[SchemaElement] = field(default_factory=list)
    selector_path: str = ""
    xpath_path: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    location: Dict[str, int] = field(default_factory=dict)  # x, y, width, height
    sample_data: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContentPattern:
    """A detected repeating content pattern"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: PatternType
    confidence: float
    sample_elements: List[SchemaElement] = field(default_factory=list)
    extraction_hint: str = ""
    css_selector: str = ""
    xpath: str = ""
    repeat_count: int = 0
    consistency_score: float = 0.0
    data_quality: float = 0.0

@dataclass
class ExtractionRule:
    """Auto-generated extraction rule"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_selector: str
    data_type: DataType
    extraction_method: str  # text(), @href, @src, etc.
    validation_rules: List[str] = field(default_factory=list)
    confidence: float = 0.0
    fallback_selectors: List[str] = field(default_factory=list)
    transformation_rules: List[str] = field(default_factory=list)

@dataclass
class PageAnalysis:
    """Complete analysis of a webpage's content structure"""
    url: str
    content_type: ContentType
    detected_schemas: List[DetectedSchema] = field(default_factory=list)
    content_patterns: List[ContentPattern] = field(default_factory=list)
    extraction_rules: List[ExtractionRule] = field(default_factory=list)
    structured_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
