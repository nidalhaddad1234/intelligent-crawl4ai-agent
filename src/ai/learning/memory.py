"""
Learning Memory - Stores patterns and outcomes for AI learning

This module manages the storage and retrieval of learning patterns,
enabling the AI to improve over time by learning from past interactions.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import hashlib

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

from ..planner import ExecutionPlan, PlanStep, PlanStatus


logger = logging.getLogger(__name__)


@dataclass
class LearningPattern:
    """Represents a learned pattern from user interaction"""
    pattern_id: str
    request: str
    plan: Dict[str, Any]  # Serialized ExecutionPlan
    outcome: str  # "success" or "failure"
    confidence: float
    execution_time: float
    timestamp: datetime
    error_details: Optional[str] = None
    user_feedback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "pattern_id": self.pattern_id,
            "request": self.request,
            "plan": self.plan,
            "outcome": self.outcome,
            "confidence": self.confidence,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "error_details": self.error_details,
            "user_feedback": self.user_feedback
        }


class LearningMemory:
    """
    Manages storage and retrieval of learning patterns using ChromaDB
    """
    
    def __init__(self, 
                 chromadb_host: str = "localhost",
                 chromadb_port: int = 8000,
                 collection_name: str = "ai_learning_patterns"):
        """
        Initialize Learning Memory
        
        Args:
            chromadb_host: ChromaDB host
            chromadb_port: ChromaDB port
            collection_name: Name of the collection to use
        """
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        if chromadb:
            try:
                # Initialize ChromaDB client
                self.client = chromadb.HttpClient(
                    host=chromadb_host,
                    port=chromadb_port,
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # Get or create collection
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "AI learning patterns from user interactions"}
                )
                
                logger.info(f"Initialized ChromaDB collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.client = None
                self.collection = None
        else:
            logger.warning("ChromaDB not available - learning memory disabled")
    
    async def store_interaction(self, 
                               request: str, 
                               plan: ExecutionPlan, 
                               outcome: str,
                               execution_time: float,
                               error_details: Optional[str] = None) -> str:
        """
        Store a learning example
        
        Args:
            request: User's original request
            plan: The execution plan that was created
            outcome: "success" or "failure"
            execution_time: Time taken to execute (seconds)
            error_details: Error details if failed
            
        Returns:
            Pattern ID
        """
        if not self.collection:
            logger.warning("ChromaDB not available - cannot store interaction")
            return ""
        
        # Create pattern ID
        pattern_id = self._generate_pattern_id(request, plan.plan_id)
        
        # Serialize plan
        plan_dict = {
            "plan_id": plan.plan_id,
            "description": plan.description,
            "confidence": plan.confidence,
            "steps": [
                {
                    "step_id": step.step_id,
                    "tool": step.tool,
                    "parameters": step.parameters,
                    "description": step.description
                }
                for step in plan.steps
            ]
        }
        
        # Create learning pattern
        pattern = LearningPattern(
            pattern_id=pattern_id,
            request=request,
            plan=plan_dict,
            outcome=outcome,
            confidence=plan.confidence,
            execution_time=execution_time,
            timestamp=datetime.now(timezone.utc),
            error_details=error_details
        )
        
        # Store in ChromaDB
        try:
            self.collection.add(
                documents=[request],  # Use request as document for embedding
                metadatas=[pattern.to_dict()],
                ids=[pattern_id]
            )
            
            logger.info(f"Stored learning pattern: {pattern_id} (outcome: {outcome})")
            return pattern_id
            
        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
            return ""
    
    async def find_similar_requests(self, 
                                   request: str, 
                                   k: int = 5,
                                   min_confidence: float = 0.7) -> List[LearningPattern]:
        """
        Find similar past requests and their successful plans
        
        Args:
            request: The user request to match
            k: Number of similar patterns to return
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of similar learning patterns
        """
        if not self.collection:
            return []
        
        try:
            # Query ChromaDB for similar documents
            results = self.collection.query(
                query_texts=[request],
                n_results=k,
                where={"outcome": "success", "confidence": {"$gte": min_confidence}}
            )
            
            # Parse results into LearningPattern objects
            patterns = []
            for i, metadata in enumerate(results.get("metadatas", [[]])[0]):
                if metadata:
                    pattern = LearningPattern(
                        pattern_id=metadata["pattern_id"],
                        request=metadata["request"],
                        plan=metadata["plan"],
                        outcome=metadata["outcome"],
                        confidence=metadata["confidence"],
                        execution_time=metadata["execution_time"],
                        timestamp=datetime.fromisoformat(metadata["timestamp"]),
                        error_details=metadata.get("error_details"),
                        user_feedback=metadata.get("user_feedback")
                    )
                    patterns.append(pattern)
            
            logger.info(f"Found {len(patterns)} similar patterns for: {request[:50]}...")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to find similar patterns: {e}")
            return []
    
    async def get_success_rate(self, tool: Optional[str] = None) -> float:
        """
        Get success rate for a specific tool or overall
        
        Args:
            tool: Tool name to filter by (None for overall)
            
        Returns:
            Success rate (0.0 to 1.0)
        """
        if not self.collection:
            return 0.0
        
        try:
            # Get all patterns
            all_results = self.collection.get()
            
            if not all_results["metadatas"]:
                return 0.0
            
            # Filter by tool if specified
            relevant_patterns = []
            for metadata in all_results["metadatas"]:
                if tool:
                    # Check if tool is used in any step
                    plan = metadata.get("plan", {})
                    steps = plan.get("steps", [])
                    if any(step.get("tool") == tool for step in steps):
                        relevant_patterns.append(metadata)
                else:
                    relevant_patterns.append(metadata)
            
            if not relevant_patterns:
                return 0.0
            
            # Calculate success rate
            successes = sum(1 for p in relevant_patterns if p.get("outcome") == "success")
            return successes / len(relevant_patterns)
            
        except Exception as e:
            logger.error(f"Failed to calculate success rate: {e}")
            return 0.0
    
    async def get_tool_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for each tool
        
        Returns:
            Dictionary mapping tool names to performance metrics
        """
        if not self.collection:
            return {}
        
        try:
            # Get all patterns
            all_results = self.collection.get()
            
            # Aggregate by tool
            tool_metrics = {}
            
            for metadata in all_results.get("metadatas", []):
                plan = metadata.get("plan", {})
                steps = plan.get("steps", [])
                outcome = metadata.get("outcome", "failure")
                execution_time = metadata.get("execution_time", 0)
                
                for step in steps:
                    tool_name = step.get("tool")
                    if tool_name:
                        if tool_name not in tool_metrics:
                            tool_metrics[tool_name] = {
                                "total_uses": 0,
                                "successes": 0,
                                "failures": 0,
                                "total_time": 0,
                                "avg_time": 0,
                                "success_rate": 0
                            }
                        
                        metrics = tool_metrics[tool_name]
                        metrics["total_uses"] += 1
                        
                        if outcome == "success":
                            metrics["successes"] += 1
                        else:
                            metrics["failures"] += 1
                        
                        metrics["total_time"] += execution_time
                        metrics["avg_time"] = metrics["total_time"] / metrics["total_uses"]
                        metrics["success_rate"] = metrics["successes"] / metrics["total_uses"]
            
            return tool_metrics
            
        except Exception as e:
            logger.error(f"Failed to get tool performance: {e}")
            return {}
    
    async def get_failure_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze failed patterns to identify common issues
        
        Args:
            limit: Maximum number of failure patterns to return
            
        Returns:
            List of failure patterns with analysis
        """
        if not self.collection:
            return []
        
        try:
            # Query for failures
            results = self.collection.query(
                query_texts=[""],  # Empty query to get all
                n_results=limit,
                where={"outcome": "failure"}
            )
            
            # Analyze failure patterns
            failure_analysis = []
            
            for metadata in results.get("metadatas", [[]])[0]:
                if metadata:
                    analysis = {
                        "request": metadata.get("request"),
                        "error_details": metadata.get("error_details"),
                        "failed_tools": [],
                        "timestamp": metadata.get("timestamp")
                    }
                    
                    # Extract failed tools
                    plan = metadata.get("plan", {})
                    for step in plan.get("steps", []):
                        analysis["failed_tools"].append(step.get("tool"))
                    
                    failure_analysis.append(analysis)
            
            return failure_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze failure patterns: {e}")
            return []
    
    async def update_user_feedback(self, pattern_id: str, feedback: str) -> bool:
        """
        Update user feedback for a pattern
        
        Args:
            pattern_id: Pattern ID to update
            feedback: User feedback
            
        Returns:
            Success status
        """
        if not self.collection:
            return False
        
        try:
            # Get existing pattern
            result = self.collection.get(ids=[pattern_id])
            
            if result["metadatas"]:
                metadata = result["metadatas"][0]
                metadata["user_feedback"] = feedback
                
                # Update in collection
                self.collection.update(
                    ids=[pattern_id],
                    metadatas=[metadata]
                )
                
                logger.info(f"Updated feedback for pattern: {pattern_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update feedback: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about learning patterns
        
        Returns:
            Dictionary with statistics
        """
        if not self.collection:
            return {
                "total_patterns": 0,
                "success_rate": 0,
                "status": "ChromaDB not available"
            }
        
        try:
            # Get all patterns
            all_results = self.collection.get()
            total = len(all_results.get("metadatas", []))
            
            if total == 0:
                return {
                    "total_patterns": 0,
                    "success_rate": 0,
                    "status": "No patterns stored yet"
                }
            
            # Calculate statistics
            successes = sum(1 for m in all_results["metadatas"] if m.get("outcome") == "success")
            
            # Get tool performance
            tool_performance = await self.get_tool_performance()
            
            # Get recent patterns
            recent_patterns = sorted(
                all_results["metadatas"],
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )[:5]
            
            return {
                "total_patterns": total,
                "successful_patterns": successes,
                "failed_patterns": total - successes,
                "success_rate": successes / total,
                "tool_performance": tool_performance,
                "recent_requests": [p.get("request", "") for p in recent_patterns],
                "status": "operational"
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "total_patterns": 0,
                "success_rate": 0,
                "status": f"Error: {str(e)}"
            }
    
    def _generate_pattern_id(self, request: str, plan_id: str) -> str:
        """Generate unique pattern ID"""
        content = f"{request}:{plan_id}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
