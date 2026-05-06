"""
FastAPI router for A2A protocol endpoints
Exposes agent communication via HTTP
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

from .grid_state import A2AMessage
from .a2a_protocol import get_message_broker, create_response_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["A2A Protocol"])


@router.post("/{agent_name}/receive")
async def receive_a2a_message(agent_name: str, message: A2AMessage) -> Dict[str, str]:
    """
    Endpoint for agents to receive A2A messages
    
    POST /agent/fault_detector/receive
    {
        "message_id": "msg_123",
        "from_agent": "load_forecaster",
        "to_agent": "fault_detector",
        "message_type": "response",
        "in_reply_to": "msg_122",
        "payload": {...},
        "timestamp": 1234567890
    }
    """
    try:
        broker = get_message_broker()
        await broker.send_message(message)
        
        logger.info(f"Received A2A message for {agent_name}: {message['message_id']}")
        
        return {
            "status": "received",
            "message_id": message["message_id"],
            "agent": agent_name
        }
    except Exception as e:
        logger.error(f"Error receiving A2A message: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_name}/messages")
async def get_agent_messages(agent_name: str) -> Dict[str, Any]:
    """
    Get all pending messages for an agent
    
    GET /agent/fault_detector/messages
    """
    try:
        broker = get_message_broker()
        messages = await broker.receive_messages(agent_name)
        
        logger.info(f"Retrieved {len(messages)} messages for {agent_name}")
        
        return {
            "agent": agent_name,
            "message_count": len(messages),
            "messages": messages
        }
    except Exception as e:
        logger.error(f"Error getting messages for {agent_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_name}/respond")
async def send_a2a_response(
    agent_name: str,
    to_agent: str,
    in_reply_to: str,
    payload: Dict[str, Any]
) -> Dict[str, str]:
    """
    Send a response message from one agent to another
    
    POST /agent/load_forecaster/respond
    {
        "to_agent": "fault_detector",
        "in_reply_to": "msg_122",
        "payload": {...}
    }
    """
    try:
        broker = get_message_broker()
        
        response = create_response_message(
            from_agent=agent_name,
            to_agent=to_agent,
            in_reply_to=in_reply_to,
            payload=payload
        )
        
        await broker.send_message(response)
        
        logger.info(f"Sent response from {agent_name} to {to_agent}: {response['message_id']}")
        
        return {
            "status": "sent",
            "message_id": response["message_id"],
            "from_agent": agent_name,
            "to_agent": to_agent
        }
    except Exception as e:
        logger.error(f"Error sending response: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def broker_status() -> Dict[str, Any]:
    """
    Get current status of the message broker
    
    GET /agent/status
    """
    try:
        broker = get_message_broker()
        
        return {
            "status": "operational",
            "broker_type": "in_memory",
            "queue_size": sum(len(msgs) for msgs in broker.message_queue.values()),
            "processed_messages": len(broker.processed_message_ids),
            "timeout_seconds": broker.timeout_seconds
        }
    except Exception as e:
        logger.error(f"Error getting broker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
