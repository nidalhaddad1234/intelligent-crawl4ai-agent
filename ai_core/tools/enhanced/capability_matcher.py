"""
Capability Matcher for Enhanced Tool Capabilities
Matches user requests to optimal tool combinations based on capabilities
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


class DataType(Enum):
    """Supported data types"""
    TEXT = "text"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    BINARY = "binary"
    URL = "url"
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"


class ProcessingCapability(Enum):
    """Processing capabilities"""
    CRAWL = "crawl"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    TRANSFORM = "transform"
    AGGREGATE = "aggregate"
    COMPARE = "compare"
    EXPORT = "export"
    STORE = "store"
    QUERY = "query"
    DETECT = "detect"


@dataclass
class ToolCapability:
    """Defines what a tool can do"""
    tool_name: str
    description: str
    input_types: Set[DataType] = field(default_factory=set)
    output_types: Set[DataType] = field(default_factory=set)
    processing_capabilities: Set[ProcessingCapability] = field(default_factory=set)
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    performance_score: float = 1.0  # 0-1, based on historical performance
    reliability_score: float = 1.0  # 0-1, based on success rate
    
    def matches_input(self, data_type: DataType) -> bool:
        """Check if tool can handle input type"""
        return data_type in self.input_types or DataType.UNSTRUCTURED in self.input_types
    
    def produces_output(self, data_type: DataType) -> bool:
        """Check if tool produces desired output type"""
        return data_type in self.output_types
    
    def has_capability(self, capability: ProcessingCapability) -> bool:
        """Check if tool has a specific capability"""
        return capability in self.processing_capabilities


class CapabilityMatcher:
    """Matches user requests to optimal tool combinations"""
    
    def __init__(self, tool_registry=None, performance_profiler=None):
        self.tool_registry = tool_registry
        self.performance_profiler = performance_profiler
        self.capability_index = {}
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.capability_vectors = None
        self.stop_words = set(stopwords.words('english'))
        
        # Build initial capability index
        self._build_capability_index()
    
    def _build_capability_index(self):
        """Build the capability index from available tools"""
        # Define capabilities for known tools
        # In a real system, this would be loaded from tool metadata
        self.capability_index = {
            'crawl_web': ToolCapability(
                tool_name='crawl_web',
                description='Crawl and extract content from a single web page',
                input_types={DataType.URL},
                output_types={DataType.HTML, DataType.TEXT, DataType.STRUCTURED},
                processing_capabilities={ProcessingCapability.CRAWL, ProcessingCapability.EXTRACT},
                keywords=['crawl', 'scrape', 'extract', 'web', 'website', 'page', 'url'],
                examples=['crawl this website', 'extract data from URL', 'scrape web page']
            ),
            
            'crawl_multiple': ToolCapability(
                tool_name='crawl_multiple',
                description='Crawl multiple web pages in parallel',
                input_types={DataType.URL},
                output_types={DataType.STRUCTURED, DataType.JSON},
                processing_capabilities={ProcessingCapability.CRAWL, ProcessingCapability.AGGREGATE},
                keywords=['crawl', 'multiple', 'websites', 'pages', 'bulk', 'batch'],
                examples=['crawl multiple websites', 'scrape these URLs', 'batch crawling']
            ),
            
            'analyze_content': ToolCapability(
                tool_name='analyze_content',
                description='Analyze content for patterns, entities, and insights',
                input_types={DataType.TEXT, DataType.STRUCTURED, DataType.JSON},
                output_types={DataType.STRUCTURED, DataType.JSON},
                processing_capabilities={ProcessingCapability.ANALYZE, ProcessingCapability.DETECT},
                keywords=['analyze', 'analysis', 'insights', 'patterns', 'entities', 'sentiment'],
                examples=['analyze this data', 'find patterns', 'extract insights']
            ),
            
            'detect_patterns': ToolCapability(
                tool_name='detect_patterns',
                description='Detect patterns, anomalies, and trends in data',
                input_types={DataType.STRUCTURED, DataType.JSON, DataType.CSV},
                output_types={DataType.STRUCTURED, DataType.JSON},
                processing_capabilities={ProcessingCapability.DETECT, ProcessingCapability.ANALYZE},
                keywords=['patterns', 'anomalies', 'trends', 'detect', 'find', 'discover'],
                examples=['find patterns in data', 'detect anomalies', 'identify trends']
            ),
            
            'compare_datasets': ToolCapability(
                tool_name='compare_datasets',
                description='Compare two or more datasets',
                input_types={DataType.STRUCTURED, DataType.JSON, DataType.CSV},
                output_types={DataType.STRUCTURED, DataType.JSON},
                processing_capabilities={ProcessingCapability.COMPARE, ProcessingCapability.ANALYZE},
                keywords=['compare', 'diff', 'difference', 'versus', 'comparison', 'match'],
                examples=['compare two datasets', 'find differences', 'match data']
            ),
            
            'store_data': ToolCapability(
                tool_name='store_data',
                description='Store data in database with automatic schema detection',
                input_types={DataType.STRUCTURED, DataType.JSON, DataType.CSV},
                output_types={DataType.STRUCTURED},
                processing_capabilities={ProcessingCapability.STORE, ProcessingCapability.TRANSFORM},
                keywords=['store', 'save', 'database', 'persist', 'insert', 'update'],
                examples=['store in database', 'save data', 'persist results']
            ),
            
            'query_data': ToolCapability(
                tool_name='query_data',
                description='Query data from database with filtering and search',
                input_types={DataType.TEXT, DataType.STRUCTURED},
                output_types={DataType.STRUCTURED, DataType.JSON},
                processing_capabilities={ProcessingCapability.QUERY, ProcessingCapability.EXTRACT},
                keywords=['query', 'search', 'find', 'filter', 'retrieve', 'get'],
                examples=['query database', 'search for data', 'retrieve records']
            ),
            
            'aggregate_data': ToolCapability(
                tool_name='aggregate_data',
                description='Aggregate data with grouping and calculations',
                input_types={DataType.STRUCTURED, DataType.JSON, DataType.CSV},
                output_types={DataType.STRUCTURED, DataType.JSON},
                processing_capabilities={ProcessingCapability.AGGREGATE, ProcessingCapability.ANALYZE},
                keywords=['aggregate', 'group', 'sum', 'average', 'count', 'statistics'],
                examples=['aggregate by category', 'calculate totals', 'group data']
            ),
            
            'export_csv': ToolCapability(
                tool_name='export_csv',
                description='Export data to CSV format',
                input_types={DataType.STRUCTURED, DataType.JSON},
                output_types={DataType.CSV},
                processing_capabilities={ProcessingCapability.EXPORT, ProcessingCapability.TRANSFORM},
                keywords=['export', 'csv', 'download', 'save'],
                examples=['export to CSV', 'save as CSV', 'download CSV']
            ),
            
            'export_json': ToolCapability(
                tool_name='export_json',
                description='Export data to JSON format',
                input_types={DataType.STRUCTURED},
                output_types={DataType.JSON},
                processing_capabilities={ProcessingCapability.EXPORT, ProcessingCapability.TRANSFORM},
                keywords=['export', 'json', 'download', 'save'],
                examples=['export to JSON', 'save as JSON', 'download JSON']
            ),
            
            'export_excel': ToolCapability(
                tool_name='export_excel',
                description='Export data to Excel format with formatting',
                input_types={DataType.STRUCTURED, DataType.JSON, DataType.CSV},
                output_types={DataType.BINARY},
                processing_capabilities={ProcessingCapability.EXPORT, ProcessingCapability.TRANSFORM},
                keywords=['export', 'excel', 'xlsx', 'spreadsheet', 'download'],
                examples=['export to Excel', 'create spreadsheet', 'save as Excel']
            )
        }
        
        # Update with performance scores if available
        if self.performance_profiler:
            for tool_name, capability in self.capability_index.items():
                profile = self.performance_profiler.get_profile(tool_name)
                if profile:
                    capability.reliability_score = profile.success_rate
                    # Normalize execution time to performance score (faster = higher score)
                    if profile.avg_execution_time > 0:
                        capability.performance_score = min(1.0, 5.0 / profile.avg_execution_time)
        
        # Build text corpus for similarity matching
        self._build_text_vectors()
    
    def _build_text_vectors(self):
        """Build TF-IDF vectors for capability matching"""
        corpus = []
        tool_names = []
        
        for tool_name, capability in self.capability_index.items():
            # Combine description, keywords, and examples
            text = f"{capability.description} {' '.join(capability.keywords)} {' '.join(capability.examples)}"
            corpus.append(text)
            tool_names.append(tool_name)
        
        if corpus:
            self.capability_vectors = self.vectorizer.fit_transform(corpus)
            self.tool_names_ordered = tool_names
    
    def match_request_to_tools(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Match user request to optimal tools
        
        Returns:
            List of tool matches with scores and reasoning
        """
        # Extract requirements from request
        requirements = self._extract_requirements(request)
        
        # Get candidate tools
        candidates = []
        
        # 1. Text similarity matching
        if self.capability_vectors is not None:
            text_matches = self._match_by_text_similarity(request, top_k * 2)
            candidates.extend(text_matches)
        
        # 2. Capability matching
        capability_matches = self._match_by_capabilities(requirements)
        candidates.extend(capability_matches)
        
        # 3. Keyword matching
        keyword_matches = self._match_by_keywords(request)
        candidates.extend(keyword_matches)
        
        # Deduplicate and score
        tool_scores = {}
        tool_reasons = {}
        
        for candidate in candidates:
            tool_name = candidate['tool_name']
            score = candidate['score']
            reason = candidate['reason']
            
            if tool_name in tool_scores:
                tool_scores[tool_name] = max(tool_scores[tool_name], score)
                tool_reasons[tool_name].append(reason)
            else:
                tool_scores[tool_name] = score
                tool_reasons[tool_name] = [reason]
        
        # Apply performance and reliability weights
        final_scores = {}
        for tool_name, base_score in tool_scores.items():
            capability = self.capability_index.get(tool_name)
            if capability:
                # Weight: 60% match score, 20% performance, 20% reliability
                final_scores[tool_name] = (
                    0.6 * base_score +
                    0.2 * capability.performance_score +
                    0.2 * capability.reliability_score
                )
            else:
                final_scores[tool_name] = base_score
        
        # Sort by score
        sorted_tools = sorted(
            final_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Format results
        results = []
        for tool_name, score in sorted_tools[:top_k]:
            capability = self.capability_index.get(tool_name, None)
            results.append({
                'tool_name': tool_name,
                'score': score,
                'reasons': tool_reasons[tool_name],
                'description': capability.description if capability else 'Unknown tool',
                'capabilities': [c.value for c in capability.processing_capabilities] if capability else [],
                'performance_score': capability.performance_score if capability else 0,
                'reliability_score': capability.reliability_score if capability else 0
            })
        
        return results
    
    def _extract_requirements(self, request: str) -> Dict[str, Any]:
        """Extract requirements from user request"""
        requirements = {
            'capabilities': set(),
            'input_types': set(),
            'output_types': set(),
            'keywords': []
        }
        
        request_lower = request.lower()
        
        # Extract capabilities
        capability_keywords = {
            ProcessingCapability.CRAWL: ['crawl', 'scrape', 'fetch'],
            ProcessingCapability.EXTRACT: ['extract', 'get', 'pull'],
            ProcessingCapability.ANALYZE: ['analyze', 'analysis', 'insights'],
            ProcessingCapability.COMPARE: ['compare', 'diff', 'versus'],
            ProcessingCapability.AGGREGATE: ['aggregate', 'combine', 'merge'],
            ProcessingCapability.EXPORT: ['export', 'download', 'save as'],
            ProcessingCapability.STORE: ['store', 'save', 'persist'],
            ProcessingCapability.QUERY: ['query', 'search', 'find'],
            ProcessingCapability.DETECT: ['detect', 'identify', 'discover']
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                requirements['capabilities'].add(capability)
        
        # Extract data types
        if re.search(r'https?://', request) or 'website' in request_lower or 'url' in request_lower:
            requirements['input_types'].add(DataType.URL)
        
        format_keywords = {
            DataType.CSV: ['csv', 'comma-separated'],
            DataType.JSON: ['json'],
            DataType.EXCEL: ['excel', 'xlsx', 'spreadsheet'],
            DataType.XML: ['xml'],
            DataType.HTML: ['html', 'web page']
        }
        
        for data_type, keywords in format_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                requirements['output_types'].add(data_type)
        
        # Extract keywords
        tokens = word_tokenize(request_lower)
        requirements['keywords'] = [
            token for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        return requirements
    
    def _match_by_text_similarity(
        self,
        request: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Match tools using text similarity"""
        if self.capability_vectors is None:
            return []
        
        # Vectorize request
        request_vector = self.vectorizer.transform([request])
        
        # Calculate similarities
        similarities = cosine_similarity(request_vector, self.capability_vectors)[0]
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        matches = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Threshold
                matches.append({
                    'tool_name': self.tool_names_ordered[idx],
                    'score': float(similarities[idx]),
                    'reason': f'Text similarity: {similarities[idx]:.2f}'
                })
        
        return matches
    
    def _match_by_capabilities(
        self,
        requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Match tools based on required capabilities"""
        matches = []
        
        for tool_name, capability in self.capability_index.items():
            score = 0
            reasons = []
            
            # Check capability matches
            cap_matches = requirements['capabilities'].intersection(capability.processing_capabilities)
            if cap_matches:
                score += len(cap_matches) / len(requirements['capabilities']) if requirements['capabilities'] else 0
                reasons.append(f"Capabilities: {', '.join(c.value for c in cap_matches)}")
            
            # Check input type compatibility
            if requirements['input_types']:
                input_matches = requirements['input_types'].intersection(capability.input_types)
                if input_matches:
                    score += 0.3
                    reasons.append(f"Input types: {', '.join(t.value for t in input_matches)}")
            
            # Check output type compatibility
            if requirements['output_types']:
                output_matches = requirements['output_types'].intersection(capability.output_types)
                if output_matches:
                    score += 0.3
                    reasons.append(f"Output types: {', '.join(t.value for t in output_matches)}")
            
            if score > 0:
                matches.append({
                    'tool_name': tool_name,
                    'score': score,
                    'reason': '; '.join(reasons)
                })
        
        return matches
    
    def _match_by_keywords(self, request: str) -> List[Dict[str, Any]]:
        """Match tools based on keyword presence"""
        matches = []
        request_lower = request.lower()
        
        for tool_name, capability in self.capability_index.items():
            keyword_matches = [
                kw for kw in capability.keywords 
                if kw in request_lower
            ]
            
            if keyword_matches:
                score = len(keyword_matches) / len(capability.keywords)
                matches.append({
                    'tool_name': tool_name,
                    'score': score * 0.8,  # Slightly lower weight than capability matching
                    'reason': f"Keywords: {', '.join(keyword_matches)}"
                })
        
        return matches
    
    def suggest_tool_combinations(
        self,
        request: str,
        matched_tools: List[Dict[str, Any]]
    ) -> List[List[str]]:
        """
        Suggest combinations of matched tools
        
        Returns:
            List of tool combinations (ordered sequences)
        """
        if not matched_tools:
            return []
        
        # Extract tool names
        tool_names = [match['tool_name'] for match in matched_tools[:5]]
        
        # Check for common patterns
        combinations = []
        
        # Pattern 1: Crawl -> Analyze -> Export
        crawl_tools = [t for t in tool_names if 'crawl' in t]
        analyze_tools = [t for t in tool_names if 'analyze' in t or 'detect' in t]
        export_tools = [t for t in tool_names if 'export' in t]
        
        if crawl_tools and analyze_tools and export_tools:
            combinations.append([crawl_tools[0], analyze_tools[0], export_tools[0]])
        
        # Pattern 2: Query -> Process -> Store
        query_tools = [t for t in tool_names if 'query' in t]
        process_tools = [t for t in tool_names if 'analyze' in t or 'aggregate' in t]
        store_tools = [t for t in tool_names if 'store' in t]
        
        if query_tools and process_tools and store_tools:
            combinations.append([query_tools[0], process_tools[0], store_tools[0]])
        
        # Pattern 3: Multiple crawl -> Compare
        if 'crawl_multiple' in tool_names and 'compare_datasets' in tool_names:
            combinations.append(['crawl_multiple', 'compare_datasets'])
        
        # Single tool if no combinations found
        if not combinations and tool_names:
            combinations.append([tool_names[0]])
        
        return combinations
    
    def get_capability_index(self) -> Dict[str, Dict[str, Any]]:
        """Get the complete capability index"""
        index = {}
        
        for tool_name, capability in self.capability_index.items():
            index[tool_name] = {
                'description': capability.description,
                'input_types': [t.value for t in capability.input_types],
                'output_types': [t.value for t in capability.output_types],
                'capabilities': [c.value for c in capability.processing_capabilities],
                'keywords': capability.keywords,
                'examples': capability.examples,
                'performance_score': capability.performance_score,
                'reliability_score': capability.reliability_score
            }
        
        return index
    
    def update_tool_capability(
        self,
        tool_name: str,
        updates: Dict[str, Any]
    ):
        """Update capability information for a tool"""
        if tool_name not in self.capability_index:
            logger.warning(f"Tool {tool_name} not found in capability index")
            return
        
        capability = self.capability_index[tool_name]
        
        # Update fields
        if 'keywords' in updates:
            capability.keywords.extend(updates['keywords'])
            capability.keywords = list(set(capability.keywords))  # Deduplicate
        
        if 'examples' in updates:
            capability.examples.extend(updates['examples'])
        
        if 'performance_score' in updates:
            capability.performance_score = updates['performance_score']
        
        if 'reliability_score' in updates:
            capability.reliability_score = updates['reliability_score']
        
        # Rebuild text vectors
        self._build_text_vectors()


# Usage example:
if __name__ == "__main__":
    # Create matcher
    matcher = CapabilityMatcher()
    
    # Test requests
    test_requests = [
        "crawl this website and analyze the content for pricing information",
        "compare data from multiple sources and export to Excel",
        "find patterns in the dataset and save to database",
        "export the analysis results as CSV"
    ]
    
    for request in test_requests:
        print(f"\nRequest: {request}")
        matches = matcher.match_request_to_tools(request)
        
        print("Matched tools:")
        for match in matches:
            print(f"  - {match['tool_name']} (score: {match['score']:.2f})")
            print(f"    Reasons: {', '.join(match['reasons'])}")
        
        # Suggest combinations
        combinations = matcher.suggest_tool_combinations(request, matches)
        if combinations:
            print("Suggested combinations:")
            for combo in combinations:
                print(f"  - {' -> '.join(combo)}")
