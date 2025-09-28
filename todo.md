# Git Auto Commit Refactoring TODO

## 1. Архитектурные улучшения
<details>
<summary><strong>✅ 1.1</strong></summary>

### Разделение API модуля

* Создан `src/api/client.py`
* Создан `src/api/openrouter.py`
* Перенесена HTTP логика

</details>

<details>
<summary><strong>✅ 1.2</strong></summary>

**Логика:** Отделить логику парсинга от API клиентов. `commit_parser.py` отвечает за обработку ответов ИИ, `diff_parser.py` - за анализ и подготовку диффов.

</details>

<details>
<summary><strong>✅ 1.3</strong></summary>

### Единый конфигурационный файл

```
config.toml  # в корне проекта
```

**Структура:**

```toml
[ai]
model = "anthropic/claude-3.5-sonnet"
temperature = 0.4
max_tokens = 250
timeout = 45

[format]
max_subject_length = 50
require_body_for_features = true
enforce_conventional = true
allowed_types = ["feat", "fix", "docs", "style", "refactor", "test", "chore"]

[context]
wip_keywords = ["TODO", "FIXME", "WIP"]
auto_detect = true

[context.presets]
wip = "Work in progress - saving current state"
checkpoint = "Partial implementation checkpoint"
breaking = "Contains breaking changes"
hotfix = "Urgent production fix"
experimental = "Experimental feature implementation"
```

</details>

<details>
<summary><strong>✅ 1.4</strong></summary>

### Конфигурационный модуль

```
src/
├── config/
│   ├── __init__.py
│   ├── loader.py     # TOML загрузка с fallback на defaults
│   └── models.py     # dataclass конфиги с валидацией
```

**Логика:** `loader.py` ищет config.toml в текущей директории, затем в домашней, затем использует defaults. `models.py` содержит typehinted конфиги с валидацией значений.

</details>

<details>
<summary><strong>✅ 1.5</strong></summary>

### Модели данных
```
src/
├── models/
│   ├── __init__.py
│   ├── commit.py     # CommitMessage, CommitStats
│   └── context.py    # ContextHint, ContextPreset
```

**Логика:** Вся типобезопасность в одном месте. `commit.py` содержит структуры для коммитов, `context.py` - для контекстных подсказок.

</details>

## 2. Система мульти-провайдеров AI

<details>
<summary><strong>✅ 2.1</strong></summary>

```tree
src/
├── api/
│   ├── providers/
│   │   ├── base.py       # BaseAIProvider абстрактный класс
│   │   ├── openrouter.py # Адаптирован к BaseAIProvider
│   │   ├── openai.py     # Новый OpenAI провайдер
│   │   ├── anthropic.py  # Новый Anthropic провайдер
│   │   └── local.py      # Для Ollama/локальных моделей
│   ├── factory.py        # ProviderFactory для создания провайдеров
│   └── manager.py        # AIProviderManager
```

**`BaseAIProvider` интерфейс:**
```python
class BaseAIProvider(ABC):
    @abstractmethod
    def generate_commit_message(self, user_content: str, system_prompt: str) -> str:
        ...

    @abstractmethod
    def test_connectivity(self) -> bool:
        ...

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        ...

    @abstractmethod
    def get_required_env_vars(self) -> List[str]:
        ...
```

</details>
<details>
<summary><strong>✅ 2.2</strong></summary>

**Структура `config.toml`:**
```toml
[ai]
base_provider = "openrouter"
context_switching = true

[ai.providers.openrouter]
model = "deepseek/deepseek-chat-v3.1:free"
api_url = "https://openrouter.ai/api/v1"
env_key = "OPENROUTER_API_KEY"

[ai.providers.openai] 
model = "gpt-4o-mini"
api_url = "https://api.openai.com/v1"
env_key = "OPENAI_API_KEY"

[ai.providers.anthropic]
model = "claude-3-5-sonnet-20240620"
api_url = "https://api.anthropic.com/v1"
env_key = "ANTHROPIC_API_KEY"

[ai.context_rules]
large_changes = { provider = "openai", threshold_lines = 500 }
documentation = { provider = "openrouter", file_patterns = ["*.md", "*.rst"] }
tests = { provider = "anthropic", file_patterns = ["test_*.py", "*_test.py"] }
```

