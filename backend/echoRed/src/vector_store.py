"""
Vector Database for storing and retrieving sensor snapshots with embeddings
Used by RecommendationAgent for RAG (Retrieval Augmented Generation)
"""
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class SimpleEmbedding:
    """Simple embedding generator for sensor data (not production-grade)"""
    
    @staticmethod
    def embed_snapshot(snapshot: Dict[str, Any]) -> np.ndarray:
        """
        Convert a sensor snapshot into a 768-dimensional embedding vector
        In production, use: OpenAI, Bedrock Titan Embeddings, or similar
        """
        # Create normalized features from snapshot
        features = []
        
        # Voltage features (normalize to 0-1)
        v = snapshot.get('voltage', 415)
        features.extend([
            (v - 300) / 500,  # voltage normalized
            abs(v - 415) / 100,  # voltage deviation from baseline
        ])
        
        # Current features
        i = snapshot.get('current', 8)
        features.extend([
            i / 15,  # current normalized
            abs(i - 8) / 5,  # current deviation
        ])
        
        # Temperature features
        t = snapshot.get('temperature', 30)
        features.extend([
            (t - 0) / 60,  # temperature normalized
            abs(t - 30) / 15,  # temperature deviation
        ])
        
        # LDR (light) features
        ldr = snapshot.get('ldr', 800)
        features.extend([
            ldr / 1024,  # ldr normalized
            abs(ldr - 800) / 200,  # ldr deviation
        ])
        
        # Power output
        kw = snapshot.get('kw', 3.0)
        features.extend([
            kw / 5,  # power normalized
            abs(kw - 3) / 2,  # power deviation
        ])
        
        # Efficiency
        eff = snapshot.get('efficiency', 90)
        features.extend([
            eff / 100,  # efficiency normalized
            abs(eff - 90) / 15,  # efficiency deviation
        ])
        
        # Fault score
        fault_score = snapshot.get('fault_score', 0.02)
        features.extend([
            fault_score,
            fault_score ** 2,  # non-linear fault indicator
        ])
        
        # Time-of-day features (sine/cosine encoding)
        timestamp = snapshot.get('timestamp', datetime.now().isoformat())
        if isinstance(timestamp, str):
            hour = datetime.fromisoformat(timestamp).hour
        elif isinstance(timestamp, (int, float)):
            hour = datetime.fromtimestamp(timestamp).hour
        else:
            hour = datetime.now().hour
        
        features.extend([
            np.sin(2 * np.pi * hour / 24),
            np.cos(2 * np.pi * hour / 24),
        ])
        
        # Pad to 768 dimensions with repeated cyclic patterns
        base_features = np.array(features, dtype=np.float32)
        embedding = np.zeros(768, dtype=np.float32)
        
        # Fill with repeated base features and their transformations
        for i in range(768):
            idx = i % len(base_features)
            embedding[i] = base_features[idx] * np.sin((i + 1) / 768 * 2 * np.pi)
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding


class VectorStore:
    """In-memory vector store with time-windowed retrieval"""
    
    def __init__(self, retention_days: int = 7):
        """
        Initialize vector store
        
        Args:
            retention_days: Keep documents for last N days (default: 7)
        """
        self.retention_days = retention_days
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Dict[str, np.ndarray] = {}  # doc_id -> embedding
        self.index_by_component: Dict[str, List[str]] = defaultdict(list)  # component -> [doc_ids]
    
    def add_document(self, document: Dict[str, Any]) -> str:
        """
        Add a document (recommendation record) to the vector store
        
        Args:
            document: Document with keys: timestamp, component, sensor_snapshot,
                     recommendation_text, confidence, status, embedding (optional)
        
        Returns:
            Document ID (hash of content)
        """
        # Generate doc ID
        doc_content = json.dumps(document, sort_keys=True, default=str)
        doc_id = hashlib.md5(doc_content.encode()).hexdigest()[:16]
        
        # Generate embedding if not provided
        if 'embedding' not in document:
            sensor_snapshot = document.get('sensor_snapshot', {})
            embedding = SimpleEmbedding.embed_snapshot(sensor_snapshot)
            document['embedding'] = embedding.tolist()  # Store as list for JSON serialization
        else:
            embedding = np.array(document['embedding'])
        
        # Store document
        document['doc_id'] = doc_id
        document['inserted_at'] = datetime.now().isoformat()
        self.documents.append(document)
        self.embeddings[doc_id] = embedding
        
        # Index by component
        component = document.get('component', 'unknown')
        self.index_by_component[component].append(doc_id)
        
        logger.info(f"Added document {doc_id} for component {component}")
        return doc_id
    
    def retrieve_similar(
        self,
        query_snapshot: Dict[str, Any],
        component: str,
        top_k: int = 3,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-K similar historical snapshots for a component
        
        Args:
            query_snapshot: Current sensor snapshot to find similar historical events
            component: Component name to filter by ("solar", "fault", "forecast", etc.)
            top_k: Number of similar documents to return
            similarity_threshold: Minimum cosine similarity to return
        
        Returns:
            List of similar documents, sorted by similarity (descending)
        """
        # Generate query embedding
        query_embedding = SimpleEmbedding.embed_snapshot(query_snapshot)
        
        # Get doc IDs for this component
        relevant_doc_ids = self.index_by_component.get(component, [])
        
        if not relevant_doc_ids:
            logger.warning(f"No historical documents for component: {component}")
            return []
        
        # Calculate similarities and filter by age
        similarities = []
        cutoff_time = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        
        for doc_id in relevant_doc_ids:
            doc = next((d for d in self.documents if d.get('doc_id') == doc_id), None)
            if not doc:
                continue
            
            # Check age
            doc_timestamp = doc.get('timestamp', '')
            if doc_timestamp < cutoff_time:
                continue  # Skip old documents
            
            # Calculate cosine similarity
            doc_embedding = np.array(doc['embedding'])
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding) + 1e-8
            )
            
            if similarity >= similarity_threshold:
                similarities.append((doc, similarity))
        
        # Sort by similarity and return top-K
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = [
            {**doc, 'similarity_score': float(sim)}
            for doc, sim in similarities[:top_k]
        ]
        
        logger.info(f"Retrieved {len(results)} similar documents for {component}")
        return results
    
    def cleanup_old_documents(self) -> int:
        """Remove documents older than retention_days"""
        cutoff_time = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        initial_count = len(self.documents)
        
        self.documents = [
            doc for doc in self.documents
            if doc.get('timestamp', '') >= cutoff_time
        ]
        
        # Rebuild index
        self.embeddings = {}
        self.index_by_component = defaultdict(list)
        for doc in self.documents:
            doc_id = doc.get('doc_id')
            if doc_id:
                self.embeddings[doc_id] = np.array(doc['embedding'])
                component = doc.get('component', 'unknown')
                self.index_by_component[component].append(doc_id)
        
        removed_count = initial_count - len(self.documents)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old documents from vector store")
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_documents': len(self.documents),
            'documents_by_component': {
                component: len(doc_ids)
                for component, doc_ids in self.index_by_component.items()
            },
            'retention_days': self.retention_days,
            'oldest_document': min(
                (doc.get('timestamp', '') for doc in self.documents),
                default=None
            ),
            'newest_document': max(
                (doc.get('timestamp', '') for doc in self.documents),
                default=None
            ),
        }


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store(retention_days: int = 7) -> VectorStore:
    """Get or create global vector store"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(retention_days=retention_days)
    return _vector_store


def reset_vector_store() -> None:
    """Reset global vector store (for testing)"""
    global _vector_store
    _vector_store = None
