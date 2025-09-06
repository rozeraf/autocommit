#!/usr/bin/env python3
"""
Git Auto Commit - автоматическое создание коммитов с помощью ИИ
"""

import subprocess
import os
import sys
import requests
import json
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

def run_command(cmd: str, show_output: bool = False) -> tuple[str, int]:
    """Выполняет команду и возвращает вывод и код возврата"""
    try:
        if show_output:
            # Показываем вывод в реальном времени для команд, которые могут иметь интерактивный вывод (например, git hooks)
            result = subprocess.run(
                cmd, 
                shell=True, 
                text=True, 
                check=False
            )
            return "", result.returncode
        else:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=False
            )
            return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def get_model_info(model_name: str) -> Optional[dict]:
    """Получает информацию о модели с OpenRouter API"""
    api_url = "https://openrouter.ai/api/v1/models"
    print("Получаю информацию о модели...")
    try:
        response = requests.get(api_url, timeout=15)
        if response.status_code != 200:
            print(f"Не удалось получить список моделей (статус: {response.status_code})")
            return None
        
        models_data = response.json().get("data", [])
        for model in models_data:
            if model.get("id") == model_name:
                print(f"Информация о модели {model_name} получена.")
                return model
        
        print(f"Модель '{model_name}' не найдена.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе информации о модели: {e}")
        return None

def get_git_diff() -> Optional[str]:
    """Получает git diff --cached для staged файлов"""
    staged_files, code = run_command("git diff --cached --name-only")
    if code != 0:
        print("Ошибка при проверке staged файлов")
        return None
    
    if not staged_files.strip():
        print("Нет staged файлов для коммита.")
        print("Сначала добавьте файлы: git add <файлы>")
        return None
    
    print(f"Staged файлы: {staged_files.replace(chr(10), ', ')}")
    
    diff, code = run_command("git diff --cached")
    if code != 0:
        print("Ошибка при получении diff")
        return None
    
    return diff

def parse_ai_response(response: str) -> Optional[Tuple[str, str, str]]:
    """Парсит ответ ИИ и извлекает тип релиза и сообщения коммитов."""
    parts = response.strip().split('---')
    if len(parts) != 3:
        print(f"Ошибка: Неверный формат ответа от ИИ. Ожидалось 3 части, получено {len(parts)}.")
        print(f"Ответ: {response}")
        return None

    release_type = parts[0].strip()
    ru_commit = parts[1].strip()
    en_commit = parts[2].strip()

    if release_type.lower() not in ["patch", "minor", "major"]:
        print(f"Ошибка: Неверный тип релиза '{release_type}'.")
        return None
    if not ru_commit or not en_commit:
        print("Ошибка: Одно из сообщений коммита пустое.")
        return None

    return release_type, ru_commit, en_commit

def split_commit_message(full_message: str) -> Tuple[str, Optional[str]]:
    """Разделяет полное сообщение коммита на заголовок и описание."""
    lines = full_message.strip().split('\n', 1)
    commit_msg = lines[0].strip()
    description = None
    if len(lines) > 1 and lines[1].strip():
        description = lines[1].strip()
    return commit_msg, description

def get_smart_diff(diff: str, context_length: Optional[int]) -> str:
    """Получает умный сжатый diff для больших изменений на основе контекста модели."""
    lines = diff.split('\n')
    diff_lines = len(lines)
    diff_chars = len(diff)
    
    print(f"Размер diff: {diff_lines} строк, {diff_chars} символов")
    
    # Значения по умолчанию, если информация о модели недоступна
    line_limit = 1000
    char_limit = 10000

    if context_length:
        # Рассчитываем лимиты на основе длины контекста модели.
        # Используем 50% контекста для diff, чтобы оставить место для промпта и ответа.
        # Эвристика: 1 токен ~ 4 символа.
        char_limit = int(context_length * 0.5 * 4)
        # Эвристика: 1 строка ~ 80 символов.
        line_limit = char_limit // 80
        print(f"Динамические лимиты (контекст {context_length}): {line_limit} строк, {char_limit} символов")
    else:
        print(f"Используются лимиты по умолчанию: {line_limit} строк, {char_limit} символов")

    if diff_lines > line_limit:
        print(f"Diff слишком большой ({diff_lines} > {line_limit} строк), используется краткая сводка.")
        
        stats_output, _ = run_command("git diff --cached --stat")
        name_status_output, _ = run_command("git diff --cached --name-status")
        
        return f"""=== СТАТИСТИКА ИЗМЕНЕНИЙ ===
{stats_output}

=== ИЗМЕНЕННЫЕ ФАЙЛЫ ===
{name_status_output}

=== ПРИМЕРЫ ИЗМЕНЕНИЙ ===
{chr(10).join(lines[:50])}
...
{chr(10).join(lines[-20:])}

(Показано первые 50 и последние 20 строк из {diff_lines} всего)"""
    
    elif diff_chars > char_limit:
        print(f"Diff большой ({diff_chars} > {char_limit} символов), сокращается...")
        return diff[:char_limit] + f"\n...(показаны первые {char_limit} символов)"
    
    return diff

