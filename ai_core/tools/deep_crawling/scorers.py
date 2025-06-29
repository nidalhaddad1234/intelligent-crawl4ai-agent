"""
URL Scoring System for Deep Crawling
Provides intelligent prioritization of discovered URLs
"""

import re
import math
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set
from urllib.parse import urlparse
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("deep_crawling.scorers")

class URLScorer(ABC):
    """Abstract base class for URL scoring strategies"""
    
    @abstractmethod
    def score_url(self, url: str, context: Dict[str, Any] = None) -> float:
        """
        Score a URL for crawling priority
        
        Args:
            url: The URL to score
            context: Additional context (parent_url, depth, discovered_links, etc.)
            
        Returns:
            Score between 0.0 and 1.0 (higher = higher priority)
        """
        pass
    
    @abstractmethod
    def get_scorer_name(self) -> str:
        """Get a human-readable name for this scorer"""
        pass

class KeywordRelevanceScorer(URLScorer):
    """
    Score URLs based on keyword relevance in the URL path
    
    Examples:
        # Prioritize contact and about pages
        scorer = KeywordRelevanceScorer(
            keywords=["contact", "about", "team"],
            keyword_weights={"contact": 1.0, "about": 0.8, "team": 0.6}
        )
    """
    
    def __init__(self, keywords: List[str], keyword_weights: Dict[str, float] = None):
        self.keywords = [kw.lower() for kw in keywords]
        self.keyword_weights = keyword_weights or {}
        
        # Default weight is 1.0 for keywords not in weights dict
        for keyword in self.keywords:
            if keyword not in self.keyword_weights:
                self.keyword_weights[keyword] = 1.0
    
    def score_url(self, url: str, context: Dict[str, Any] = None) -> float:
        try:
            url_lower = url.lower()
            total_score = 0.0
            max_possible_score = sum(self.keyword_weights.values())
            
            for keyword in self.keywords:
                if keyword in url_lower:
                    weight = self.keyword_weights[keyword]
                    
                    # Bonus for exact segment match vs. substring
                    url_parts = urlparse(url_lower).path.split('/')
                    if keyword in url_parts:
                        total_score += weight * 1.0  # Full weight for exact match
                    else:
                        total_score += weight * 0.5  # Half weight for substring
            
            # Normalize to 0-1 range
            return min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Failed to score URL {url} for keywords: {e}")
            return 0.0
    
    def get_scorer_name(self) -> str:
        return f"KeywordRelevanceScorer(keywords={self.keywords})"

class PathDepthScorer(URLScorer):
    """
    Score URLs based on path depth preference
    
    Examples:
        # Prefer shallow pages (often more important)
        scorer = PathDepthScorer(prefer_shallow=True)
        
        # Prefer deeper pages (detailed content)
        scorer = PathDepthScorer(prefer_shallow=False, optimal_depth=3)
    """
    
    def __init__(self, prefer_shallow: bool = True, optimal_depth: int = 2, max_depth: int = 10):
        self.prefer_shallow = prefer_shallow
        self.optimal_depth = optimal_depth
        self.max_depth = max_depth
    
    def score_url(self, url: str, context: Dict[str, Any] = None) -> float:
        try:
            path = urlparse(url).path
            # Count path segments (excluding empty strings)
            depth = len([segment for segment in path.split('/') if segment])
            
            if self.prefer_shallow:
                # Higher score for shallower paths
                # Score decreases exponentially with depth
                return max(0.0, 1.0 - (depth / self.max_depth))
            else:
                # Score peaks at optimal depth
                distance_from_optimal = abs(depth - self.optimal_depth)
                max_distance = max(self.optimal_depth, self.max_depth - self.optimal_depth)
                return max(0.0, 1.0 - (distance_from_optimal / max_distance))
                
        except Exception as e:
            logger.warning(f"Failed to score URL {url} for path depth: {e}")
            return 0.5  # Default middle score

    def get_scorer_name(self) -> str:
        return f"PathDepthScorer(prefer_shallow={self.prefer_shallow}, optimal={self.optimal_depth})"

class DomainAuthorityScorer(URLScorer):
    """
    Score URLs based on domain authority/reputation
    
    Examples:
        # High-authority domains get higher scores
        scorer = DomainAuthorityScorer(
            domain_scores={"company.com": 1.0, "blog.company.com": 0.8}
        )
    """
    
    def __init__(self, domain_scores: Dict[str, float] = None, default_score: float = 0.5):
        self.domain_scores = domain_scores or {}
        self.default_score = default_score
        
        # Add common high-authority patterns
        self.authority_patterns = {
            r'\.edu$': 0.9,      # Educational domains
            r'\.gov$': 0.9,      # Government domains  
            r'\.org$': 0.7,      # Organization domains
            r'^www\.': 0.1,      # Small bonus for www
            r'blog\.': 0.8,      # Blog subdomains often have good content
            r'news\.': 0.8,      # News subdomains
        }
    
    def score_url(self, url: str, context: Dict[str, Any] = None) -> float:
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check explicit domain scores first
            if domain in self.domain_scores:
                return self.domain_scores[domain]
            
            # Check patterns
            pattern_score = self.default_score
            for pattern, score in self.authority_patterns.items():
                if re.search(pattern, domain):
                    pattern_score = max(pattern_score, score)
            
            return pattern_score
            
        except Exception as e:
            logger.warning(f"Failed to score URL {url} for domain authority: {e}")
            return self.default_score
    
    def get_scorer_name(self) -> str:
        return f"DomainAuthorityScorer(domains={len(self.domain_scores)})"

