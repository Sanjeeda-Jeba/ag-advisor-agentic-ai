"""
API Router

Routes API calls to the appropriate client based on API type.
Handles initialization of clients with proper authentication.
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_clients.weather_client import WeatherAPIClient
from config.credentials import get_api_key


class APIRouter:
    """
    Route API calls to the appropriate client.
    
    Manages client initialization and routes requests based on API type.
    """
    
    def __init__(self):
        """Initialize the API router with available clients."""
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all available API clients."""
        # Initialize Weather API client
        try:
            weather_api_key = get_api_key("OPENWEATHER_API_KEY")
            if weather_api_key:
                self.clients['weather'] = WeatherAPIClient(api_key=weather_api_key)
                print("✅ Weather API client initialized")
            else:
                print("⚠️  Weather API key not found - weather queries will not work")
        except Exception as e:
            print(f"❌ Failed to initialize Weather API client: {e}")
        
        # Add more clients here as they are implemented
        # Example:
        # try:
        #     openai_api_key = get_api_key("OPENAI_API_KEY")
        #     if openai_api_key:
        #         self.clients['openai'] = OpenAIClient(api_key=openai_api_key)
        # except Exception as e:
        #     print(f"Failed to initialize OpenAI client: {e}")
    
    def call_api(
        self,
        api_type: str,
        params: Dict[str, Any],
        api_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route the API call to the correct client.
        
        Args:
            api_type: Type of API (e.g., 'weather', 'openai', 'usda')
            params: Parameters for the API call
            api_name: Optional specific API name for logging
        
        Returns:
            API response dictionary
        
        Example:
            >>> router = APIRouter()
            >>> response = router.call_api('weather', {'city': 'London'})
            >>> if response['success']:
            ...     print(f"Temperature: {response['temperature']}°C")
        """
        # Check if API type is supported
        if api_type not in self.clients:
            return {
                "success": False,
                "error": f"API type '{api_type}' not available",
                "message": f"❌ {api_type.title()} API is not configured or not available",
                "available_apis": list(self.clients.keys())
            }
        
        # Get the appropriate client
        client = self.clients[api_type]
        
        # Make the API call
        try:
            print(f"📡 Calling {api_type} API with params: {params}")
            response = client.call(params)
            
            if response.get('success'):
                print(f"✅ {api_type} API call successful")
            else:
                print(f"⚠️  {api_type} API call failed: {response.get('message')}")
            
            return response
            
        except Exception as e:
            error_msg = f"Failed to call {api_type} API: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ {error_msg}"
            }
    
    def is_api_available(self, api_type: str) -> bool:
        """
        Check if an API type is available.
        
        Args:
            api_type: Type of API to check
        
        Returns:
            True if API is initialized and available
        """
        return api_type in self.clients
    
    def get_available_apis(self) -> list:
        """
        Get list of available API types.
        
        Returns:
            List of API type strings
        """
        return list(self.clients.keys())
    
    def get_api_status(self) -> Dict[str, bool]:
        """
        Get status of all API clients.
        
        Returns:
            Dictionary mapping API types to their availability status
        """
        return {api_type: True for api_type in self.clients.keys()}
    
    def close_all(self):
        """Close all API client sessions."""
        for client in self.clients.values():
            if hasattr(client, 'close'):
                client.close()


# Singleton instance for global use
_router_instance = None


def get_router() -> APIRouter:
    """
    Get the singleton APIRouter instance.
    
    Returns:
        APIRouter instance
    """
    global _router_instance
    if _router_instance is None:
        _router_instance = APIRouter()
    return _router_instance


# Test the router if run directly
if __name__ == "__main__":
    print("🔀 Testing API Router\n")
    
    # Create router
    router = APIRouter()
    
    # Check available APIs
    print(f"Available APIs: {router.get_available_apis()}\n")
    
    # Test weather API if available
    if router.is_api_available('weather'):
        print("🌤️  Testing Weather API")
        print("-" * 50)
        
        test_params = {
            'city': 'London',
            'units': 'metric'
        }
        
        result = router.call_api('weather', test_params)
        
        if result.get('success'):
            print(f"\n✅ Success!")
            print(f"Location: {result.get('location')}")
            print(f"Temperature: {result.get('temperature')}°C")
            print(f"Description: {result.get('description')}")
        else:
            print(f"\n❌ Error: {result.get('message')}")
    else:
        print("⚠️  Weather API not available")
    
    # Clean up
    router.close_all()







