# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2025-09-20

### Added
- Context detection system (`src/context/detector.py`) to analyze changes and provide hints to the AI.
- New CLI arguments to control commit context:
  - `-c, --context`: Use a named preset from the configuration (e.g., `wip`).
  - `-i, --hint`: Provide a one-time, custom hint directly to the AI.
- Configuration for context presets and keywords in `config.toml` under `[context]` and `[context.presets]`.
- System prompt is now configurable in `config.toml` under `[ai.prompts]`.

### Changed
- The AI prompt now includes a `Context:` section to make the model aware of hints.
- `main.py` logic was updated to handle context priority: custom hint > preset context > auto-detection.
- `OpenRouterClient` was refactored to accept and use the prompt context.


## [2.1.0] - 2025-09-20

### Added
- Comprehensive test suite for the `git_utils` module, covering various command execution scenarios.

### Changed
- Major refactoring of data models into a dedicated `src/models` package to improve architecture and type safety.
- Replaced the `toml` library with the built-in `tomllib` (Python 3.11+) to reduce dependencies.

### Fixed
- Corrected the API client instantiation logic in `main.py` to prevent redundant sessions.
- Fixed failing tests for `run_command` by correctly asserting for empty string output on errors.

### Removed
- Old model files (`src/api/models.py`, `src/config/models.py`) after refactoring.

### Chore
- Fixed `ruff` linting errors (E712) for boolean comparisons in tests.
- Renamed test files for better clarity and consistency.
- Removed insecure logging of partial API keys.


## [2.0.0] - 2025-09-19

### Added
- Rich terminal UI module (`src/ui.py`) with beautiful formatting
- Comprehensive test suite with 10+ test cases for AI response parsing
- Self-testing functionality with `--test` flag for health checks
- Loading spinners with progress feedback using `halo` library
- Colored terminal output with `colorama` for cross-platform support
- Smart commit message parsing with markdown cleanup
- Mermaid diagram support in AI responses
- Complex AI response parsing with conventional commit detection
- Interactive confirmation prompts (Y/N/Regenerate)
- Command preview with git syntax
- Word/character statistics display
- Length warnings for commit message readability
- Terminal-adaptive layouts with optimal sizing
- Debug logging mode with `--debug` flag
- Enhanced error handling and user guidance

### Changed
- **BREAKING**: Extracted UI logic from main.py to separate `src/ui.py` module
- Improved commit message parsing accuracy with better regex patterns
- Enhanced API response handling with robust cleanup
- Switched from Poetry to pip for dependency management
- Updated project structure with modular architecture

### Fixed
- Fixed overly aggressive regex patterns that removed commit message content
- Fixed newline handling to preserve subject/description separation
- Fixed bullet point preservation in descriptions
- Fixed import path issues in test files
- Fixed Rich library border style compatibility issues

### Removed
- Poetry lock file and configuration
- Mock commit message generation from main flow
- Redundant error handling and verbose logging

## [1.0.0] - 2025-09-14

### Added
- Initial AI-powered git auto commit tool
- OpenRouter API integration with multiple model support
- Git diff parsing and smart compression for large changes
- Commit message generation with Conventional Commits format
- Confirmation prompts and dry-run mode
- Model override functionality with `--model` flag
- Robust retry logic for API requests
- Timeout support for git operations
- Modular architecture with `src` package
- Error handling for command execution
- Bilingual commit message support (later simplified to English-only)

### Changed
- Refactored from single file to modular package structure
- Simplified commit message generation to English-only
- Improved command execution to use argument lists instead of shell strings
- Enhanced error handling and timeout management

### Fixed
- Shell injection vulnerabilities in git command execution
- Error handling for various git command failures
- Timeout issues with long-running operations

## [0.1.0] - 2025-09-06

### Added
- Basic git auto commit functionality
- OpenRouter API integration
- Simple commit message generation
- Basic confirmation prompts
- Initial project setup with requirements.txt

---

**Legend:**
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes