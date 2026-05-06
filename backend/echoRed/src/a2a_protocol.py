"""
Agent-to-Agent (A2A) Communication Protocol
Handles inter-agent messaging with timeout and deduplication
"""
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .grid_state import A2AMessage
import logging

logger = logging.getLogger(__name__)


class A2AMessageBroker:
    """In-memory message broker for agent-to-agent communication"""
    
    def __init__(self, timeout_seconds: int = 5):
        self.timeout_seconds = timeout_seconds
        self.message_queue: Dict[str, List[A2AMessage]] = {}  # agent_name -> [messages]
        self.processed_message_ids: set = set()  # Prevent duplicates
        self.pending_responses: Dict[str, asyncio.Event] = {}  # message_id -> Event
        
    async def send_message(self, message: A2AMessage) -> str:
        """Send a message from one agent to another"""
        message_id = message.get("message_id", str(uuid.uuid4()))
        message["message_id"] = message_id
        
        # Deduplication check
        if message_id in self.processed_message_ids:
            logger.warning(f"Duplicate message {message_id} ignored")
            return message_id
        
        to_agent = message["to_agent"]
        
        # Create queue for agent if not exists
        if to_agent not in self.message_queue:
            self.message_queue[to_agent] = []
        
        self.message_queue[to_agent].append(message)
        logger.info(f"A2A Message {message_id}: {message['from_agent']} -> {to_agent}")
        
        return message_id
    
    async def receive_messages(self, agent_name: str) -> List[A2AMessage]:
        """Receive all pending messages for an agent"""
        messages = self.message_queue.get(agent_name, [])
        self.message_queue[agent_name] = []
        
        for msg in messages:
            self.processed_message_ids.add(msg["message_id"])
        
        return messages
    
    async def wait_for_response(self, message_id: str, timeout: Optional[int] = None) -> Optional[A2AMessage]:
        """Wait for a response to a message (for request-reply patterns)"""
        timeout = timeout or self.timeout_seconds
        event = asyncio.Event()
        self.pending_responses[message_id] = event
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            # Response received (would be set by responding agent)
            return None  # Placeholder for actual response handling
        except asyncio.TimeoutError:
            logger.warning(f"No response to message {message_id} within {timeout}s")
            return None
        finally:
            del self.pending_responses[message_id]


# Global message broker instance
_message_broker: Optional[A2AMessageBroker] = None


def get_message_broker() -> A2AMessageBroker:
    """Get or create the global message broker"""
    global _message_broker
    if _message_broker is None:
        _message_broker = A2AMessageBroker()
    return _message_broker


def reset_message_broker():
    """Reset the message broker (for testing)"""
    global _message_broker
    _message_broker = None


# A2A Message Builders

def create_query_message(
    from_agent: str,
    to_agent: str,
    payload: Dict[str, Any]
) -> A2AMessage:
    """Create a query message"""
    return {
        "message_id": str(uuid.uuid4()),
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_type": "query",
        "in_reply_to": None,
        "payload": payload,
        "timestamp": datetime.now().timestamp(),
    }


def create_response_message(
    from_agent: str,
    to_agent: str,
    in_reply_to: str,
    payload: Dict[str, Any]
) -> A2AMessage:
    """Create a response message"""
    return {
        "message_id": str(uuid.uuid4()),
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_type": "response",
        "in_reply_to": in_reply_to,
        "payload": payload,
        "timestamp": datetime.now().timestamp(),
    }


def create_consensus_check_message(
    from_agent: str,
    to_agents: List[str],
    payload: Dict[str, Any]
) -> List[A2AMessage]:
    """Create consensus check messages to multiple agents"""
    messages = []
    for to_agent in to_agents:
        messages.append({
            "message_id": str(uuid.uuid4()),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": "consensus_check",
            "in_reply_to": None,
            "payload": payload,
            "timestamp": datetime.now().timestamp(),
        })
    return messages
