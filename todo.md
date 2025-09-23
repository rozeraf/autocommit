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

### 2.1 Базовый интерфейс провайдеров
```
src/
├── api/
│   ├── base.py       # BaseAIProvider абстрактный класс
│   ├── factory.py    # ProviderFactory для создания провайдеров
│   ├── openrouter.py # существующий, адаптировать к BaseAIProvider
│   ├── openai.py     # новый OpenAI провайдер
│   ├── anthropic.py  # новый Anthropic провайдер
│   └── local.py      # для Ollama/локальных моделей
```

**BaseAIProvider интерфейс:**
```python
class BaseAIProvider:
    def generate_commit_message(self, diff: str, context: str) -> CommitMessage
    def test_connectivity(self) -> bool
    def get_model_info(self) -> ModelInfo
    def get_required_env_vars(self) -> List[str]
```

### 2.2 Конфигурационная система провайдеров

**Структура config.toml:**
```toml
[ai]
# Базовый провайдер (по умолчанию)
base_provider = "openrouter"
# Контекстное переключение
context_switching = true

[ai.providers.openrouter]
model = "deepseek/deepseek-chat-v3.1:free"
api_url = "https://openrouter.ai/api/v1"
temperature = 0.3
max_tokens = 1000
timeout = 45
env_key = "OPENROUTER_API_KEY"

[ai.providers.openai] 
model = "gpt-4o-mini"
api_url = "https://api.openai.com/v1"
temperature = 0.3
max_tokens = 1000
timeout = 30
env_key = "OPENAI_API_KEY"

[ai.providers.anthropic]
model = "claude-3-5-sonnet-20241022"
api_url = "https://api.anthropic.com/v1"
temperature = 0.3
max_tokens = 1000
timeout = 60
env_key = "ANTHROPIC_API_KEY"

[ai.providers.local]
model = "llama3.1:8b"
api_url = "http://localhost:11434/api"
temperature = 0.3
max_tokens = 1000
timeout = 120
# Локальные модели не требуют API ключа

# Правила переключения контекста
[ai.context_rules]
# Большие рефакторинги -> более мощная модель
large_changes = { provider = "openai", threshold_lines = 500 }
# Документация -> быстрая модель
documentation = { provider = "openrouter", file_patterns = ["*.md", "*.rst"] }
# Тесты -> специализированная модель  
tests = { provider = "anthropic", file_patterns = ["test_*.py", "*_test.py"] }
```

### 2.3 Фабрика провайдеров и менеджер

```python
# src/api/factory.py
class ProviderFactory:
    @staticmethod
    def create_provider(provider_name: str, config: dict) -> BaseAIProvider
    
    @staticmethod
    def get_available_providers() -> List[str]
    
    @staticmethod
    def validate_provider_config(provider_name: str, config: dict) -> bool

# src/api/manager.py  
class AIProviderManager:
    def __init__(self, config: Config)
    def get_provider_for_context(self, diff: str, context: str) -> BaseAIProvider
    def get_base_provider(self) -> BaseAIProvider
    def test_all_providers(self) -> Dict[str, bool]
```

**Логика переключения:**
1. Проверить правила context_rules в конфиге
2. Если совпадение найдено - использовать указанный провайдер
3. Иначе использовать base_provider
4. Fallback на первый доступный провайдер

### 2.4 CLI интеграция провайдеров

**Новые аргументы:**
```bash
gac --provider openai           # принудительный выбор провайдера
gac --list-providers           # показать доступные провайдеры
gac --test-providers           # проверить подключение всех провайдеров
gac --provider-info openai     # информация о провайдере
```

**Environment variables:**
```bash
# В .env или системных переменных
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 2.5 Промпты для разных провайдеров

**Конфигурация промптов:**
```toml
[ai.prompts]
# Базовый промпт (по умолчанию)
default = """Your task is to generate..."""

# Специфичные для провайдеров
openrouter = """Enhanced prompt for OpenRouter models..."""
openai = """GPT-optimized prompt with specific formatting..."""
anthropic = """Claude-style conversational prompt..."""
local = """Simplified prompt for local models..."""
```

**Загрузка промптов:**
- Сначала ищет prompt для конкретного провайдера
- Fallback на default промпт
- Fallback на hardcoded DEFAULT_SYSTEM_PROMPT



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

## 7. Порядок реализации

1. **Фаза 1:** Создать config.toml и config модуль
2. **Фаза 2:** Реализовать систему мульти-провайдеров AI (пункт 2)
3. **Фаза 3:** Разделить api_client.py на api/ и parsers/
4. **Фаза 4:** Добавить модели данных
5. **Фаза 5:** Реализовать контекстную систему
6. **Фаза 6:** Добавить интерактивные функции
7. **Фаза 7:** Внедрить анализатор качества
8. **Фаза 8:** Добавить тесты для новых модулей

Каждая фаза должна сохранять работоспособность существующего функционала.