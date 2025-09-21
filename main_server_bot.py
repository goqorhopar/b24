"""
Главный файл серверного бота для автоматизации встреч
Интегрирует Telegram бота с серверной системой автоматизации встреч
"""
import os
import logging
import threading
import time
import requests
from flask import Flask, request
from typing import Dict, Any, Optional

# Загрузка переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables only")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

from config import config
from server_meeting_bot import server_bot
from gemini_client import analyze_transcript_structured
from bitrix import update_lead_comprehensive

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, str(config.LOG_LEVEL).upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("main_server_bot")

# Логирование конфигурации
try:
    log.info(f"Runtime config: {config.runtime_summary()}")
except Exception:
    log.info("Runtime config: unable to render summary")

# Flask app
app = Flask(__name__)

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не найден в окружении!")

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
PORT = int(os.getenv("PORT", "3000"))
USE_POLLING = os.getenv("USE_POLLING", "true").lower() == "true"

# Состояния пользователей
user_states = {}  # {chat_id: {"state": "idle"/"awaiting_lead_id", "meeting_data": dict}}

def send_message(chat_id: int, text: str) -> None:
    """Отправка сообщения в Telegram"""
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=15
        )
        resp.raise_for_status()
    except Exception as e:
        log.error(f"Ошибка HTTP при отправке сообщения в чат {chat_id}: {e}")

def _is_meeting_url(url: str) -> bool:
    """Проверка, является ли URL ссылкой на встречу"""
    try:
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Поддерживаемые платформы
        supported_domains = [
            'zoom.us', 'meet.google.com', 'teams.microsoft.com', 
            'talk.kontur.ru', 'ktalk.ru', 'telemost.yandex.ru',
            '2a14p7ld.ktalk.ru', 'us05web.zoom.us'
        ]
        
        return any(domain in parsed.netloc.lower() for domain in supported_domains)
        
    except Exception:
        return False

