# Git Auto Commit

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)

Automatic git commit message generation using AI with a beautiful terminal interface and comprehensive testing.

## Features

- **Multi-Provider AI**: Supports OpenRouter, OpenAI, and Anthropic backends.
- **Beautiful UI**: Rich terminal interface with colored output and styled boxes.
- **Smart Parsing**: Robust commit message parsing with markdown cleanup.
- **Interactive**: Preview, confirm, or regenerate commit messages.
- **Self-Testing**: Built-in health checks and a comprehensive test suite.
- **Conventional Commits**: Enforces best practices for commit messages.

## Quick Start

### 1. Setup Environment

Ensure Python 3.11+ and Git are installed. You can use pyenv for version management:

```bash
# Install pyenv (if needed)
curl https://pyenv.run | bash
# Add to ~/.zshrc and source it

pyenv install 3.11.13
pyenv local 3.11.13
```

### 2. Install Dependencies

```bash
# Clone repo
git clone https://github.com/rozeraf/autocommit.git
cd autocommit

# Install with pip
pip install -r requirements.txt
```

### 3. Configure API Keys

Create a `.env` file with your API keys. You only need to add the keys for the providers you intend to use.

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your keys from:
- **OpenRouter**: https://openrouter.ai
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys

### 4. Configuration (Optional)

The application uses `config.toml` for all settings. A default configuration is used if the file is not present.

Create `config.toml` in the project root to customize settings. Example:

```toml
# Default provider to use
base_provider = "openrouter"

# Settings for each provider
[ai.providers.openrouter]
model = "deepseek/deepseek-chat-v3.1:free"
temperature = 0.3
env_key = "OPENROUTER_API_KEY"

[ai.providers.openai] 
model = "gpt-4o-mini"
temperature = 0.3
env_key = "OPENAI_API_KEY"

[ai.providers.anthropic]
model = "claude-3-5-sonnet-20240620"
temperature = 0.3
env_key = "ANTHROPIC_API_KEY"

# Other settings
[format]
max_subject_length = 70

[context]
auto_detect = true
```

### 5. Usage

```bash
# Stage changes
git add .

# Create an AI-generated commit message
python3 main.py

# --- Provider Management ---

# Use a specific provider (e.g., openai)
python3 main.py --provider openai

# List all available providers
python3 main.py --list-providers

# Test connectivity for all configured providers
python3 main.py --test-providers

# Get detailed info about a provider
python3 main.py --provider-info anthropic

# --- Other Options ---

# Skip confirmation prompt
python3 main.py -y

# Generate message without committing (dry run)
python3 main.py --dry-run

# Run comprehensive self-tests
python3 main.py --test
```

## What's New

This project has undergone significant improvements with the latest v2.3 release:

- **Multi-Provider AI**: Switch between OpenRouter, OpenAI, and Anthropic.
- **New CLI Commands**: Manage and test providers directly from the command line.
- **Enhanced Test Suite**: Full test coverage for the new provider system.

For detailed information about all changes, see [CHANGELOG.md](CHANGELOG.md).

## Dependencies

Managed via pip in `requirements.txt`. Key packages:
- `requests` - API communication
- `python-dotenv` - Environment variable management
- `colorama` - Cross-platform colored terminal output
- `halo` - Beautiful loading spinners
- `rich` - Enhanced terminal formatting and UI

Development: `ruff`, `pytest`, `pytest-cov`.

## Project Structure

```
autocommit/
├── src/
│   ├── api/                # AI provider implementations
│   ├── config/             # Configuration system
│   ├── context/            # Context detection module
│   ├── models/             # Data models (dataclasses)
│   ├── parsers/            # Message and diff parsing
│   ├── git_utils.py        # Git operations
│   └── ui.py               # Rich terminal interface
├── tests/
│   ├── test_providers.py   # Tests for AI providers
│   ├── test_factory.py     # Tests for ProviderFactory
│   ├── test_manager.py     # Tests for AIProviderManager
│   └── ...                 # Other existing tests
├── main.py                 # CLI entrypoint
├── config.toml             # Main configuration file
├── requirements.txt        # pip dependencies
└── LICENSE
```

## Testing

The project includes comprehensive testing:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run application self-tests
python3 main.py --test

# Test API connection
python3 main.py --test-api
```

Test coverage includes:
- AI response parsing edge cases
- Markdown and code block cleanup
- Complex AI response handling
- Whitespace and formatting
- Conventional commit detection

## Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Install dev deps: `pip install -r requirements.txt`
4. Run tests: `pytest`
5. Commit with AI: `git add . && python3 main.py`
6. Push and create PR

Ensure Python 3.11+ and all tests pass before submitting.

For detailed information about changes and version history, see [CHANGELOG.md](CHANGELOG.md).

## License

GPL-3.0 - See [LICENSE](LICENSE) file for details.

## Screenshots

The application features a beautiful terminal interface with:
- Styled commit preview boxes
- Interactive confirmation prompts
- Loading spinners with progress feedback
- Colored output and statistics
- Responsive terminal layouts

## Advanced Usage

```bash
# Use different AI models
python3 main.py --model anthropic/claude-3.5-sonnet
python3 main.py --model openrouter/sonoma-dusk-alpha

# Debug mode for troubleshooting
python3 main.py --debug

# Skip confirmation
python3 main.py -y

# Generate message without committing
python3 main.py --dry-run
```

## Performance

- **Fast**: Optimized API calls with smart diff truncation
- **Reliable**: Comprehensive error handling and retries
- **Smart**: Context-aware parsing for complex AI responses
- **Responsive**: Terminal-adaptive UI that works on any screen size
