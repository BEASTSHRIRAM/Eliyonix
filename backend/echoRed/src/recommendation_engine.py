"""
AI Recommendation Engine
Uses semantic search on vector DB to provide intelligent suggestions
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .qdrant_store import get_qdrant_store

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates AI recommendations based on historical patterns in vector DB"""
    
    def __init__(self):
        self.qdrant = get_qdrant_store()
    
    async def get_recommendations(
        self,
        village_id: str,
        current_sensor_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI recommendations for a village based on:
        1. Historical patterns (last 7 days from vector DB)
        2. Current sensor state (if provided)
        3. Semantic search for similar past situations
        
        Returns comprehensive recommendations with confidence scores
        """
        if self.qdrant.mock_mode:
            return self._get_mock_recommendations(village_id)
        
        try:
            # Get 7 days of historical data
            historical_data = await self.qdrant.get_historical_data(village_id, days=7)
            
            if not historical_data:
                return {
                    "status": "no_data",
                    "message": "No historical data available for recommendations",
                    "recommendations": []
                }
            
            # Analyze patterns
            analysis = self._analyze_patterns(historical_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(analysis, current_sensor_data)
            
            return {
                "status": "success",
                "village_id": village_id,
                "analysis_period": "7 days",
                "data_points_analyzed": len(historical_data),
                "analysis": analysis,
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "status": "error",
                "message": str(e),
                "recommendations": []
            }
    
    def _analyze_patterns(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze historical data to identify patterns"""
        
        # Calculate statistics
        total_readings = len(historical_data)
        fault_readings = [d for d in historical_data if d.get("fault_detected")]
        fault_rate = len(fault_readings) / total_readings if total_readings > 0 else 0
        
        # Average values
        avg_voltage = sum(d.get("voltage", 0) for d in historical_data) / total_readings
        avg_current = sum(d.get("current", 0) for d in historical_data) / total_readings
        avg_temp = sum(d.get("temperature", 0) for d in historical_data) / total_readings
        avg_power = sum(d.get("power_kw", 0) for d in historical_data) / total_readings
        
        # Fault type breakdown
        fault_types = {}
        for f in fault_readings:
            ft = f.get("fault_type", "unknown")
            fault_types[ft] = fault_types.get(ft, 0) + 1
        
        # Time-based patterns
        daytime_readings = [d for d in historical_data if 6 <= d.get("hour", 0) <= 18]
        nighttime_readings = [d for d in historical_data if d.get("hour", 0) < 6 or d.get("hour", 0) > 18]
        
        daytime_faults = len([d for d in daytime_readings if d.get("fault_detected")])
        nighttime_faults = len([d for d in nighttime_readings if d.get("fault_detected")])
        
        # Performance trend (last 3 days vs first 3 days)
        mid_point = len(historical_data) // 2
        recent_avg_power = sum(d.get("power_kw", 0) for d in historical_data[:mid_point]) / mid_point if mid_point > 0 else 0
        older_avg_power = sum(d.get("power_kw", 0) for d in historical_data[mid_point:]) / (len(historical_data) - mid_point) if mid_point > 0 else 0
        
        performance_trend = "improving" if recent_avg_power > older_avg_power * 1.05 else \
                           "declining" if recent_avg_power < older_avg_power * 0.95 else "stable"
        
        return {
            "total_readings": total_readings,
            "fault_rate": fault_rate,
            "fault_count": len(fault_readings),
            "fault_types": fault_types,
            "avg_voltage": avg_voltage,
            "avg_current": avg_current,
            "avg_temperature": avg_temp,
            "avg_power_kw": avg_power,
            "daytime_fault_rate": daytime_faults / len(daytime_readings) if daytime_readings else 0,
            "nighttime_fault_rate": nighttime_faults / len(nighttime_readings) if nighttime_readings else 0,
            "performance_trend": performance_trend,
            "efficiency_score": self._calculate_efficiency(historical_data),
        }
    
    def _calculate_efficiency(self, historical_data: List[Dict]) -> float:
        """Calculate overall system efficiency (0-100)"""
        if not historical_data:
            return 0.0
        
        # Factors: uptime, power output, fault rate
        fault_rate = len([d for d in historical_data if d.get("fault_detected")]) / len(historical_data)
        uptime_score = (1 - fault_rate) * 100
        
        # Power output score (compared to expected 3.5 kW average)
        avg_power = sum(d.get("power_kw", 0) for d in historical_data) / len(historical_data)
        power_score = min(100, (avg_power / 3.5) * 100)
        
        # Combined efficiency
        efficiency = (uptime_score * 0.6 + power_score * 0.4)
        return round(efficiency, 1)
    
    def _generate_recommendations(
        self,
        analysis: Dict[str, Any],
        current_sensor_data: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # 1. High fault rate
        if analysis["fault_rate"] > 0.10:  # >10% fault rate
            recommendations.append({
                "priority": "high",
                "category": "maintenance",
                "title": "High Fault Rate Detected",
                "description": f"System experiencing {analysis['fault_rate']*100:.1f}% fault rate over the past week. Immediate inspection recommended.",
                "action": "Schedule technician visit within 24 hours",
                "confidence": 0.95,
                "impact": "Critical - may lead to system failure"
            })
        
        # 2. Specific fault patterns
        if "inverter_overtemp" in analysis["fault_types"]:
            count = analysis["fault_types"]["inverter_overtemp"]
            recommendations.append({
                "priority": "high",
                "category": "cooling",
                "title": "Overheating Issues",
                "description": f"Inverter overheating detected {count} times in past 7 days.",
                "action": "Check ventilation, clean cooling fans, verify ambient temperature",
                "confidence": 0.90,
                "impact": "High - reduces lifespan and efficiency"
            })
        
        if "inverter_overvoltage" in analysis["fault_types"]:
            count = analysis["fault_types"]["inverter_overvoltage"]
            recommendations.append({
                "priority": "medium",
                "category": "electrical",
                "title": "Voltage Regulation Issues",
                "description": f"Overvoltage events: {count} times. May indicate grid instability.",
                "action": "Install voltage stabilizer or check grid connection",
                "confidence": 0.85,
                "impact": "Medium - can damage equipment"
            })
        
        # 3. Performance declining
        if analysis["performance_trend"] == "declining":
            recommendations.append({
                "priority": "medium",
                "category": "efficiency",
                "title": "Declining Performance",
                "description": f"Power output decreased by {((analysis['avg_power_kw'] / 3.5) - 1) * 100:.1f}% compared to expected.",
                "action": "Clean solar panels, check for dust/debris, inspect wiring",
                "confidence": 0.80,
                "impact": "Medium - revenue loss"
            })
        
        # 4. Low efficiency
        if analysis["efficiency_score"] < 70:
            recommendations.append({
                "priority": "medium",
                "category": "optimization",
                "title": "Low System Efficiency",
                "description": f"Overall efficiency at {analysis['efficiency_score']:.1f}%. Below optimal range (>80%).",
                "action": "Comprehensive system audit recommended",
                "confidence": 0.75,
                "impact": "Medium - underperforming investment"
            })
        
        # 5. Weather-based (if rainy pattern detected)
        if analysis["daytime_fault_rate"] > 0.15:
            recommendations.append({
                "priority": "low",
                "category": "weather",
                "title": "Weather Impact",
                "description": "High daytime fault rate suggests weather-related issues (rain, clouds).",
                "action": "Monitor weather patterns, consider battery backup for cloudy days",
                "confidence": 0.70,
                "impact": "Low - seasonal variation"
            })
        
        # 6. Preventive maintenance (if no major issues)
        if analysis["fault_rate"] < 0.05 and analysis["efficiency_score"] > 80:
            recommendations.append({
                "priority": "low",
                "category": "preventive",
                "title": "System Performing Well",
                "description": f"Efficiency at {analysis['efficiency_score']:.1f}%, fault rate only {analysis['fault_rate']*100:.1f}%.",
                "action": "Continue routine monthly maintenance checks",
                "confidence": 0.95,
                "impact": "Positive - maintain current practices"
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order[x["priority"]])
        
        return recommendations
    
    def _get_mock_recommendations(self, village_id: str) -> Dict[str, Any]:
        """Mock recommendations when Qdrant is not available"""
        return {
            "status": "mock",
            "village_id": village_id,
            "message": "Using mock recommendations (Qdrant not connected)",
            "recommendations": [
                {
                    "priority": "medium",
                    "category": "system",
                    "title": "Connect to Vector Database",
                    "description": "Enable Qdrant connection to get AI-powered recommendations based on historical patterns.",
                    "action": "Fix network/firewall or run local Qdrant instance",
                    "confidence": 1.0,
                    "impact": "Required for intelligent recommendations"
                }
            ]
        }


# Global instance
_recommendation_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create the global recommendation engine"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine
