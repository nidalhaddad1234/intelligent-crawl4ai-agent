"""
Advanced Content Filtering Strategies
Intelligent content filtering using BM25, LLM, and other algorithms
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass
import math
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Result from content filtering"""
    content: str
    score: float
    metadata: Dict[str, Any]
    filtered_sections: List[str]
    kept_sections: List[str]


class ContentFilter(ABC):
    """Base class for content filters"""
    
    @abstractmethod
    def filter(self, content: str, context: Dict[str, Any] = None) -> FilterResult:
        """Filter content and return result with score"""
        pass


class BM25ContentFilter(ContentFilter):
    """BM25-based content filtering for relevance scoring"""
    
    def __init__(self, 
                 keywords: List[str],
                 relevance_threshold: float = 0.7,
                 k1: float = 1.2,
                 b: float = 0.75):
        self.keywords = [kw.lower() for kw in keywords]
        self.relevance_threshold = relevance_threshold
        self.k1 = k1
        self.b = b
        self.idf_cache = {}
        
    def filter(self, content: str, context: Dict[str, Any] = None) -> FilterResult:
        """Filter content using BM25 relevance scoring"""
        # Split content into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return FilterResult(
                content="",
                score=0.0,
                metadata={"method": "bm25", "total_sentences": 0},
                filtered_sections=[],
                kept_sections=[]
            )
        
        # Calculate BM25 scores for each sentence
        sentence_scores = []
        for sentence in sentences:
            score = self._calculate_bm25_score(sentence, sentences)
            sentence_scores.append((sentence, score))
        
        # Filter sentences above threshold
        kept_sentences = []
        filtered_sentences = []
        
        for sentence, score in sentence_scores:
            if score >= self.relevance_threshold:
                kept_sentences.append(sentence)
            else:
                filtered_sentences.append(sentence)
        
        # Calculate overall score
        if sentence_scores:
            avg_score = sum(score for _, score in sentence_scores) / len(sentence_scores)
        else:
            avg_score = 0.0
        
        filtered_content = '. '.join(kept_sentences)
        if filtered_content and not filtered_content.endswith('.'):
            filtered_content += '.'
        
        return FilterResult(
            content=filtered_content,
            score=avg_score,
            metadata={
                "method": "bm25",
                "total_sentences": len(sentences),
                "kept_sentences": len(kept_sentences),
                "filtered_sentences": len(filtered_sentences),
                "relevance_threshold": self.relevance_threshold,
                "keywords": self.keywords
            },
            filtered_sections=filtered_sentences,
            kept_sections=kept_sentences
        )
    
    def _calculate_bm25_score(self, query_sentence: str, document_sentences: List[str]) -> float:
        """Calculate BM25 score for a sentence"""
        query_terms = self._tokenize(query_sentence)
        doc_terms = self._tokenize(query_sentence)
        
        if not query_terms or not doc_terms:
            return 0.0
        
        # Calculate term frequencies
        tf = Counter(doc_terms)
        doc_length = len(doc_terms)
        
        # Average document length (approximation)
        avg_doc_length = sum(len(self._tokenize(s)) for s in document_sentences) / len(document_sentences)
        
        score = 0.0
        for term in self.keywords:
            if term in tf:
                # Term frequency component
                term_freq = tf[term]
                tf_component = (term_freq * (self.k1 + 1)) / (
                    term_freq + self.k1 * (1 - self.b + self.b * (doc_length / avg_doc_length))
                )
                
                # IDF component (simplified)
                idf = self._get_idf(term, document_sentences)
                
                score += tf_component * idf
        
        return score
    
    def _get_idf(self, term: str, documents: List[str]) -> float:
        """Calculate IDF for a term"""
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        # Count documents containing the term
        doc_count = sum(1 for doc in documents if term in self._tokenize(doc))
        
        if doc_count == 0:
            idf = 0.0
        else:
            idf = math.log((len(documents) - doc_count + 0.5) / (doc_count + 0.5))
        
        self.idf_cache[term] = idf
        return idf
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        return re.findall(r'\b\w+\b', text.lower())


