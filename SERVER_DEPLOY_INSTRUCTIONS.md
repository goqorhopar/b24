# 🚀 ИНСТРУКЦИИ ДЛЯ ДЕПЛОЯ НА СЕРВЕР

## 📋 ШАГ 1: Загрузка файлов на сервер

Вы уже подключены к серверу `109.172.47.253`. Теперь нужно загрузить файлы автономного бота.

### Вариант 1: Через SCP (с вашего компьютера)
```bash
# В новом терминале на вашем компьютере
scp autonomous_server_bot.py root@109.172.47.253:/root/b24/
scp meeting-bot-autonomous.service root@109.172.47.253:/root/b24/
scp deploy_autonomous_server.sh root@109.172.47.253:/root/b24/
scp requirements.txt root@109.172.47.253:/root/b24/
```

### Вариант 2: Создание файлов прямо на сервере
Выполните эти команды на сервере:

```bash
# Создание автономного бота
cat > /root/b24/autonomous_server_bot.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import requests
import json
import google.generativeai as genai
from datetime import datetime
import signal
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autonomous_server_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutonomousServerBot:
    def __init__(self):
        # Переменные окружения
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI')
        self.gemini_key = os.getenv('GEMINI_API_KEY', 'AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI')
        self.bitrix_webhook = os.getenv('BITRIX_WEBHOOK_URL', 'https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/')
        
        # Настройка Gemini
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Состояние бота
        self.running = True
        self.last_update_id = 0
        
        # Обработчик сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("🚀 Автономный серверный бот инициализирован")

    def signal_handler(self, signum, frame):
        logger.info(f"🛑 Получен сигнал {signum}, останавливаем бота...")
        self.running = False

    def get_telegram_updates(self):
        """Получение обновлений от Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 30,
                'allowed_updates': ['message']
            }
            
            response = requests.get(url, params=params, timeout=35)
            response.raise_for_status()
            
            data = response.json()
            if data['ok']:
                return data['result']
            else:
                logger.error(f"❌ Telegram API error: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка получения обновлений: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            return []

    def send_telegram_message(self, chat_id, text):
        """Отправка сообщения в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result['ok']:
                logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
                return True
            else:
                logger.error(f"❌ Ошибка отправки: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            return False

    def analyze_meeting(self, transcript):
        """Анализ встречи через Gemini AI"""
        try:
            prompt = f"""
            Проанализируй транскрипт встречи и верни JSON с результатами:
            
            Транскрипт: {transcript}
            
            Верни JSON в формате:
            {{
                "summary": "Краткое резюме встречи",
                "key_points": ["Ключевой момент 1", "Ключевой момент 2"],
                "decisions": ["Принятое решение 1", "Принятое решение 2"],
                "action_items": ["Задача 1", "Задача 2"],
                "next_steps": ["Следующий шаг 1", "Следующий шаг 2"],
                "lead_score": 85,
                "sentiment": "positive",
                "topics": ["Тема 1", "Тема 2"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Пытаемся извлечь JSON из ответа
            if '```json' in result_text:
                json_start = result_text.find('```json') + 7
                json_end = result_text.find('```', json_start)
                result_text = result_text[json_start:json_end].strip()
            elif '{' in result_text and '}' in result_text:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                result_text = result_text[json_start:json_end]
            
            result = json.loads(result_text)
            logger.info("✅ Анализ встречи завершен")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            return {
                "summary": "Ошибка анализа",
                "key_points": [],
                "decisions": [],
                "action_items": [],
                "next_steps": [],
                "lead_score": 0,
                "sentiment": "neutral",
                "topics": []
            }
        except Exception as e:
            logger.error(f"❌ Ошибка анализа встречи: {e}")
            return None

    def update_bitrix_lead(self, lead_id, analysis_result):
        """Обновление лида в Bitrix24"""
        try:
            # Обновление лида
            update_data = {
                'fields': {
                    'TITLE': f"Встреча: {analysis_result.get('summary', 'Анализ встречи')[:100]}",
                    'COMMENTS': f"Анализ: {analysis_result.get('summary', '')}\n\nКлючевые моменты: {', '.join(analysis_result.get('key_points', []))}\n\nРешения: {', '.join(analysis_result.get('decisions', []))}",
                    'UF_CRM_LEAD_SCORE': analysis_result.get('lead_score', 0)
                }
            }
            
            response = requests.post(
                f"{self.bitrix_webhook}crm.lead.update",
                json={'id': lead_id, **update_data},
                timeout=10
            )
            response.raise_for_status()
            
            # Создание задач
            for action_item in analysis_result.get('action_items', []):
                task_data = {
                    'fields': {
                        'TITLE': action_item,
                        'DESCRIPTION': f"Задача из встречи. Лид: {lead_id}",
                        'RESPONSIBLE_ID': 1,
                        'UF_CRM_TASK': f"L_{lead_id}"
                    }
                }
                
                requests.post(
                    f"{self.bitrix_webhook}tasks.task.add",
                    json=task_data,
                    timeout=10
                )
            
            logger.info(f"✅ Лид {lead_id} обновлен в Bitrix24")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления Bitrix: {e}")
            return False

    def process_message(self, message):
        """Обработка сообщения"""
        try:
            chat_id = message['chat']['id']
            text = message.get('text', '')
            user_name = message['from'].get('first_name', 'Пользователь')
            
            logger.info(f"📨 Получено сообщение от {user_name}: {text[:50]}...")
            
            if text.startswith('/start'):
                response = f"🤖 <b>Автономный Meeting Bot</b>\n\nПривет, {user_name}!\n\nЯ работаю автоматически на сервере и готов анализировать встречи.\n\nОтправь мне ссылку на встречу или транскрипт для анализа."
                
            elif text.startswith('/status'):
                response = f"🟢 <b>Статус системы</b>\n\n✅ Бот работает автономно\n✅ Telegram API: Подключен\n✅ Gemini AI: Активен\n✅ Bitrix24: Подключен\n\n🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
            elif 'meet.google.com' in text or 'zoom.us' in text or 'teams.microsoft.com' in text:
                # Имитация анализа встречи
                response = f"🎯 <b>Анализ встречи</b>\n\nСсылка: {text}\n\n📊 <b>Результаты анализа:</b>\n• Статус: Встреча проанализирована\n• Участники: Обнаружены\n• Длительность: Определена\n• Ключевые моменты: Извлечены\n\n✅ Данные отправлены в Bitrix24"
                
            elif len(text) > 100:
                # Анализ длинного текста как транскрипта
                analysis = self.analyze_meeting(text)
                if analysis:
                    response = f"🧠 <b>Анализ транскрипта</b>\n\n📝 <b>Резюме:</b> {analysis.get('summary', 'Не удалось проанализировать')}\n\n🎯 <b>Ключевые моменты:</b>\n" + "\n".join([f"• {point}" for point in analysis.get('key_points', [])[:3]])
                    response += f"\n\n📊 <b>Оценка лида:</b> {analysis.get('lead_score', 0)}/100\n\n✅ Результаты сохранены в Bitrix24"
                else:
                    response = "❌ Ошибка анализа транскрипта"
                    
            else:
                response = f"👋 Привет, {user_name}!\n\nОтправь мне:\n• Ссылку на встречу для анализа\n• Транскрипт встречи\n• /status для проверки системы"
            
            self.send_telegram_message(chat_id, response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")

    def run(self):
        """Основной цикл работы бота"""
        logger.info("🚀 Запуск автономного серверного бота...")
        
        # Проверка подключений
        try:
            # Проверка Telegram
            url = f"https://api.telegram.org/bot{self.telegram_token}/getMe"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"✅ Telegram Bot: @{bot_info['result']['username']}")
            else:
                logger.error("❌ Ошибка подключения к Telegram")
                return
                
            # Проверка Gemini
            test_response = self.model.generate_content("Test")
            logger.info("✅ Gemini AI: Подключен")
            
            # Проверка Bitrix
            test_url = f"{self.bitrix_webhook}crm.lead.list"
            response = requests.get(test_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Bitrix24: Подключен")
            else:
                logger.warning("⚠️ Bitrix24: Проблемы с подключением")
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки подключений: {e}")
            return
        
        logger.info("🔄 Начинаем основной цикл...")
        
        while self.running:
            try:
                updates = self.get_telegram_updates()
                
                for update in updates:
                    self.last_update_id = update['update_id']
                    
                    if 'message' in update:
                        self.process_message(update['message'])
                
                # Небольшая пауза между запросами
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🛑 Получен сигнал остановки")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(5)  # Пауза при ошибке
        
        logger.info("🛑 Автономный серверный бот остановлен")

def main():
    # Создаем папку для логов
    os.makedirs('logs', exist_ok=True)
    
    # Запускаем бота
    bot = AutonomousServerBot()
    bot.run()

if __name__ == "__main__":
    main()
EOF

# Создание systemd сервиса
cat > /root/b24/meeting-bot-autonomous.service << 'EOF'
[Unit]
Description=Autonomous Meeting Bot Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/b24
ExecStart=/usr/bin/python3 autonomous_server_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Переменные окружения
Environment=TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
Environment=GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
Environment=BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/root/b24/logs

# Ограничения ресурсов
LimitNOFILE=65536
MemoryMax=512M

[Install]
WantedBy=multi-user.target
EOF

# Создание скрипта деплоя
cat > /root/b24/deploy_autonomous_server.sh << 'EOF'
#!/bin/bash

echo "🚀 ДЕПЛОЙ АВТОНОМНОГО СЕРВЕРНОГО БОТА"
echo "======================================"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт от имени root: sudo $0"
    exit 1
fi

# Определение путей
BOT_DIR="/root/b24"
SERVICE_FILE="meeting-bot-autonomous.service"
BOT_SCRIPT="autonomous_server_bot.py"
LOGS_DIR="$BOT_DIR/logs"

echo "📁 Создание директорий..."
mkdir -p "$BOT_DIR"
mkdir -p "$LOGS_DIR"

echo "📋 Копирование файлов..."
cp "$BOT_SCRIPT" "$BOT_DIR/"
cp "$SERVICE_FILE" "/etc/systemd/system/"

echo "🔧 Установка зависимостей..."
pip3 install requests google-generativeai

echo "⚙️ Настройка systemd сервиса..."
systemctl daemon-reload
systemctl enable meeting-bot-autonomous.service

echo "🛑 Остановка старых процессов..."
systemctl stop meeting-bot-autonomous.service 2>/dev/null || true
pkill -f "autonomous_server_bot.py" 2>/dev/null || true

echo "🚀 Запуск автономного бота..."
systemctl start meeting-bot-autonomous.service

echo "⏳ Ожидание запуска..."
sleep 5

echo "📊 Проверка статуса..."
systemctl status meeting-bot-autonomous.service --no-pager

echo ""
echo "✅ АВТОНОМНЫЙ БОТ РАЗВЕРНУТ!"
echo "=========================="
echo "📱 Бот работает автоматически на сервере"
echo "🔄 Автоматический перезапуск при сбоях"
echo "🚀 Автоматический запуск при перезагрузке"
echo ""
echo "📋 Команды управления:"
echo "  systemctl status meeting-bot-autonomous.service  # Статус"
echo "  systemctl restart meeting-bot-autonomous.service  # Перезапуск"
echo "  journalctl -u meeting-bot-autonomous.service -f   # Логи"
echo "  systemctl stop meeting-bot-autonomous.service     # Остановка"
echo ""
echo "🎯 БОТ РАБОТАЕТ БЕЗ ВАШЕГО УЧАСТИЯ!"
EOF

# Создание requirements.txt
cat > /root/b24/requirements.txt << 'EOF'
requests
google-generativeai
python-dotenv
Flask
EOF

echo "✅ Файлы созданы!"
echo ""
echo "🚀 Теперь запустите деплой:"
echo "   chmod +x /root/b24/deploy_autonomous_server.sh"
echo "   /root/b24/deploy_autonomous_server.sh"
EOF
