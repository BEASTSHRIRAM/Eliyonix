"""
Qdrant Vector Database Integration
Stores sensor data with structured embeddings for AI recommendations
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
import hashlib
import math

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Collection names
SENSOR_DATA_COLLECTION = "sensor_readings"
FAULT_HISTORY_COLLECTION = "fault_history"


class QdrantStore:
    """Manages sensor data in Qdrant with structured embeddings"""
    
    def __init__(self):
        """Initialize Qdrant client"""
        if not QDRANT_URL:
            logger.warning("QDRANT_URL not found - using mock mode")
            self.client = None
            self.mock_mode = True
            return
        
        try:
            logger.info(f"Connecting to Qdrant at {QDRANT_URL}...")
            
            # Handle local vs cloud
            if "localhost" in QDRANT_URL or "127.0.0.1" in QDRANT_URL:
                self.client = QdrantClient(url=QDRANT_URL, timeout=30, prefer_grpc=False)
            else:
                self.client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=30,
                    prefer_grpc=False,
                    https=True,
                )
            
            collections = self.client.get_collections()
            logger.info(f"✓ Connected! Found {len(collections.collections)} collections")
            
            self.mock_mode = False
            self._initialize_collections()
            
        except Exception as e:
            logger.error(f"✗ Qdrant connection failed: {e}")
            logger.warning("Using mock mode")
            self.client = None
            self.mock_mode = True
    
    def _initialize_collections(self):
        """Create collections with 8D embeddings and payload indexes"""
        if self.mock_mode:
            return
        
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            
            # Sensor readings: 8D [V, I, T, LDR, hour_sin, hour_cos, dow_sin, dow_cos]
            if SENSOR_DATA_COLLECTION not in collections:
                self.client.create_collection(
                    collection_name=SENSOR_DATA_COLLECTION,
                    vectors_config=VectorParams(size=8, distance=Distance.COSINE),
                )
                logger.info(f"✓ Created {SENSOR_DATA_COLLECTION} (8D embeddings)")
            
            # Create payload indexes for filtering
            try:
                self.client.create_payload_index(
                    collection_name=SENSOR_DATA_COLLECTION,
                    field_name="village_id",
                    field_schema="keyword"
                )
                logger.info(f"✓ Created index on village_id for {SENSOR_DATA_COLLECTION}")
            except Exception as e:
                # Index might already exist
                logger.debug(f"Index creation skipped: {e}")
            
            # Fault history: 8D [V, I, T, LDR, score, hour_sin, hour_cos, fault_type]
            if FAULT_HISTORY_COLLECTION not in collections:
                self.client.create_collection(
                    collection_name=FAULT_HISTORY_COLLECTION,
                    vectors_config=VectorParams(size=8, distance=Distance.COSINE),
                )
                logger.info(f"✓ Created {FAULT_HISTORY_COLLECTION} (8D embeddings)")
            
            # Create payload indexes for fault history
            try:
                self.client.create_payload_index(
                    collection_name=FAULT_HISTORY_COLLECTION,
                    field_name="village_id",
                    field_schema="keyword"
                )
                logger.info(f"✓ Created index on village_id for {FAULT_HISTORY_COLLECTION}")
            except Exception as e:
                logger.debug(f"Index creation skipped: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing collections: {e}")
    
    def _create_embedding(self, sensor_data: Dict, anomaly_score: float = 0, fault_type: str = None) -> List[float]:
        """Create 8D embedding with cyclic time encoding"""
        dt = datetime.fromtimestamp(sensor_data.get("timestamp", datetime.now().timestamp()))
        
        # Normalize sensors
        v_norm = float(sensor_data.get("voltage", 415)) / 500.0
        i_norm = float(sensor_data.get("current", 8)) / 20.0
        t_norm = float(sensor_data.get("temperature", 32)) / 100.0
        ldr_norm = float(sensor_data.get("ldr", 800)) / 1024.0
        
        # Cyclic time (captures periodicity)
        hour_sin = math.sin(2 * math.pi * dt.hour / 24)
        hour_cos = math.cos(2 * math.pi * dt.hour / 24)
        dow_sin = math.sin(2 * math.pi * dt.weekday() / 7)
        dow_cos = math.cos(2 * math.pi * dt.weekday() / 7)
        
        if fault_type:
            # Fault embedding: replace dow with fault_type encoding
            fault_map = {"inverter_overvoltage": 0.2, "inverter_undervoltage": 0.4, 
                        "inverter_overtemp": 0.6, "inverter_undertemp": 0.8,
                        "inverter_overcurrent": 1.0, "inverter_fault": 0.1}
            return [v_norm, i_norm, t_norm, ldr_norm, anomaly_score, hour_sin, hour_cos, fault_map.get(fault_type, 0)]
        
        return [v_norm, i_norm, t_norm, ldr_norm, hour_sin, hour_cos, dow_sin, dow_cos]
    
    async def store_sensor_reading(self, sensor_data: Dict, anomaly_score: float, fault_detected: bool, fault_type: Optional[str] = None) -> bool:
        """Store every sensor reading with structured embedding"""
        if self.mock_mode:
            logger.debug(f"Mock: logged reading (fault={fault_detected})")
            return True
        
        try:
            dt = datetime.fromtimestamp(sensor_data.get("timestamp", datetime.now().timestamp()))
            vector = self._create_embedding(sensor_data)
            
            # Unique ID
            id_str = f"{sensor_data.get('timestamp')}_{sensor_data.get('village_id')}_{sensor_data.get('inverter_id')}"
            point_id = int(hashlib.md5(id_str.encode()).hexdigest()[:15], 16)
            
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "voltage": float(sensor_data.get("voltage", 0)),
                    "current": float(sensor_data.get("current", 0)),
                    "temperature": float(sensor_data.get("temperature", 0)),
                    "ldr": int(sensor_data.get("ldr", 0)),
                    "timestamp": sensor_data.get("timestamp"),
                    "datetime": dt.isoformat(),
                    "inverter_id": sensor_data.get("inverter_id"),
                    "village_id": sensor_data.get("village_id"),
                    "hour": dt.hour,
                    "day_of_week": dt.weekday(),
                    "date": dt.strftime("%Y-%m-%d"),
                    "anomaly_score": float(anomaly_score),
                    "fault_detected": fault_detected,
                    "fault_type": fault_type,
                    "power_kw": float(sensor_data.get("voltage", 0)) * float(sensor_data.get("current", 0)) / 1000,
                }
            )
            
            self.client.upsert(collection_name=SENSOR_DATA_COLLECTION, points=[point])
            logger.info(f"✓ Stored: {sensor_data.get('village_id')} at {dt.strftime('%H:%M:%S')} (fault={fault_detected})")
            return True
            
        except Exception as e:
            logger.warning(f"Store failed: {e}")
            return False
    
    async def store_fault_event(self, sensor_data: Dict, anomaly_score: float, fault_type: str, should_alert: bool, alert_message: Optional[str] = None) -> bool:
        """Store fault events for pattern learning"""
        if self.mock_mode:
            logger.debug(f"Mock: logged fault ({fault_type})")
            return True
        
        try:
            dt = datetime.fromtimestamp(sensor_data.get("timestamp", datetime.now().timestamp()))
            vector = self._create_embedding(sensor_data, anomaly_score, fault_type)
            
            id_str = f"fault_{sensor_data.get('timestamp')}_{fault_type}"
            point_id = int(hashlib.md5(id_str.encode()).hexdigest()[:15], 16)
            
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "voltage": float(sensor_data.get("voltage", 0)),
                    "current": float(sensor_data.get("current", 0)),
                    "temperature": float(sensor_data.get("temperature", 0)),
                    "ldr": int(sensor_data.get("ldr", 0)),
                    "timestamp": sensor_data.get("timestamp"),
                    "datetime": dt.isoformat(),
                    "village_id": sensor_data.get("village_id"),
                    "inverter_id": sensor_data.get("inverter_id"),
                    "anomaly_score": float(anomaly_score),
                    "fault_type": fault_type,
                    "should_alert": should_alert,
                    "alert_message": alert_message,
                    "date": dt.strftime("%Y-%m-%d"),
                }
            )
            
            self.client.upsert(collection_name=FAULT_HISTORY_COLLECTION, points=[point])
            logger.info(f"✓ Stored fault: {fault_type} (alert={should_alert})")
            return True
            
        except Exception as e:
            logger.warning(f"Fault store failed: {e}")
            return False
    
    async def get_historical_data(self, village_id: str, days: int = 7) -> List[Dict]:
        """Get last N days of data for AI recommendations"""
        if self.mock_mode:
            return []
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).timestamp()
            
            # Scroll without filter (get all data, then filter in Python)
            # This avoids the index requirement issue
            results = self.client.scroll(
                collection_name=SENSOR_DATA_COLLECTION,
                limit=1000,
                with_payload=True,
            )
            
            # Filter by village_id and timestamp in Python
            data = []
            for point in results[0]:
                payload = point.payload
                if (payload.get("village_id") == village_id and 
                    payload.get("timestamp", 0) >= cutoff):
                    data.append(payload)
            
            logger.info(f"Retrieved {len(data)} readings for {village_id} (last {days} days)")
            return data
            
        except Exception as e:
            logger.error(f"Historical data fetch failed: {e}")
            return []


# Global instance
_qdrant_store: Optional[QdrantStore] = None

def get_qdrant_store() -> QdrantStore:
    global _qdrant_store
    if _qdrant_store is None:
        _qdrant_store = QdrantStore()
    return _qdrant_store

def reset_qdrant_store():
    global _qdrant_store
    _qdrant_store = None
