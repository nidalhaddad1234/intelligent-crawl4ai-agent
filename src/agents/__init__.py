"""
Agents Module - Intelligent Crawl4AI Agent System

This module provides intelligent agents for:
- Website analysis and strategy selection
- High-volume execution and coordination  
- Intelligent extraction orchestration
- Performance monitoring and optimization

Each agent is designed to be:
- Autonomous and intelligent
- Service-oriented architecture
- Production-ready with monitoring
- Easily extensible and configurable
"""

from .intelligent_analyzer import IntelligentAnalyzer, WebsiteAnalysis, WebsiteType, ExtractionPurpose
from .strategy_selector import StrategySelector, StrategyRecommendation
from .high_volume_executor import HighVolumeExecutor, ExecutionResult, BatchJobConfig, JobStatus, JobPriority
from .orchestrator import ExtractionOrchestrator, OrchestrationConfig, WorkflowConfig, OrchestrationResult

__all__ = [
    'IntelligentAnalyzer',
    'StrategySelector', 
    'HighVolumeExecutor',
    'ExtractionOrchestrator',
    'WebsiteAnalysis',
    'WebsiteType',
    'ExtractionPurpose',
    'StrategyRecommendation',
    'ExecutionResult',
    'BatchJobConfig',
    'JobStatus',
    'JobPriority',
    'OrchestrationConfig',
    'WorkflowConfig',
    'OrchestrationResult'
]

# Agent system version
__version__ = "2.0.0"