def generate_commit_message(diff: str, model_info: Optional[dict]) -> Optional[Tuple[str, str, str]]:
    """Генерирует сообщение коммита через OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        print("Ошибка: Не установлен OPENROUTER_API_KEY в .env файле.")
        print("Создайте .env файл с OPENROUTER_API_KEY=ваш_ключ")
        return None
    
    print(f"Используется API ключ: {api_key[:8]}...")
    print(f"URL: {api_url}")
    print(f"Модель: {model}")
    
    context_length = None
    if model_info and "context_length" in model_info:
        context_length = int(model_info["context_length"])
        print(f"Длина контекста модели: {context_length} токенов")
    else:
        print("Не удалось определить длину контекста, используются значения по умолчанию.")

    smart_diff = get_smart_diff(diff, context_length)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/rozeraf/git-auto-commit",
        "X-Title": "Git Auto Commit"
    }
    
    system_prompt = """Твоя задача - генерировать сообщения для коммитов на основе предоставленного diff.

Выходной формат должен быть СТРОГО следующим:
[ТИП_РЕЛИЗА]
---
[СООБЩЕНИЕ_НА_RU]
---
[СООБЩЕНИЕ_НА_EN]

### ПРАВИЛА:

1.  **ТИП_РЕЛИЗА**:
    - Укажи `patch`, `minor` или `major`.
    - `major`: если есть обратно несовместимые изменения (BREAKING CHANGE).
    - `minor`: если добавлена новая функциональность (`feat`).
    - `patch`: для всего остального (`fix`, `perf`, `docs` и т.д.).

2.  **СООБЩЕНИЕ_НА_RU / СООБЩЕНИЕ_НА_EN**:
    - Это полное сообщение коммита, включая заголовок, тело и футер, отформатированное по правилам Conventional Commits.
    - Генерируй идентичное по смыслу сообщение на двух языках: русском и английском.

3.  **Формат Conventional Commits**:
    - `тип(область): заголовок`
    - (пустая строка)
    - `тело коммита (опционально)`
    - (пустая строка)
    - `BREAKING CHANGE: описание (опционально)`

4.  **Типы коммитов**:
    - `feat`: Новая функциональность.
    - `fix`: Исправление ошибки.
    - `docs`: Изменения в документации.
    - `style`: Стилистические правки (форматирование и т.д.).
    - `refactor`: Рефакторинг кода без изменения поведения.
    - `perf`: Улучшение производительности.
    - `test`: Добавление или исправление тестов.
    - `build`: Изменения в системе сборки или зависимостях.
    - `ci`: Изменения в конфигурации CI/CD.
    - `chore`: Прочие изменения, не затрагивающие код.
    - `revert`: Откат предыдущего коммита.

