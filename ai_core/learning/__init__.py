"""
AI Learning System - Enables continuous improvement through pattern recognition

This package provides learning capabilities that allow the AI to:
- Store and retrieve successful patterns
- Learn from failures
- Improve planning accuracy over time
- Adapt successful patterns to new requests
"""

from .memory import LearningMemory, LearningPattern
from .trainer import PatternTrainer

__all__ = [
    'LearningMemory',
    'LearningPattern', 
    'PatternTrainer'
]
