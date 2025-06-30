#!/usr/bin/env python3
"""
Adaptive Crawler Helper Methods
Supporting methods for adaptive crawler strategy
"""

import json
import hashlib
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
import re

logger = logging.getLogger("adaptive_crawler_helpers")

class AdaptiveCrawlerHelpers:
    """Helper methods for adaptive crawler strategy"""
    
    @staticmethod
    async def analyze_website_structure(url: str, html_content: str, purpose: str,
                                       llm_service, vector_service, config) -> Dict[str, Any]:
        """Analyze website structure for pattern recognition"""
        
        from urllib.parse import urlparse
        
        # Basic URL analysis
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path_depth = len([p for p in parsed_url.path.split('/') if p])
        
        # Content analysis
        content_features = AdaptiveCrawlerHelpers.extract_content_features(html_content)
        
        # LLM-enhanced analysis
        llm_analysis = {}
        if llm_service and config.enable_content_analysis:
            try:
                llm_analysis = await llm_service.analyze_website_content(
                    url, html_content, purpose
                )
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}")
        
        # Generate content embedding for similarity matching
        content_embedding = None
        if vector_service:
            try:
                # Create a summary of content for embedding
                content_summary = AdaptiveCrawlerHelpers.create_content_summary(html_content, content_features)
                content_embedding = await vector_service.generate_embedding(content_summary)
            except Exception as e:
                logger.warning(f"Content embedding failed: {e}")
        
        return {
            "url": url,
            "domain": domain,
            "path_depth": path_depth,
            "content_features": content_features,
            "llm_analysis": llm_analysis,
            "content_embedding": content_embedding,
            "timestamp": time.time()
        }
    
    @staticmethod
    def extract_content_features(html_content: str) -> Dict[str, Any]:
        """Extract quantitative features from HTML content"""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            features = {
                # Structure features
                "total_tags": len(soup.find_all()),
                "div_count": len(soup.find_all('div')),
                "span_count": len(soup.find_all('span')),
                "p_count": len(soup.find_all('p')),
                "table_count": len(soup.find_all('table')),
                "form_count": len(soup.find_all('form')),
                "image_count": len(soup.find_all('img')),
                "link_count": len(soup.find_all('a')),
                
                # Content characteristics
                "text_length": len(soup.get_text()),
                "has_json_ld": bool(soup.find('script', type='application/ld+json')),
                "has_microdata": bool(soup.find(attrs={"itemscope": True})),
                "has_tables": len(soup.find_all('table')) > 0,
                
                # CSS complexity indicators
                "class_diversity": len(set([
                    cls for elem in soup.find_all(class_=True)
                    for cls in elem.get('class', [])
                ])),
                "id_count": len(soup.find_all(id=True)),
                
                # Interactive elements
                "button_count": len(soup.find_all('button')),
                "input_count": len(soup.find_all('input')),
                "select_count": len(soup.find_all('select')),
                
                # Meta information
                "has_viewport": bool(soup.find('meta', attrs={'name': 'viewport'})),
                "has_charset": bool(soup.find('meta', attrs={'charset': True})),
                "title_present": bool(soup.find('title')),
                
                # E-commerce indicators
                "price_indicators": len(soup.find_all(text=lambda t: t and ('$' in str(t) or '€' in str(t) or '£' in str(t)))),
                "cart_indicators": len(soup.find_all(text=lambda t: t and 'cart' in str(t).lower())),
            }
            
            return features
            
        except Exception as e:
            logger.warning(f"Feature extraction failed: {e}")
            return {}
    
    @staticmethod
    def create_content_summary(html_content: str, features: Dict[str, Any]) -> str:
        """Create a concise summary for embedding generation"""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract key text elements
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            # Get first few paragraphs
            paragraphs = soup.find_all('p')[:3]
            paragraph_text = " ".join([p.get_text()[:100] for p in paragraphs])
            
            # Combine with structural features
            summary = f"""
            Title: {title_text}
            Content: {paragraph_text}
            Structure: {features.get('div_count', 0)} divs, {features.get('table_count', 0)} tables, {features.get('form_count', 0)} forms
            Interactive: {features.get('button_count', 0)} buttons, {features.get('input_count', 0)} inputs
            Type indicators: {'ecommerce' if features.get('price_indicators', 0) > 0 else 'content'}
            """
            
            return summary.strip()
            
        except Exception:
            return f"Features: {json.dumps(features)}"
    
    @staticmethod
    async def find_similar_embeddings(vector_service, current_embedding: List[float]) -> List[Tuple[str, float]]:
        """Find similar content embeddings using vector service"""
        
        try:
            # Query vector database for similar embeddings
            results = await vector_service.similarity_search(
                query_embedding=current_embedding,
                collection_name="website_patterns",
                limit=10
            )
            
            return [(result["id"], result["similarity"]) for result in results]
            
        except Exception as e:
            logger.warning(f"Embedding similarity search failed: {e}")
            return []
    
    @staticmethod
    def calculate_feature_similarity(features1: Dict[str, Any], 
                                   features2: Dict[str, Any]) -> float:
        """Calculate similarity between two feature sets"""
        
        if not features1 or not features2:
            return 0.0
        
        # Get common features
        common_features = set(features1.keys()) & set(features2.keys())
        if not common_features:
            return 0.0
        
        # Calculate normalized differences
        similarities = []
        
        for feature in common_features:
            val1 = features1[feature]
            val2 = features2[feature]
            
            if isinstance(val1, bool) and isinstance(val2, bool):
                # Boolean features
                similarities.append(1.0 if val1 == val2 else 0.0)
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numeric features - use normalized difference
                max_val = max(abs(val1), abs(val2), 1)  # Avoid division by zero
                diff = abs(val1 - val2) / max_val
                similarities.append(max(0.0, 1.0 - diff))
            else:
                # String features
                similarities.append(1.0 if str(val1) == str(val2) else 0.0)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    @staticmethod
    async def get_llm_strategy_recommendation(llm_service, website_analysis: Dict[str, Any], 
                                            purpose: str, available_strategies: List[str]) -> Dict[str, Any]:
        """Get strategy recommendation from LLM"""
        
        prompt = f"""
Analyze this website and recommend the best extraction strategy:

Website Analysis:
- Domain: {website_analysis.get('domain', 'unknown')}
- Path Depth: {website_analysis.get('path_depth', 0)}
- Content Features: {json.dumps(website_analysis.get('content_features', {}), indent=2)}
- LLM Analysis: {json.dumps(website_analysis.get('llm_analysis', {}), indent=2)}

Purpose: {purpose}

Available Strategies: {', '.join(available_strategies)}

Recommend the most effective strategy and provide confidence (0-1).
Consider website complexity, content structure, and extraction purpose.
"""
        
        schema = {
            "type": "object",
            "properties": {
                "strategy": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reasoning": {"type": "string"}
            },
            "required": ["strategy", "confidence"]
        }
        
        return await llm_service.generate_structured(prompt, schema)
    
    @staticmethod
    def hash_features(features: Dict[str, Any]) -> str:
        """Create hash of features for pattern identification"""
        
        # Sort features for consistent hashing
        sorted_features = sorted(features.items())
        features_str = json.dumps(sorted_features, sort_keys=True)
        
        return hashlib.md5(features_str.encode()).hexdigest()[:12]
