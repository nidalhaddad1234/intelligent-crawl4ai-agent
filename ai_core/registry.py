"""
AI Tool Registry - Central registry for all AI-discoverable tools

This module implements the tool registration system that allows AI to discover
and understand available capabilities.
"""

import json
from typing import Dict, Any, Callable, List, Optional
from functools import wraps
import inspect
from dataclasses import dataclass, asdict


@dataclass
class ToolParameter:
    """Represents a parameter for an AI tool"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None


@dataclass
class ToolExample:
    """Example usage of a tool"""
    scenario: str
    parameters: Dict[str, Any]
    expected_outcome: Optional[str] = None


@dataclass
class ToolInfo:
    """Complete information about a tool"""
    name: str
    description: str
    category: str
    parameters: List[ToolParameter]
    examples: List[ToolExample]
    capabilities: List[str]
    performance: Dict[str, Any]
    returns: str


class ToolRegistry:
    """Central registry for all AI-discoverable tools"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._tool_instances: Dict[str, Callable] = {}
    
    def register(self, tool_info: ToolInfo, tool_callable: Callable):
        """Register a tool with its metadata and callable"""
        self.tools[tool_info.name] = asdict(tool_info)
        self._tool_instances[tool_info.name] = tool_callable
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool instance by name"""
        return self._tool_instances.get(name)
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool metadata by name"""
        return self.tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered tools"""
        return self.tools.copy()
    
    def get_tool_manifest(self) -> Dict[str, Any]:
        """Generate AI-readable tool documentation"""
        manifest = {
            "version": "1.0",
            "tools": []
        }
        
        for name, info in self.tools.items():
            tool_doc = {
                "name": name,
                "description": info["description"],
                "category": info["category"],
                "when_to_use": info["capabilities"],
                "parameters": [
                    {
                        "name": param["name"],
                        "type": param["type"],
                        "description": param["description"],
                        "required": param["required"],
                        "default": param["default"],
                        "choices": param["choices"]
                    }
                    for param in info["parameters"]
                ],
                "examples": info["examples"],
                "returns": info["returns"]
            }
            manifest["tools"].append(tool_doc)
        
        return manifest
    
    def search_tools_by_capability(self, capability: str) -> List[str]:
        """Find tools that match a specific capability"""
        matching_tools = []
        capability_lower = capability.lower()
        
        for name, info in self.tools.items():
            for cap in info["capabilities"]:
                if capability_lower in cap.lower():
                    matching_tools.append(name)
                    break
        
        return matching_tools
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """Get all tools in a specific category"""
        return [
            name for name, info in self.tools.items()
            if info["category"].lower() == category.lower()
        ]


# Global registry instance
tool_registry = ToolRegistry()


def ai_tool(
    name: str,
    description: str,
    category: str = "general",
    examples: Optional[List[ToolExample]] = None,
    capabilities: Optional[List[str]] = None,
    performance: Optional[Dict[str, Any]] = None
):
    """
    Decorator to register a function as an AI-discoverable tool
    
    Args:
        name: Unique name for the tool
        description: Human-readable description of what the tool does
        category: Category of the tool (e.g., "extraction", "analysis", "export")
        examples: List of example usages
        capabilities: List of capabilities this tool provides
        performance: Performance characteristics (speed, reliability, etc.)
    """
    def decorator(func: Callable) -> Callable:
        # Extract parameter information from function signature
        sig = inspect.signature(func)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            # Get type annotation
            param_type = "any"
            if param.annotation != inspect.Parameter.empty:
                param_type = str(param.annotation).replace("<class '", "").replace("'>", "")
            
            # Get default value
            has_default = param.default != inspect.Parameter.empty
            default_value = param.default if has_default else None
            
            # Extract parameter description from docstring
            param_desc = f"Parameter {param_name}"
            if func.__doc__:
                # Simple extraction - could be improved
                doc_lines = func.__doc__.split('\n')
                for line in doc_lines:
                    if param_name in line and ':' in line:
                        param_desc = line.split(':')[1].strip()
                        break
            
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=param_desc,
                required=not has_default,
                default=default_value
            ))
        
        # Extract return type
        return_type = "any"
        if sig.return_annotation != inspect.Parameter.empty:
            return_type = str(sig.return_annotation).replace("<class '", "").replace("'>", "")
        
        # Create tool info
        tool_info = ToolInfo(
            name=name,
            description=description or func.__doc__ or "No description provided",
            category=category,
            parameters=parameters,
            examples=examples or [],
            capabilities=capabilities or [],
            performance=performance or {"speed": "medium", "reliability": "high"},
            returns=return_type
        )
        
        # Register the tool
        tool_registry.register(tool_info, func)
        
        # Wrap the function to add metadata
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Add metadata to the wrapper
        wrapper.tool_name = name
        wrapper.tool_info = tool_info
        
        return wrapper
    
    return decorator


# Helper function to create tool examples
def create_example(scenario: str, **kwargs) -> ToolExample:
    """Helper to create tool examples"""
    return ToolExample(scenario=scenario, parameters=kwargs)
