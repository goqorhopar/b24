#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import json

def check_github_actions_status(repo_owner, repo_name, token=None):
    """
    Проверка статуса последнего workflow в GitHub Actions
    """
    try:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        if token:
            headers["Authorization"] = f"token {token}"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("workflow_runs"):
                latest_run = data["workflow_runs"][0]
                return {
                    "status": latest_run["status"],
                    "conclusion": latest_run.get("conclusion"),
                    "created_at": latest_run["created_at"],
                    "html_url": latest_run["html_url"]
                }
        
        return None
        
    except Exception as e:
        print(f"Ошибка проверки GitHub Actions: {e}")
        return None

def main():
    repo_owner = "goqorhopar"
    repo_name = "b24"
    
    print("🔍 Проверяем статус GitHub Actions...")
    
    status = check_github_actions_status(repo_owner, repo_name)
    
    if status:
        print(f"📊 Статус последнего workflow:")
        print(f"   Статус: {status['status']}")
        print(f"   Результат: {status.get('conclusion', 'В процессе')}")
        print(f"   Время создания: {status['created_at']}")
        print(f"   Ссылка: {status['html_url']}")
        
        if status['status'] == 'completed' and status.get('conclusion') == 'success':
            print("✅ Деплой выполнен успешно!")
        elif status['status'] == 'completed' and status.get('conclusion') == 'failure':
            print("❌ Деплой завершился с ошибкой!")
        else:
            print("⏳ Деплой в процессе...")
    else:
        print("❌ Не удалось получить статус GitHub Actions")

if __name__ == "__main__":
    main()