Отвечай ТОЛЬКО в указанном формате, без лишних слов."""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Создай сообщение коммита для этих изменений:\n{smart_diff}"
            }
        ],
        "max_tokens": 400, 
        "temperature": 0.4
    }
    
    try:
        print("Генерация сообщения коммита...")
        print("Отправка запроса к API...")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=45
        )
        
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Ошибка API: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Детали ошибки: {error_data}")
            except json.JSONDecodeError:
                print(f"Тело ответа: {response.text}")
            return None
        
        response_text = response.text.strip()
        if not response_text:
            print("Пустой ответ от API")
            return None
            
        print(f"Получен ответ ({len(response_text)} символов)")
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            print(f"Первые 200 символов ответа: {response_text[:200]}")
            return None
        
        if "choices" not in data or len(data["choices"]) == 0:
            print(f"Неверный формат ответа: {data}")
            return None
        
        if "message" not in data["choices"][0]:
            print(f"Отсутствует поле message: {data['choices'][0]}")
            return None
            
        ai_response = data["choices"][0]["message"]["content"].strip()
        print(f"Ответ ИИ:\n{ai_response}")
        
        return parse_ai_response(ai_response)
        
    except requests.exceptions.Timeout:
        print("Таймаут запроса (45 сек). Попробуйте еще раз.")
        return None
    except requests.exceptions.ConnectionError:
        print("Ошибка подключения к API. Проверьте интернет.")
        return None
    except KeyboardInterrupt:
        print("\nЗапрос отменен пользователем")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def commit_changes(message: str, description: Optional[str] = None) -> bool:
    """Создает коммит с указанным сообщением"""
    full_message = message
    if description:
        full_message = f"{message}\n\n{description}"
    
    escaped_message = full_message.replace('"', '\"').replace('`', '\`')
    
    print("\nСоздание коммита...")
    
    # Используем show_output=True чтобы видеть вывод git hooks
    _, code = run_command(f'git commit -m "{escaped_message}"', show_output=True)
    
    if code == 0:
        print("Коммит успешно создан!")
        return True
    else:
        print(f"Ошибка при создании коммита (код: {code})")
        return False

def show_confirmation(
    release_type: str,
    ru_msg: str, ru_desc: Optional[str],
    en_msg: str, en_desc: Optional[str]
) -> Optional[str]:
    """Показывает подтверждение и спрашивает язык коммита."""
    print("\n--- Предпросмотр коммита ---")
    print(f"Рекомендуемый тип релиза: {release_type.upper()}")
    
    print("\n--- РУССКАЯ ВЕРСИЯ ---")
    print(f"Сообщение: {ru_msg}")
    if ru_desc:
        print(f"Описание:\n{ru_desc}")

    print("\n--- АНГЛИЙСКАЯ ВЕРСИЯ ---")
    print(f"Message: {en_msg}")
    if en_desc:
        print(f"Description:\n{en_desc}")
    
    print("-----------------------------\n")

    if len(sys.argv) > 1 and sys.argv[1] in ["-y", "--yes"]:
        print("Выбран английский язык (по умолчанию для -y).")
        return "en"

    choice = input("Сделать коммит? [Y/n/ru/en]: ").lower()
    
    if choice in ( "", "y", "yes", "en"):
        return "en"
    elif choice == "ru":
        return "ru"
    else:
        return None

def test_api_key():
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        print("Ошибка: Не установлен OPENROUTER_API_KEY в .env файле")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    try:
        print("Тестирование API ключа...")
        print(f"URL: {api_url}")
        print(f"Модель: {model}")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            print("API ключ работает!")
            return True
        else:
            print(f"Проблема с API ключом: {response.text}")
            return False
            
    except Exception as e:
        print(f"Ошибка тестирования: {e}")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test-api":
        test_api_key()
        return
    
    print("Git Auto Commit: генерация коммита для staged файлов...")
    
    _, code = run_command("git rev-parse --git-dir")
    if code != 0:
        print("Ошибка: не найден git репозиторий.")
        sys.exit(1)

    model_name = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    model_info = get_model_info(model_name)
    
    diff = get_git_diff()
    if not diff:
        sys.exit(1)
    
    result = generate_commit_message(diff, model_info)
    if not result:
        print("Не удалось сгенерировать сообщение коммита.")
        print("Попробуйте: python3 main.py --test-api")
        sys.exit(1)
    
    release_type, ru_full, en_full = result

    ru_msg, ru_desc = split_commit_message(ru_full)
    en_msg, en_desc = split_commit_message(en_full)

    chosen_lang = show_confirmation(release_type, ru_msg, ru_desc, en_msg, en_desc)

    if chosen_lang == "ru":
        print(f"\nВыбран русский язык. Рекомендуемый релиз: {release_type.upper()}")
        success = commit_changes(ru_msg, ru_desc)
    elif chosen_lang == "en":
        print(f"\nВыбран английский язык. Рекомендуемый релиз: {release_type.upper()}")
        success = commit_changes(en_msg, en_desc)
    else:
        print("Коммит отменен.")
        sys.exit(1)

    if success:
        print("Готово!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
