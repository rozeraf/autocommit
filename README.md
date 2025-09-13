# Git Auto Commit

Automatic git commit message generation using AI via OpenRouter API.

## 🚀 Quick Start

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

# Install with Poetry
curl -sSL https://install.python-poetry.org | python3 -
poetry install
poetry run pre-commit install
```

### 3. Configure API Key

Create `.env` file:

```bash
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env
echo "OPENROUTER_MODEL=openrouter/sonoma-dusk-alpha" >> .env
```

Get key from https://openrouter.ai.

### 4. Usage

```bash
# Stage changes
git add .

# Create AI commit
poetry run python main.py

# Or with confirmation skip
poetry run python main.py -y

# Test API
poetry run python main.py --test-api
```

## 🛠️ Features

- Analyzes Git changes for meaningful commit messages
- Integrates with OpenRouter AI models
- Secure Git operations without shell injection
- CLI-friendly interface

## 📦 Dependencies

Managed via Poetry in `pyproject.toml`. Key packages:
- `requests` for API calls
- `python-dotenv` for environment vars

Development: `ruff`, `pytest`, `mypy`, `pre-commit`.

## 📁 Project Structure

```
autocommit/
├── src/                    # Core package
│   ├── __init__.py
│   ├── api_client.py      # OpenRouter integration
│   └── git_utils.py       # Git operations
├── main.py                # CLI entrypoint
├── pyproject.toml         # Poetry config
├── requirements.txt       # Legacy pip support
└── LICENSE                # GPL-3.0
```

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Install dev deps: `poetry install --with dev`
4. Commit: `git add . && poetry run python main.py`
5. Push and create PR

Ensure Python 3.11.13 and run `poetry run pytest` before submitting.

## 📄 License

GPL-3.0 - See [LICENSE](LICENSE) file for details.

---

**Status: Production Ready** | **Python: 3.11+** | **License: GPL-3.0**