class FreshnessScorer(URLScorer):
    """
    Score URLs based on content freshness indicators
    
    Examples:
        # Prefer recent content
        scorer = FreshnessScorer(prefer_recent=True)
        
        # Look for date patterns in URLs
        scorer = FreshnessScorer(date_patterns=[r'/202[0-9]/', r'/news/'])
    """
    
    def __init__(self, prefer_recent: bool = True, date_patterns: List[str] = None):
        self.prefer_recent = prefer_recent
        self.date_patterns = date_patterns or [
            r'/202[0-9]/',           # Years 2020-2029
            r'/\d{4}/\d{2}/',        # YYYY/MM format
            r'/news/',               # News sections
            r'/blog/',               # Blog sections  
            r'/press/',              # Press releases
            r'/update/',             # Updates
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.date_patterns]
    
    def score_url(self, url: str, context: Dict[str, Any] = None) -> float:
        try:
            base_score = 0.5
            
            # Check for date patterns
            for pattern in self.compiled_patterns:
                if pattern.search(url):
                    base_score += 0.2
            
            # Extract year if present and score based on recency
            year_match = re.search(r'/20([0-2][0-9])/', url)
            if year_match:
                year = int('20' + year_match.group(1))
                current_year = datetime.now().year
                year_diff = current_year - year
                
                if self.prefer_recent:
                    # Higher score for recent years
                    if year_diff == 0:
                        base_score += 0.3  # Current year
                    elif year_diff == 1:
                        base_score += 0.2  # Last year
                    elif year_diff <= 3:
                        base_score += 0.1  # Recent years
                else:
                    # Stable scoring regardless of year
                    base_score += 0.1
            
            return min(base_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Failed to score URL {url} for freshness: {e}")
            return 0.5
    
    def get_scorer_name(self) -> str:
        return f"FreshnessScorer(prefer_recent={self.prefer_recent})"

class LinkPopularityScorer(URLScorer):
    """
    Score URLs based on how many other pages link to them
    
    Examples:
        # Higher score for URLs mentioned multiple times
        scorer = LinkPopularityScorer()
    """
    
    def __init__(self):
        self.link_counts: Dict[str, int] = {}
        self.total_links = 0
    
    def add_discovered_links(self, page_url: str, discovered_links: List[str]):
        """Add discovered links to tracking"""
        for link in discovered_links:
            self.link_counts[link] = self.link_counts.get(link, 0) + 1
            self.total_links += 1
    
    def score_url(self, url: str, context: Dict[str, Any] = None) -> float:
        if self.total_links == 0:
            return 0.5  # No data yet
        
        link_count = self.link_counts.get(url, 0)
        
        # Use log scale to prevent extremely popular pages from dominating
        if link_count == 0:
            return 0.3  # Pages not linked to get low score
        
        # Score based on relative popularity
        max_links = max(self.link_counts.values()) if self.link_counts else 1
        relative_popularity = link_count / max_links
        
        # Apply log scaling and normalize
        score = 0.3 + (0.7 * math.log(1 + relative_popularity * 9) / math.log(10))
        return min(score, 1.0)
    
    def get_scorer_name(self) -> str:
        return f"LinkPopularityScorer(tracked_links={len(self.link_counts)})"

class CompositeScorer(URLScorer):
    """
    Combines multiple scorers with configurable weights
    
    Examples:
        # Weighted combination of multiple scoring factors
        scorer = CompositeScorer([
            (KeywordRelevanceScorer(["contact", "about"]), 0.4),
            (PathDepthScorer(prefer_shallow=True), 0.3),
            (FreshnessScorer(), 0.3)
        ])
    """
    
    def __init__(self, scorers_and_weights: List[tuple]):
        """
        Args:
            scorers_and_weights: List of (scorer, weight) tuples
        """
        self.scorers_and_weights = scorers_and_weights
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weight for _, weight in scorers_and_weights)
        if total_weight > 0:
            self.scorers_and_weights = [
                (scorer, weight / total_weight) 
                for scorer, weight in scorers_and_weights
            ]
    
    def score_url(self, url: str, context: Dict[str, Any] = None) -> float:
        total_score = 0.0
        
        for scorer, weight in self.scorers_and_weights:
            try:
                score = scorer.score_url(url, context)
                total_score += score * weight
            except Exception as e:
                logger.warning(f"Scorer {scorer.get_scorer_name()} failed for URL {url}: {e}")
                # Use neutral score for failed scorers
                total_score += 0.5 * weight
        
        return min(total_score, 1.0)
    
    def get_scorer_name(self) -> str:
        scorer_names = [f"{scorer.get_scorer_name()}({weight:.2f})" 
                       for scorer, weight in self.scorers_and_weights]
        return f"CompositeScorer({', '.join(scorer_names)})"
    
    def get_component_scores(self, url: str, context: Dict[str, Any] = None) -> Dict[str, float]:
        """Get individual scores from each component scorer"""
        scores = {}
        for scorer, weight in self.scorers_and_weights:
            try:
                score = scorer.score_url(url, context)
                scores[scorer.get_scorer_name()] = {
                    "score": score,
                    "weight": weight,
                    "weighted_score": score * weight
                }
            except Exception as e:
                scores[scorer.get_scorer_name()] = {
                    "score": 0.5,
                    "weight": weight,
                    "weighted_score": 0.5 * weight,
                    "error": str(e)
                }
        return scores