class LLMContentFilter(ContentFilter):
    """LLM-based content filtering for quality assessment"""
    
    def __init__(self, 
                 quality_threshold: float = 0.8,
                 llm_provider: str = "ollama",
                 model_name: str = "deepseek-coder:1.3b"):
        self.quality_threshold = quality_threshold
        self.llm_provider = llm_provider
        self.model_name = model_name
        
    def filter(self, content: str, context: Dict[str, Any] = None) -> FilterResult:
        """Filter content using LLM quality assessment"""
        if not content.strip():
            return FilterResult(
                content="",
                score=0.0,
                metadata={"method": "llm", "error": "empty_content"},
                filtered_sections=[],
                kept_sections=[]
            )
        
        # Split into paragraphs for analysis
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            paragraphs = [content]
        
        # Analyze each paragraph (simplified - in production would use actual LLM)
        analyzed_paragraphs = []
        for para in paragraphs:
            score = self._analyze_paragraph_quality(para, context)
            analyzed_paragraphs.append((para, score))
        
        # Filter based on quality scores
        kept_paragraphs = []
        filtered_paragraphs = []
        
        for para, score in analyzed_paragraphs:
            if score >= self.quality_threshold:
                kept_paragraphs.append(para)
            else:
                filtered_paragraphs.append(para)
        
        # Calculate overall score
        if analyzed_paragraphs:
            avg_score = sum(score for _, score in analyzed_paragraphs) / len(analyzed_paragraphs)
        else:
            avg_score = 0.0
        
        filtered_content = '\n\n'.join(kept_paragraphs)
        
        return FilterResult(
            content=filtered_content,
            score=avg_score,
            metadata={
                "method": "llm",
                "provider": self.llm_provider,
                "model": self.model_name,
                "total_paragraphs": len(paragraphs),
                "kept_paragraphs": len(kept_paragraphs),
                "filtered_paragraphs": len(filtered_paragraphs),
                "quality_threshold": self.quality_threshold
            },
            filtered_sections=filtered_paragraphs,
            kept_sections=kept_paragraphs
        )
    
    def _analyze_paragraph_quality(self, paragraph: str, context: Dict[str, Any] = None) -> float:
        """Analyze paragraph quality (simplified heuristic-based approach)"""
        if not paragraph:
            return 0.0
        
        score = 0.0
        
        # Length score (moderate length is better)
        length = len(paragraph)
        if 50 <= length <= 500:
            score += 0.3
        elif 20 <= length <= 1000:
            score += 0.2
        
        # Sentence structure score
        sentences = re.split(r'[.!?]+', paragraph)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
            if 10 <= avg_sentence_length <= 100:
                score += 0.2
        
        # Information density score
        words = re.findall(r'\b\w+\b', paragraph.lower())
        unique_words = set(words)
        
        if words:
            uniqueness_ratio = len(unique_words) / len(words)
            score += min(uniqueness_ratio * 0.3, 0.3)
        
        # Context relevance (if keywords provided)
        if context and 'keywords' in context:
            keywords = [kw.lower() for kw in context['keywords']]
            text_lower = paragraph.lower()
            
            keyword_matches = sum(1 for kw in keywords if kw in text_lower)
            if keywords:
                relevance_score = keyword_matches / len(keywords)
                score += relevance_score * 0.2
        
        return min(score, 1.0)


class PruningContentFilter(ContentFilter):
    """Filter to remove noise and irrelevant content"""
    
    def __init__(self, remove_noise: bool = True):
        self.remove_noise = remove_noise
        
        # Patterns for noise content
        self.noise_patterns = [
            r'cookie\s+policy',
            r'privacy\s+policy', 
            r'terms\s+of\s+service',
            r'advertisement',
            r'click\s+here',
            r'subscribe\s+to',
            r'follow\s+us',
            r'social\s+media',
            r'loading\.\.\.',
            r'please\s+wait',
            r'error\s+\d+',
            r'page\s+not\s+found',
            r'access\s+denied'
        ]
        
        # Navigation and UI elements
        self.ui_patterns = [
            r'home\s*\|\s*about\s*\|\s*contact',
            r'menu',
            r'navigation',
            r'breadcrumb',
            r'previous\s+page',
            r'next\s+page',
            r'page\s+\d+\s+of\s+\d+',
            r'items\s+per\s+page'
        ]
    
    def filter(self, content: str, context: Dict[str, Any] = None) -> FilterResult:
        """Remove noise and irrelevant content"""
        if not content.strip():
            return FilterResult(
                content="",
                score=0.0,
                metadata={"method": "pruning", "error": "empty_content"},
                filtered_sections=[],
                kept_sections=[]
            )
        
        original_content = content
        filtered_sections = []
        
        # Split into lines for processing
        lines = content.split('\n')
        kept_lines = []
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                kept_lines.append(line)
                continue
            
            should_remove = False
            
            if self.remove_noise:
                # Check for noise patterns
                for pattern in self.noise_patterns + self.ui_patterns:
                    if re.search(pattern, line_clean, re.IGNORECASE):
                        should_remove = True
                        filtered_sections.append(line_clean)
                        break
                
                # Remove very short lines (likely navigation/UI)
                if not should_remove and len(line_clean) < 10 and not re.search(r'[.!?]$', line_clean):
                    should_remove = True
                    filtered_sections.append(line_clean)
                
                # Remove lines with too many special characters
                if not should_remove:
                    special_chars = len(re.findall(r'[^\w\s]', line_clean))
                    if special_chars > len(line_clean) * 0.3:
                        should_remove = True
                        filtered_sections.append(line_clean)
            
            if not should_remove:
                kept_lines.append(line)
        
        filtered_content = '\n'.join(kept_lines)
        
        # Calculate quality score based on content reduction
        original_length = len(original_content)
        filtered_length = len(filtered_content)
        
        if original_length > 0:
            reduction_ratio = (original_length - filtered_length) / original_length
            # Good pruning removes some noise but not too much content
            if 0.05 <= reduction_ratio <= 0.3:
                score = 0.9
            elif 0.0 <= reduction_ratio <= 0.5:
                score = 0.7
            else:
                score = 0.5
        else:
            score = 0.0
        
        return FilterResult(
            content=filtered_content,
            score=score,
            metadata={
                "method": "pruning",
                "original_length": original_length,
                "filtered_length": filtered_length,
                "reduction_ratio": (original_length - filtered_length) / original_length if original_length > 0 else 0,
                "removed_sections": len(filtered_sections)
            },
            filtered_sections=filtered_sections,
            kept_sections=kept_lines
        )