def process_meeting_message(msg: dict):
    """Обработка сообщения с ссылкой на встречу"""
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    user_name = msg.get("from", {}).get("first_name", "Пользователь")
    
    # Инициализация состояния
    if chat_id not in user_states:
        user_states[chat_id] = {"state": "idle", "meeting_data": None}
    
    state = user_states[chat_id]["state"]
    
    # Проверка на ссылку встречи
    if _is_meeting_url(text):
        if state in ["processing_meeting", "awaiting_lead_id"]:
            send_message(chat_id, "⏳ Уже обрабатывается встреча. Дождитесь завершения.")
            return
        
        send_message(chat_id, "🚀 Получил ссылку на встречу! Начинаю автоматическое присоединение как 'Асистент Григория'...")
        
        # Запуск обработки встречи в отдельном потоке
        def process_meeting():
            try:
                user_states[chat_id]["state"] = "processing_meeting"
                
                # Обработка встречи
                result = server_bot.process_meeting(text, chat_id)
                
                if result['success']:
                    # Сохранение данных встречи
                    user_states[chat_id]["meeting_data"] = {
                        'transcript': result.get('transcript'),
                        'analysis': result.get('analysis'),
                        'meeting_url': text,
                        'user_name': user_name,
                        'timestamp': time.time()
                    }
                    
                    # Отправка результатов
                    send_meeting_results(chat_id, result)
                    
                    # Запрос ID лида
                    send_message(chat_id, "🔍 Пожалуйста, отправьте ID лида в Bitrix24 для обновления:")
                    user_states[chat_id]["state"] = "awaiting_lead_id"
                    
                else:
                    send_message(chat_id, f"❌ Ошибка при обработке встречи: {result['message']}")
                    user_states[chat_id]["state"] = "idle"
                    
            except Exception as e:
                log.error(f"Ошибка при обработке встречи: {e}")
                send_message(chat_id, f"❌ Критическая ошибка: {e}")
                user_states[chat_id]["state"] = "idle"
        
        # Запуск в отдельном потоке
        meeting_thread = threading.Thread(target=process_meeting, daemon=True)
        meeting_thread.start()
        
        return
    
    # Обработка ID лида
    elif state == "awaiting_lead_id" and text.isdigit():
        lead_id = text
        send_message(chat_id, f"🔄 Обновляю лид {lead_id} на основе анализа встречи...")
        
        try:
            meeting_data = user_states[chat_id]["meeting_data"]
            if not meeting_data or not meeting_data.get('analysis'):
                send_message(chat_id, "❌ Данные встречи не найдены. Попробуйте отправить ссылку на встречу снова.")
                user_states[chat_id]["state"] = "idle"
                return
            
            # Обновление лида
            lead_update_result = update_lead_comprehensive(lead_id, meeting_data['analysis'])
            
            if lead_update_result.get('updated') or lead_update_result.get('task_created'):
                # Успешное обновление
                message = f"✅ Лид {lead_id} успешно обновлен!\n\n"
                
                # Информация о задачах
                if lead_update_result.get('task_created'):
                    tasks = lead_update_result.get('tasks', [])
                    if tasks:
                        message += f"📋 Создано задач: {len(tasks)}\n"
                        for i, task in enumerate(tasks[:3], 1):
                            message += f"{i}. {task.get('title', 'Без названия')}\n"
                        message += "\n"
                
                # Информация о полях
                fields_updated = lead_update_result.get('fields_updated', [])
                if fields_updated:
                    message += f"📝 Обновлено полей: {len(fields_updated)}\n"
                
                if lead_update_result.get('comment_updated'):
                    message += "💬 Комментарий добавлен\n"
                
                send_message(chat_id, message)
                
                # Уведомление администратора
                notify_admin_about_lead_update(chat_id, lead_id, lead_update_result, meeting_data)
                
            else:
                send_message(chat_id, f"⚠️ Не удалось обновить лид {lead_id}. Проверьте ID и попробуйте снова.")
            
            # Сброс состояния
            user_states[chat_id] = {"state": "idle", "meeting_data": None}
            
        except Exception as e:
            log.error(f"Ошибка при обновлении лида {lead_id}: {e}")
            send_message(chat_id, f"❌ Ошибка при обновлении лида: {e}")
            user_states[chat_id]["state"] = "idle"
        
        return
    
    # Обработка команд
    elif text.lower() in ("/start", "start"):
        send_message(chat_id, 
            "👋 Привет! Я автоматический ассистент для встреч.\n\n"
            "📋 Что я умею:\n"
            "• Автоматически присоединяюсь к встречам как 'Асистент Григория'\n"
            "• Записываю и транскрибирую встречи\n"
            "• Анализирую содержание через AI\n"
            "• Обновляю лиды в Bitrix24\n"
            "• Создаю задачи по результатам\n\n"
            "🚀 Просто отправьте мне ссылку на встречу!"
        )
        user_states[chat_id] = {"state": "idle", "meeting_data": None}
        return
    
    elif text.lower() in ("/help", "help"):
        send_message(chat_id,
            "ℹ️ **Инструкция по использованию:**\n\n"
            "1️⃣ Отправьте ссылку на встречу (Zoom, Google Meet, Teams, Контур.Толк, Яндекс.Телемост)\n"
            "2️⃣ Я автоматически присоединюсь как 'Асистент Григория'\n"
            "3️⃣ Запишу и проанализирую встречу\n"
            "4️⃣ Отправлю результаты анализа\n"
            "5️⃣ Вы введете ID лида для обновления\n"
            "6️⃣ Я обновлю лид и создам задачи\n\n"
            "📞 **Поддерживаемые платформы:**\n"
            "• Zoom\n"
            "• Google Meet\n"
            "• Microsoft Teams\n"
            "• Контур.Толк\n"
            "• Яндекс.Телемост"
        )
        return
    
    elif text.lower() in ("/status", "status"):
        # Показать статус
        state = user_states.get(chat_id, {}).get("state", "idle")
        if state == "processing_meeting":
            send_message(chat_id, "⏳ Обрабатываю встречу...")
        elif state == "awaiting_lead_id":
            send_message(chat_id, "⏳ Ожидаю ID лида для обновления...")
        else:
            send_message(chat_id, "✅ Готов к работе. Отправьте ссылку на встречу.")
        return
    
    # Если в idle состоянии пришло не ссылка
    elif state == "idle":
        send_message(chat_id, "👋 Отправьте мне ссылку на встречу, и я автоматически присоединюсь, запишу и проанализирую её.")

