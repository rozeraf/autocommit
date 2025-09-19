"""
Universal HTTP client for Git Auto Commit

Copyright (C) 2025 rozeraf
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


class HTTPClient:
    """Universal HTTP client with retry logic and session management"""
    
    def __init__(self, 
                 base_url: str = "",
                 timeout: int = 30,
                 max_retries: int = 3,
                 backoff_factor: float = 1.0,
                 status_forcelist: list = None):
        """
        Initialize HTTP client
        
        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for retry delays
            status_forcelist: HTTP status codes to retry on
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure retry strategy
        if status_forcelist is None:
            status_forcelist = [429, 500, 502, 503, 504]
            
        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def get(self, 
            endpoint: str, 
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = None) -> requests.Response:
        """Make GET request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if self.base_url else endpoint
        timeout = timeout or self.timeout
        
        logger.debug(f"GET {url}")
        return self.session.get(url, headers=headers, timeout=timeout)
    
    def post(self, 
             endpoint: str, 
             data: Optional[Dict[str, Any]] = None,
             json: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None,
             timeout: Optional[int] = None) -> requests.Response:
        """Make POST request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if self.base_url else endpoint
        timeout = timeout or self.timeout
        
        logger.debug(f"POST {url}")
        return self.session.post(
            url, 
            data=data, 
            json=json, 
            headers=headers, 
            timeout=timeout
        )
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
