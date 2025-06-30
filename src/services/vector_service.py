#!/usr/bin/env python3
"""
Vector Service
Enhanced ChromaDB management with production features and intelligent pattern storage
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import time
import hashlib
import struct

import chromadb
from chromadb.config import Settings

logger = logging.getLogger("vector_service")

@dataclass
class VectorConfig:
    """Configuration for vector service"""
    host: str = "localhost"
    port: int = 8000
    persistent_path: str = "./chromadb_data"
    collection_prefix: str = "crawl4ai"
    max_collection_size: int = 100000
    embedding_dimension: int = 384

@dataclass 
class SearchResult:
    """Structured search result"""
    content: str
    metadata: Dict[str, Any]
    similarity: float
    collection: str

class VectorService:
    """
    Production-ready vector storage service with ChromaDB
    Enhanced with learning capabilities and pattern recognition
    """
    
    def __init__(self, config: VectorConfig = None, llm_service=None):
        self.config = config or VectorConfig()
        self.llm_service = llm_service
        self.client = None
        self.collections = {}
        self.collection_stats = {}
        
    async def initialize(self) -> bool:
        """Initialize ChromaDB client and collections"""
        
        try:
            # Try HTTP client first, fall back to persistent
            try:
                self.client = chromadb.HttpClient(
                    host=self.config.host,
                    port=self.config.port,
                    settings=Settings(allow_reset=True)
                )
                # Test connection
                self.client.heartbeat()
                logger.info(f"Connected to ChromaDB server at {self.config.host}:{self.config.port}")
                
            except Exception as e:
                logger.warning(f"HTTP client failed, using persistent client: {e}")
                self.client = chromadb.PersistentClient(
                    path=self.config.persistent_path,
                    settings=Settings(allow_reset=True)
                )
                logger.info(f"Using persistent ChromaDB at {self.config.persistent_path}")
            
            # Create collections
            await self._create_collections()
            
            # Load collection statistics
            await self._refresh_collection_stats()
            
            logger.info(f"Vector service initialized with {len(self.collections)} collections")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            return False
    
    async def _create_collections(self):
        """Create necessary collections for intelligent pattern storage"""
        
        collection_configs = {
            "extraction_results": {
                "name": f"{self.config.collection_prefix}_extraction_results",
                "metadata": {"hnsw:space": "cosine"},
                "description": "Successful extraction results with embeddings"
            },
            "strategy_patterns": {
                "name": f"{self.config.collection_prefix}_strategy_patterns",
                "metadata": {"hnsw:space": "cosine"},
                "description": "Successful extraction strategies and patterns"
            },
            "website_analysis": {
                "name": f"{self.config.collection_prefix}_website_analysis", 
                "metadata": {"hnsw:space": "cosine"},
                "description": "Website analysis results for similar site detection"
            },
            "learned_selectors": {
                "name": f"{self.config.collection_prefix}_learned_selectors",
                "metadata": {"hnsw:space": "cosine"},
                "description": "CSS selectors that worked well for specific patterns"
            },
            "performance_logs": {
                "name": f"{self.config.collection_prefix}_performance_logs",
                "metadata": {"hnsw:space": "cosine"},
                "description": "Performance and optimization data"
            }
        }
        
        for collection_id, config in collection_configs.items():
            try:
                collection = self.client.get_or_create_collection(
                    name=config["name"],
                    metadata=config["metadata"]
                )
                self.collections[collection_id] = collection
                logger.debug(f"Collection '{config['name']}' ready")
                
            except Exception as e:
                logger.error(f"Failed to create collection {config['name']}: {e}")
                raise
    
    async def _refresh_collection_stats(self):
        """Refresh statistics for all collections"""
        
        for collection_id, collection in self.collections.items():
            try:
                count = collection.count()
                self.collection_stats[collection_id] = {
                    "document_count": count,
                    "last_updated": time.time(),
                    "status": "healthy"
                }
            except Exception as e:
                self.collection_stats[collection_id] = {
                    "document_count": 0,
                    "last_updated": time.time(),
                    "status": f"error: {e}"
                }
    
    async def store_extraction_result(self, url: str, result: Dict[str, Any],
                                    strategy_name: str, purpose: str,
                                    processing_time: float = 0) -> bool:
        """Store successful extraction result for learning"""
        
        if not result.get("success", False):
            return False  # Only store successful extractions
        
        try:
            # Create comprehensive embedding text
            embedding_text = self._create_extraction_embedding_text(
                url, result, strategy_name, purpose
            )
            
            # Generate embedding
            embedding = await self._generate_embedding(embedding_text)
            
            # Create document metadata
            metadata = {
                "url": url,
                "purpose": purpose,
                "strategy": strategy_name,
                "success_rate": result.get("confidence", 0.8),
                "timestamp": time.time(),
                "processing_time": processing_time,
                "extracted_fields": list(result.get("extracted_data", {}).keys()),
                "data_quality": result.get("data_quality", "unknown"),
                "record_count": len(result.get("extracted_data", {}))
            }
            
            # Generate unique document ID
            document_id = f"extraction_{int(time.time())}_{hash(url) % 10000}"
            
            # Store in collection
            self.collections["extraction_results"].add(
                documents=[embedding_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[document_id]
            )
            
            logger.debug(f"Stored extraction result for {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store extraction result: {e}")
            return False
    
    async def store_strategy_learning(self, learning_data: Dict[str, Any]) -> bool:
        """Store strategy learning data for future optimization"""
        
        try:
            # Create strategy embedding text
            strategy_text = f"""
