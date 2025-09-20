# Git Auto Commit

Automatic git commit message generation using AI via OpenRouter API with beautiful terminal interface and comprehensive testing.

## Features

- **AI-Powered**: Uses OpenRouter API with multiple model support
- **Beautiful UI**: Rich terminal interface with colored output and styled boxes
- **Smart Parsing**: Robust commit message parsing with markdown cleanup
- **Interactive**: Preview, confirm, or regenerate commit messages
- **Self-Testing**: Built-in health checks and comprehensive test suite
- **Responsive**: Terminal-adaptive layouts with optimal sizing
- **Secure**: Safe git operations without shell injection
- **Fast**: Loading spinners and progress indicators
- **Conventional Commits**: Enforces best practices for commit messages

## Quick Start

### 1. Setup Environment

Ensure Python 3.11+ and Git are installed. Use pyenv for version management:

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

### 3. Configure API Key

Create `.env` file with your OpenRouter API key:

```bash
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env
```

Get your API key from https://openrouter.ai.

### 4. Configuration (Optional)

The application uses `config.toml` for configuration. If not present, defaults are used.

Create `config.toml` in the project root to customize settings:

```toml
[ai]
model = "anthropic/claude-3.5-sonnet"
api_url = "https://openrouter.ai/api/v1"
temperature = 0.4
max_tokens = 1000
timeout = 45

[format]
max_subject_length = 70
require_body_for_features = true
enforce_conventional = true
allowed_types = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]

[diff]
context_reserve = 4000
char_per_line_ratio = 80
```

### 5. Usage

```bash
# Stage changes
git add .

# Create AI commit
python3 main.py

# Skip confirmation prompt
python3 main.py -y

# Generate message without committing (dry run)
python3 main.py --dry-run

# Use a specific model
python3 main.py --model anthropic/claude-3.5-sonnet

# Test API connection
python3 main.py --test-api

# Run comprehensive self-tests
python3 main.py --test

# Enable debug logging
python3 main.py --debug
```

## What's New

This project has undergone significant improvements with the latest v2.0 release:

- **Rich Terminal Interface**: Beautiful UI with styled boxes, colors, and interactive prompts
- **Comprehensive Testing**: Full test suite with automated health checks
- **Enhanced AI Parsing**: Smart commit message extraction from complex AI responses
- **Loading Indicators**: Progress feedback with spinners and status updates
- **Self-Diagnostics**: Built-in checks for repository and API configuration

For detailed information about all changes, see [CHANGELOG.md](CHANGELOG.md).

## Dependencies

Managed via pip in `requirements.txt`. Key packages:
- `requests` - API communication with OpenRouter
- `python-dotenv` - Environment variable management
- `colorama` - Cross-platform colored terminal output
- `halo` - Beautiful loading spinners
- `rich` - Enhanced terminal formatting and UI

Development: `ruff`, `pytest`, `pytest-cov`, `pre-commit`.

## Project Structure

```
autocommit/
├── src/                    # Core package
│   ├── __init__.py
│   ├── api/                # API client modules
│   │   ├── __init__.py
│   │   ├── client.py       # HTTP client
│   │   ├── models.py       # Data models
│   │   ├── openrouter.py   # OpenRouter integration
│   │   └── tcp_check.py   # Connectivity checks
│   ├── config/             # Configuration system
│   │   ├── __init__.py
│   │   ├── loader.py       # TOML config loader
│   │   └── models.py       # Config data classes
│   ├── parsers/            # Message parsing
│   │   ├── __init__.py
│   │   ├── commit_parser.py # Commit message parsing
│   │   └── diff_parser.py  # Diff processing
│   ├── git_utils.py        # Git operations & smart diff
│   └── ui.py               # Rich terminal interface
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_diff_parser.py
│   └── test_tcp_check.py
├── main.py                # CLI entrypoint with self-tests
├── config.toml            # Configuration file (optional)
├── requirements.txt       # pip dependencies
├── setup.py               # Package configuration
└── LICENSE                # GPL-3.0
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

# Skip confirmation for automation
python3 main.py -y

# Generate message without committing
python3 main.py --dry-run
```

## Performance

- **Fast**: Optimized API calls with smart diff truncation
- **Reliable**: Comprehensive error handling and retries
- **Smart**: Context-aware parsing for complex AI responses
- **Responsive**: Terminal-adaptive UI that works on any screen size

---

**Status: Production Ready** | **Python: 3.11+** | **License: GPL-3.0** | **Version: 2.0+**