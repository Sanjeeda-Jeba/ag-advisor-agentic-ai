"""
Base API Client
Abstract base class for all API clients
"""

from abc import ABC, abstractmethod
import requests
from typing import Dict, Any, Optional
import time


class BaseAPIClient(ABC):
    """
    Abstract base class for API clients
    
    Provides common functionality:
    - HTTP request handling
    - Error handling
    - Rate limiting
    - Response validation
    """
    
    def __init__(self):
        """Initialize base client"""
        self.session = requests.Session()
        self.timeout = 30  # Default timeout in seconds
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    def _wait_for_rate_limit(self):
        """Implement simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> requests.Response:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            headers: Request headers
            data: Form data
            json: JSON data
        
        Returns:
            Response object
        
        Raises:
            requests.exceptions.RequestException: On request failure
        """
        self._wait_for_rate_limit()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                json=json,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout:
            raise requests.exceptions.RequestException(
                f"Request to {url} timed out after {self.timeout}s"
            )
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.RequestException(
                f"Failed to connect to {url}. Check your internet connection."
            )
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise requests.exceptions.RequestException(
                    "Authentication failed. Check your API key."
                )
            elif status_code == 429:
                raise requests.exceptions.RequestException(
                    "Rate limit exceeded. Please wait before making more requests."
                )
            elif status_code == 404:
                raise requests.exceptions.RequestException(
                    "Resource not found. Check your request parameters."
                )
            else:
                raise requests.exceptions.RequestException(
                    f"HTTP {status_code} error: {str(e)}"
                )
    
    def get(self, url: str, params: Optional[Dict] = None, 
            headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make GET request
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
        
        Returns:
            JSON response as dict
        """
        response = self._make_request("GET", url, params=params, headers=headers)
        return response.json()
    
    def post(self, url: str, data: Optional[Dict] = None,
             json: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make POST request
        
        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Request headers
        
        Returns:
            JSON response as dict
        """
        response = self._make_request("POST", url, data=data, json=json, headers=headers)
        return response.json()
    
    @abstractmethod
    def _validate_params(self, **kwargs) -> bool:
        """
        Validate request parameters
        Should be implemented by subclasses
        
        Args:
            **kwargs: Parameters to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If parameters are invalid
        """
        pass
    
    def __del__(self):
        """Cleanup: close session"""
        if hasattr(self, 'session'):
            self.session.close()