# Pre-built scorer configurations for common use cases
class CommonScorers:
    """Pre-built scorer configurations for common crawling scenarios"""
    
    @staticmethod
    def contact_discovery() -> CompositeScorer:
        """Scorer optimized for finding contact information"""
        return CompositeScorer([
            (KeywordRelevanceScorer([
                "contact", "about", "team", "staff", "management",
                "leadership", "office", "location", "address"
            ]), 0.5),
            (PathDepthScorer(prefer_shallow=True, optimal_depth=2), 0.3),
            (DomainAuthorityScorer(), 0.2)
        ])
    
    @staticmethod
    def product_discovery() -> CompositeScorer:
        """Scorer optimized for finding product information"""
        return CompositeScorer([
            (KeywordRelevanceScorer([
                "product", "service", "solution", "offering",
                "catalog", "shop", "store", "features"
            ]), 0.4),
            (PathDepthScorer(prefer_shallow=False, optimal_depth=3), 0.3),
            (FreshnessScorer(prefer_recent=True), 0.3)
        ])
    
    @staticmethod
    def news_content() -> CompositeScorer:
        """Scorer optimized for finding news and blog content"""
        return CompositeScorer([
            (KeywordRelevanceScorer([
                "news", "blog", "article", "post", "press",
                "announcement", "update", "story"
            ]), 0.3),
            (FreshnessScorer(prefer_recent=True), 0.5),
            (PathDepthScorer(prefer_shallow=False, optimal_depth=3), 0.2)
        ])
    
    @staticmethod
    def comprehensive_discovery() -> CompositeScorer:
        """Balanced scorer for general site exploration"""
        return CompositeScorer([
            (KeywordRelevanceScorer([
                "about", "contact", "product", "service", "news",
                "team", "company", "business", "information"
            ]), 0.25),
            (PathDepthScorer(prefer_shallow=True), 0.25),
            (DomainAuthorityScorer(), 0.25),
            (FreshnessScorer(), 0.25)
        ])
    
    @staticmethod
    def quality_focused() -> CompositeScorer:
        """Scorer that prioritizes content quality indicators"""
        return CompositeScorer([
            (DomainAuthorityScorer(), 0.4),
            (PathDepthScorer(prefer_shallow=True, optimal_depth=2), 0.3),
            (LinkPopularityScorer(), 0.3)
        ])

class ScoringEngine:
    """
    Main scoring engine that manages URL prioritization
    """
    
    def __init__(self, scorer: URLScorer):
        self.scorer = scorer
        self.scored_urls: Dict[str, float] = {}
        self.scoring_history: List[Dict[str, Any]] = []
    
    def score_urls(self, urls: List[str], context: Dict[str, Any] = None) -> Dict[str, float]:
        """Score a list of URLs and return sorted results"""
        scores = {}
        
        for url in urls:
            try:
                score = self.scorer.score_url(url, context)
                scores[url] = score
                self.scored_urls[url] = score
                
                # Track scoring history
                self.scoring_history.append({
                    "url": url,
                    "score": score,
                    "scorer": self.scorer.get_scorer_name(),
                    "context": context,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Failed to score URL {url}: {e}")
                scores[url] = 0.5  # Default score
        
        return scores
    
    def get_prioritized_urls(self, urls: List[str], context: Dict[str, Any] = None, limit: int = None) -> List[tuple]:
        """
        Get URLs sorted by priority score
        
        Returns:
            List of (url, score) tuples sorted by score (highest first)
        """
        scores = self.score_urls(urls, context)
        sorted_urls = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if limit:
            sorted_urls = sorted_urls[:limit]
        
        return sorted_urls
    
    def get_scoring_statistics(self) -> Dict[str, Any]:
        """Get statistics about the scoring process"""
        if not self.scored_urls:
            return {"message": "No URLs scored yet"}
        
        scores = list(self.scored_urls.values())
        
        return {
            "total_urls_scored": len(self.scored_urls),
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "score_distribution": {
                "high (0.8-1.0)": len([s for s in scores if s >= 0.8]),
                "medium (0.5-0.8)": len([s for s in scores if 0.5 <= s < 0.8]),
                "low (0.0-0.5)": len([s for s in scores if s < 0.5])
            },
            "scorer_name": self.scorer.get_scorer_name()
        }
