#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import subprocess
import os

def test_mcp_method(method, params):
    """Тестирование MCP метода"""
    print(f"\n🧪 Тестирование: {method}")
    print(f"📋 Параметры: {json.dumps(params, ensure_ascii=False, indent=2)}")
    
    request = {
        "method": method,
        "params": params
    }
    
    try:
        # Запускаем MCP сервер
        process = subprocess.Popen(
            ["python", "router.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        # Отправляем запрос
        stdout, stderr = process.communicate(input=json.dumps(request))
        
        print(f"📤 Запрос отправлен")
        print(f"📥 Ответ: {stdout}")
        if stderr:
            print(f"⚠️ Ошибки: {stderr}")
        
        # Парсим ответ
        try:
            response = json.loads(stdout)
            if response.get("status") == "success":
                print(f"✅ Успешно: {response.get('message', '')}")
                return True
            else:
                print(f"❌ Ошибка: {response.get('error', '')}")
                return False
        except json.JSONDecodeError:
            print(f"❌ Неверный JSON ответ")
            return False
            
    except Exception as e:
        print(f"💥 Исключение: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование MCP сервера")
    print("=" * 50)
    
    # Создаем директорию для логов
    os.makedirs('logs', exist_ok=True)
    
    tests = [
        {
            "method": "meeting_join",
            "params": {
                "meeting_url": "https://meet.google.com/test-meeting"
            }
        },
        {
            "method": "meeting_analyze",
            "params": {
                "transcript": "Встреча с клиентом прошла успешно. Обсудили требования к системе автоматизации. Клиент заинтересован в интеграции с существующими системами. Договорились о подготовке технического предложения. Назначили следующую встречу на следующую неделю. Клиент готов к началу проекта в следующем месяце.",
                "meeting_url": "https://meet.google.com/test-meeting"
            }
        },
        {
            "method": "checklist",
            "params": {
                "prompt": "Подготовить техническое предложение, назначить встречу, согласовать бюджет проекта"
            }
        },
        {
            "method": "bitrix_update",
            "params": {
                "lead_id": 123,
                "summary": "Встреча прошла успешно, клиент заинтересован",
                "tasks": [
                    {
                        "task": "Подготовить техническое предложение",
                        "assignee": "Менеджер",
                        "deadline": "2025-09-30",
                        "priority": "High"
                    }
                ],
                "lead_score": 8
            }
        }
    ]
    
    success_count = 0
    for test in tests:
        if test_mcp_method(test["method"], test["params"]):
            success_count += 1
    
    print(f"\n📊 Результат: {success_count}/{len(tests)} тестов прошли успешно")
    
    if success_count == len(tests):
        print("🎉 Все тесты прошли успешно!")
    else:
        print("⚠️ Некоторые тесты не прошли")

if __name__ == "__main__":
    main()
