#!/usr/bin/env python3
# Отслеживание изменений файлов и автоматический коммит

import os
import time
import subprocess
from datetime import datetime

def run_command(command: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)

def check_changes():
    success, _ = run_command("git diff --quiet")
    if success:
        success, _ = run_command("git diff --cached --quiet")
        if success:
            return False
    return True

def auto_commit():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Обнаружены изменения, создаю коммит...")
    
    success, output = run_command("git add .")
    if not success:
        print(f"Ошибка добавления файлов: {output}")
        return False
    
    commit_message = f"Auto commit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success, output = run_command(f'git commit -m "{commit_message}"')
    
    if not success:
        print(f"Ошибка коммита: {output}")
        return False
    
    print(f"Коммит создан: {commit_message}")
    
    success, output = run_command("python auto_deploy.py --commit")
    
    if success:
        print("Автоматический деплой выполнен")
        return True
    else:
        print(f"Ошибка деплоя: {output}")
        return False

def main():
    print("Запускаю отслеживание изменений файлов...")
    print("Для остановки нажмите Ctrl+C")
    
    last_check = 0
    check_interval = 10
    
    try:
        while True:
            current_time = time.time()
            
            if current_time - last_check >= check_interval:
                if check_changes():
                    auto_commit()
                last_check = current_time
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Отслеживание остановлено")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