</details>
<details>
<summary><strong>✅ 2.3</strong></summary>

**`ProviderFactory` в `src/api/factory.py`:**
```python
class ProviderFactory:
    @staticmethod
    def create_provider(provider_name: str, config: dict) -> BaseAIProvider:
        ...
    
    @staticmethod
    def get_available_providers() -> List[str]:
        ...
```

**`AIProviderManager` в `src/api/manager.py`:**
```python
class AIProviderManager:
    def __init__(self, config: Config):
        ...

    def get_provider_for_context(self, diff: str) -> BaseAIProvider:
        ...

    def get_base_provider(self) -> BaseAIProvider:
        ...

    def test_all_providers() -> Dict[str, bool]:
        ...
```

</details>

<details>
<summary><strong>✅ 2.4</strong></summary>

**Новые аргументы:**
```bash
gac --provider openai           # Принудительный выбор провайдера
gac --list-providers           # Показать доступные провайдеры
gac --test-providers           # Проверить подключение всех провайдеров
gac --provider-info openai     # Информация о провайдере
```

**Переменные окружения:**
```bash
# В .env или системных переменных
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

</details>

<details>
<summary><strong>✅ 2.5</strong></summary>

**Конфигурация промптов в `config.toml`:**
```toml
[ai.prompts]
default = """Your task is to generate..."""
openrouter = """Enhanced prompt for OpenRouter models..."""
openai = """GPT-optimized prompt with specific formatting..."""
anthropic = """Claude-style conversational prompt..."""
```

**Логика загрузки:**
1. Ищет промпт для конкретного провайдера.
2. Fallback на `default` промпт.
3. Fallback на `DEFAULT_SYSTEM_PROMPT` в коде.

</details>

## 3. Контекстная система

<details>
<summary><strong>✅ 3.1</strong></summary>

### 3.1 Детектор контекста
```
src/
├── context/
│   ├── __init__.py
│   ├── detector.py   # автоопределение по diff
│   ├── manager.py    # управление контекстами
│   └── hints.py      # генерация подсказок для ИИ
```

**Логика детектора:**
- Сканирует diff на ключевые слова (TODO, FIXME, test, package.json)
- Анализирует соотношение добавленного/удаленного кода
- Проверяет типы файлов (конфиги, тесты, документация)

</details>

<details>
<summary><strong>✅ 3.2</strong></summary>

### 3.2 CLI интеграция
```
# Новые аргументы в main.py
-c, --context     # предустановленный контекст
-h, --hint        # кастомная подсказка
--auto-context    # автоопределение контекста
```

**Приоритет:** custom hint > explicit context > auto-detected context > none

</details>

<details>
<summary><strong>✅ 3.3</strong></summary>

### 3.3 Менеджер контекста
**Функции:**
- Загружает пресеты из config.toml
- Объединяет автоопределенный и явно указанный контекст
- Генерирует финальную подсказку для ИИ
- Сохраняет историю использованных контекстов

</details>

## 4. Новые функции

### 4.1 Интерактивное редактирование
```
src/
├── interactive/
│   ├── __init__.py
│   ├── editor.py     # запуск $EDITOR для коммита
│   └── selector.py   # выбор файлов для staging
```

**Логика:** После генерации коммита предложить отредактировать в текстовом редакторе. Использовать $EDITOR или fallback на nano/vim.

### 4.2 Шаблонная система
```
src/
├── templates/
│   ├── __init__.py
│   ├── manager.py    # загрузка и применение шаблонов
│   └── builtin.py    # встроенные шаблоны
```

**Шаблоны в config.toml:**
```toml
[templates]
feature = "feat({scope}): {description}\n\n- {details}"
bugfix = "fix({scope}): {description}\n\nFixes: {issue}"
```

### 4.3 Анализатор качества
```
src/
├── analyzer/
│   ├── __init__.py
│   ├── quality.py    # проверка качества коммита
│   └── rules.py      # правила валидации
```

**Метрики:**
- Длина subject line
- Соответствие Conventional Commits
- Наличие описания для крупных изменений
- Грамматические ошибки (базовые)

## 5. CLI команды

### 5.1 Новые флаги
```
gac --interactive     # интерактивный выбор файлов
gac --template feat   # использовать шаблон
gac --analyze         # только анализ без коммита  
gac --edit           # редактировать после генерации
```

### 5.2 Конфигурационные команды
```
gac --config-check   # проверить конфигурацию
gac --config-init    # создать дефолтный config.toml
```

## 6. Обновленная структура проекта

```
git-auto-commit/
├── config.toml
├── main.py
├── src/
│   ├── __init__.py
│   ├── ui.py                    # существующий
│   ├── git_utils.py            # существующий
│   ├── api/
│   ├── parsers/
│   ├── config/
│   ├── models/
│   ├── context/
│   ├── interactive/
│   ├── templates/
│   └── analyzer/
└── tests/
```

## 7. Улучшения качества и надежности

### 7.1 Отказоустойчивость и обработка ошибок
<details>
<summary><strong>🔄 7.1.1</strong></summary>

**API Retry с экспоненциальной задержкой:**
```python
# src/api/client.py
class HTTPClientWithRetry:
    def __init__(self, max_retries=3, backoff_factor=2):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def request_with_retry(self, method, url, **kwargs):
        # Реализация exponential backoff для всех API вызовов
