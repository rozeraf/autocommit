# Autocommit

Утилита CLI для автоматической генерации содержательных git-коммитов.

## Установка

```bash
# Локально в проект
pnpm add -D autocommit

# Глобально
pnpm install -g autocommit

# Одноразово через npx / pnpm dlx
npx autocommit
pnpm dlx autocommit
```

## Быстрый старт

1. Создайте `.env` на основе `.env.example` (при необходимости).
2. (Опционально) Добавьте раздел `autocommit` в `package.json` или файл `.autocommitrc.*`.
3. В терминале:
   ```bash
   autocommit         # полный режим
   autocommit --short # однострочное сообщение
   autocommit --dry-run # посмотреть сообщение без коммита
   ```

## Конфигурация

### Переменные окружения (`.env`)

- `AUTOCOMMIT_PREFIX` — префикс заголовка (по умолчанию `Auto-commit:`).
- `AUTOCOMMIT_SHORT_TEMPLATE` — шаблон для `--short`, поддерживает плейсхолдеры:
  - `{files}` — список файлов,
  - `{count}` — число файлов.
- `AUTOCOMMIT_INCLUDE_DIFF_STAT` — `true`/`false`: включать статистику `git diff --stat`.

### Файл конфигурации

В `package.json`:

```json
"autocommit": {
  "prefix": "[auto]",
  "shortTemplate": "{files}{count,?+: +{count} more}",
  "longTemplate": "{prefix} {summary}\n\nChanges:\n{stat}"
}
```

Или в файле `.autocommitrc.json`:

```json
{
  "prefix": "[auto]",
  "includeKeywords": false,
  "maxSummaryLength": 200
}
```

## Опции CLI

- `--no-stage` — не выполнять `git add .`.
- `--dry-run` — показать сообщение без коммита.
- `--short` — однострочное сообщение.
- `-c, --config <path>` — путь к конфигу.
- `--verbose` — подробный лог.

## Шаблоны

Шаблоны используют плейсхолдеры:

- `{prefix}` — префикс из конфига.
- `{summary}` — автоматически сформированный краткий список изменений.
- `{stat}` — вывод `git diff --stat`.
- `{files}` — названия файлов через запятую.
- `{count}` — число изменённых файлов.

## Примеры

```bash
autocommit --dry-run
```

```
Auto-commit: src/index.js (modified) | README.md (added)

Changes:
 src/index.js |  5 +++--
 README.md    |  2 ++
```

```bash
autocommit --short --dry-run
```

```
[auto] src/index.js, README.md +2 more
```

---

Лучшая практика — протестировать все опции и задокументировать дополнительные сценарии по мере развития проекта.
