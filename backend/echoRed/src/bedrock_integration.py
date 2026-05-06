"""
Bedrock Integration for Alert Generation
Generates localized alert messages using Claude
"""
import boto3
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BedrockAlertGenerator:
    """Generates alert messages using AWS Bedrock Claude"""
    
    def __init__(self, region: str = "us-east-1", model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        """
        Initialize Bedrock client
        model_id: Claude model to use
        """
        self.bedrock = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = model_id
    
    async def generate_alert_kannada(
        self,
        fault_type: str,
        village_id: str,
        confidence: float,
        inverter_id: str,
        sensor_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate WhatsApp alert message in Kannada
        
        Args:
            fault_type: Type of fault (e.g., "inverter_overvoltage")
            village_id: Village identifier
            confidence: Confidence level 0-1
            inverter_id: Inverter identifier
            sensor_data: Current sensor readings
        
        Returns:
            Alert message in Kannada script
        """
        sensor_context = ""
        if sensor_data:
            sensor_context = f"""
            Current readings:
            - Voltage: {sensor_data.get('voltage', 0):.1f}V
            - Current: {sensor_data.get('current', 0):.1f}A
            - Temperature: {sensor_data.get('temperature', 0):.1f}°C
            """
        
        prompt = f"""You are a utility company's alert system for rural electrification.
Generate a WhatsApp alert message in Kannada for a technician about a solar inverter fault.

FAULT DETAILS:
- Fault Type: {fault_type}
- Inverter ID: {inverter_id}
- Village: {village_id}
- Confidence: {confidence*100:.0f}% certain this is a real fault
{sensor_context}

REQUIREMENTS:
1. Write ONLY in Kannada script (ಕನ್ನಡ)
2. Keep to 1-2 lines maximum
3. Make it actionable (what technician should do)
4. Include urgency level: HIGH if confidence > 0.9, MEDIUM if > 0.7, LOW otherwise
5. Add estimated repair cost if available
6. Use common technician terminology
7. No English text, NO TRANSLATIONS

FAULT TYPE GUIDELINES:
- "inverter_overvoltage": ಓವರ್ವೋಲ್ಟೇಜ್ (overvoltage problem)
- "inverter_undervoltage": ಅಂಡರ್ವೋಲ್ಟೇಜ್ (undervoltage problem)
- "inverter_overtemp": ಓವರ್ಹೀಟಿಂಗ್ (overheating)
- "inverter_fault": ಇನ್ವರ್ಟರ್ ಸ್ಪಷ್ಟೀಕರಣ ಅಗತ್ಯ (needs inspection)

EXAMPLE (inverter_overvoltage):
"ಇನ್ವರ್ಟರ್ ಓವರ್ವೋಲ್ಟೇಜ್. ಬುಧವಾರ ಪರಿವರ್ತನೆ ಮಾಡಿ. ₹2000-3000 ಖರ್ಚು."

Generate the alert now:"""
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.3,  # Lower temp for consistent formatting
                })
            )
            
            result = json.loads(response["body"].read().decode())
            alert_message = result["content"][0]["text"].strip()
            logger.info(f"Generated Kannada alert for {fault_type} in {village_id}")
            return alert_message
            
        except Exception as e:
            logger.error(f"Error generating alert via Bedrock: {e}")
            return self._get_fallback_kannada_alert(fault_type, confidence)
    
    async def generate_alert_hindi(
        self,
        fault_type: str,
        village_id: str,
        confidence: float,
        inverter_id: str,
        sensor_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate alert message in Hindi"""
        sensor_context = ""
        if sensor_data:
            sensor_context = f"""
            मौजूदा रीडिंग:
            - वोल्टेज: {sensor_data.get('voltage', 0):.1f}V
            - करंट: {sensor_data.get('current', 0):.1f}A
            - तापमान: {sensor_data.get('temperature', 0):.1f}°C
            """
        
        prompt = f"""आप एक ग्रामीण विद्युतीकरण प्रणाली के लिए एक अलर्ट सिस्टम हैं।
एक तकनीशियन को सौर इनवर्टर खराबी के बारे में एक व्हाट्सएप अलर्ट संदेश हिंदी में उत्पन्न करें।

खराबी विवरण:
- खराबी प्रकार: {fault_type}
- इनवर्टर ID: {inverter_id}
- गांव: {village_id}
- विश्वास: {confidence*100:.0f}% निश्चित
{sensor_context}

आवश्यकताएं:
1. केवल हिंदी लिपि में लिखें (देवनागरी)
2. अधिकतम 1-2 पंक्तियां रखें
3. कार्रवाई योग्य बनाएं
4. कीमत का अनुमान जोड़ें
5. कोई अंग्रेजी नहीं

संदेश अब उत्पन्न करें:"""
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.3,
                })
            )
            
            result = json.loads(response["body"].read().decode())
            alert_message = result["content"][0]["text"].strip()
            logger.info(f"Generated Hindi alert for {fault_type} in {village_id}")
            return alert_message
            
        except Exception as e:
            logger.error(f"Error generating Hindi alert via Bedrock: {e}")
            return self._get_fallback_hindi_alert(fault_type, confidence)
    
    def _get_fallback_kannada_alert(self, fault_type: str, confidence: float) -> str:
        """Fallback alert messages in Kannada if Bedrock fails"""
        alerts = {
            "inverter_overvoltage": "ಇನ್ವರ್ಟರ್ ಓವರ್ವೋಲ್ಟೇಜ್. ಬೇರೆ ತೀರ್ಪು ಮಾಡಿ.",
            "inverter_undervoltage": "ಇನ್ವರ್ಟರ್ ಲೋ ವೋಲ್ಟೇಜ್. ಆನ್/ಆಫ್ ಪುನರಾರಂಭ ಮಾಡಿ.",
            "inverter_overtemp": "ಇನ್ವರ್ಟರ್ ಹೆಚ್ಚು ಬೆಚ್ಚಗಿದೆ. ತಣ್ಣನೆಯ ಜಾಗಕ್ಕೆ ಸ್ಥಳಾಂತರಿಸಿ.",
            "inverter_fault": "ಇನ್ವರ್ಟರ್ ಆ ತೀರ್ಪು ಅಗತ್ಯ. ವೆಚ್ಚಾನಿಂದ ಸಹಾಯ ಪಡೆ.",
        }
        
        return alerts.get(fault_type, "ಇನ್ವರ್ಟರ್ ಆ ತೀರ್ಪು ಅಗತ್ಯ.")
    
    def _get_fallback_hindi_alert(self, fault_type: str, confidence: float) -> str:
        """Fallback alert messages in Hindi if Bedrock fails"""
        alerts = {
            "inverter_overvoltage": "इनवर्टर ओवरवोल्टेज। तकनीशियन को कॉल करें।",
            "inverter_undervoltage": "इनवर्टर कम वोल्टेज। रीबूट करने की कोशिश करें।",
            "inverter_overtemp": "इनवर्टर गर्म है। ठंडी जगह चेक करें।",
            "inverter_fault": "इनवर्टर खराबी। तकनीशियन से सहायता लें।",
        }
        
        return alerts.get(fault_type, "इनवर्टर की समस्या है।")


# Global alert generator instance
_alert_generator: Optional[BedrockAlertGenerator] = None


def get_alert_generator() -> BedrockAlertGenerator:
    """Get or create the global alert generator"""
    global _alert_generator
    if _alert_generator is None:
        _alert_generator = BedrockAlertGenerator()
    return _alert_generator


def set_alert_generator(generator: BedrockAlertGenerator):
    """Set a custom alert generator"""
    global _alert_generator
    _alert_generator = generator
