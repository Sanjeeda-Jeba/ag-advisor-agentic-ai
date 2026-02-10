"""
USDA Soil Data Access API Client - Real Data Only
Uses USDA Web Soil Survey REST API - NO MOCK DATA FALLBACKS

API Documentation: https://sdmdataaccess.sc.egov.usda.gov/
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api_clients.base_client import BaseAPIClient
from typing import Dict, Any, Optional
import requests
import json


class USDASoilClient(BaseAPIClient):
    """
    USDA Soil Data Access API Client - Real Data Only
    
    Provides REAL soil data for US locations from USDA NRCS.
    
    Key Features:
    - Uses USDA Soil Data Access (SDA) REST API
    - Works for US locations only
    - NO mock data - fails if API unavailable
    - Returns actual USDA soil survey data
    
    Data includes:
    - pH levels (soil acidity/alkalinity)
    - Organic matter content
    - Soil texture (clay, sand, silt percentages)
    - Cation exchange capacity (CEC)
    - And more soil properties
    
    Note: This API is free but works ONLY for US locations.
    """
    
    # USDA REST API endpoint
    BASE_URL = "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest"
    
    def __init__(self):
        """Initialize USDA soil client"""
        super().__init__()
        self.timeout = 30  # USDA API can be slow
    
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
        Get REAL soil properties from USDA for a US location
        
        Args:
            lat: Latitude (US locations only: 24-50°N)
            lon: Longitude (US locations only: -125 to -66°W)
            location: Location name (will be geocoded to lat/lon)
        
        Returns:
            Dict with REAL USDA soil information:
            {
                "success": True,
                "location": {"lat": 41.8781, "lon": -93.0977, "name": "Iowa"},
                "source": "USDA NRCS Soil Data Access",
                "properties": {
                    "ph": {"value": 6.8, "unit": "pH", "label": "pH Level"},
                    "organic_matter": {"value": 2.5, "unit": "%", "label": "Organic Matter"},
                    ...
                }
            }
        
        Raises:
            ValueError: If location is outside US or invalid
            Exception: If USDA API fails (NO FALLBACK)
        """
        # Validate parameters
        self._validate_params(lat=lat, lon=lon, location=location)
        
        # If location name provided, geocode it first
        location_name = None
        if location:
            location_name = location
            coords = self._geocode_location(location)
            if not coords:
                return {
                    "success": False,
                    "error": f"Could not geocode location: {location}. Please provide valid US location or coordinates."
                }
            lat = coords["lat"]
            lon = coords["lon"]
        
        # Validate US coordinates
        if not self._is_us_location(lat, lon):
            return {
                "success": False,
                "error": f"Location ({lat}, {lon}) appears to be outside the United States. USDA data is only available for US locations."
            }
        
        # Get REAL USDA data - NO FALLBACK
        try:
            return self._get_usda_soil_data(lat, lon, location_name)
        except Exception as e:
            # NO FALLBACK - return error
            return {
                "success": False,
                "error": f"USDA API error: {str(e)}",
                "message": "Unable to fetch real soil data from USDA. The API may be temporarily unavailable."
            }
    
    def _is_us_location(self, lat: float, lon: float) -> bool:
        """
        Check if coordinates are within US boundaries
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            True if location is in continental US, Alaska, or Hawaii
        """
        # Continental US
        if 24.0 <= lat <= 50.0 and -125.0 <= lon <= -66.0:
            return True
        
        # Alaska
        if 51.0 <= lat <= 72.0 and -180.0 <= lon <= -129.0:
            return True
        
        # Hawaii
        if 18.0 <= lat <= 23.0 and -161.0 <= lon <= -154.0:
            return True
        
        return False
    
    def _get_usda_soil_data(
        self,
        lat: float,
        lon: float,
        location_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get REAL soil data from USDA Soil Data Access REST API
        
        Uses the simplified REST endpoint with SQL queries.
        Documentation: https://sdmdataaccess.sc.egov.usda.gov/
        
        NO MOCK DATA - Returns real USDA soil survey data only.
        """
        # SQL query to get soil properties at a point location
        # This uses the mapunit and component tables
        sql_query = f"""
        SELECT TOP 1
            c.compname as component_name,
            c.comppct_r as component_percent,
            chorizon.hzdept_r as depth_top,
            chorizon.hzdepb_r as depth_bottom,
            chorizon.ph1to1h2o_r as ph,
            chorizon.om_r as organic_matter,
            chorizon.cec7_r as cation_exchange,
            chorizon.claytotal_r as clay_percent,
            chorizon.sandtotal_r as sand_percent,
            chorizon.silttotal_r as silt_percent,
            chorizon.ksat_r as saturated_hydraulic_conductivity,
            chorizon.awc_r as available_water_capacity
        FROM 
            SDA_Get_Mukey_from_intersection_with_WktWgs84('point({lon} {lat})') AS mukey
            INNER JOIN mapunit ON mapunit.mukey = mukey.mukey
            INNER JOIN component AS c ON c.mukey = mapunit.mukey
            INNER JOIN chorizon ON chorizon.cokey = c.cokey
        WHERE 
            chorizon.hzdept_r = 0
        ORDER BY c.comppct_r DESC
        """
        
        # Prepare REST API request
        # USDA REST API expects form data with 'query' and 'format'
        payload = {
            'query': sql_query,
            'format': 'JSON'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            print(f"📡 Calling USDA API for location ({lat}, {lon})...")
            
            # Make POST request to USDA REST API
            response = requests.post(
                self.BASE_URL,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # USDA API returns data in different formats
            # It can be a list directly, or a dict with 'Table' key
            if isinstance(data, list):
                table_data = data
            elif isinstance(data, dict) and 'Table' in data:
                table_data = data['Table']
            else:
                return {
                    "success": False,
                    "error": "Unexpected response format from USDA API.",
                    "message": "Unable to parse USDA soil data response."
                }
            
            # Check if we got results
            if not table_data or len(table_data) == 0:
                return {
                    "success": False,
                    "error": "No soil data available for this specific location.",
                    "message": "USDA soil survey may not cover this exact point. Try a nearby location."
                }
            
            # Extract first result (most dominant component)
            soil_data = table_data[0]
            
            # Format the response
            return self._format_usda_response(soil_data, lat, lon, location_name)
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "USDA API request timed out after 30 seconds.",
                "message": "The USDA server is slow or unresponsive. Please try again later."
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"USDA API request failed: {str(e)}",
                "message": "Could not connect to USDA Soil Data Access API."
            }
        
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON response from USDA API: {str(e)}",
                "message": "USDA API returned unexpected data format."
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "message": "An error occurred while processing USDA soil data."
            }
    
    def _format_usda_response(
        self,
        soil_data,  # Can be list or dict
        lat: float,
        lon: float,
        location_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format USDA API response into our standard format
        
        Args:
            soil_data: Raw data from USDA API (list or dict)
            lat: Latitude
            lon: Longitude
            location_name: Optional location name
        
        Returns:
            Formatted soil data dict
        """
        # USDA API returns data as a list in column order
        # Parse based on whether it's a list or dict
        if isinstance(soil_data, list):
            # Data is returned as list in SQL SELECT order:
            # [component_name, component_percent, depth_top, depth_bottom,
            #  ph, organic_matter, cation_exchange, clay_percent,
            #  sand_percent, silt_percent, hydraulic_conductivity, water_capacity]
            try:
                component_name = soil_data[0] if len(soil_data) > 0 else None
                component_percent = soil_data[1] if len(soil_data) > 1 else None
                depth_top = soil_data[2] if len(soil_data) > 2 else None
                depth_bottom = soil_data[3] if len(soil_data) > 3 else None
                ph = soil_data[4] if len(soil_data) > 4 else None
                organic_matter = soil_data[5] if len(soil_data) > 5 else None
                cec = soil_data[6] if len(soil_data) > 6 else None
                clay = soil_data[7] if len(soil_data) > 7 else None
                sand = soil_data[8] if len(soil_data) > 8 else None
                silt = soil_data[9] if len(soil_data) > 9 else None
                ksat = soil_data[10] if len(soil_data) > 10 else None
                awc = soil_data[11] if len(soil_data) > 11 else None
            except (IndexError, TypeError) as e:
                return {
                    "success": False,
                    "error": f"Failed to parse USDA response: {str(e)}"
                }
        else:
            # Fallback: treat as dict
            component_name = soil_data.get('component_name')
            component_percent = soil_data.get('component_percent')
            depth_top = soil_data.get('depth_top')
            depth_bottom = soil_data.get('depth_bottom')
            ph = soil_data.get('ph')
            organic_matter = soil_data.get('organic_matter')
            cec = soil_data.get('cation_exchange')
            clay = soil_data.get('clay_percent')
            sand = soil_data.get('sand_percent')
            silt = soil_data.get('silt_percent')
            ksat = soil_data.get('saturated_hydraulic_conductivity')
            awc = soil_data.get('available_water_capacity')
        
        # Build properties dict
        properties = {}
        
        if ph is not None:
            properties['ph'] = {
                'value': round(float(ph), 2),
                'unit': 'pH',
                'label': 'Soil pH',
                'description': 'Soil acidity/alkalinity (0-14 scale, 7 is neutral)'
            }
        
        if organic_matter is not None:
            properties['organic_matter'] = {
                'value': round(float(organic_matter), 2),
                'unit': '%',
                'label': 'Organic Matter',
                'description': 'Percentage of organic matter in soil'
            }
        
        if cec is not None:
            properties['cation_exchange'] = {
                'value': round(float(cec), 2),
                'unit': 'meq/100g',
                'label': 'Cation Exchange Capacity',
                'description': 'Ability of soil to retain and exchange nutrients'
            }
        
        if clay is not None:
            properties['clay'] = {
                'value': round(float(clay), 1),
                'unit': '%',
                'label': 'Clay Content',
                'description': 'Percentage of clay particles'
            }
        
        if sand is not None:
            properties['sand'] = {
                'value': round(float(sand), 1),
                'unit': '%',
                'label': 'Sand Content',
                'description': 'Percentage of sand particles'
            }
        
        if silt is not None:
            properties['silt'] = {
                'value': round(float(silt), 1),
                'unit': '%',
                'label': 'Silt Content',
                'description': 'Percentage of silt particles'
            }
        
        if ksat is not None:
            properties['hydraulic_conductivity'] = {
                'value': round(float(ksat), 2),
                'unit': 'µm/s',
                'label': 'Saturated Hydraulic Conductivity',
                'description': 'Rate at which water moves through saturated soil'
            }
        
        if awc is not None:
            properties['water_capacity'] = {
                'value': round(float(awc), 3),
                'unit': 'cm/cm',
                'label': 'Available Water Capacity',
                'description': 'Amount of water soil can hold for plant use'
            }
        
        # Build final response
        result = {
            'success': True,
            'source': 'USDA NRCS Soil Data Access',
            'location': {
                'lat': lat,
                'lon': lon
            },
            'component': {
                'name': str(component_name) if component_name else 'Unknown',
                'percent': float(component_percent) if component_percent else None,
                'depth_range': f"{depth_top or 0}-{depth_bottom or 0} cm"
            },
            'properties': properties
        }
        
        if location_name:
            result['location']['name'] = location_name
        
        # Add data quality note
        if len(properties) < 3:
            result['note'] = "⚠️ Limited soil data available for this location. Some properties may be missing from USDA survey."
        
        return result
    
    def _geocode_location(self, location: str) -> Optional[Dict[str, float]]:
        """
        Convert location name to coordinates using OpenWeatherMap
        
        Args:
            location: Location name (e.g., "Iowa", "California", "Ames, Iowa")
        
        Returns:
            Dict with lat and lon, or None if geocoding fails
        """
        try:
            from src.config.credentials import CredentialsManager
            creds = CredentialsManager()
            api_key = creds.get_api_key("openweather")
            
            if not api_key:
                print("⚠️ OpenWeatherMap API key not found for geocoding")
                return None
            
            url = "http://api.openweathermap.org/geo/1.0/direct"
            params = {
                "q": f"{location}, USA",  # Add USA to prioritize US results
                "limit": 1,
                "appid": api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                return {
                    "lat": data[0]["lat"],
                    "lon": data[0]["lon"]
                }
            return None
            
        except Exception as e:
            print(f"⚠️ Geocoding failed: {e}")
            return None


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("USDA Soil Client - REAL DATA ONLY (No Mock Fallbacks)")
    print("=" * 80)
    
    client = USDASoilClient()
    
    test_locations = [
        ("Iowa", None, None),
        ("Ames, Iowa", None, None),
        (None, 41.8781, -93.0977),  # Des Moines, Iowa
        ("California", None, None),
    ]
    
    for location, lat, lon in test_locations:
        print(f"\n{'=' * 80}")
        if location:
            print(f"📍 Testing: {location}")
        else:
            print(f"📍 Testing: Coordinates ({lat}, {lon})")
        print("=" * 80)
        
        try:
            if location:
                result = client.get_soil_data(location=location)
            else:
                result = client.get_soil_data(lat=lat, lon=lon)
            
            if result.get("success"):
                print(f"✅ SUCCESS - Real USDA Data!")
                print(f"   Source: {result['source']}")
                print(f"   Location: {result['location']}")
                
                if 'component' in result:
                    print(f"   Soil Component: {result['component']['name']} ({result['component']['percent']}%)")
                    print(f"   Depth: {result['component']['depth_range']}")
                
                print(f"\n🌱 Soil Properties:")
                for prop_name, prop_data in result['properties'].items():
                    print(f"   • {prop_data['label']}: {prop_data['value']} {prop_data['unit']}")
                
                if 'note' in result:
                    print(f"\n   {result['note']}")
            else:
                print(f"❌ FAILED")
                print(f"   Error: {result.get('error')}")
                print(f"   Message: {result.get('message')}")
        
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
    
    print(f"\n{'=' * 80}")
    print("Testing complete!")
    print("=" * 80)

