"""
Recommendation Agent
LLM-powered recommendation engine using RAG + VectorDB
Runs every 60 minutes or on-demand, generates contextual recommendations
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import boto3

from ..grid_state import GridState, SensorData
from ..vector_store import get_vector_store, SimpleEmbedding
from ..bedrock_integration import BedrockAlertGenerator
from ..memory_store import (
    get_memory_store,
    initialize_agent_memory,
    append_to_memory_list,
)

logger = logging.getLogger(__name__)


class RecommendationPrompts:
    """LLM prompt templates for each component"""
    
    SYSTEM_PROMPT = """You are an expert energy grid recommendation agent for a rural microgrid system in Munnar, Kerala. Your role is to:
1. Analyze current sensor data and fault indicators
2. Review similar historical events retrieved from the knowledge base
3. Generate concise, actionable recommendations specific to the component
4. Provide confidence scores and reference past patterns

Guidelines:
- Keep recommendations to 2-3 lines maximum
- Be specific with numbers and timeframes
- Reference similar past events when relevant
- Categorize recommendation status: ACTION_REQUIRED | MONITOR | OPTIMAL
- Format: Recommendation text | Confidence (0-1) | Status

Focus on rural context: limited technician availability, weather patterns, resource constraints."""

    @staticmethod
    def solar_output_prompt(
        current_kw: float,
        efficiency: float,
        ldr: int,
        hour: int,
        retrieved_events: List[Dict[str, Any]]
    ) -> str:
        """Prompt for solar output recommendations"""
        events_context = ""
        if retrieved_events:
            events_context = "\nSimilar past events:\n"
            for i, event in enumerate(retrieved_events, 1):
                rec = event.get('recommendation_text', 'N/A')
                score = event.get('similarity_score', 0)
                events_context += f"{i}. [{score:.0%}] {rec[:100]}...\n"
        
        return f"""Current Solar Output Data:
- Power output: {current_kw:.1f} kW
- Panel efficiency: {efficiency:.0f}%
- Light sensor (LDR): {ldr}/1024 (0=dark, 1024=bright)
- Time of day: {hour:02d}:00 hours
{events_context}

Generate a recommendation for optimizing solar output. Consider cloud cover patterns, panel efficiency trends, and maintenance needs."""

    @staticmethod
    def fault_score_prompt(
        fault_score: float,
        anomaly_type: str,
        voltage: float,
        current: float,
        temperature: float,
        retrieved_events: List[Dict[str, Any]]
    ) -> str:
        """Prompt for fault detection recommendations"""
        events_context = ""
        if retrieved_events:
            events_context = "\nHistorical fault patterns:\n"
            for i, event in enumerate(retrieved_events, 1):
                fault_info = event.get('sensor_snapshot', {})
                conf = event.get('confidence', 0)
                events_context += f"{i}. [{conf:.0%}] Score: {fault_info.get('fault_score', 0):.2f} - {event.get('recommendation_text', 'N/A')[:80]}...\n"
        
        return f"""Current Fault Detection Data:
- Anomaly score: {fault_score:.3f} (0=normal, 1=fault)
- Anomaly type: {anomaly_type}
- Voltage: {voltage:.1f}V
- Current: {current:.1f}A
- Temperature: {temperature:.1f}°C
{events_context}

Generate a recommendation about fault likelihood and required actions."""

    @staticmethod
    def load_forecast_prompt(
        current_demand: float,
        forecast_2h: float,
        forecast_4h: float,
        retrieved_events: List[Dict[str, Any]]
    ) -> str:
        """Prompt for load forecasting recommendations"""
        events_context = ""
        if retrieved_events:
            events_context = "\nPast demand spikes:\n"
            for i, event in enumerate(retrieved_events, 1):
                snapshot = event.get('sensor_snapshot', {})
                events_context += f"{i}. Forecast: {snapshot.get('demand_2h', 0):.1f}kW - {event.get('recommendation_text', 'N/A')[:80]}...\n"
        
        return f"""Current Load Forecast Data:
- Current demand: {current_demand:.1f}A
- 2-hour forecast: {forecast_2h:.1f}A
- 4-hour forecast: {forecast_4h:.1f}A
{events_context}

Generate a recommendation about demand management and pre-emptive load shedding if needed."""

    @staticmethod
    def alert_history_prompt(
        active_alerts: int,
        last_alert_age_minutes: float,
        alert_types: List[str],
        retrieved_events: List[Dict[str, Any]]
    ) -> str:
        """Prompt for active alerts recommendations"""
        events_context = ""
        if retrieved_events:
            events_context = "\nRecent alert history:\n"
            for i, event in enumerate(retrieved_events[:3], 1):
                events_context += f"{i}. {event.get('recommendation_text', 'N/A')[:100]}...\n"
        
        alert_types_str = ", ".join(alert_types) if alert_types else "none"
        
        return f"""Current Alert Data:
