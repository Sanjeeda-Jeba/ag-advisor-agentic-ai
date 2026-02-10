"""
Alternative Soil Data Sources
Using USDA Soil Data Access API (US locations) or mock data
"""

from src.api_clients.base_client import BaseAPIClient
from typing import Dict, Any, Optional
import requests


class SoilClientV2(BaseAPIClient):
    """
    Alternative Soil Data Client
    
    Uses multiple sources:
    1. USDA Soil Data Access API (US locations only, more reliable)
    2. Mock data fallback (for development/demo)
    
    Note: USDA API requires registration but is free
    """
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize soil client
        
        Args:
            use_mock: If True, use mock data directly (fast, no API needed)
        """
        super().__init__()
        self.use_mock = use_mock
        self.usda_base_url = "https://sdmdataaccess.nrcs.usda.gov/SDMAccess"
    
    def _validate_params(self, **kwargs) -> bool:
        """Validate request parameters"""
        if "lat" not in kwargs or "lon" not in kwargs:
            if "location" not in kwargs:
                raise ValueError(
                    "Either 'lat' and 'lon' OR 'location' must be provided"
                )
        return True
    
    def get_soil_data(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get soil properties for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            location: Location name (will be geocoded)
        
        Returns:
            Dict with soil information
        """
        # Validate parameters
        self._validate_params(lat=lat, lon=lon, location=location)
        
        # If location name provided, geocode it first
        if location:
            coords = self._geocode_location(location)
            if not coords:
                return {
                    "success": False,
                    "error": f"Could not geocode location: {location}"
                }
            lat = coords["lat"]
            lon = coords["lon"]
        
        # For now, use mock data (reliable and fast)
        # USDA API requires registration and is US-only
        if self.use_mock:
            return self._get_mock_data(lat, lon, location)
        
        # Try USDA API for US locations (if implemented)
        # For now, fall back to mock
        return self._get_mock_data(lat, lon, location)
    
    def _get_mock_data(
        self, 
        lat: float, 
        lon: float, 
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate realistic mock soil data
        
        This provides consistent, realistic soil data for development/demo.
        Values are based on typical agricultural soil properties.
        """
        import random
        import hashlib
        
        # Use location to generate consistent "random" data
        # Same location = same data (deterministic)
        seed_string = f"{lat}_{lon}_{location}"
        seed = int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # Generate realistic soil properties based on location
        # Adjust ranges based on latitude (rough approximation)
        if lat is not None:
            if 25 < lat < 50:  # US Midwest/Great Plains
                ph_range = (6.0, 7.2)
                soc_range = (2.0, 4.0)
                nitrogen_range = (0.15, 0.35)
            elif lat > 50:  # Northern regions
                ph_range = (5.5, 6.8)
                soc_range = (3.0, 5.0)
                nitrogen_range = (0.2, 0.4)
            else:  # Southern/tropical
                ph_range = (6.5, 7.5)
                soc_range = (1.5, 3.0)
                nitrogen_range = (0.1, 0.25)
        else:
            ph_range = (6.0, 7.0)
            soc_range = (2.0, 3.0)
            nitrogen_range = (0.15, 0.25)
        
        # Generate values
        ph_value = round(random.uniform(*ph_range), 2)
        soc_value = round(random.uniform(*soc_range), 2)
        nitrogen_value = round(random.uniform(*nitrogen_range), 2)
        
        # Soil texture (clay + sand + silt should sum to ~100)
        clay = round(random.uniform(20, 40), 2)
        sand = round(random.uniform(30, 50), 2)
        silt = round(100 - clay - sand, 2)
        
        # Ensure silt is positive
        if silt < 0:
            silt = round(random.uniform(20, 30), 2)
            sand = round(100 - clay - silt, 2)
        
        return {
            "success": True,
            "location": {"lat": lat, "lon": lon},
            "source": "mock_data",
            "properties": {
                "phh2o": {
                    "value": ph_value,
                    "unit": "pH",
                    "label": "pH Level",
                    "description": "Soil acidity/alkalinity (0-14 scale)"
                },
                "soc": {
                    "value": soc_value,
                    "unit": "g/kg",
                    "label": "Organic Carbon",
                    "description": "Soil organic carbon content"
                },
                "nitrogen": {
                    "value": nitrogen_value,
                    "unit": "cg/kg",
                    "label": "Nitrogen Content",
                    "description": "Total nitrogen content"
                },
                "clay": {
                    "value": clay,
                    "unit": "g/kg",
                    "label": "Clay Content",
                    "description": "Percentage of clay particles"
                },
                "sand": {
                    "value": sand,
                    "unit": "g/kg",
                    "label": "Sand Content",
                    "description": "Percentage of sand particles"
                },
                "silt": {
                    "value": silt,
                    "unit": "g/kg",
                    "label": "Silt Content",
                    "description": "Percentage of silt particles"
                }
            }
        }
    
    def _geocode_location(self, location: str) -> Optional[Dict[str, float]]:
        """Convert location name to coordinates"""
        try:
            from src.config.credentials import CredentialsManager
            creds = CredentialsManager()
            api_key = creds.get_api_key("openweather")
            
            url = "http://api.openweathermap.org/geo/1.0/direct"
            params = {
                "q": location,
                "limit": 1,
                "appid": api_key
            }
            
            response = self._make_request("GET", url, params=params)
            data = response.json()
            
            if data and len(data) > 0:
                return {
                    "lat": data[0]["lat"],
                    "lon": data[0]["lon"]
                }
            return None
            
        except Exception:
            return None


# Test function
if __name__ == "__main__":
    print("Testing Soil Client V2 (Mock Data)...")
    print("-" * 70)
    
    client = SoilClientV2(use_mock=True)
    
    test_locations = [
        ("Iowa", 41.8781, -93.0977),
        ("California", 36.7783, -119.4179),
        ("Texas", 31.9686, -99.9018),
    ]
    
    for location_name, lat, lon in test_locations:
        print(f"\n📍 Location: {location_name}")
        print("-" * 70)
        
        soil = client.get_soil_data(lat=lat, lon=lon)
        
        if soil.get("success"):
            print(f"✅ Success! (Source: {soil.get('source', 'unknown')})")
            print(f"\n🌱 Soil Properties:")
            for prop_name, prop_data in soil["properties"].items():
                print(f"  • {prop_data['label']}: {prop_data['value']} {prop_data['unit']}")
        else:
            print(f"❌ Error: {soil.get('error')}")

