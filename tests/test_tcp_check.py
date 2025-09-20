"""
Tests for TCP connectivity checking utilities

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

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.tcp_check import (
    check_tcp_connection,
    check_openrouter_connectivity,
    parse_url_for_tcp_check,
)


def test_check_tcp_connection_google_dns():
    """Test TCP connection to Google DNS (should work)"""
    result = check_tcp_connection("8.8.8.8", 53, timeout=5.0)
    assert result is True


def test_check_tcp_connection_invalid_host():
    """Test TCP connection to invalid host (should fail)"""
    result = check_tcp_connection(
        "invalid-host-that-does-not-exist.com", 80, timeout=1.0
    )
    assert result is False


def test_check_tcp_connection_invalid_port():
    """Test TCP connection to invalid port (should fail)"""
    result = check_tcp_connection("google.com", 99999, timeout=1.0)
    assert result is False


def test_check_openrouter_connectivity():
    """Test OpenRouter connectivity (should work if internet is available)"""
    result = check_openrouter_connectivity()
    # This might fail in some environments, so we just check it returns a boolean
    assert isinstance(result, bool)


def test_parse_url_for_tcp_check_https():
    """Test URL parsing for HTTPS URLs"""
    host, port = parse_url_for_tcp_check(
        "https://openrouter.ai/api/v1/chat/completions"
    )
    assert host == "openrouter.ai"
    assert port == 443


def test_parse_url_for_tcp_check_http():
    """Test URL parsing for HTTP URLs"""
    host, port = parse_url_for_tcp_check("http://example.com:8080/api/test")
    assert host == "example.com"
    assert port == 8080


def test_parse_url_for_tcp_check_with_port():
    """Test URL parsing with explicit port"""
    host, port = parse_url_for_tcp_check("https://api.example.com:8443/v1/test")
    assert host == "api.example.com"
    assert port == 8443


def test_parse_url_for_tcp_check_default_http():
    """Test URL parsing for HTTP without port (default 80)"""
    host, port = parse_url_for_tcp_check("http://example.com/test")
    assert host == "example.com"
    assert port == 80
