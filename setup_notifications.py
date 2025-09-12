#!/usr/bin/env python3
"""
Скрипт для настройки уведомлений о деплое
"""

import os
import requests
import json
from typing import Dict, Any

class NotificationManager:
    """Менеджер уведомлений"""
    
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        self.slack_webhook = os.getenv('SLACK_WEBHOOK')
    
    def send_telegram_notification(self, message: str, chat_id: str = None) -> bool:
        """Отправка уведомления в Telegram"""
        if not self.telegram_token:
            print("❌ TELEGRAM_BOT_TOKEN не настроен")
            return False
        
        chat_id = chat_id or self.admin_chat_id
        if not chat_id:
            print("❌ ADMIN_CHAT_ID не настроен")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            print("✅ Уведомление отправлено в Telegram")
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки в Telegram: {e}")
            return False
    
    def send_slack_notification(self, message: str) -> bool:
        """Отправка уведомления в Slack"""
        if not self.slack_webhook:
            print("❌ SLACK_WEBHOOK не настроен")
            return False
        
        data = {
            'text': message,
            'username': 'Deploy Bot',
            'icon_emoji': ':rocket:'
        }
        
        try:
            response = requests.post(self.slack_webhook, json=data, timeout=10)
            response.raise_for_status()
            print("✅ Уведомление отправлено в Slack")
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки в Slack: {e}")
            return False
    
    def send_deployment_notification(self, status: str, branch: str, commit: str = None) -> bool:
        """Отправка уведомления о деплое"""
        emoji = "✅" if status == "success" else "❌"
        status_text = "успешно" if status == "success" else "с ошибкой"
        
        message = f"""
{emoji} <b>Деплой {status_text}</b>

🌿 Ветка: <code>{branch}</code>
📝 Коммит: <code>{commit or 'N/A'}</code>
🕐 Время: {self._get_current_time()}
🌐 Сервер: <code>109.172.47.253</code>
        """.strip()
        
        # Отправляем в Telegram
        telegram_sent = self.send_telegram_notification(message)
        
        # Отправляем в Slack
        slack_message = f"{emoji} Деплой {status_text} - ветка {branch}"
        slack_sent = self.send_slack_notification(slack_message)
        
        return telegram_sent or slack_sent
    
    def send_error_notification(self, error: str, context: str = None) -> bool:
        """Отправка уведомления об ошибке"""
        message = f"""
🚨 <b>Ошибка деплоя</b>

❌ Ошибка: <code>{error}</code>
📋 Контекст: <code>{context or 'N/A'}</code>
🕐 Время: {self._get_current_time()}
🌐 Сервер: <code>109.172.47.253</code>
        """.strip()
        
        return self.send_telegram_notification(message)
    
    def _get_current_time(self) -> str:
        """Получение текущего времени"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def setup_environment_variables():
    """Настройка переменных окружения для уведомлений"""
    print("🔧 Настройка уведомлений о деплое")
    print("=" * 40)
    
    # Проверяем существующие переменные
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_chat_id = os.getenv('ADMIN_CHAT_ID')
    slack_webhook = os.getenv('SLACK_WEBHOOK')
    
    print(f"TELEGRAM_BOT_TOKEN: {'✅' if telegram_token else '❌'}")
    print(f"ADMIN_CHAT_ID: {'✅' if admin_chat_id else '❌'}")
    print(f"SLACK_WEBHOOK: {'✅' if slack_webhook else '❌'}")
    
    if not telegram_token:
        print("\n⚠️ Для уведомлений в Telegram настройте:")
        print("   TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        print("   ADMIN_CHAT_ID=ваш_chat_id")
    
    if not slack_webhook:
        print("\n⚠️ Для уведомлений в Slack настройте:")
        print("   SLACK_WEBHOOK=https://hooks.slack.com/services/...")
    
    print("\n📋 Добавьте эти переменные в:")
    print("   1. .env файл на сервере")
    print("   2. GitHub Secrets для Actions")
    print("   3. deploy_webhook.php на сервере")

def test_notifications():
    """Тестирование уведомлений"""
    print("\n🧪 Тестирование уведомлений...")
    
    manager = NotificationManager()
    
    # Тест Telegram
    if manager.telegram_token and manager.admin_chat_id:
        success = manager.send_telegram_notification("🧪 Тестовое уведомление о деплое")
        if success:
            print("✅ Telegram уведомления работают")
        else:
            print("❌ Проблема с Telegram уведомлениями")
    else:
        print("⚠️ Telegram не настроен")
    
    # Тест Slack
    if manager.slack_webhook:
        success = manager.send_slack_notification("🧪 Тестовое уведомление о деплое")
        if success:
            print("✅ Slack уведомления работают")
        else:
            print("❌ Проблема с Slack уведомлениями")
    else:
        print("⚠️ Slack не настроен")

if __name__ == "__main__":
    setup_environment_variables()
    test_notifications()
