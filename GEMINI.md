# Gemini Project Context: autocommit

## Key Commands
- **Run all tests:** `pytest`
- **Run health checks:** `python3 main.py --test`
- **Check code quality:** `ruff check .`
- **Format code:** `ruff format .`

## Development Notes
- The project has a detailed refactoring plan in `todo.md`. Always consult it before making structural changes.
- The goal is a highly modular structure with separation of concerns (api, parsers, models, config, etc.).
- All data models should reside in `src/models/`.
