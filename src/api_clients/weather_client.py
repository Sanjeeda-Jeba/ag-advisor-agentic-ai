"""
OpenWeatherMap API Client
Fetches current weather data for any location
"""

from src.api_clients.base_client import BaseAPIClient
from src.config.credentials import CredentialsManager
from typing import Dict, Any, Optional
import requests


class WeatherClient(BaseAPIClient):
    """
    OpenWeatherMap API Client
    
    Provides current weather data including:
    - Temperature
    - Humidity
    - Wind speed
    - Weather description
    - Coordinates
    
    Usage:
        client = WeatherClient()
        weather = client.get_weather(city="London")
        print(f"Temperature: {weather['temperature']}°C")
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather client
        
        Args:
            api_key: OpenWeatherMap API key (optional, loads from .env if not provided)
        """
        super().__init__()
        
        # Get API key
        if api_key is None:
            creds = CredentialsManager()
            api_key = creds.get_api_key("openweather")
        
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def _validate_params(self, **kwargs) -> bool:
        """
        Validate request parameters
        
        Args:
            **kwargs: Parameters to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If parameters are invalid
        """
        if "city" not in kwargs and ("lat" not in kwargs or "lon" not in kwargs):
            raise ValueError(
                "Either 'city' or both 'lat' and 'lon' must be provided"
            )
        return True
    
    def get_weather(
        self,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        units: str = "metric",
        country_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current weather for a location
        
        Args:
            city: City name (e.g., "London", "New York")
            lat: Latitude (alternative to city)
            lon: Longitude (alternative to city)
            units: Temperature units ("metric" for Celsius, "imperial" for Fahrenheit)
            country_code: ISO 3166 country code (e.g., "US", "GB")
        
        Returns:
            Dict with weather information:
            {
                "success": True,
                "city": "London",
                "country": "GB",
                "temperature": 15.5,
                "feels_like": 14.2,
                "humidity": 72,
                "pressure": 1013,
                "wind_speed": 5.2,
                "wind_direction": 250,
                "description": "partly cloudy",
                "icon": "☁️",
                "lat": 51.5074,
                "lon": -0.1278,
                "timestamp": 1699632000
            }
        
        Raises:
            ValueError: If parameters are invalid
            requests.exceptions.RequestException: If API request fails
        """
        # Validate parameters
        self._validate_params(city=city, lat=lat, lon=lon)
        
        # Build query parameters
        params = {
            "appid": self.api_key,
            "units": units
        }
        
        # Add location parameters
        if city:
            query = f"{city},{country_code}" if country_code else city
            params["q"] = query
        else:
            params["lat"] = lat
            params["lon"] = lon
        
        # Make API request
        try:
            endpoint = f"{self.base_url}/weather"
            data = self.get(endpoint, params=params)
            
            # Format response
            return self._format_response(data, units)
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_response(self, data: Dict, units: str) -> Dict[str, Any]:
        """
        Format OpenWeatherMap API response
        
        Args:
            data: Raw API response
            units: Temperature units
        
        Returns:
            Formatted weather data
        """
        # Determine temperature unit symbol
        temp_unit = "°C" if units == "metric" else "°F"
        
        # Get weather icon emoji
        weather_id = data["weather"][0]["id"]
        icon = self._get_weather_icon(weather_id)
        
        return {
            "success": True,
            "city": data["name"],
            "country": data["sys"].get("country", ""),
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "temp_min": round(data["main"]["temp_min"], 1),
            "temp_max": round(data["main"]["temp_max"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": round(data["wind"]["speed"], 1),
            "wind_direction": data["wind"].get("deg", 0),
            "description": data["weather"][0]["description"],
            "icon": icon,
            "icon_code": data["weather"][0]["icon"],
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
            "timestamp": data["dt"],
            "timezone": data.get("timezone", 0),
            "temp_unit": temp_unit,
            "units": units
        }
    
    def _get_weather_icon(self, weather_id: int) -> str:
        """
        Get emoji icon for weather condition
        
        Args:
            weather_id: OpenWeatherMap weather condition ID
        
        Returns:
            Emoji string
        """
        # Weather ID ranges
        if 200 <= weather_id < 300:
            return "⛈️"  # Thunderstorm
        elif 300 <= weather_id < 400:
            return "🌦️"  # Drizzle
        elif 500 <= weather_id < 600:
            return "🌧️"  # Rain
        elif 600 <= weather_id < 700:
            return "❄️"  # Snow
        elif 700 <= weather_id < 800:
            return "🌫️"  # Atmosphere (fog, mist, etc.)
        elif weather_id == 800:
            return "☀️"  # Clear
        elif 801 <= weather_id < 900:
            return "☁️"  # Clouds
        else:
            return "🌤️"  # Default


# Test function
if __name__ == "__main__":
    print("Testing Weather Client...")
    print("-" * 50)
    
    try:
        client = WeatherClient()
        
        # Test with a city
        print("\n📍 Testing with city: London")
        weather = client.get_weather(city="London")
        
        if weather.get("success"):
            print(f"✅ Success!")
            print(f"🌍 Location: {weather['city']}, {weather['country']}")
            print(f"🌡️  Temperature: {weather['temperature']}{weather['temp_unit']}")
            print(f"🤔 Feels like: {weather['feels_like']}{weather['temp_unit']}")
            print(f"💧 Humidity: {weather['humidity']}%")
            print(f"💨 Wind: {weather['wind_speed']} m/s")
            print(f"{weather['icon']} {weather['description'].title()}")
        else:
            print(f"❌ Error: {weather.get('error')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Created .env file with OPENWEATHER_API_KEY")
        print("   2. Installed dependencies: python-dotenv, requests")

