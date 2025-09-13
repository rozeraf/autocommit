"""
OpenRouter API client for generating commit messages
"""

import os
import json
from typing import Optional, Tuple
import requests


def get_model_info(model_name: str) -> Optional[dict]:
    """Gets model information from the OpenRouter API"""
    api_url = "https://openrouter.ai/api/v1/models"
    print("Getting model information...")
    try:
        response = requests.get(api_url, timeout=15)
        if response.status_code != 200:
            print(f"Failed to get model list (status: {response.status_code})")
            return None
        
        models_data = response.json().get("data", [])
        for model in models_data:
            if model.get("id") == model_name:
                print(f"Model information for {model_name} received.")
                return model
        
        print(f"Model '{model_name}' not found.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error requesting model information: {e}")
        return None


def parse_ai_response(full_message: str) -> Tuple[str, Optional[str]]:
    """Splits the full commit message into a subject and description."""
    lines = full_message.strip().split('\n', 1)
    commit_msg = lines[0].strip()
    description = None
    if len(lines) > 1 and lines[1].strip():
        description = lines[1].strip()
    return commit_msg, description


def generate_commit_message(diff: str, model_info: Optional[dict]) -> Optional[Tuple[str, Optional[str]]]:
    """Generates a commit message via the OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        print("Error: OPENROUTER_API_KEY is not set in the .env file.")
        print("Create a .env file with OPENROUTER_API_KEY=your_key")
        return None
    
    print(f"Using API key: {api_key[:8]}...")
    print(f"URL: {api_url}")
    print(f"Model: {model}")
    
    context_length = None
    if model_info and "context_length" in model_info:
        context_length = int(model_info["context_length"])
        print(f"Model context length: {context_length} tokens")
    else:
        print("Could not determine context length, using default values.")

    from . import git_utils
    smart_diff = git_utils.get_smart_diff(diff, context_length)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/rozeraf/git-auto-commit",
        "X-Title": "Git Auto Commit"
    }
    
    system_prompt = '''Your task is to generate a commit message based on the provided diff, following the Conventional Commits specification.

RULES:
1. The output must be ONLY the commit message text, without any extra words or explanations.
2. The message must be in English.
3. The format is: `type(scope): subject`
    - Followed by an optional longer body.
    - Followed by an optional `BREAKING CHANGE:` footer.
4. Use the following types:
    - `feat`: A new feature.
    - `fix`: A bug fix.
    - `docs`: Documentation only changes.
    - `style`: Code style changes (formatting, etc).
    - `refactor`: A code change that neither fixes a bug nor adds a feature.
    - `perf`: A code change that improves performance.
    - `test`: Adding missing tests or correcting existing tests.
    - `build`: Changes that affect the build system or external dependencies.
    - `ci`: Changes to CI configuration files and scripts.
    - `chore`: Other changes that don't modify src or test files.
    - `revert`: Reverts a previous commit.
5. The body, if present, should have a header, a list of changes starting with `-`, and an optional footer.'''

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Create a commit message for these changes:\n{smart_diff}"
            }
        ],
        "max_tokens": 250, 
        "temperature": 0.4
    }
    
    try:
        print("Generating commit message...")
        print("Sending request to API...")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=45
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except json.JSONDecodeError:
                print(f"Response body: {response.text}")
            return None
        
        response_text = response.text.strip()
        if not response_text:
            print("Empty response from API")
            return None
            
        print(f"Received response ({len(response_text)} characters)")
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"First 200 characters of response: {response_text[:200]}")
            return None
        
        if "choices" not in data or len(data["choices"]) == 0:
            print(f"Invalid response format: {data}")
            return None
        
        if "message" not in data["choices"][0]:
            print(f"Missing message field: {data['choices'][0]}")
            return None
            
        ai_response = data["choices"][0]["message"]["content"].strip()
        print(f"AI Response:\n{ai_response}")
        
        return parse_ai_response(ai_response)
        
    except requests.exceptions.Timeout:
        print("Request timeout (45s). Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        print("API connection error. Check your internet connection.")
        return None
    except KeyboardInterrupt:
        print("\nRequest cancelled by user")
        return None
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_api_key() -> bool:
    """Tests if the OpenRouter API key is valid and working"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        print("Error: OPENROUTER_API_KEY is not set in the .env file.")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    try:
        print("Testing API key...")
        print(f"URL: {api_url}")
        print(f"Model: {model}")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("API key is working!")
            return True
        else:
            print(f"Problem with API key: {response.text}")
            return False
            
    except Exception as e:
        print(f"Testing error: {e}")
        return False