```

**Circuit Breaker Pattern:**
```python
# src/api/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        # Предотвращение каскадных сбоев при проблемах с API
```

</details>

<details>
<summary><strong>🔄 7.1.2</strong></summary>

**Улучшенные сообщения об ошибках:**
```python
# src/errors/user_messages.py
ERROR_MESSAGES = {
    "missing_api_key": "API key for {provider} not found. Set {env_var} environment variable.",
    "network_error": "Network connection failed. Check your internet connection and try again.",
    "invalid_config": "Configuration error in {file}: {details}",
}
```

</details>

### 7.2 Безопасность
<details>
<summary><strong>🔄 7.2.1</strong></summary>

**Валидация API ключей:**
```python
# src/security/validation.py
class APIKeyValidator:
    @staticmethod
    def validate_key_format(key: str, provider: str) -> bool:
        # Проверка формата ключей перед использованием
    
    @staticmethod 
    def test_key_validity(provider: BaseAIProvider) -> bool:
        # Проверка действительности ключа через test API call
```

</details>

<details>
<summary><strong>🔄 7.2.2</strong></summary>

**Security scanning integration:**
```bash
# В CI/CD pipeline или pre-commit hooks
pip-audit --desc --output json
safety check --json
```

**Конфигурация в pyproject.toml:**
```toml
[tool.safety]
ignore = []  # Игнорируемые уязвимости с обоснованием
```

</details>

### 7.3 Наблюдаемость
<details>
<summary><strong>🔄 7.3.1</strong></summary>

**Структурированное логирование:**
```python
# src/logging/structured.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
            "provider": getattr(record, 'provider', None),
            "commit_hash": getattr(record, 'commit_hash', None)
        })
```

</details>

<details>
<summary><strong>🔄 7.3.2</strong></summary>

**Audit logging:**
```python
# src/logging/audit.py
class AuditLogger:
    def log_commit_generation(self, provider: str, success: bool, duration: float):
        # Журнал успешных/неудачных генераций коммитов
    
    def log_config_change(self, section: str, old_value: Any, new_value: Any):
        # Аудит изменений конфигурации
```

</details>

### 7.4 Оптимизация производительности
<details>
<summary><strong>🔄 7.4.1</strong></summary>

**Оптимизация больших diff:**
```python
# src/parsers/optimized_diff_parser.py
class OptimizedDiffParser:
    def __init__(self, max_lines_threshold=1000):
        self.max_lines_threshold = max_lines_threshold
    
    def parse_large_diff(self, diff: str) -> SmartDiff:
        # Chunking и selective parsing для больших изменений
        # Приоритизация важных частей diff
