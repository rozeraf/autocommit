"""
TCP connection checker for API testing without making actual requests

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

import socket
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def check_tcp_connection(host: str, port: int, timeout: float = 4.0) -> bool:
    """
    Check if TCP connection to host:port is possible

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception as e:
        logger.debug(f"TCP connection failed: {e}")
        return False


def check_openrouter_connectivity() -> bool:
    """
    Check if OpenRouter API is reachable via TCP

    Returns:
        True if OpenRouter is reachable, False otherwise
    """
    return check_tcp_connection("openrouter.ai", 443, timeout=5.0)


def parse_url_for_tcp_check(url: str) -> Tuple[str, int]:
    """
    Parse URL to extract host and port for TCP check

    Args:
        url: Full URL (e.g., https://openrouter.ai/api/v1/chat/completions)

    Returns:
        Tuple of (host, port)
    """
    import urllib.parse

    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or "openrouter.ai"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    return host, port
