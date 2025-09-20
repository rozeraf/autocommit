# Git Auto Commit Refactoring TODO

## 1. Архитектурные улучшения

Вот обновлённый вариант с пометкой о выполнении 1.3 и 1.4:

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

## 2. Контекстная система

### 2.1 Детектор контекста
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

### 2.2 CLI интеграция
```
# Новые аргументы в main.py
-c, --context     # предустановленный контекст
-h, --hint        # кастомная подсказка
--auto-context    # автоопределение контекста
```

**Приоритет:** custom hint > explicit context > auto-detected context > none

### 2.3 Менеджер контекста
**Функции:**
- Загружает пресеты из config.toml
- Объединяет автоопределенный и явно указанный контекст
- Генерирует финальную подсказку для ИИ
- Сохраняет историю использованных контекстов

## 3. Новые функции

### 3.1 Интерактивное редактирование
```
src/
├── interactive/
│   ├── __init__.py
│   ├── editor.py     # запуск $EDITOR для коммита
│   └── selector.py   # выбор файлов для staging
```

**Логика:** После генерации коммита предложить отредактировать в текстовом редакторе. Использовать $EDITOR или fallback на nano/vim.

### 3.2 Шаблонная система
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

### 3.3 Анализатор качества
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

## 4. CLI команды

### 4.1 Новые флаги
```
gac --interactive     # интерактивный выбор файлов
gac --template feat   # использовать шаблон
gac --analyze         # только анализ без коммита  
gac --edit           # редактировать после генерации
```

### 4.2 Конфигурационные команды
```
gac --config-check   # проверить конфигурацию
gac --config-init    # создать дефолтный config.toml
```

## 5. Обновленная структура проекта

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

## 6. Порядок реализации

1. **Фаза 1:** Создать config.toml и config модуль
2. **Фаза 2:** Разделить api_client.py на api/ и parsers/
3. **Фаза 3:** Добавить модели данных
4. **Фаза 4:** Реализовать контекстную систему
5. **Фаза 5:** Добавить интерактивные функции
6. **Фаза 6:** Внедрить анализатор качества

Каждая фаза должна сохранять работоспособность существующего функционала.