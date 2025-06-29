"""
Content Chunking Strategies
Advanced chunking algorithms for content processing
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class ContentChunk:
    """A chunk of content with metadata"""
    content: str
    start_position: int
    end_position: int
    chunk_id: str
    metadata: Dict[str, Any]
    overlap_with_previous: int = 0
    overlap_with_next: int = 0


class ChunkingStrategy(ABC):
    """Base class for content chunking strategies"""
    
    @abstractmethod
    def chunk(self, content: str, context: Dict[str, Any] = None) -> List[ContentChunk]:
        """Chunk content into pieces"""
        pass


class RegexChunking(ChunkingStrategy):
    """Regex-based content chunking"""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 overlap: int = 100,
                 split_patterns: List[str] = None):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.split_patterns = split_patterns or [
            r'\n\n+',  # Paragraph breaks
            r'\n',     # Line breaks
            r'\. ',    # Sentence ends
            r', ',     # Clause breaks
            r' '       # Word breaks
        ]
    
    def chunk(self, content: str, context: Dict[str, Any] = None) -> List[ContentChunk]:
        """Chunk content using regex patterns"""
        if not content:
            return []
        
        # Try different split patterns in order of preference
        chunks = []
        remaining_content = content
        position = 0
        chunk_id = 0
        
        while remaining_content:
            if len(remaining_content) <= self.chunk_size:
                # Last chunk
                chunk = ContentChunk(
                    content=remaining_content,
                    start_position=position,
                    end_position=position + len(remaining_content),
                    chunk_id=f"chunk_{chunk_id}",
                    metadata={
                        "method": "regex",
                        "chunk_size": len(remaining_content),
                        "is_last": True
                    }
                )
                chunks.append(chunk)
                break
            
            # Find best split point
            split_point = self._find_best_split(remaining_content, self.chunk_size)
            
            chunk_content = remaining_content[:split_point]
            
            # Add overlap from previous chunk
            overlap_start = max(0, position - self.overlap)
            if chunks and overlap_start < position:
                overlap_content = content[overlap_start:position]
                chunk_content = overlap_content + chunk_content
            
            chunk = ContentChunk(
                content=chunk_content,
                start_position=position,
                end_position=position + split_point,
                chunk_id=f"chunk_{chunk_id}",
                metadata={
                    "method": "regex",
                    "chunk_size": len(chunk_content),
                    "original_size": split_point,
                    "overlap_added": len(chunk_content) - split_point if chunks else 0
                }
            )
            
            chunks.append(chunk)
            
            # Move to next chunk
            remaining_content = remaining_content[split_point - self.overlap:]
            position += split_point - self.overlap
            chunk_id += 1
        
        return chunks
    
    def _find_best_split(self, content: str, max_size: int) -> int:
        """Find the best split point using regex patterns"""
        if len(content) <= max_size:
            return len(content)
        
        # Try each pattern in order of preference
        for pattern in self.split_patterns:
            matches = list(re.finditer(pattern, content[:max_size]))
            if matches:
                # Use the last match before max_size
                return matches[-1].end()
        
        # Fallback to hard split at max_size
        return max_size


class SemanticChunking(ChunkingStrategy):
    """Semantic-based content chunking using sentence similarity"""
    
    def __init__(self, 
                 target_chunk_size: int = 1000,
                 similarity_threshold: float = 0.7,
                 min_chunk_size: int = 200):
        self.target_chunk_size = target_chunk_size
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
    
    def chunk(self, content: str, context: Dict[str, Any] = None) -> List[ContentChunk]:
        """Chunk content based on semantic similarity"""
        if not content:
            return []
        
        # Split into sentences
        sentences = self._split_sentences(content)
        if not sentences:
            return [ContentChunk(
                content=content,
                start_position=0,
                end_position=len(content),
                chunk_id="chunk_0",
                metadata={"method": "semantic", "sentence_count": 0}
            )]
        
        # Group sentences into chunks based on similarity
        chunks = []
        current_chunk_sentences = []
        current_chunk_size = 0
        chunk_id = 0
        position = 0
        
        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence)
            
            # Check if we should start a new chunk
            should_start_new = False
            
            if current_chunk_sentences:
                # Check size constraint
                if current_chunk_size + sentence_size > self.target_chunk_size:
                    should_start_new = True
                
                # Check semantic similarity (simplified)
                elif not self._is_semantically_similar(current_chunk_sentences[-1], sentence):
                    should_start_new = True
            
            if should_start_new and current_chunk_size >= self.min_chunk_size:
                # Create chunk from current sentences
                chunk_content = ' '.join(current_chunk_sentences)
                chunk = ContentChunk(
                    content=chunk_content,
                    start_position=position,
                    end_position=position + len(chunk_content),
                    chunk_id=f"chunk_{chunk_id}",
                    metadata={
                        "method": "semantic",
                        "sentence_count": len(current_chunk_sentences),
                        "avg_similarity": self._calculate_avg_similarity(current_chunk_sentences)
                    }
                )
                chunks.append(chunk)
                
                position += len(chunk_content)
                chunk_id += 1
                current_chunk_sentences = []
                current_chunk_size = 0
            
            current_chunk_sentences.append(sentence)
            current_chunk_size += sentence_size
        
        # Handle remaining sentences
        if current_chunk_sentences:
            chunk_content = ' '.join(current_chunk_sentences)
            chunk = ContentChunk(
                content=chunk_content,
                start_position=position,
                end_position=position + len(chunk_content),
                chunk_id=f"chunk_{chunk_id}",
                metadata={
                    "method": "semantic",
                    "sentence_count": len(current_chunk_sentences),
                    "avg_similarity": self._calculate_avg_similarity(current_chunk_sentences),
                    "is_last": True
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_sentences(self, content: str) -> List[str]:
        """Split content into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _is_semantically_similar(self, sentence1: str, sentence2: str) -> bool:
        """Check if two sentences are semantically similar (simplified)"""
        # Simplified similarity based on common words
        words1 = set(re.findall(r'\b\w+\b', sentence1.lower()))
        words2 = set(re.findall(r'\b\w+\b', sentence2.lower()))
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard_similarity = len(intersection) / len(union) if union else 0
        return jaccard_similarity >= self.similarity_threshold
    
    def _calculate_avg_similarity(self, sentences: List[str]) -> float:
        """Calculate average similarity within a group of sentences"""
        if len(sentences) < 2:
            return 1.0
        
        similarities = []
        for i in range(len(sentences) - 1):
            sim = self._sentence_similarity(sentences[i], sentences[i + 1])
            similarities.append(sim)
        
        return sum(similarities) / len(similarities)
    
    def _sentence_similarity(self, sentence1: str, sentence2: str) -> float:
        """Calculate similarity between two sentences"""
        words1 = set(re.findall(r'\b\w+\b', sentence1.lower()))
        words2 = set(re.findall(r'\b\w+\b', sentence2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class HierarchicalChunking(ChunkingStrategy):
    """Hierarchical chunking based on document structure"""
    
    def __init__(self, 
                 chunk_sizes: List[int] = None,
                 structure_patterns: Dict[str, str] = None):
        self.chunk_sizes = chunk_sizes or [2000, 1000, 500]  # Large, medium, small
        self.structure_patterns = structure_patterns or {
            'heading1': r'^#\s+(.+)$',
            'heading2': r'^##\s+(.+)$', 
            'heading3': r'^###\s+(.+)$',
            'paragraph': r'\n\n',
            'sentence': r'[.!?]+\s+'
        }
    
    def chunk(self, content: str, context: Dict[str, Any] = None) -> List[ContentChunk]:
        """Create hierarchical chunks at multiple levels"""
        if not content:
            return []
        
        all_chunks = []
        
        # Create chunks at each level
        for level, chunk_size in enumerate(self.chunk_sizes):
            level_chunks = self._create_level_chunks(content, chunk_size, level)
            all_chunks.extend(level_chunks)
        
        return all_chunks
    
    def _create_level_chunks(self, content: str, chunk_size: int, level: int) -> List[ContentChunk]:
        """Create chunks for a specific level"""
        chunks = []
        
        # Find structure boundaries
        boundaries = self._find_structure_boundaries(content)
        
        # Create chunks respecting structure
        current_chunk = ""
        current_start = 0
        chunk_id = 0
        
        for boundary in boundaries + [len(content)]:
            section = content[len(current_chunk):boundary]
            
            if len(current_chunk) + len(section) <= chunk_size:
                current_chunk += section
            else:
                if current_chunk:
                    # Create chunk
                    chunk = ContentChunk(
                        content=current_chunk,
                        start_position=current_start,
                        end_position=current_start + len(current_chunk),
                        chunk_id=f"L{level}_chunk_{chunk_id}",
                        metadata={
                            "method": "hierarchical",
                            "level": level,
                            "target_size": chunk_size,
                            "actual_size": len(current_chunk),
                            "respects_structure": True
                        }
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Start new chunk
                current_start = len(current_chunk)
                current_chunk = section
        
        # Handle remaining content
        if current_chunk:
            chunk = ContentChunk(
                content=current_chunk,
                start_position=current_start,
                end_position=current_start + len(current_chunk),
                chunk_id=f"L{level}_chunk_{chunk_id}",
                metadata={
                    "method": "hierarchical",
                    "level": level,
                    "target_size": chunk_size,
                    "actual_size": len(current_chunk),
                    "is_last": True
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _find_structure_boundaries(self, content: str) -> List[int]:
        """Find structural boundaries in content"""
        boundaries = set()
        
        # Find heading boundaries
        for pattern_name, pattern in self.structure_patterns.items():
            if 'heading' in pattern_name:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    boundaries.add(match.start())
        
        # Find paragraph boundaries
        for match in re.finditer(self.structure_patterns['paragraph'], content):
            boundaries.add(match.start())
        
        return sorted(list(boundaries))


# Usage example and testing
if __name__ == "__main__":
    sample_content = """
    This is the first paragraph. It contains multiple sentences. Each sentence adds information.
    
    This is the second paragraph. It's about a different topic. The content shifts here.
    
    # Main Heading
    
    This section is under the main heading. It has structured content.
    
    ## Subheading
    
    More detailed information goes here. It's hierarchically organized.
    """
    
    # Test regex chunking
    regex_chunker = RegexChunking(chunk_size=100, overlap=20)
    regex_chunks = regex_chunker.chunk(sample_content)
    
    print("Regex Chunking Results:")
    for chunk in regex_chunks:
        print(f"Chunk {chunk.chunk_id}: {len(chunk.content)} chars")
        print(f"Content: {chunk.content[:50]}...")
        print()
    
    # Test semantic chunking
    semantic_chunker = SemanticChunking(target_chunk_size=150)
    semantic_chunks = semantic_chunker.chunk(sample_content)
    
    print("Semantic Chunking Results:")
    for chunk in semantic_chunks:
        print(f"Chunk {chunk.chunk_id}: {chunk.metadata}")
        print(f"Content: {chunk.content[:50]}...")
        print()
