"""
Parameter Discovery System for Enhanced Tool Capabilities
Automatically infers missing parameters from context and previous results
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ParameterContext:
    """Context information for parameter inference"""
    previous_results: Dict[str, Any] = None
    user_request: str = ""
    execution_history: List[Dict] = None
    similar_patterns: List[Dict] = None
    
    def __post_init__(self):
        if self.previous_results is None:
            self.previous_results = {}
        if self.execution_history is None:
            self.execution_history = []
        if self.similar_patterns is None:
            self.similar_patterns = []


class ParameterInferenceEngine:
    """Intelligently infers missing parameters from context"""
    
    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry
        self.inference_rules = self._build_inference_rules()
        self.type_patterns = self._build_type_patterns()
        
    def _build_inference_rules(self) -> Dict[str, List[Dict]]:
        """Build rules for inferring parameters based on context"""
        return {
            'url': [
                {
                    'source': 'previous_results',
                    'patterns': ['url', 'website', 'link', 'href'],
                    'extractor': self._extract_url_from_results
                },
                {
                    'source': 'user_request',
                    'patterns': [r'https?://[^\s]+', r'www\.[^\s]+'],
                    'extractor': self._extract_url_from_text
                }
            ],
            'data': [
                {
                    'source': 'previous_results',
                    'patterns': ['data', 'results', 'output', 'extracted'],
                    'extractor': self._extract_data_from_results
                }
            ],
            'filename': [
                {
                    'source': 'user_request',
                    'patterns': [r'save as (\w+\.\w+)', r'export to (\w+\.\w+)'],
                    'extractor': self._extract_filename_from_text
                },
                {
                    'source': 'context',
                    'generator': self._generate_filename
                }
            ],
            'format': [
                {
                    'source': 'user_request',
                    'patterns': ['csv', 'json', 'excel', 'xml', 'html'],
                    'extractor': self._extract_format_from_text
                }
            ]
        }
    
    def _build_type_patterns(self) -> Dict[str, Dict]:
        """Build patterns for type inference"""
        return {
            'url': {
                'regex': r'^https?://.*',
                'validator': lambda x: x.startswith(('http://', 'https://'))
            },
            'email': {
                'regex': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'validator': lambda x: '@' in x and '.' in x
            },
            'number': {
                'regex': r'^-?\d+(\.\d+)?$',
                'validator': lambda x: x.replace('.', '').replace('-', '').isdigit()
            },
            'boolean': {
                'values': ['true', 'false', 'yes', 'no', '1', '0'],
                'validator': lambda x: str(x).lower() in ['true', 'false', 'yes', 'no', '1', '0']
            }
        }
    
    def infer_missing_params(
        self, 
        tool_name: str, 
        provided_params: Dict[str, Any], 
        context: ParameterContext,
        required_params: List[str]
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Infer missing parameters from context
        
        Returns:
            Tuple of (inferred_params, confidence_scores)
        """
        inferred_params = provided_params.copy()
        confidence_scores = {}
        
        # Get tool metadata if available
        tool_metadata = self._get_tool_metadata(tool_name)
        
        # Identify missing required parameters
        missing_params = [
            param for param in required_params 
            if param not in provided_params or provided_params[param] is None
        ]
        
        logger.info(f"Inferring {len(missing_params)} missing parameters for {tool_name}: {missing_params}")
        
        for param in missing_params:
            value, confidence = self._infer_parameter(
                param, 
                context, 
                tool_metadata
            )
            
            if value is not None:
                inferred_params[param] = value
                confidence_scores[param] = confidence
                logger.info(f"Inferred {param}={value} with confidence {confidence:.2f}")
        
        return inferred_params, confidence_scores
    
    def _infer_parameter(
        self, 
        param_name: str, 
        context: ParameterContext,
        tool_metadata: Dict
    ) -> Tuple[Any, float]:
        """Infer a single parameter value"""
        
        # Try inference rules first
        if param_name in self.inference_rules:
            for rule in self.inference_rules[param_name]:
                value, confidence = self._apply_inference_rule(
                    rule, 
                    param_name, 
                    context
                )
                if value is not None:
                    return value, confidence
        
        # Try to infer from similar patterns
        if context.similar_patterns:
            value, confidence = self._infer_from_patterns(
                param_name, 
                context.similar_patterns
            )
            if value is not None:
                return value, confidence
        
        # Try type-based inference
        value, confidence = self._infer_by_type(
            param_name, 
            context, 
            tool_metadata
        )
        if value is not None:
            return value, confidence
        
        # Generate default if possible
        value = self._generate_default(param_name, tool_metadata)
        if value is not None:
            return value, 0.5  # Low confidence for defaults
        
        return None, 0.0
    
    def _apply_inference_rule(
        self, 
        rule: Dict, 
        param_name: str, 
        context: ParameterContext
    ) -> Tuple[Any, float]:
        """Apply a specific inference rule"""
        
        if 'extractor' in rule:
            return rule['extractor'](param_name, context, rule.get('patterns', []))
        elif 'generator' in rule:
            return rule['generator'](param_name, context)
        
        return None, 0.0
    
    def _extract_url_from_results(
        self, 
        param_name: str, 
        context: ParameterContext, 
        patterns: List[str]
    ) -> Tuple[Optional[str], float]:
        """Extract URL from previous results"""
        
        for pattern in patterns:
            if pattern in context.previous_results:
                value = context.previous_results[pattern]
                if isinstance(value, str) and self._is_url(value):
                    return value, 0.9
                elif isinstance(value, list) and value and self._is_url(value[0]):
                    return value[0], 0.8
        
        return None, 0.0
    
    def _extract_url_from_text(
        self, 
        param_name: str, 
        context: ParameterContext, 
        patterns: List[str]
    ) -> Tuple[Optional[str], float]:
        """Extract URL from user request text"""
        
        for pattern in patterns:
            matches = re.findall(pattern, context.user_request)
            if matches:
                return matches[0], 0.85
        
        return None, 0.0
    
    def _extract_data_from_results(
        self, 
        param_name: str, 
        context: ParameterContext, 
        patterns: List[str]
    ) -> Tuple[Any, float]:
        """Extract data from previous results"""
        
        # Look for data in previous step results
        for pattern in patterns:
            if pattern in context.previous_results:
                return context.previous_results[pattern], 0.95
        
        # If previous results is the data itself
        if context.previous_results and not any(
            key in ['status', 'message', 'error'] 
            for key in context.previous_results
        ):
            return context.previous_results, 0.9
        
        return None, 0.0
    
    def _extract_filename_from_text(
        self, 
        param_name: str, 
        context: ParameterContext, 
        patterns: List[str]
    ) -> Tuple[Optional[str], float]:
        """Extract filename from user request"""
        
        for pattern in patterns:
            matches = re.search(pattern, context.user_request, re.IGNORECASE)
            if matches:
                return matches.group(1), 0.9
        
        return None, 0.0
    
    def _generate_filename(
        self, 
        param_name: str, 
        context: ParameterContext
    ) -> Tuple[str, float]:
        """Generate a filename based on context"""
        
        # Extract format from request
        format_match = re.search(
            r'\b(csv|json|excel|xml|html)\b', 
            context.user_request.lower()
        )
        
        if format_match:
            extension = format_match.group(1)
            if extension == 'excel':
                extension = 'xlsx'
        else:
            extension = 'json'  # Default
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Try to extract meaningful name from request
        if 'export' in context.user_request.lower():
            base_name = 'export'
        elif 'save' in context.user_request.lower():
            base_name = 'data'
        elif 'crawl' in context.user_request.lower():
            base_name = 'crawled_data'
        else:
            base_name = 'output'
        
        filename = f"{base_name}_{timestamp}.{extension}"
        return filename, 0.7
    
    def _extract_format_from_text(
        self, 
        param_name: str, 
        context: ParameterContext, 
        patterns: List[str]
    ) -> Tuple[Optional[str], float]:
        """Extract format from user request"""
        
        text_lower = context.user_request.lower()
        for format_type in patterns:
            if format_type in text_lower:
                # Map common terms to actual formats
                format_map = {
                    'excel': 'xlsx',
                    'csv': 'csv',
                    'json': 'json',
                    'xml': 'xml',
                    'html': 'html'
                }
                return format_map.get(format_type, format_type), 0.9
        
        return None, 0.0
    
    def _infer_from_patterns(
        self, 
        param_name: str, 
        similar_patterns: List[Dict]
    ) -> Tuple[Any, float]:
        """Infer parameter from similar successful patterns"""
        
        # Look for this parameter in similar patterns
        param_values = []
        for pattern in similar_patterns:
            if 'parameters' in pattern and param_name in pattern['parameters']:
                param_values.append(pattern['parameters'][param_name])
        
        if not param_values:
            return None, 0.0
        
        # If all values are the same, high confidence
        if len(set(str(v) for v in param_values)) == 1:
            return param_values[0], 0.85
        
        # Otherwise, return most common value
        from collections import Counter
        most_common = Counter(param_values).most_common(1)[0][0]
        confidence = Counter(param_values)[most_common] / len(param_values)
        
        return most_common, confidence * 0.8
    
    def _infer_by_type(
        self, 
        param_name: str, 
        context: ParameterContext,
        tool_metadata: Dict
    ) -> Tuple[Any, float]:
        """Infer parameter based on type patterns"""
        
        # Check if parameter type is defined in metadata
        if tool_metadata and 'parameters' in tool_metadata:
            param_info = tool_metadata['parameters'].get(param_name, {})
            param_type = param_info.get('type', 'string')
            
            # Try to extract value of the expected type from context
            if param_type == 'number':
                numbers = re.findall(r'\b\d+\b', context.user_request)
                if numbers:
                    return int(numbers[0]), 0.6
            
            elif param_type == 'boolean':
                bool_words = re.findall(
                    r'\b(yes|no|true|false|enable|disable)\b', 
                    context.user_request.lower()
                )
                if bool_words:
                    return bool_words[0] in ['yes', 'true', 'enable'], 0.7
        
        return None, 0.0
    
    def _generate_default(
        self, 
        param_name: str, 
        tool_metadata: Dict
    ) -> Optional[Any]:
        """Generate a default value for the parameter"""
        
        # Common defaults
        defaults = {
            'limit': 10,
            'offset': 0,
            'page': 1,
            'timeout': 30,
            'retries': 3,
            'format': 'json',
            'encoding': 'utf-8'
        }
        
        if param_name in defaults:
            return defaults[param_name]
        
        # Check tool metadata for defaults
        if tool_metadata and 'parameters' in tool_metadata:
            param_info = tool_metadata['parameters'].get(param_name, {})
            if 'default' in param_info:
                return param_info['default']
        
        return None
    
    def _get_tool_metadata(self, tool_name: str) -> Dict:
        """Get metadata for a tool from the registry"""
        if self.tool_registry:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                return tool.metadata
        return {}
    
    def _is_url(self, value: str) -> bool:
        """Check if a value is a valid URL"""
        if not isinstance(value, str):
            return False
        return bool(re.match(r'^https?://', value))
    
    def validate_inferred_params(
        self, 
        tool_name: str, 
        params: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate inferred parameters
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        tool_metadata = self._get_tool_metadata(tool_name)
        
        if not tool_metadata:
            return True, []  # Can't validate without metadata
        
        param_specs = tool_metadata.get('parameters', {})
        
        for param_name, param_value in params.items():
            if param_name in param_specs:
                spec = param_specs[param_name]
                
                # Type validation
                expected_type = spec.get('type', 'string')
                if not self._validate_type(param_value, expected_type):
                    errors.append(
                        f"Parameter '{param_name}' expected type '{expected_type}' "
                        f"but got '{type(param_value).__name__}'"
                    )
                
                # Required validation
                if spec.get('required', False) and param_value is None:
                    errors.append(f"Required parameter '{param_name}' is missing")
                
                # Pattern validation
                if 'pattern' in spec and isinstance(param_value, str):
                    if not re.match(spec['pattern'], param_value):
                        errors.append(
                            f"Parameter '{param_name}' does not match pattern '{spec['pattern']}'"
                        )
        
        return len(errors) == 0, errors
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type"""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        if expected_type in type_map:
            return isinstance(value, type_map[expected_type])
        
        return True  # Unknown type, assume valid


# Usage example:
if __name__ == "__main__":
    # Example context
    context = ParameterContext(
        previous_results={'url': 'https://example.com'},
        user_request="analyze the website and export to CSV",
        execution_history=[],
        similar_patterns=[]
    )
    
    # Example usage
    engine = ParameterInferenceEngine()
    
    # Infer missing parameters
    provided = {'data': None}  # Missing URL and filename
    required = ['url', 'data', 'filename']
    
    inferred, confidence = engine.infer_missing_params(
        'analyze_website',
        provided,
        context,
        required
    )
    
    print(f"Inferred parameters: {inferred}")
    print(f"Confidence scores: {confidence}")
