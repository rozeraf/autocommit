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

---

## Refactoring and Improvement Plan

### Stage 1: Small Fixes & Improvements (Done)

- [x] Rename `tests/test_api_client.py` to `tests/test_commit_parser.py`.
- [x] Eliminate `OpenRouterClient` duplication in `main.py`.
- [x] Replace `toml` library with built-in `tomllib`.
- [x] Remove insecure logging of the API key.
- [x] Fix `ruff` linting errors.

### Stage 2: Structural Refactoring (Done)

- [x] Create `src/models/` directory.
- [x] Move and reorganize all data models (`CommitMessage`, `ModelInfo`, `AppConfig`, etc.) into the new directory.

### Stage 3: Expand Test Coverage (Next)

- [x] Add missing tests, primarily for the critical `src/git_utils.py` module.