- Active alerts: {active_alerts}
- Last alert: {last_alert_age_minutes:.0f} minutes ago
- Recent alert types: {alert_types_str}
{events_context}

Generate a recommendation about system health and alert status."""

    @staticmethod
    def sensor_feed_prompt(
        voltage: float,
        current: float,
        temperature: float,
        ldr: int,
        retrieved_events: List[Dict[str, Any]]
    ) -> str:
        """Prompt for live sensor feed recommendations"""
        events_context = ""
        if retrieved_events:
            events_context = "\nRecent sensor patterns:\n"
            for i, event in enumerate(retrieved_events[:3], 1):
                events_context += f"{i}. {event.get('recommendation_text', 'N/A')[:100]}...\n"
        
        return f"""Current Live Sensor Data:
- Voltage: {voltage:.1f}V
- Current: {current:.1f}A
- Temperature: {temperature:.1f}°C
- Light sensor: {ldr}/1024
{events_context}

Generate a recommendation about current sensor readings and trends."""

    @staticmethod
    def agent_decisions_prompt(
        fault_score: float,
        forecast_confidence: float,
        alert_count: int,
        retrieved_events: List[Dict[str, Any]]
    ) -> str:
        """Prompt for agent coordination recommendations"""
        events_context = ""
        if retrieved_events:
            events_context = "\nAgent performance history:\n"
            for i, event in enumerate(retrieved_events[:3], 1):
                events_context += f"{i}. {event.get('recommendation_text', 'N/A')[:100]}...\n"
        
        return f"""Current Agent Status:
- Fault detector confidence: {fault_score:.0%}
- Load forecaster confidence: {forecast_confidence:.0%}
- Alert dispatcher queue: {alert_count} items
{events_context}

