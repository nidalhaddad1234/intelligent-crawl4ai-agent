"""
Web UI Core Models
All data models, enums, and base classes for the web UI
"""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field


# ==================== ENUMS ====================

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(Enum):
    SITE_ANALYSIS = "site_analysis"
    COMPETITOR_DISCOVERY = "competitor_discovery"
    DATA_EXTRACTION = "data_extraction"
    MONITORING_SETUP = "monitoring_setup"
    COMPARISON_PREP = "comparison_prep"
    EXPORT_GENERATION = "export_generation"


class ProgressEventType(Enum):
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    MILESTONE_REACHED = "milestone_reached"
    ESTIMATE_UPDATED = "estimate_updated"
    INSIGHT_DISCOVERED = "insight_discovered"
    WARNING_ISSUED = "warning_issued"


class ProgressInsight(Enum):
    ANTI_BOT_DETECTED = "anti_bot_detected"
    RATE_LIMIT_ENCOUNTERED = "rate_limit_encountered"
    DATA_PATTERN_FOUND = "data_pattern_found"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"
    QUALITY_IMPROVEMENT = "quality_improvement"
    PERFORMANCE_GAIN = "performance_gain"


class StreamEventType(Enum):
    STREAM_STARTED = "stream_started"
    DATA_CHUNK = "data_chunk"
    LIVE_UPDATE = "live_update"
    STREAM_COMPLETED = "stream_completed"
    STREAM_ERROR = "stream_error"
    RATE_LIMIT_HIT = "rate_limit_hit"
    CONNECTION_RESTORED = "connection_restored"
    QUALITY_ALERT = "quality_alert"


class DataStreamType(Enum):
    EXTRACTION_RESULTS = "extraction_results"
    MONITORING_ALERTS = "monitoring_alerts"
    COMPARISON_UPDATES = "comparison_updates"
    PRICE_FEEDS = "price_feeds"
    CONTENT_CHANGES = "content_changes"
    PERFORMANCE_METRICS = "performance_metrics"
    ERROR_LOGS = "error_logs"


class StreamPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ToolSelection(Enum):
    BEST_FIT = "best_fit"
    MULTI_TOOL = "multi_tool"
    FALLBACK_CHAIN = "fallback_chain"
    PARALLEL_EXECUTION = "parallel_execution"


class ToolCategory(Enum):
    WEB_CRAWLER = "web_crawler"
    DATA_EXTRACTOR = "data_extractor"
    CONTENT_ANALYZER = "content_analyzer"
    EXPORT_HANDLER = "export_handler"
    MONITORING_AGENT = "monitoring_agent"
    COMPARISON_ENGINE = "comparison_engine"


# ==================== JOB MODELS ====================

@dataclass
class BackgroundJob:
    """Individual background job with progress tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: JobType = JobType.SITE_ANALYSIS
    status: JobStatus = JobStatus.PENDING
    description: str = ""
    target_url: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # seconds

    def start(self):
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def complete(self, result: Dict[str, Any]):
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.result = result
        self.progress = 100.0

    def fail(self, error: str):
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error = error

    def update_progress(self, progress: float, description: str = None):
        self.progress = min(100.0, max(0.0, progress))
        if description:
            self.description = description


@dataclass
class JobPlan:
    """Plan for executing jobs in parallel"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    immediate_jobs: List[BackgroundJob] = field(default_factory=list)
    clarification_dependent_jobs: List[BackgroundJob] = field(default_factory=list)
    total_estimated_time: int = 0  # seconds
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== PATTERN & LEARNING MODELS ====================

@dataclass
class SuccessfulPattern:
    """Stores a successful interaction pattern for learning"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_text: str = ""
    intent_analysis: Optional[Dict[str, Any]] = None
    execution_config: Dict[str, Any] = field(default_factory=dict)
    success_metrics: Dict[str, Any] = field(default_factory=dict)
    user_feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reuse_count: int = 0
    success_score: float = 0.0
    context_tags: List[str] = field(default_factory=list)


# ==================== PROGRESS & TRACKING MODELS ====================

@dataclass
class ProgressEvent:
    """Enhanced progress event with rich metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ProgressEventType = ProgressEventType.TASK_PROGRESS
    task_id: str = ""
    task_name: str = ""
    progress: float = 0.0
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Enhanced metadata
    estimated_completion: Optional[datetime] = None
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0

    # Insights and discoveries
    insight: Optional[ProgressInsight] = None
    insight_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskMilestone:
    """Represents a significant milestone in task execution"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    expected_time: float = 0.0
    actual_time: Optional[float] = None
    completed: bool = False
    insights: List[str] = field(default_factory=list)
    data_discovered: Dict[str, Any] = field(default_factory=dict)


# ==================== STREAMING MODELS ====================

@dataclass
class DataChunk:
    """Individual chunk of streaming data"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stream_id: str = ""
    chunk_index: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_type: str = "generic"
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamEvent:
    """Real-time streaming event with rich context"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: StreamEventType = StreamEventType.DATA_CHUNK
    stream_id: str = ""
    stream_name: str = ""
    priority: StreamPriority = StreamPriority.NORMAL
    data: Union[DataChunk, Dict[str, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Stream metadata
    source_url: Optional[str] = None
    data_count: int = 0
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    performance_info: Dict[str, Any] = field(default_factory=dict)

    # User context
    session_id: str = ""
    alert_level: str = "info"  # info, warning, error, success
    action_required: bool = False


@dataclass
class StreamConfiguration:
    """Configuration for data streams"""
    stream_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    stream_type: DataStreamType = DataStreamType.EXTRACTION_RESULTS
    target_urls: List[str] = field(default_factory=list)

    # Streaming parameters
    update_interval: float = 5.0  # seconds
    max_chunk_size: int = 100
    buffer_size: int = 1000
    auto_reconnect: bool = True

    # Quality controls
    quality_threshold: float = 0.7
    error_tolerance: int = 3
    rate_limit_strategy: str = "adaptive"  # adaptive, fixed, exponential

    # Filtering and processing
    data_filters: Dict[str, Any] = field(default_factory=dict)


# ==================== TOOL MODELS ====================

@dataclass
class ToolCapability:
    """Represents a specific capability of a tool"""
    name: str
    description: str
    performance_score: float = 0.8
    reliability_score: float = 0.9
    supported_scenarios: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolConfiguration:
    """Dynamic configuration for a selected tool"""
    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3
    priority: int = 5
    fallback_tools: List[str] = field(default_factory=list)
    performance_hints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolSelectionResult:
    """Result of autonomous tool selection"""
    primary_tool: str
    configuration: ToolConfiguration
    alternative_tools: List[str] = field(default_factory=list)
    strategy: ToolSelection = ToolSelection.BEST_FIT
    confidence: float = 0.8
    reasoning: str = ""
    estimated_performance: Dict[str, float] = field(default_factory=dict)


# ==================== API MODELS (Pydantic) ====================

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PureChatRequest(BaseModel):
    """Pure natural language request - no structured inputs"""
    message: str = Field(..., description="Natural language message/query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    success: bool = Field(True, description="Whether the request was successful")
    intent_analysis: Optional[Dict[str, Any]] = Field(None, description="AI intent analysis")


class IntentAnalysis(BaseModel):
    """AI analysis of user intent"""
    primary_intent: str = Field(..., description="Primary identified intent")
    confidence: float = Field(..., description="Confidence score 0-1")
    targets: List[str] = Field(default_factory=list, description="Identified targets/URLs")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Inferred parameters")
    needs_clarification: bool = Field(False, description="Whether clarification is needed")
    reasoning: str = Field("", description="AI reasoning for this interpretation")