Website Type: {learning_data.get('website_type', 'unknown')}
Purpose: {learning_data.get('purpose', 'unknown')}
Strategy: {learning_data.get('strategy', 'unknown')}
Complexity: {learning_data.get('complexity', 'medium')}
Frameworks: {' '.join(learning_data.get('frameworks', []))}
Success Rate: {learning_data.get('success_rate', 0)}
Processing Time: {learning_data.get('processing_time', 0)}
Data Quality: {learning_data.get('data_quality', 'unknown')}
"""
            
            embedding = await self._generate_embedding(strategy_text)
            
            document_id = f"strategy_{int(time.time())}_{hash(learning_data.get('url', '')) % 10000}"
            
            self.collections["strategy_patterns"].add(
                documents=[strategy_text],
                embeddings=[embedding],
                metadatas=[learning_data],
                ids=[document_id]
            )
            
            logger.debug(f"Stored strategy learning for {learning_data.get('url', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store strategy learning: {e}")
            return False
    
    async def store_website_analysis(self, url: str, analysis: Dict[str, Any]) -> bool:
        """Store website analysis for future similar site detection"""
        
        try:
            analysis_text = f"""
URL: {url}
Website Type: {analysis.get('website_type', 'unknown')}
Content Patterns: {', '.join(analysis.get('content_patterns', []))}
Structure: {analysis.get('structure_analysis', '')}
Technology Stack: {', '.join(analysis.get('technologies', []))}
Complexity: {analysis.get('complexity', 'medium')}
"""
            
            embedding = await self._generate_embedding(analysis_text)
            
            metadata = {
                **analysis,
                "url": url,
                "timestamp": time.time(),
                "analysis_version": "1.0"
            }
            
            document_id = f"analysis_{int(time.time())}_{hash(url) % 10000}"
            
            self.collections["website_analysis"].add(
                documents=[analysis_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[document_id]
            )
            
            logger.debug(f"Stored website analysis for {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store website analysis: {e}")
            return False
    
    async def query_similar_strategies(self, website_type: str, purpose: str,
                                     complexity: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Query for similar successful strategies"""
        
        try:
            query_text = f"Strategy for {purpose} on {website_type} websites"
            if complexity:
                query_text += f" with {complexity} complexity"
            
            query_embedding = await self._generate_embedding(query_text)
            
            # Build where clause for filtering
            where_clause = {
                "$and": [
                    {"purpose": purpose},
                    {"success_rate": {"$gte": 0.7}}  # Only high-success strategies
                ]
            }
            
            if website_type:
                where_clause["$and"].append({"website_type": website_type})
            
            if complexity:
                where_clause["$and"].append({"complexity": complexity})
            
            results = self.collections["strategy_patterns"].query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )
            
            if results and results["metadatas"]:
                return results["metadatas"][0]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to query similar strategies: {e}")
            return []
    
    async def find_similar_websites(self, target_url: str, analysis: Dict[str, Any],
                                  limit: int = 5) -> List[SearchResult]:
        """Find websites with similar characteristics"""
        
        try:
            website_type = analysis.get("website_type", "unknown")
            patterns = analysis.get("content_patterns", [])
            
            query_text = f"Website type: {website_type}, patterns: {', '.join(patterns)}"
            query_embedding = await self._generate_embedding(query_text)
            
            results = self.collections["website_analysis"].query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"website_type": website_type}
            )
            
            search_results = []
            if results and results["documents"]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0], 
                    results["distances"][0]
                ):
                    search_results.append(SearchResult(
                        content=doc,
                        metadata=meta,
                        similarity=1 - dist,
                        collection="website_analysis"
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to find similar websites: {e}")
            return []
    
    async def semantic_search(self, query: str, collection_names: List[str] = None,
                            filters: Dict[str, Any] = None, limit: int = 10) -> List[SearchResult]:
        """Perform semantic search across collections"""
        
        try:
            query_embedding = await self._generate_embedding(query)
            all_results = []
            
            # Default to searching all collections if none specified
            collections_to_search = collection_names or list(self.collections.keys())
            
            for collection_name in collections_to_search:
                if collection_name not in self.collections:
                    continue
                
                try:
                    results = self.collections[collection_name].query(
                        query_embeddings=[query_embedding],
                        n_results=limit,
                        where=filters
                    )
                    
                    if results and results["documents"]:
                        for doc, meta, dist in zip(
                            results["documents"][0],
                            results["metadatas"][0],
                            results["distances"][0]
                        ):
                            all_results.append(SearchResult(
                                content=doc,
                                metadata=meta,
                                similarity=1 - dist,
                                collection=collection_name
                            ))
                            
                except Exception as e:
                    logger.warning(f"Search failed for collection {collection_name}: {e}")
                    continue
            
            # Sort by similarity and return top results
            all_results.sort(key=lambda x: x.similarity, reverse=True)
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def get_best_selectors(self, website_type: str, content_type: str,
                               min_success_rate: float = 0.8) -> List[str]:
        """Get the best CSS selectors for specific patterns"""
        
        try:
            query_text = f"CSS selectors for {content_type} on {website_type} websites"
            query_embedding = await self._generate_embedding(query_text)
            
            results = self.collections["learned_selectors"].query(
                query_embeddings=[query_embedding],
                n_results=10,
                where={
                    "$and": [
                        {"website_type": website_type},
                        {"content_type": content_type},
                        {"success_rate": {"$gte": min_success_rate}}
                    ]
                }
            )
            
            if results and results["metadatas"]:
                selectors = []
                for metadata in results["metadatas"][0]:
                    selectors.extend(metadata.get("selectors", []))
                
                # Return unique selectors sorted by success rate
                unique_selectors = list(set(selectors))
                return unique_selectors[:10]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get best selectors: {e}")
            return []
    
    async def store_successful_selectors(self, website_type: str, content_type: str,
                                       selectors: List[str], success_rate: float,
                                       context: Dict[str, Any] = None) -> bool:
        """Store CSS selectors that worked well"""
        
        try:
            selector_text = f"""
Content Type: {content_type}
Website Type: {website_type}
Selectors: {', '.join(selectors)}
Success Rate: {success_rate}
Context: {json.dumps(context or {}, indent=2)}
"""
            
            embedding = await self._generate_embedding(selector_text)
            
            metadata = {
                "website_type": website_type,
                "content_type": content_type,
                "selectors": selectors,
                "success_rate": success_rate,
                "timestamp": time.time(),
                "context": context or {}
            }
            
            document_id = f"selectors_{int(time.time())}_{hash(website_type + content_type) % 10000}"
            
            self.collections["learned_selectors"].add(
                documents=[selector_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[document_id]
            )
            
            logger.debug(f"Stored successful selectors for {website_type} - {content_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store selectors: {e}")
            return False
    
    async def log_performance_data(self, operation: str, metrics: Dict[str, Any]) -> bool:
        """Log performance data for optimization"""
        
        try:
            performance_text = f"""
Operation: {operation}
Processing Time: {metrics.get('processing_time', 0)}
Success Rate: {metrics.get('success_rate', 0)}
Strategy Used: {metrics.get('strategy', 'unknown')}
Data Quality: {metrics.get('data_quality', 'unknown')}
Metrics: {json.dumps(metrics, indent=2)}
"""
            
            embedding = await self._generate_embedding(performance_text)
            
            metadata = {
                **metrics,
                "operation": operation,
                "timestamp": time.time()
            }
            
            document_id = f"perf_{int(time.time())}_{hash(operation) % 10000}"
            
            self.collections["performance_logs"].add(
                documents=[performance_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[document_id]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log performance data: {e}")
            return False
    
    def _create_extraction_embedding_text(self, url: str, result: Dict[str, Any],
                                        strategy: str, purpose: str) -> str:
        """Create comprehensive text for extraction result embedding"""
        
        extracted_data = result.get("extracted_data", {})
        
        text_parts = [
            f"URL: {url}",
            f"Purpose: {purpose}",
            f"Strategy: {strategy}",
            f"Success: {result.get('success', False)}",
            f"Confidence: {result.get('confidence', 0)}",
            f"Processing Time: {result.get('processing_time', 0)}",
            f"Data Quality: {result.get('data_quality', 'unknown')}",
            f"Record Count: {len(extracted_data)}",
            f"Fields Extracted: {', '.join(extracted_data.keys())}",
            f"Sample Data: {json.dumps(extracted_data, indent=2)[:1000]}"  # First 1000 chars
        ]
        
        return "\n".join(text_parts)
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using LLM service or fallback method"""
        
        if self.llm_service:
            try:
                embedding = await self.llm_service.embeddings(text)
                if embedding:
                    return embedding
            except Exception as e:
                logger.warning(f"LLM embedding failed, using fallback: {e}")
        
        # Fallback: deterministic hash-based embedding
        return self._create_hash_embedding(text)
    
    def _create_hash_embedding(self, text: str) -> List[float]:
        """Create a deterministic hash-based embedding"""
        
        # Create multiple hash variations for better distribution
        hashes = []
        for i in range(3):
            hash_input = f"{text}_{i}"
            hash_obj = hashlib.sha256(hash_input.encode())
            hashes.append(hash_obj.digest())
        
        # Convert to float vector
        embedding = []
        for hash_bytes in hashes:
            for i in range(0, len(hash_bytes), 4):
                if i + 4 <= len(hash_bytes):
                    chunk = hash_bytes[i:i+4]
                    try:
                        float_val = struct.unpack('f', chunk)[0]
                        # Normalize to [-1, 1] range
                        float_val = max(-1.0, min(1.0, float_val / 1e10))
                        embedding.append(float_val)
                    except struct.error:
                        embedding.append(0.0)
        
        # Ensure consistent dimension
        target_dim = self.config.embedding_dimension
        if len(embedding) < target_dim:
            embedding.extend([0.0] * (target_dim - len(embedding)))
        
        return embedding[:target_dim]
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        
        await self._refresh_collection_stats()
        
        total_documents = sum(
            stats.get("document_count", 0) 
            for stats in self.collection_stats.values()
        )
        
        return {
            "collections": self.collection_stats,
            "total_documents": total_documents,
            "client_type": "HTTP" if "HttpClient" in str(type(self.client)) else "Persistent",
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "persistent_path": self.config.persistent_path,
                "collection_prefix": self.config.collection_prefix
            },
            "service_health": "healthy" if self.client else "disconnected"
        }
    
    async def optimize_collections(self) -> Dict[str, Any]:
        """Optimize collections by removing old or redundant data"""
        
        optimization_results = {}
        
        for collection_name, collection in self.collections.items():
            try:
                initial_count = collection.count()
                
                # For now, just log the count - actual optimization would depend on use case
                optimization_results[collection_name] = {
                    "initial_count": initial_count,
                    "status": "analyzed"
                }
                
                logger.info(f"Collection {collection_name}: {initial_count} documents")
                
            except Exception as e:
                optimization_results[collection_name] = {
                    "status": f"error: {e}"
                }
        
        return optimization_results
    
    async def cleanup(self):
        """Clean up resources"""
        # ChromaDB client doesn't require explicit cleanup
        logger.info("Vector service cleanup completed")
