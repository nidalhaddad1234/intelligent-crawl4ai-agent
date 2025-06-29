#!/usr/bin/env python3
"""
Missing Crawl4AI Strategies Implementation
Adds RegexExtractionStrategy, JsonXPathExtractionStrategy, and CosineStrategy
"""

import re
import time
import math
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from bs4 import BeautifulSoup
from lxml import html, etree
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

class RegexExtractionStrategy(BaseExtractionStrategy):
    """
    Fast pattern-based extraction using pre-compiled regular expressions
    Matches Crawl4AI's RegexExtractionStrategy functionality
    """
    
    # Built-in pattern catalog (matches Crawl4AI patterns)
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        'url': r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
        'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        'time': r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AaPp][Mm])?\b',
        'currency': r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s?(?:USD|EUR|GBP|JPY|CAD|AUD)',
        'social_security': r'\b\d{3}-\d{2}-\d{4}\b',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'zip_code': r'\b\d{5}(?:-\d{4})?\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    }
    
    def __init__(self, patterns: Union[str, List[str], Dict[str, str]] = None, **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        
        self.custom_patterns = {}
        self.compiled_patterns = {}
        
        if patterns:
            if isinstance(patterns, str):
                # Single built-in pattern
                if patterns in self.PATTERNS:
                    self.custom_patterns[patterns] = self.PATTERNS[patterns]
            elif isinstance(patterns, list):
                # Multiple built-in patterns
                for pattern in patterns:
                    if pattern in self.PATTERNS:
                        self.custom_patterns[pattern] = self.PATTERNS[pattern]
            elif isinstance(patterns, dict):
                # Custom pattern dictionary
                self.custom_patterns.update(patterns)
        else:
            # Default to common patterns
            self.custom_patterns = {
                'email': self.PATTERNS['email'],
                'phone': self.PATTERNS['phone'],
                'url': self.PATTERNS['url']
            }
        
        # Compile patterns for performance
        for name, pattern in self.custom_patterns.items():
            try:
                self.compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                self.logger.warning(f"Failed to compile pattern '{name}': {e}")
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Extract text content from HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            # Extract data using compiled patterns
            extracted_data = {}
            
            for pattern_name, compiled_pattern in self.compiled_patterns.items():
                matches = compiled_pattern.findall(text_content)
                if matches:
                    # Remove duplicates while preserving order
                    unique_matches = list(dict.fromkeys(matches))
                    extracted_data[pattern_name] = unique_matches
            
            # Calculate confidence based on number of matches
            total_matches = sum(len(matches) for matches in extracted_data.values())
            confidence = min(0.3 + (total_matches * 0.1), 1.0)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="RegexExtractionStrategy",
                execution_time=execution_time,
                metadata={
                    "patterns_used": list(self.compiled_patterns.keys()),
                    "total_matches": total_matches,
                    "text_length": len(text_content)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="RegexExtractionStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Regex strategy works well for pattern-based data extraction"""
        if purpose in ["contact_discovery", "data_validation", "pattern_extraction"]:
            return 0.8
        return 0.4  # Lower for complex semantic tasks
    
    def supports_purpose(self, purpose: str) -> bool:
        """Regex strategy supports pattern-based extraction purposes"""
        supported_purposes = [
            "contact_discovery", "data_validation", "pattern_extraction",
            "email_extraction", "phone_extraction", "url_extraction"
        ]
        return purpose in supported_purposes

class JsonXPathExtractionStrategy(BaseExtractionStrategy):
    """
    XPath-based structured data extraction
    Matches Crawl4AI's JsonXPathExtractionStrategy functionality
    """
    
    def __init__(self, schema: Dict[str, Any], **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        self.schema = schema
        
        # Validate schema
        if not isinstance(schema, dict) or 'name' not in schema:
            raise ValueError("Schema must be a dictionary with 'name' field")
        
        self.base_xpath = schema.get('baseSelector', '//body')
        self.fields = schema.get('fields', [])
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Parse HTML with lxml
            tree = html.fromstring(html_content)
            
            extracted_data = []
            
            # Find base elements using XPath
            base_elements = tree.xpath(self.base_xpath)
            
            if not base_elements:
                # Try alternative approach - extract from entire document
                base_elements = [tree]
            
            for element in base_elements:
                item_data = {}
                
                for field in self.fields:
                    field_name = field.get('name')
                    field_xpath = field.get('selector', field.get('xpath'))
                    field_type = field.get('type', 'text')
                    attribute = field.get('attribute')
                    
                    if not field_xpath:
                        continue
                    
                    try:
                        # Execute XPath query
                        field_elements = element.xpath(field_xpath)
                        
                        if field_elements:
                            if field_type == 'attribute' and attribute:
                                value = field_elements[0].get(attribute, '')
                            elif field_type == 'html':
                                value = etree.tostring(field_elements[0], encoding='unicode')
                            else:  # text
                                value = field_elements[0].text_content().strip()
                            
                            if value:
                                item_data[field_name] = value
                                
                    except Exception as e:
                        self.logger.warning(f"XPath extraction failed for field '{field_name}': {e}")
                
                if item_data:
                    extracted_data.append(item_data)
            
            # Format result based on schema structure
            result_data = {}
            if extracted_data:
                if len(extracted_data) == 1:
                    result_data = extracted_data[0]
                else:
                    result_data[self.schema['name'].lower().replace(' ', '_')] = extracted_data
            
            confidence = self.calculate_confidence(result_data, [f['name'] for f in self.fields])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(result_data),
                extracted_data=result_data,
                confidence_score=confidence,
                strategy_used="JsonXPathExtractionStrategy",
                execution_time=execution_time,
                metadata={
                    "base_xpath": self.base_xpath,
                    "fields_extracted": len(result_data),
                    "items_found": len(extracted_data)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="JsonXPathExtractionStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """XPath strategy confidence based on content structure"""
        try:
            tree = html.fromstring(html_content)
            base_elements = tree.xpath(self.base_xpath)
            
            if base_elements:
                return 0.8
            else:
                return 0.3
        except:
            return 0.2
    
    def supports_purpose(self, purpose: str) -> bool:
        """XPath strategy supports structured data extraction"""
        supported_purposes = [
            "product_data", "news_content", "company_info",
            "structured_extraction", "xml_data", "html_parsing"
        ]
        return purpose in supported_purposes

class CosineStrategy(BaseExtractionStrategy):
    """
    Similarity-based content clustering and extraction
    Matches Crawl4AI's CosineStrategy functionality
    """
    
    def __init__(self, 
                 semantic_filter: str = None,
                 word_count_threshold: int = 10,
                 sim_threshold: float = 0.3,
                 max_dist: float = 0.2,
                 top_k: int = 3,
                 **kwargs):
        super().__init__(strategy_type=StrategyType.HYBRID, **kwargs)
        
        self.semantic_filter = semantic_filter
        self.word_count_threshold = word_count_threshold
        self.sim_threshold = sim_threshold
        self.max_dist = max_dist
        self.top_k = top_k
        
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)
        )
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Extract text content and split into sections
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Split content into paragraphs/sections
            paragraphs = []
            for element in soup.find_all(['p', 'div', 'section', 'article']):
                text = element.get_text(strip=True)
                if len(text.split()) >= self.word_count_threshold:
                    paragraphs.append({
                        'text': text,
                        'element_type': element.name,
                        'classes': element.get('class', [])
                    })
            
            if not paragraphs:
                return StrategyResult(
                    success=False,
                    extracted_data={},
                    confidence_score=0.0,
                    strategy_used="CosineStrategy",
                    execution_time=time.time() - start_time,
                    metadata={},
                    error="No content sections found"
                )
            
            # Extract text for vectorization
            texts = [p['text'] for p in paragraphs]
            
            # Compute TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Perform clustering based on similarity
            clusters = self._cluster_by_similarity(tfidf_matrix, paragraphs)
            
            # Filter by semantic filter if provided
            if self.semantic_filter:
                filtered_clusters = self._apply_semantic_filter(clusters, self.semantic_filter)
            else:
                filtered_clusters = clusters
            
            # Select top clusters
            top_clusters = sorted(filtered_clusters, 
                                key=lambda x: x['similarity_score'], 
                                reverse=True)[:self.top_k]
            
            extracted_data = {
                'clusters': top_clusters,
                'total_sections': len(paragraphs),
                'clusters_found': len(clusters),
                'top_clusters': len(top_clusters)
            }
            
            confidence = min(0.5 + (len(top_clusters) * 0.1), 1.0)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(top_clusters),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="CosineStrategy",
                execution_time=execution_time,
                metadata={
                    "semantic_filter": self.semantic_filter,
                    "similarity_threshold": self.sim_threshold,
                    "sections_analyzed": len(paragraphs)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="CosineStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _cluster_by_similarity(self, tfidf_matrix, paragraphs) -> List[Dict[str, Any]]:
        """Cluster paragraphs by cosine similarity"""
        
        # Compute pairwise cosine similarities
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        clusters = []
        used_indices = set()
        
        for i in range(len(paragraphs)):
            if i in used_indices:
                continue
            
            # Find similar paragraphs
            cluster_indices = [i]
            similarities = similarity_matrix[i]
            
            for j in range(len(paragraphs)):
                if j != i and j not in used_indices:
                    if similarities[j] >= self.sim_threshold:
                        cluster_indices.append(j)
            
            # Create cluster
            cluster_texts = [paragraphs[idx]['text'] for idx in cluster_indices]
            avg_similarity = np.mean([similarities[idx] for idx in cluster_indices])
            
            cluster = {
                'texts': cluster_texts,
                'indices': cluster_indices,
                'similarity_score': float(avg_similarity),
                'size': len(cluster_indices),
                'combined_text': ' '.join(cluster_texts)
            }
            
            clusters.append(cluster)
            used_indices.update(cluster_indices)
        
        return clusters
    
    def _apply_semantic_filter(self, clusters, semantic_filter: str) -> List[Dict[str, Any]]:
        """Filter clusters based on semantic relevance to filter term"""
        
        filtered_clusters = []
        
        # Create TF-IDF vector for semantic filter
        filter_texts = [semantic_filter] + [cluster['combined_text'] for cluster in clusters]
        filter_tfidf = self.vectorizer.fit_transform(filter_texts)
        
        # Compute similarity to filter term
        filter_vector = filter_tfidf[0:1]  # First row is the filter term
        cluster_vectors = filter_tfidf[1:]  # Rest are cluster texts
        
        similarities = cosine_similarity(filter_vector, cluster_vectors)[0]
        
        for i, cluster in enumerate(clusters):
            filter_similarity = similarities[i]
            if filter_similarity >= self.sim_threshold:
                cluster['filter_similarity'] = float(filter_similarity)
                cluster['similarity_score'] = float(filter_similarity)  # Use filter similarity as main score
                filtered_clusters.append(cluster)
        
        return filtered_clusters
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Cosine strategy confidence based on content richness"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Count paragraphs/sections
        content_elements = soup.find_all(['p', 'div', 'section', 'article'])
        rich_content = [el for el in content_elements 
                       if len(el.get_text(strip=True).split()) >= self.word_count_threshold]
        
        if len(rich_content) >= 5:
            return 0.8
        elif len(rich_content) >= 2:
            return 0.6
        else:
            return 0.3
    
    def supports_purpose(self, purpose: str) -> bool:
        """Cosine strategy supports content analysis and clustering"""
        supported_purposes = [
            "content_analysis", "topic_clustering", "similarity_search",
            "relevant_content", "news_content", "research_analysis"
        ]
        return purpose in supported_purposes
