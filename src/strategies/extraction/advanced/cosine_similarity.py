#!/usr/bin/env python3
"""
Cosine Similarity Strategy
Similarity-based content clustering and extraction
"""

import time
import numpy as np
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

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
                    "sections_analyzed": len(paragraphs),
                    "word_count_threshold": self.word_count_threshold
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
                'combined_text': ' '.join(cluster_texts),
                'element_types': [paragraphs[idx]['element_type'] for idx in cluster_indices]
            }
            
            clusters.append(cluster)
            used_indices.update(cluster_indices)
        
        return clusters
    
    def _apply_semantic_filter(self, clusters, semantic_filter: str) -> List[Dict[str, Any]]:
        """Filter clusters based on semantic relevance to filter term"""
        
        filtered_clusters = []
        
        # Create TF-IDF vector for semantic filter
        filter_texts = [semantic_filter] + [cluster['combined_text'] for cluster in clusters]
        
        try:
            filter_tfidf = self.vectorizer.fit_transform(filter_texts)
        except ValueError:
            # Fallback if filter creates issues
            return clusters
        
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
    
    def analyze_content_similarity(self, html_content: str) -> Dict[str, Any]:
        """Analyze content similarity without extraction"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract paragraphs
        paragraphs = []
        for element in soup.find_all(['p', 'div', 'section', 'article']):
            text = element.get_text(strip=True)
            if len(text.split()) >= self.word_count_threshold:
                paragraphs.append(text)
        
        if len(paragraphs) < 2:
            return {"analysis": "insufficient_content", "paragraphs": len(paragraphs)}
        
        try:
            # Compute TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(paragraphs)
            
            # Compute similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Analyze similarity distribution
            similarities = []
            for i in range(len(paragraphs)):
                for j in range(i + 1, len(paragraphs)):
                    similarities.append(similarity_matrix[i][j])
            
            return {
                "analysis": "success",
                "paragraphs": len(paragraphs),
                "avg_similarity": float(np.mean(similarities)),
                "max_similarity": float(np.max(similarities)),
                "min_similarity": float(np.min(similarities)),
                "high_similarity_pairs": sum(1 for s in similarities if s >= self.sim_threshold)
            }
            
        except Exception as e:
            return {"analysis": "error", "error": str(e)}
    
    def set_parameters(self, 
                      semantic_filter: str = None,
                      word_count_threshold: int = None,
                      sim_threshold: float = None,
                      top_k: int = None):
        """Update strategy parameters"""
        
        if semantic_filter is not None:
            self.semantic_filter = semantic_filter
        if word_count_threshold is not None:
            self.word_count_threshold = max(1, word_count_threshold)
        if sim_threshold is not None:
            self.sim_threshold = max(0.0, min(1.0, sim_threshold))
        if top_k is not None:
            self.top_k = max(1, top_k)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters"""
        return {
            "semantic_filter": self.semantic_filter,
            "word_count_threshold": self.word_count_threshold,
            "sim_threshold": self.sim_threshold,
            "max_dist": self.max_dist,
            "top_k": self.top_k
        }
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Cosine strategy confidence based on content richness"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Count paragraphs/sections
        content_elements = soup.find_all(['p', 'div', 'section', 'article'])
        rich_content = [el for el in content_elements 
                       if len(el.get_text(strip=True).split()) >= self.word_count_threshold]
        
        if len(rich_content) >= 10:
            return 0.9
        elif len(rich_content) >= 5:
            return 0.8
        elif len(rich_content) >= 2:
            return 0.6
        else:
            return 0.3
    
    def supports_purpose(self, purpose: str) -> bool:
        """Cosine strategy supports content analysis and clustering"""
        supported_purposes = [
            "content_analysis", "topic_clustering", "similarity_search",
            "relevant_content", "news_content", "research_analysis",
            "document_clustering", "text_similarity"
        ]
        return purpose in supported_purposes
