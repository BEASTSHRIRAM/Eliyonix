"""
Agent Memory Management
Handles persistence and loading of agent memory from storage
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
from .grid_state import AgentMemory, BaselineMetrics, AnomalyRecord, AlertRecord
import logging

logger = logging.getLogger(__name__)


class MemoryStore:
    """Abstract base class for memory storage backends"""
    
    async def save_agent_memory(self, agent_name: str, memory: Dict[str, Any]) -> bool:
        """Save agent memory to storage"""
        raise NotImplementedError
    
    async def load_agent_memory(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Load agent memory from storage"""
        raise NotImplementedError


class InMemoryStore(MemoryStore):
    """In-memory storage for development/testing"""
    
    def __init__(self):
        self.storage: Dict[str, Dict[str, Any]] = {}
    
    async def save_agent_memory(self, agent_name: str, memory: Dict[str, Any]) -> bool:
        """Save agent memory"""
        self.storage[agent_name] = memory
        logger.info(f"Saved memory for {agent_name}")
        return True
    
    async def load_agent_memory(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Load agent memory"""
        memory = self.storage.get(agent_name)
        if memory:
            logger.info(f"Loaded memory for {agent_name}")
        return memory
    
    def clear(self):
        """Clear all storage"""
        self.storage.clear()


class RDSMemoryStore(MemoryStore):
    """RDS-based memory storage (PostgreSQL via psycopg2)"""
    
    def __init__(self, connection_string: str):
        """
        Initialize RDS memory store
        connection_string: "postgresql://user:password@host:5432/dbname"
        """
        self.connection_string = connection_string
        self._init_tables()
    
    def _init_tables(self):
        """Initialize database tables (would connect to RDS)"""
        # This would be implemented with actual psycopg2 connection
        # CREATE TABLE agent_memory (
        #     agent_name VARCHAR(255) PRIMARY KEY,
        #     memory_json JSONB,
        #     last_updated TIMESTAMP
        # );
        pass
    
    async def save_agent_memory(self, agent_name: str, memory: Dict[str, Any]) -> bool:
        """Save agent memory to RDS"""
        try:
            # In production: UPDATE agent_memory SET memory_json = $1, last_updated = NOW()
            logger.info(f"Saved memory for {agent_name} to RDS")
            return True
        except Exception as e:
            logger.error(f"Error saving memory for {agent_name}: {e}")
            return False
    
    async def load_agent_memory(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Load agent memory from RDS"""
        try:
            # In production: SELECT memory_json FROM agent_memory WHERE agent_name = $1
            logger.info(f"Loaded memory for {agent_name} from RDS")
            return None  # Placeholder
        except Exception as e:
            logger.error(f"Error loading memory for {agent_name}: {e}")
            return None


# Global memory store instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """Get or create the global memory store"""
    global _memory_store
    if _memory_store is None:
        _memory_store = InMemoryStore()
    return _memory_store


def set_memory_store(store: MemoryStore):
    """Set a custom memory store"""
    global _memory_store
    _memory_store = store


# Helper functions for memory operations

async def initialize_agent_memory(agent_name: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize memory for an agent if not exists"""
    store = get_memory_store()
    existing = await store.load_agent_memory(agent_name)
    
    if existing:
        return existing
    
    # Create initial memory
    memory = {
        "agent_name": agent_name,
        "baseline_metrics": initial_state.get("baseline_metrics"),
        "anomaly_history": [],
        "forecast_history": [],
        "alerts_sent": [],
        "learned_patterns": {},
        "last_updated": datetime.now().timestamp(),
    }
    
    await store.save_agent_memory(agent_name, memory)
    return memory


async def update_agent_memory(agent_name: str, updates: Dict[str, Any]):
    """Update agent memory with new data"""
    store = get_memory_store()
    memory = await store.load_agent_memory(agent_name) or {}
    
    memory.update(updates)
    memory["last_updated"] = datetime.now().timestamp()
    
    await store.save_agent_memory(agent_name, memory)


async def append_to_memory_list(agent_name: str, list_key: str, item: Dict[str, Any]):
    """Append item to a list in agent memory"""
    store = get_memory_store()
    memory = await store.load_agent_memory(agent_name) or {}
    
    if list_key not in memory:
        memory[list_key] = []
    
    memory[list_key].append(item)
    
    # Keep only last 100 items to prevent unbounded growth
    if len(memory[list_key]) > 100:
        memory[list_key] = memory[list_key][-100:]
    
    memory["last_updated"] = datetime.now().timestamp()
    await store.save_agent_memory(agent_name, memory)


# Default initial memory structures

def get_fault_detector_initial_memory() -> Dict[str, Any]:
    """Get initial memory structure for Fault Detector"""
    return {
        "baseline_metrics": {
            "voltage_mean": 415.0,
            "voltage_std": 2.5,
            "current_mean": 8.0,
            "current_std": 1.0,
            "temp_mean": 32.0,
            "temp_std": 2.0,
        },
        "anomaly_history": [],
        "learned_patterns": {
            "afternoon_overvoltage_normal": True,
            "monsoon_dropout_expected": True,
        },
    }


def get_load_forecaster_initial_memory() -> Dict[str, Any]:
    """Get initial memory structure for Load Forecaster"""
    return {
        "baseline_metrics": {
            "demand_mean": 3.5,
            "demand_std": 0.8,
        },
        "forecast_history": [],
        "learned_patterns": {
            "morning_peak_hour": 8,
            "afternoon_peak_hour": 14,
            "evening_peak_hour": 19,
        },
    }


def get_alert_dispatcher_initial_memory() -> Dict[str, Any]:
    """Get initial memory structure for Alert Dispatcher"""
    return {
        "alerts_sent": [],
        "non_alerts": [],
        "false_alarm_rate": 0.0,
        "technician_response_time": [],  # in seconds
        "alert_effectiveness": {
            "prevented_outages": 0,
            "false_alarms": 0,
            "pending_confirmation": 0,
        },
    }
