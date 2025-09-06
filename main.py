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
            # Показываем вывод в реальном времени для важных команд (типа husky)
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

def get_git_diff() -> Optional[str]:
    """Получает git diff --cached"""
    # Сначала добавляем все файлы
    print("📁 Добавляю файлы...")
    _, code = run_command("git add .")
    if code != 0:
        print("❌ Ошибка при добавлении файлов")
        return None
    
    # Получаем diff
    diff, code = run_command("git diff --cached")
    if code != 0:
        print("❌ Ошибка при получении diff")
        return None
    
    if not diff.strip():
        print("ℹ️  Нет изменений для коммита")
        return None
    
    return diff

def parse_ai_response(response: str) -> Tuple[str, Optional[str]]:
    """Парсит ответ ИИ и извлекает сообщение и описание коммита"""
    lines = response.strip().split('\n')
    
    commit_msg = ""
    description = ""
    
    # Ищем разделение на сообщение и описание
    if len(lines) == 1:
        # Только одна строка - это сообщение коммита
        commit_msg = lines[0].strip()
    else:
        # Первая строка - сообщение, остальные - описание
        commit_msg = lines[0].strip()
        if len(lines) > 1:
            # Пропускаем пустые строки и берем описание
            desc_lines = [line.strip() for line in lines[1:] if line.strip()]
            if desc_lines:
                description = '\n'.join(desc_lines)
    
    # Убираем возможные префиксы и кавычки
    commit_msg = commit_msg.replace('Сообщение:', '').replace('Message:', '').strip()
    commit_msg = commit_msg.strip('"\'`')
    
    return commit_msg, description if description else None

def generate_commit_message(diff: str) -> Optional[Tuple[str, Optional[str]]]:
    """Генерирует сообщение коммита через OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Не установлен OPENROUTER_API_KEY")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [
            {
                "role": "system",
                "content": """Генерируй сообщения коммитов по conventional commits. 
Формат ответа:
- Первая строка: краткое сообщение коммита (до 50 символов)
- Вторая строка: пустая (если есть описание)
- Остальные строки: подробное описание (если нужно)

Используй типы: feat, fix, docs, style, refactor, test, chore.
Отвечай ТОЛЬКО текстом коммита, без лишних слов."""
            },
            {
                "role": "user",
                "content": f"Создай сообщение коммита для этих изменений:\n{diff}"
            }
        ]
    }
    
    try:
        print("🤖 Генерирую сообщение коммита...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
        
        data = response.json()
        ai_response = data["choices"][0]["message"]["content"].strip()
        
        commit_msg, description = parse_ai_response(ai_response)
        
        return commit_msg, description
        
    except Exception as e:
        print(f"❌ Ошибка при обращении к API: {e}")
        return None

def commit_changes(message: str, description: Optional[str] = None) -> bool:
    """Создает коммит с указанным сообщением"""
    # Формируем полное сообщение коммита
    full_message = message
    if description:
        full_message = f"{message}\n\n{description}"
    
    # Экранируем кавычки в сообщении
    escaped_message = full_message.replace('"', '\\"').replace('`', '\\`')
    
    print("🔄 Создаю коммит...")
    print("=" * 50)
    
    # Используем show_output=True чтобы видеть вывод husky и других хуков
    _, code = run_command(f'git commit -m "{escaped_message}"', show_output=True)
    
    print("=" * 50)
    
    if code == 0:
        print(f"✅ Коммит успешно создан!")
        return True
    else:
        print(f"❌ Ошибка при создании коммита (код: {code})")
        return False

def show_confirmation(commit_msg: str, description: Optional[str]) -> bool:
    """Показывает подтверждение перед коммитом"""
    print("\n" + "=" * 60)
    print("📝 ПРЕДПРОСМОТР КОММИТА")
    print("=" * 60)
    print(f"Сообщение: {commit_msg}")
    if description:
        print(f"Описание: {description}")
    print("=" * 60)
    
    # Спрашиваем подтверждение
    if len(sys.argv) > 1 and sys.argv[1] in ["-y", "--yes"]:
        return True
    
    confirm = input("Сделать коммит? [Y/n]: ").lower()
    return confirm in ("", "y", "yes", "да")

def test_api_key():
    """Тестирует API ключ"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        print("❌ Не установлен OPENROUTER_API_KEY в .env файле")
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
        print("🧪 Тестирую API ключ...")
        print(f"🌐 URL: {api_url}")
        print(f"🤖 Модель: {model}")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📡 Статус: {response.status_code}")
        if response.status_code == 200:
            print("✅ API ключ работает!")
            return True
        else:
            print(f"❌ Проблема с API ключом: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Основная функция"""
    # Если передан флаг --test-api, тестируем API и выходим
    if len(sys.argv) > 1 and sys.argv[1] == "--test-api":
        test_api_key()
        return
    
    print("🤖 Git Auto Commit - генерация коммита для staged файлов...")
    
    # Проверяем что мы в git репозитории
    _, code = run_command("git rev-parse --git-dir")
    if code != 0:
        print("❌ Не найден git репозиторий")
        sys.exit(1)
    
    # Получаем изменения только для staged файлов
    diff = get_git_diff()
    if not diff:
        sys.exit(1)
    
    # Генерируем сообщение коммита
    result = generate_commit_message(diff)
    if not result:
        print("❌ Не удалось сгенерировать сообщение коммита")
        print("💡 Попробуй: python3 gac.py --test-api")
        sys.exit(1)
    
    commit_msg, description = result
    
    # Показываем подтверждение
    if show_confirmation(commit_msg, description):
        success = commit_changes(commit_msg, description)
        if success:
            print("🎉 Готово!")
        else:
            sys.exit(1)
    else:
        print("❌ Коммит отменен")
        sys.exit(1)

if __name__ == "__main__":
    main()