Generate a recommendation about agent system health and performance."""


class RecommendationAgent:
    """Generates contextual recommendations using LLM + RAG"""
    
    AGENT_NAME = "recommendation"
    COMPONENTS = ["solar", "fault", "forecast", "alerts", "sensor", "agents"]
    
    def __init__(self):
        self.memory: Dict[str, Any] = {}
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1"
        )
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.vector_store = get_vector_store()
    
    async def initialize(self):
        """Initialize agent memory"""
        initial_memory = {
            "last_run": None,
            "recommendations_count": 0,
            "avg_confidence": 0.0,
            "last_recommendations": {},
        }
        self.memory = await initialize_agent_memory(self.AGENT_NAME, initial_memory)
        logger.info(f"Initialized {self.AGENT_NAME}")
    
    async def execute(self, state: GridState) -> GridState:
        """
        Execute recommendation generation for all components
        
        Args:
            state: Current grid state
        
        Returns:
            Updated grid state with recommendations
        """
        try:
            sensor_data = state["sensor_data"]
            recommendations = {}
            
            logger.info(f"Generating recommendations for {len(self.COMPONENTS)} components")
            
            # Generate recommendation for each component
            for component in self.COMPONENTS:
                try:
                    rec = await self._generate_recommendation(component, state)
                    if rec:
                        recommendations[component] = rec
                        
                        # Store in vector store for future retrieval
                        self.vector_store.add_document({
                            'timestamp': datetime.now().isoformat(),
                            'component': component,
                            'sensor_snapshot': sensor_data,
                            'recommendation_text': rec.get('text', ''),
                            'confidence': rec.get('confidence', 0),
                            'status': rec.get('status', 'MONITOR'),
                        })
                        
                except Exception as e:
                    logger.error(f"Error generating recommendation for {component}: {e}")
                    recommendations[component] = {
                        'text': f'Error generating recommendation: {str(e)}',
                        'confidence': 0,
                        'status': 'ERROR',
                    }
            
            # Update memory
            self.memory['last_run'] = datetime.now().isoformat()
            self.memory['last_recommendations'] = recommendations
            self.memory['recommendations_count'] = self.memory.get('recommendations_count', 0) + 1
            
            avg_conf = sum(
                r.get('confidence', 0) for r in recommendations.values()
                if r.get('confidence')
            ) / max(len(recommendations), 1)
            self.memory['avg_confidence'] = avg_conf
            
            await append_to_memory_list(
                self.AGENT_NAME,
                "recommendations_history",
                {
                    "timestamp": sensor_data["timestamp"],
                    "recommendations": recommendations,
                    "avg_confidence": avg_conf,
                }
            )
            
            # Update state
            state['recommendations'] = recommendations
            state['recommendation_memory'] = self.memory
            
            logger.info(f"Generated recommendations: {list(recommendations.keys())}")
            return state
            
        except Exception as e:
            logger.error(f"Error in recommendation agent: {e}")
            state["errors"].append(f"Recommendation agent error: {str(e)}")
            return state
    
    async def _generate_recommendation(
        self,
        component: str,
        state: GridState
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a single recommendation for a component
        
        Args:
            component: Component name
            state: Grid state
        
        Returns:
            Recommendation dict with text, confidence, and status
        """
        sensor_data = state["sensor_data"]
        
        try:
            # Retrieve similar historical events from vector store
            retrieved_events = self.vector_store.retrieve_similar(
                query_snapshot=sensor_data,
                component=component,
                top_k=3,
                similarity_threshold=0.2
            )
            
            # Build component-specific prompt
            prompt = self._build_prompt(component, state, retrieved_events)
            
            if not prompt:
                return None
            
            # Call Bedrock LLM
            response = await self._call_bedrock(prompt)
            
            if not response:
                return None
            
            # Parse response
            recommendation = self._parse_response(response)
            
            logger.info(
                f"Generated {component} recommendation: "
                f"confidence={recommendation.get('confidence', 0):.0%}, "
                f"status={recommendation.get('status', 'UNKNOWN')}"
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating {component} recommendation: {e}")
            return None
    
    def _build_prompt(
        self,
        component: str,
        state: GridState,
        retrieved_events: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Build component-specific prompt"""
        sensor = state["sensor_data"]
        hour = datetime.fromtimestamp(sensor["timestamp"]).hour
        
        if component == "solar":
            kw = state.get("solar_output", 3.4)
            eff = state.get("panel_efficiency", 88)
            ldr = state.get("ldr_value", 812)
            return RecommendationPrompts.solar_output_prompt(kw, eff, ldr, hour, retrieved_events)
        
        elif component == "fault":
            score = state.get("anomaly_score", 0.02)
            atype = state.get("fault_type", "none")
            return RecommendationPrompts.fault_score_prompt(
                score, atype, sensor["voltage"], sensor["current"],
                sensor["temperature"], retrieved_events
            )
        
        elif component == "forecast":
            demand = sensor["current"]
            f2h = state.get("demand_forecast", {}).get("demand_2h", demand)
            f4h = state.get("demand_forecast", {}).get("demand_4h", demand)
            return RecommendationPrompts.load_forecast_prompt(demand, f2h, f4h, retrieved_events)
        
        elif component == "alerts":
            alerts = state.get("active_alerts_count", 0)
            age = state.get("last_alert_age_minutes", 0)
            types = state.get("alert_types", [])
            return RecommendationPrompts.alert_history_prompt(alerts, age, types, retrieved_events)
        
        elif component == "sensor":
            return RecommendationPrompts.sensor_feed_prompt(
                sensor["voltage"], sensor["current"],
                sensor["temperature"], state.get("ldr_value", 812),
                retrieved_events
            )
        
        elif component == "agents":
            score = state.get("anomaly_score", 0)
            conf = state.get("forecast_confidence", 0.7)
            alerts = state.get("active_alerts_count", 0)
            return RecommendationPrompts.agent_decisions_prompt(score, conf, alerts, retrieved_events)
        
        return None
    
    async def _call_bedrock(self, prompt: str) -> Optional[str]:
        """Call Bedrock Claude to generate recommendation"""
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-06-01",
                    "max_tokens": 200,
                    "system": RecommendationPrompts.SYSTEM_PROMPT,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response["body"].read())
            
            if result.get("content"):
                return result["content"][0]["text"]
            
            return None
            
        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            return None
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured recommendation
        
        Expected format:
        "Recommendation text here | Confidence: 0.85 | Status: MONITOR"
        """
        try:
            parts = response_text.split("|")
            
            text = parts[0].strip() if len(parts) > 0 else response_text
            confidence = 0.7
            status = "MONITOR"
            
            if len(parts) > 1:
                conf_str = parts[1].lower()
                if "confidence" in conf_str:
                    # Extract number like "0.85" or "85%"
                    import re
                    match = re.search(r"(\d+\.?\d*)", conf_str)
                    if match:
                        val = float(match.group(1))
                        confidence = min(val, 1.0) if val > 1 else val
            
            if len(parts) > 2:
                status_str = parts[2].upper().strip()
                if "ACTION" in status_str:
                    status = "ACTION_REQUIRED"
                elif "OPTIMAL" in status_str:
                    status = "OPTIMAL"
                else:
                    status = "MONITOR"
            
            return {
                'text': text,
                'confidence': confidence,
                'status': status,
                'retrieved_count': 0,  # Will be populated by caller
            }
            
        except Exception as e:
            logger.error(f"Error parsing recommendation response: {e}")
            return {
                'text': response_text[:200],
                'confidence': 0.5,
                'status': 'MONITOR',
            }


# Node function for LangGraph
async def recommendation_agent_node(state: GridState) -> GridState:
    """LangGraph node for recommendation agent"""
    agent = RecommendationAgent()
    await agent.initialize()
    return await agent.execute(state)
