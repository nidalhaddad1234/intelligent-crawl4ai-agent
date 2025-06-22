#!/usr/bin/env python3
"""
ChromaDB Manager
Manages vector storage for learning and pattern recognition
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import time

import chromadb
from chromadb.config import Settings

logger = logging.getLogger("chromadb_manager")

class ChromaDBManager:
    """Manages ChromaDB for intelligent pattern storage and retrieval"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.client = None
        self.collections = {}
        
    async def initialize(self):
        """Initialize ChromaDB client and collections"""
        
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(allow_reset=True)
            )
            
            # Create collections for different data types
            await self._create_collections()
            
            logger.info(f"ChromaDB initialized successfully at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def _create_collections(self):
        """Create necessary collections for the intelligent agent"""
        
        collection_configs = {
            "extraction_results": {
                "name": "extraction_results",
                "metadata": {"hnsw:space": "cosine"},
                "description": "Stores successful extraction results with embeddings"
            },
            "strategy_patterns": {
                "name": "strategy_patterns", 
                "metadata": {"hnsw:space": "cosine"},
                "description": "Stores successful extraction strategies and patterns"
            },
            "website_analysis": {
                "name": "website_analysis",
                "metadata": {"hnsw:space": "cosine"},
                "description": "Stores website analysis results for similar site detection"
            },
            "learned_selectors": {
                "name": "learned_selectors",
                "metadata": {"hnsw:space": "cosine"},
                "description": "Stores CSS selectors that worked well for specific patterns"
            }
        }
        
        for collection_id, config in collection_configs.items():
            try:
                collection = self.client.get_or_create_collection(
                    name=config["name"],
                    metadata=config["metadata"]
                )
                self.collections[collection_id] = collection
                logger.info(f"Collection '{config['name']}' ready")
                
            except Exception as e:
                logger.warning(f"Failed to create collection {config['name']}: {e}")
    
    async def store_extraction_result(self, url: str, result: Dict[str, Any], 
                                    strategy: Any, purpose: str):
        """Store successful extraction result for learning"""
        
        if not result.get("success", False):
            return  # Only store successful extractions
        
        try:
            # Create embedding text from the extraction
            embedding_text = self._create_embedding_text(url, result, strategy, purpose)
            
            # Generate embedding (placeholder - would use actual embedding model)
            embedding = await self._generate_embedding(embedding_text)
            
            # Store in extraction_results collection
            document_id = f"extraction_{int(time.time())}_{hash(url) % 10000}"
            
            self.collections["extraction_results"].add(
                documents=[embedding_text],
                embeddings=[embedding],
                metadatas=[{
                    "url": url,
                    "purpose": purpose,
                    "strategy": strategy.primary_strategy,
                    "success_rate": strategy.estimated_success_rate,
                    "timestamp": time.time(),
                    "extracted_fields": list(result.get("extracted_data", {}).keys())
                }],
                ids=[document_id]
            )
            
            logger.debug(f"Stored extraction result for {url}")
            
        except Exception as e:
            logger.error(f"Failed to store extraction result: {e}")
    
    async def store_strategy_learning(self, learning_data: Dict[str, Any]):
        """Store strategy learning data for future optimization"""
        
        try:
            # Create embedding text for strategy pattern
            strategy_text = f"""
            Website: {learning_data['website_type']} 
            Purpose: {learning_data['purpose']}
            Strategy: {learning_data['strategy']}
            Complexity: {learning_data['complexity']}
            Frameworks: {' '.join(learning_data.get('frameworks', []))}
            Success Rate: {learning_data['success_rate']}
            """
            
            embedding = await self._generate_embedding(strategy_text)
            
            document_id = f"strategy_{int(time.time())}_{hash(learning_data['url']) % 10000}"
            
            self.collections["strategy_patterns"].add(
                documents=[strategy_text],
                embeddings=[embedding],
                metadatas=[learning_data],
                ids=[document_id]
            )
            
            logger.debug(f"Stored strategy learning for {learning_data['url']}")
            
        except Exception as e:
            logger.error(f"Failed to store strategy learning: {e}")
    
    async def query_similar_strategies(self, query_text: str, website_type: str, 
                                     purpose: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query for similar successful strategies"""
        
        try:
            query_embedding = await self._generate_embedding(query_text)
            
            results = self.collections["strategy_patterns"].query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={
                    "$and": [
                        {"website_type": website_type},
                        {"purpose": purpose},
                        {"success_rate": {"$gte": 0.7}}  # Only high-success strategies
                    ]
                }
            )
            
            if results and results["metadatas"]:
                return results["metadatas"][0]  # Return first result set
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to query similar strategies: {e}")
            return []
    
    async def semantic_search(self, query: str, data_type: str = None, 
                            limit: int = 10) -> Dict[str, Any]:
        """Perform semantic search on stored extraction results"""
        
        try:
            query_embedding = await self._generate_embedding(query)
            
            # Search in extraction results
            search_filters = {}
            if data_type:
                search_filters["purpose"] = data_type
            
            results = self.collections["extraction_results"].query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=search_filters if search_filters else None
            )
            
            if results and results["documents"]:
                return {
                    "query": query,
                    "results_count": len(results["documents"][0]),
                    "results": [
                        {
                            "content": doc,
                            "metadata": meta,
                            "similarity": 1 - dist  # Convert distance to similarity
                        }
                        for doc, meta, dist in zip(
                            results["documents"][0],
                            results["metadatas"][0],
                            results["distances"][0]
                        )
                    ]
                }
            
            return {"query": query, "results_count": 0, "results": []}
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"error": str(e)}
    
    async def get_best_selectors(self, website_type: str, content_type: str) -> List[str]:
        """Get the best CSS selectors for a specific website and content type"""
        
        try:
            query_text = f"CSS selectors for {content_type} on {website_type} websites"
            query_embedding = await self._generate_embedding(query_text)
            
            results = self.collections["learned_selectors"].query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={
                    "$and": [
                        {"website_type": website_type},
                        {"content_type": content_type},
                        {"success_rate": {"$gte": 0.8}}
                    ]
                }
            )
            
            if results and results["metadatas"]:
                selectors = []
                for metadata in results["metadatas"][0]:
                    selectors.extend(metadata.get("selectors", []))
                
                # Return unique selectors sorted by success rate
                unique_selectors = list(set(selectors))
                return unique_selectors[:10]  # Top 10 selectors
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get best selectors: {e}")
            return []
    
    async def store_successful_selectors(self, website_type: str, content_type: str,
                                       selectors: List[str], success_rate: float):
        """Store CSS selectors that worked well"""
        
        try:
            selector_text = f"CSS selectors for {content_type}: {', '.join(selectors)}"
            embedding = await self._generate_embedding(selector_text)
            
            document_id = f"selectors_{int(time.time())}_{hash(website_type + content_type) % 10000}"
            
            self.collections["learned_selectors"].add(
                documents=[selector_text],
                embeddings=[embedding],
                metadatas=[{
                    "website_type": website_type,
                    "content_type": content_type,
                    "selectors": selectors,
                    "success_rate": success_rate,
                    "timestamp": time.time()
                }],
                ids=[document_id]
            )
            
            logger.debug(f"Stored successful selectors for {website_type} - {content_type}")
            
        except Exception as e:
            logger.error(f"Failed to store selectors: {e}")
    
    def _create_embedding_text(self, url: str, result: Dict[str, Any], 
                              strategy: Any, purpose: str) -> str:
        """Create text representation for embedding"""
        
        extracted_data = result.get("extracted_data", {})
        
        # Create comprehensive text for embedding
        text_parts = [
            f"URL: {url}",
            f"Purpose: {purpose}",
            f"Strategy: {strategy.primary_strategy}",
            f"Data extracted: {json.dumps(extracted_data, indent=2)}"
        ]
        
        if hasattr(strategy, 'reasoning'):
            text_parts.append(f"Strategy reasoning: {strategy.reasoning}")
        
        return "\n".join(text_parts)
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (placeholder implementation)"""
        
        # TODO: Integrate with actual embedding model (Ollama nomic-embed-text)
        # For now, return a simple hash-based embedding
        
        import hashlib
        import struct
        
        # Create a simple hash-based embedding (384 dimensions)
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float vector
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            if i + 4 <= len(hash_bytes):
                chunk = hash_bytes[i:i+4]
                float_val = struct.unpack('f', chunk)[0] if len(chunk) == 4 else 0.0
                embedding.append(float_val)
        
        # Normalize to 384 dimensions
        while len(embedding) < 384:
            embedding.append(0.0)
        
        return embedding[:384]
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        
        stats = {}
        
        for collection_name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[collection_name] = {
                    "document_count": count,
                    "status": "healthy"
                }
            except Exception as e:
                stats[collection_name] = {
                    "document_count": 0,
                    "status": f"error: {e}"
                }
        
        return {
            "collections": stats,
            "total_documents": sum(s.get("document_count", 0) for s in stats.values()),
            "chromadb_host": self.host,
            "chromadb_port": self.port
        }