class RelevantContentFilter(ContentFilter):
    """Filter content based on keyword relevance"""
    
    def __init__(self, 
                 keywords: List[str],
                 min_keyword_density: float = 0.01,
                 context_window: int = 2):
        self.keywords = [kw.lower() for kw in keywords]
        self.min_keyword_density = min_keyword_density
        self.context_window = context_window
        
    def filter(self, content: str, context: Dict[str, Any] = None) -> FilterResult:
        """Filter content based on keyword relevance"""
        if not content.strip():
            return FilterResult(
                content="",
                score=0.0,
                metadata={"method": "relevance", "error": "empty_content"},
                filtered_sections=[],
                kept_sections=[]
            )
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return FilterResult(
                content=content,
                score=0.0,
                metadata={"method": "relevance", "total_sentences": 0},
                filtered_sections=[],
                kept_sections=[content]
            )
        
        # Find sentences with keywords
        relevant_indices = set()
        sentence_scores = []
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            keyword_count = sum(1 for kw in self.keywords if kw in sentence_lower)
            
            if keyword_count > 0:
                relevant_indices.add(i)
                # Add context window
                for j in range(max(0, i - self.context_window), 
                              min(len(sentences), i + self.context_window + 1)):
                    relevant_indices.add(j)
            
            # Calculate sentence relevance score
            words = re.findall(r'\b\w+\b', sentence_lower)
            if words:
                keyword_density = keyword_count / len(words)
                sentence_scores.append(keyword_density)
            else:
                sentence_scores.append(0.0)
        
        # Build filtered content
        kept_sentences = []
        filtered_sentences = []
        
        for i, sentence in enumerate(sentences):
            if i in relevant_indices:
                kept_sentences.append(sentence)
            else:
                filtered_sentences.append(sentence)
        
        # Calculate overall relevance score
        if sentence_scores:
            avg_score = sum(sentence_scores) / len(sentence_scores)
        else:
            avg_score = 0.0
        
        filtered_content = '. '.join(kept_sentences)
        if filtered_content and not filtered_content.endswith('.'):
            filtered_content += '.'
        
        return FilterResult(
            content=filtered_content,
            score=avg_score,
            metadata={
                "method": "relevance",
                "keywords": self.keywords,
                "total_sentences": len(sentences),
                "relevant_sentences": len(kept_sentences),
                "filtered_sentences": len(filtered_sentences),
                "keyword_density_threshold": self.min_keyword_density,
                "context_window": self.context_window
            },
            filtered_sections=filtered_sentences,
            kept_sections=kept_sentences
        )


class ContentFilterChain:
    """Chain multiple content filters together"""
    
    def __init__(self, filters: List[ContentFilter], logic: str = "AND"):
        self.filters = filters
        self.logic = logic.upper()  # "AND" or "OR"
        
    def filter(self, content: str, context: Dict[str, Any] = None) -> FilterResult:
        """Apply all filters in sequence"""
        if not self.filters:
            return FilterResult(
                content=content,
                score=1.0,
                metadata={"method": "chain", "filters": 0},
                filtered_sections=[],
                kept_sections=[content]
            )
        
        current_content = content
        all_scores = []
        all_metadata = {}
        all_filtered_sections = []
        
        for i, filter_obj in enumerate(self.filters):
            result = filter_obj.filter(current_content, context)
            
            all_scores.append(result.score)
            all_metadata[f"filter_{i}"] = result.metadata
            all_filtered_sections.extend(result.filtered_sections)
            
            if self.logic == "AND":
                # For AND logic, use output of each filter as input to next
                current_content = result.content
            # For OR logic, keep original content and combine results
        
        # Calculate final score based on logic
        if self.logic == "AND":
            final_score = min(all_scores) if all_scores else 0.0
            final_content = current_content
        else:  # OR logic
            final_score = max(all_scores) if all_scores else 0.0
            # For OR, we'd need more complex content merging logic
            final_content = current_content
        
        return FilterResult(
            content=final_content,
            score=final_score,
            metadata={
                "method": "chain",
                "logic": self.logic,
                "filter_count": len(self.filters),
                "individual_scores": all_scores,
                "filter_details": all_metadata
            },
            filtered_sections=all_filtered_sections,
            kept_sections=[final_content]
        )