```

</details>

<details>
<summary><strong>🔄 7.4.2</strong></summary>

**Кэширование API ответов:**
```python
# src/cache/response_cache.py
class CommitMessageCache:
    def __init__(self, cache_dir: Path, ttl_hours=24):
        # Кэш для идентичных diff с TTL
    
    def get_cached_response(self, diff_hash: str) -> Optional[CommitMessage]:
        # Возврат кэшированного ответа для идентичных diff
```

**Конфигурация кэширования:**
```toml
[cache]
enabled = true
ttl_hours = 24
max_entries = 1000
cache_identical_diffs = true
```

</details>

### 7.5 Улучшения UX
<details>
<summary><strong>🔄 7.5.1</strong></summary>

**Консистентные прогресс индикаторы:**
```python
# src/ui/progress.py
class ProgressManager:
    def __init__(self):
        self.spinner = Halo()
    
    @contextmanager
    def api_request(self, provider: str):
        self.spinner.start(f"Generating commit with {provider}...")
        try:
            yield
            self.spinner.succeed(f"Generated with {provider}")
        except Exception as e:
            self.spinner.fail(f"Failed: {str(e)}")
```

</details>

<details>
<summary><strong>🔄 7.5.2</strong></summary>

**Расширенные help сообщения:**
```python
# main.py
def create_parser():
    parser = argparse.ArgumentParser(
        description="AI-powered git commit message generator",
        epilog="""
Examples:
  gac                           # Auto-generate commit for staged changes
  gac --provider openai         # Use specific AI provider
  gac --hint "fixing memory leak" # Provide context hint
  gac --interactive            # Choose files interactively
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
```

</details>

### 7.6 Качество кода
<details>
<summary><strong>🔄 7.6.1</strong></summary>

**Улучшенные type hints:**
```python
# Везде в кодовой базе
from typing import Protocol, TypeVar, Generic, Literal, TypedDict

class AIProviderProtocol(Protocol):
    def generate_commit_message(self, content: str, prompt: str) -> str: ...

T = TypeVar('T', bound=BaseAIProvider)
```

</details>

<details>
<summary><strong>🔄 7.6.2</strong></summary>

**Comprehensive docstrings:**
```python
def generate_commit_message(
    self, 
    user_content: str, 
    system_prompt: str
) -> str:
    """Generate commit message using AI provider.
    
    Args:
        user_content: Git diff and context information
        system_prompt: Instructions for AI model
        
    Returns:
        Generated commit message text
        
    Raises:
        APIError: When API request fails
        ValidationError: When response format is invalid
        
    Example:
        >>> provider.generate_commit_message("feat: add new feature", "...")
        "feat(ui): add login button\\n\\n- Add styled login button..."
    """
```

</details>

<details>
<summary><strong>🔄 7.6.3</strong></summary>

**Расширенное тестирование:**
```python
# tests/integration/
class TestFullWorkflow:
    def test_end_to_end_commit_generation(self):
        # Полный тест от CLI до commit creation
        
    def test_provider_failover(self):
        # Тест переключения между провайдерами при ошибках
        
    def test_large_repository_performance(self):
        # Тест производительности на больших репозиториях
```

**Coverage targets:**
```toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/test_*"]

[tool.coverage.report]
fail_under = 85
show_missing = true
```

</details>

## 8. Порядок реализации

1. **Фаза 1:** ✅ Создать config.toml и config модуль
2. **Фаза 2:** ✅ Реализовать систему мульти-провайдеров AI
3. **Фаза 3:** Разделить api_client.py на api/ и parsers/
4. **Фаза 4:** Добавить модели данных
5. **Фаза 5:** Реализовать контекстную систему
6. **Фаза 6:** Добавить интерактивные функции
7. **Фаза 7:** 🔄 Внедрить улучшения качества и надежности (пункт 7)
8. **Фаза 8:** Внедрить анализатор качества
9. **Фаза 9:** Добавить тесты для новых модулей

Каждая фаза должна сохранять работоспособность существующего функционала.