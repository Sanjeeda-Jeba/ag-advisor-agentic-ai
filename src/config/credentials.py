"""
Credentials Manager for API Keys
Loads and manages API keys from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class CredentialsManager:
    """
    Manages API credentials from environment variables
    
    Usage:
        creds = CredentialsManager()
        weather_key = creds.get_api_key("openweather")
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize credentials manager
        
        Args:
            env_file: Path to .env file (default: project_root/.env)
        """
        if env_file is None:
            # Default to .env in project root
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
        
        # Load environment variables
        load_dotenv(env_file)
        
        # Map of API names to environment variable names
        self.api_key_map = {
            "openweather": "OPENWEATHER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "tavily": "TAVILY_API_KEY"
        }
    
    def get_api_key(self, api_name: str) -> str:
        """
        Get API key for a specific service
        
        Args:
            api_name: Name of the API (e.g., "openweather", "openai")
        
        Returns:
            API key string
        
        Raises:
            ValueError: If API key is not found or is a placeholder
        """
        env_var_name = self.api_key_map.get(api_name)
        
        if not env_var_name:
            raise ValueError(
                f"Unknown API: {api_name}. "
                f"Known APIs: {list(self.api_key_map.keys())}"
            )
        
        api_key = os.getenv(env_var_name)
        
        if not api_key:
            raise ValueError(
                f"API key for '{api_name}' not found in environment. "
                f"Please add {env_var_name} to your .env file. "
                f"See env_template.txt for an example."
            )
        
        # Check for placeholder values
        if "your_" in api_key.lower() or "placeholder" in api_key.lower():
            raise ValueError(
                f"API key for '{api_name}' appears to be a placeholder. "
                f"Please replace it with your actual API key in .env file."
            )
        
        return api_key
    
    def has_api_key(self, api_name: str) -> bool:
        """
        Check if an API key is available
        
        Args:
            api_name: Name of the API
        
        Returns:
            True if key is available and valid, False otherwise
        """
        try:
            self.get_api_key(api_name)
            return True
        except ValueError:
            return False
    
    def get_all_available_keys(self) -> dict:
        """
        Get status of all configured API keys
        
        Returns:
            Dict mapping API name to availability status
        """
        status = {}
        for api_name in self.api_key_map.keys():
            status[api_name] = self.has_api_key(api_name)
        return status


# Test function
if __name__ == "__main__":
    print("Testing Credentials Manager...")
    print("-" * 50)
    
    creds = CredentialsManager()
    
    # Check all API keys
    status = creds.get_all_available_keys()
    
    for api_name, available in status.items():
        status_icon = "✅" if available else "❌"
        print(f"{status_icon} {api_name}: {'Available' if available else 'Not configured'}")
    
    # Try to get OpenWeather key
    print("\n" + "-" * 50)
    try:
        key = creds.get_api_key("openweather")
        print(f"✅ OpenWeather API Key loaded: {key[:10]}...")
    except ValueError as e:
        print(f"❌ Error: {e}")

