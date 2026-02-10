"""
Weather Tool
Wrapper for weather API client to work with conversational system

Flow:
1. Extract parameters from question
2. Call Weather API
3. Return structured data (LLM will generate final response)
"""

from src.api_clients.weather_client import WeatherClient
from src.utils.parameter_extractor import extract_city_from_query, detect_temperature_unit
from typing import Dict


def execute_weather_tool(question: str) -> Dict:
    """
    Execute weather tool - get weather data for a location
    
    Args:
        question: User's natural language question
    
    Returns:
        Dict with tool execution result:
        {
            "success": True/False,
            "tool": "weather",
            "data": {...weather data...} or None,
            "error": "error message" if failed
        }
    
    Examples:
        >>> execute_weather_tool("What's the weather in London?")
        {
            "success": True,
            "tool": "weather",
            "data": {
                "city": "London",
                "temperature": 15.5,
                ...
            }
        }
    """
    try:
        # Extract parameters from question
        city = extract_city_from_query(question)
        units = detect_temperature_unit(question)
        
        if not city:
            return {
                "success": False,
                "tool": "weather",
                "error": "Could not extract city name from your question. Please specify a location."
            }
        
        # Create weather client and fetch data
        client = WeatherClient()
        weather_data = client.get_weather(city=city, units=units)
        
        # Check if API call was successful
        if not weather_data.get("success"):
            return {
                "success": False,
                "tool": "weather",
                "error": weather_data.get("error", "Failed to fetch weather data")
            }
        
        # Return successful result
        return {
            "success": True,
            "tool": "weather",
            "data": weather_data
        }
    
    except Exception as e:
        return {
            "success": False,
            "tool": "weather",
            "error": f"Unexpected error: {str(e)}"
        }


def format_weather_response(data: Dict) -> str:
    """
    Format weather data into natural language response
    
    Args:
        data: Weather data dict from API
    
    Returns:
        Natural language response string
    """
    if not data:
        return "I couldn't retrieve weather information."
    
    city = data.get("city", "the requested location")
    country = data.get("country", "")
    temp = data.get("temperature", "N/A")
    feels_like = data.get("feels_like", "N/A")
    temp_unit = data.get("temp_unit", "°C")
    humidity = data.get("humidity", "N/A")
    wind_speed = data.get("wind_speed", "N/A")
    description = data.get("description", "unclear")
    icon = data.get("icon", "")
    
    # Build response
    location_str = f"{city}, {country}" if country else city
    response = f"{icon} The current weather in {location_str} is {temp}{temp_unit} with {description}. "
    
    # Add feels like temperature if different
    if isinstance(temp, (int, float)) and isinstance(feels_like, (int, float)):
        if abs(temp - feels_like) > 2:
            response += f"It feels like {feels_like}{temp_unit}. "
    
    # Add humidity and wind
    response += f"Humidity is at {humidity}% and wind speed is {wind_speed} m/s."
    
    # Add contextual advice
    if isinstance(temp, (int, float)):
        if temp < 5:
            response += " ❄️ It's quite cold, dress warmly!"
        elif temp > 30:
            response += " ☀️ It's hot outside, stay hydrated!"
        elif 15 <= temp <= 25:
            response += " 🌤️ Perfect weather!"
    
    return response


# Test function
if __name__ == "__main__":
    print("Testing Weather Tool...")
    print("-" * 50)
    
    test_questions = [
        "What's the weather in London?",
        "Show me temperature in Tokyo",
        "Is it raining in Paris?"
    ]
    
    for question in test_questions:
        print(f"\n📝 Question: {question}")
        print("-" * 50)
        
        result = execute_weather_tool(question)
        
        if result["success"]:
            print("✅ Success!")
            response = format_weather_response(result["data"])
            print(f"🤖 Response: {response}")
        else:
            print(f"❌ Error: {result['error']}")