def send_meeting_results(chat_id: int, result: Dict[str, Any]):
    """Отправка результатов встречи пользователю"""
    try:
        transcript = result.get('transcript', {})
        analysis = result.get('analysis', {})
        
        # Основная информация
        message = "📊 **Анализ встречи завершен!**\n\n"
        
        # Информация о транскрипции
        if transcript:
            text_length = len(transcript.get('text', ''))
            message += f"📝 **Транскрипция:** {text_length} символов\n"
            message += f"⏱️ **Время обработки:** {transcript.get('duration', 0):.1f} сек\n\n"
        
        # Краткий анализ
        if analysis:
            # Ключевые поля из анализа
            key_request = analysis.get('key_request', 'Не указано')
            pains_text = analysis.get('pains_text', 'Не указано')
            sentiment = analysis.get('sentiment', 'Нейтральное')
            budget = analysis.get('ad_budget', 'Не указано')
            
            message += "🎯 **Ключевые результаты:**\n"
            message += f"• **Запрос:** {key_request}\n"
            message += f"• **Проблемы:** {pains_text}\n"
            message += f"• **Настроение:** {sentiment}\n"
            message += f"• **Бюджет:** {budget}\n\n"
            
            # ЛПР и встреча
            is_lpr = analysis.get('is_lpr')
            meeting_scheduled = analysis.get('meeting_scheduled')
            meeting_done = analysis.get('meeting_done')
            
            if is_lpr is not None:
                message += f"👤 **ЛПР:** {'Найден' if is_lpr else 'Не найден'}\n"
            if meeting_scheduled is not None:
                message += f"📅 **Встреча запланирована:** {'Да' if meeting_scheduled else 'Нет'}\n"
            if meeting_done is not None:
                message += f"✅ **Встреча проведена:** {'Да' if meeting_done else 'Нет'}\n"
            
            message += "\n"
        
        # Полный анализ (если не слишком длинный)
        if analysis and analysis.get('analysis'):
            analysis_text = analysis['analysis']
            if len(analysis_text) <= 2000:
                message += "📋 **Полный анализ:**\n"
                message += analysis_text[:2000]
                if len(analysis_text) > 2000:
                    message += "..."
            else:
                message += "📋 **Анализ:** Слишком длинный для отображения в чате\n"
        
        send_message(chat_id, message)
        
    except Exception as e:
        log.error(f"Ошибка при отправке результатов встречи: {e}")
        send_message(chat_id, f"✅ Встреча обработана, но произошла ошибка при отправке результатов: {e}")

def notify_admin_about_lead_update(chat_id: int, lead_id: str, update_result: Dict[str, Any], meeting_data: Dict[str, Any]):
    """Уведомление администратора об обновлении лида"""
    try:
        admin_chat_id = config.ADMIN_CHAT_ID
        if not admin_chat_id:
            return
        
        message = f"✅ **Лид успешно обновлен!**\n\n"
        message += f"👤 **Пользователь:** {meeting_data.get('user_name', 'Unknown')}\n"
        message += f"💬 **Chat ID:** {chat_id}\n"
        message += f"🔢 **ID лида:** {lead_id}\n"
        message += f"🌐 **Платформа:** {meeting_data.get('meeting_url', 'Unknown')}\n\n"
        
        # Результаты обновления
        if update_result.get('updated'):
            message += "✅ **Поля лида обновлены**\n"
        
        if update_result.get('comment_updated'):
            message += "💬 **Комментарий добавлен**\n"
        
        if update_result.get('task_created'):
            tasks = update_result.get('tasks', [])
            message += f"🗓 **Создано задач:** {len(tasks)}\n"
            for task in tasks:
                message += f"  • {task.get('title', 'Unknown')}\n"
        
        send_message(int(admin_chat_id), message)
        
    except Exception as e:
        log.error(f"Ошибка при уведомлении администратора: {e}")

