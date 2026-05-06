import os
import json
import asyncio
from datetime import datetime
import anthropic
import httpx
from typing import Optional

# Initialize Anthropic client (AWS Bedrock)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Weather API (using Open-Meteo which is free and doesn't require API key)
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

# Village coordinates for weather
VILLAGE_COORDS = {
    "KA_001": {"lat": 10.3881, "lon": 77.0470, "name": "Munnar"},
    "KA_002": {"lat": 13.2009, "lon": 75.9670, "name": "Hassan"},
    "KA_003": {"lat": 12.3352, "lon": 75.5272, "name": "Kodagu"},
    "KA_004": {"lat": 12.2958, "lon": 76.6394, "name": "Mysore"},
    "KA_005": {"lat": 15.8497, "lon": 74.4977, "name": "Belgaum"},
}


async def get_weather_forecast(village_id: str) -> str:
    """Fetch weather forecast for a village"""
    coords = VILLAGE_COORDS.get(village_id)
    if not coords:
        return "Location not found"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                WEATHER_API,
                params={
                    "latitude": coords["lat"],
                    "longitude": coords["lon"],
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                    "timezone": "Asia/Kolkata",
                    "forecast_days": 7,
                }
            )
            data = response.json()

            forecast_text = f"7-day weather forecast for {coords['name']}:\n"
            for i, date in enumerate(data["daily"]["time"]):
                weather_code = data["daily"]["weather_code"][i]
                temp_max = data["daily"]["temperature_2m_max"][i]
                temp_min = data["daily"]["temperature_2m_min"][i]
                rain = data["daily"]["precipitation_sum"][i]
                wind = data["daily"]["wind_speed_10m_max"][i]

                weather_desc = get_weather_description(weather_code)
                forecast_text += f"\n{date}: {weather_desc}, High {temp_max}°C, Low {temp_min}°C, Rain {rain}mm, Wind {wind} km/h"

            return forecast_text
    except Exception as e:
        return f"Could not fetch weather: {str(e)}"


def get_weather_description(code: int) -> str:
    """Convert weather code to description"""
    descriptions = {
        0: "Clear",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Foggy with rime",
        51: "Light drizzle",
        61: "Slight rain",
        71: "Slight snow",
        80: "Moderate rain showers",
        85: "Heavy snow showers",
        95: "Thunderstorm",
    }
    return descriptions.get(code, "Unknown")


async def get_productivity_recommendations(
    village_id: str, current_data: Optional[dict] = None
) -> str:
    """Get solar productivity recommendations based on weather and historical data"""
    weather = await get_weather_forecast(village_id)

    # Simulate historical data analysis
    recommendations = """
    Based on weather patterns and historical solar data, here are recommendations to increase productivity:

    1. **Dust Cleaning Schedule**: Morning cleaning recommended on clear days improves output by 15-20%
    2. **Panel Angle Optimization**: Adjust panels 5-10 degrees with seasonal changes
    3. **Peak Hours Utilization**: Focus on 10 AM to 3 PM when solar intensity is highest
    4. **Weather-based Planning**: Plan high-load activities during clear weather windows
    5. **Maintenance**: Monthly cleaning of inverter vents improves cooling efficiency by 10%
    """
    return f"{weather}\n\n{recommendations}"


async def process_voice_query(
    query: str, village_id: str, language_code: str
) -> str:
    """Process voice query using Claude and weather/productivity data"""

    # Prepare context
    context = ""

    if any(word in query.lower() for word in ["weather", "rain", "temperature", "forecast"]):
        context = await get_weather_forecast(village_id)

    if any(
        word in query.lower()
        for word in ["productivity", "output", "efficiency", "increase", "improve", "recommendation"]
    ):
        context = await get_productivity_recommendations(village_id)

    # System prompt for Claude
    system_prompt = f"""You are a helpful agricultural extension agent for Indian farmers using solar mini-grids.
You speak {get_language_name(language_code)} and provide practical, actionable advice.
Always respond in the same language as the user's query.
Keep responses concise, friendly, and farmer-friendly.
Use simple terms and examples relevant to their situation.

Context about their village and weather:
{context}

Important: Always be encouraging and provide practical solutions."""

    # Call Claude via AWS Bedrock
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": query}
            ]
        )

        return message.content[0].text
    except Exception as e:
        return f"Sorry, I'm having trouble processing your request. Please try again. Error: {str(e)}"


def get_language_name(code: str) -> str:
    """Get language name from code"""
    names = {
        "kn": "Kannada",
        "hi": "Hindi",
        "en": "English",
        "ta": "Tamil",
        "te": "Telugu",
    }
    return names.get(code, "English")


async def handle_voice_agent_request(body: dict) -> dict:
    """Main handler for voice agent requests"""
    query = body.get("query", "")
    village_id = body.get("village_id", "KA_001")
    language = body.get("language", "en")

    if not query:
        return {"error": "No query provided"}

    response = await process_voice_query(query, village_id, language)

    return {
        "response": response,
        "village_id": village_id,
        "language": language,
        "timestamp": datetime.now().isoformat(),
    }