def process_message(msg: dict):
    """Обработка одного сообщения от Telegram"""
    if not msg:
        return
    
    try:
        process_meeting_message(msg)
    except Exception as e:
        log.error(f"Ошибка при обработке сообщения: {e}")
        chat_id = msg.get("chat", {}).get("id")
        if chat_id:
            send_message(chat_id, f"❌ Произошла ошибка при обработке сообщения: {e}")

def polling_worker():
    """Фоновый процесс для polling"""
    offset = 0
    log.info("Запущен polling для получения сообщений...")
    
    # Получаем последний update_id
    try:
        response = requests.get(f"{BASE_URL}/getUpdates", params={"offset": -1, "limit": 1})
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("result"):
                last_update = data["result"][-1]
                offset = last_update["update_id"] + 1
                log.info(f"Начинаем с offset: {offset}")
    except Exception as e:
        log.warning(f"Не удалось получить последний offset: {e}")
        offset = 0
    
    while True:
        try:
            response = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok"):
                updates = data.get("result", [])
                for update in updates:
                    if "message" in update:
                        process_message(update["message"])
                    offset = update["update_id"] + 1
                    
        except requests.exceptions.RequestException as e:
            log.error(f"Ошибка сети в polling: {e}")
            time.sleep(5)
        except Exception as e:
            log.error(f"Критическая ошибка в polling: {e}")
            time.sleep(15)

# Маршруты Flask
@app.route("/", methods=["GET"])
def index():
    """Проверка, что сервис работает"""
    return {"ok": True, "message": "Server meeting bot is running", "version": "2.0"}, 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook для получения обновлений от Telegram"""
    if request.method == "POST":
        update = request.get_json()
        if "message" in update:
            process_message(update["message"])
        return {"ok": True}
    return {"error": "Method not allowed"}, 405

@app.route("/status", methods=["GET"])
def status():
    """Статус бота"""
    active_meetings = len([s for s in user_states.values() if s["state"] == "processing_meeting"])
    awaiting_leads = len([s for s in user_states.values() if s["state"] == "awaiting_lead_id"])
    
    return {
        "status": "running",
        "active_meetings": active_meetings,
        "awaiting_leads": awaiting_leads,
        "total_users": len(user_states),
        "bot_configured": bool(TELEGRAM_BOT_TOKEN),
        "server_bot_ready": server_bot is not None
    }, 200

def main():
    """Основная функция запуска бота"""
    log.info("Запуск серверного бота для автоматизации встреч")
    
    # Проверка конфигурации
    validation = config.validate()
    if not validation['valid']:
        missing = ', '.join(validation['missing_vars'])
        log.error(f"Отсутствуют обязательные переменные окружения: {missing}")
        return
    
    if USE_POLLING:
        # Удаление существующего вебхука
        try:
            log.info("Удаление существующего вебхука...")
            requests.get(f"{BASE_URL}/deleteWebhook", timeout=5)
        except Exception as e:
            log.warning(f"Не удалось удалить вебхук: {e}")
        
        # Запуск polling
        polling_thread = threading.Thread(target=polling_worker, daemon=True)
        polling_thread.start()
        log.info("Polling запущен в фоновом режиме")
    
    # Запуск веб-сервера
    log.info(f"Запуск веб-сервера на порту {PORT}")
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)

if __name__ == "__main__":
    main()
