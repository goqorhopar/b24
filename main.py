import os
import logging
import requests
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from db import init_db, set_session, get_session, clear_session
from gemini_client import analyze_transcript
from bitrix import update_lead_comment

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Переменные окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')
PORT = int(os.getenv('PORT', 3000))

# Проверка обязательных переменных
required_vars = {
    'TELEGRAM_BOT_TOKEN': TOKEN,
    'GEMINI_API_KEY': GEMINI_API_KEY,
    'RENDER_EXTERNAL_URL': RENDER_EXTERNAL_URL
}

for var_name, var_value in required_vars.items():
    if not var_value:
        raise RuntimeError(f"Переменная окружения {var_name} обязательна!")

# API URLs
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL.rstrip('/')}/webhook"

# Инициализация базы данных
init_db()
app = Flask(__name__)

def send_message(chat_id, text, parse_mode="HTML"):
    """Отправка сообщения в Telegram с обработкой ошибок"""
    try:
        # Разбиваем длинные сообщения
        max_length = 4096
        if len(text) > max_length:
            for i in range(0, len(text), max_length):
                chunk = text[i:i+max_length]
                response = requests.post(
                    f"{TELEGRAM_API_URL}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": parse_mode
                    },
                    timeout=30
                )
                response.raise_for_status()
                time.sleep(0.1)  # Небольшая задержка между сообщениями
        else:
            response = requests.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=30
            )
            response.raise_for_status()
        
        log.info(f"Сообщение отправлено в чат {chat_id}")
        
    except requests.exceptions.RequestException as e:
        log.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
        # Уведомляем админа об ошибке
        if ADMIN_CHAT_ID and str(chat_id) != str(ADMIN_CHAT_ID):
            try:
                requests.post(
                    f"{TELEGRAM_API_URL}/sendMessage",
                    json={
                        "chat_id": ADMIN_CHAT_ID,
                        "text": f"❌ Ошибка отправки сообщения в чат {chat_id}: {str(e)[:500]}"
                    },
                    timeout=15
                )
            except:
                pass

def notify_admin(message):
    """Уведомление администратора"""
    if ADMIN_CHAT_ID:
        try:
            requests.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    "chat_id": ADMIN_CHAT_ID,
                    "text": f"🔔 Admin: {message}"
                },
                timeout=15
            )
        except Exception as e:
            log.error(f"Ошибка уведомления админа: {e}")

def validate_lead_id(lead_id):
    """Валидация ID лида"""
    try:
        # Проверяем что это число
        int(lead_id)
        return True
    except ValueError:
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка webhook от Telegram"""
    try:
        data = request.get_json()
        log.info(f"Получен webhook: {data}")
        
        if not data:
            log.warning("Пустые данные webhook")
            return jsonify({"ok": True})
        
        message = data.get('message')
        if not message:
            log.warning("Сообщение не найдено в webhook")
            return jsonify({"ok": True})
        
        chat_id = message['chat']['id']
        user_name = message.get('from', {}).get('username', 'Unknown')
        text = message.get('text', '').strip()
        
        log.info(f"Обработка сообщения от {user_name} (chat_id: {chat_id}): {text[:100]}...")
        
        if not text:
            send_message(chat_id, "❌ Пустое сообщение. Пожалуйста, отправьте текст.")
            return jsonify({"ok": True})
        
        # Команды
        if text.startswith('/start'):
            send_message(chat_id, 
                "🤖 <b>Бот анализа встреч</b>\n\n"
                "Отправьте мне транскрипт встречи с клиентом, "
                "затем ID лида из Bitrix24.\n\n"
                "Я проанализирую встречу через Gemini AI и обновлю лид в Bitrix.\n\n"
                "<i>Команды:</i>\n"
                "/start - начать работу\n"
                "/cancel - отменить текущую операцию\n"
                "/help - помощь"
            )
            clear_session(chat_id)
            return jsonify({"ok": True})
        
        if text.startswith('/cancel'):
            clear_session(chat_id)
            send_message(chat_id, "✅ Операция отменена. Можете отправить новый транскрипт.")
            return jsonify({"ok": True})
        
        if text.startswith('/help'):
            send_message(chat_id,
                "<b>Инструкция по использованию:</b>\n\n"
                "1️⃣ Отправьте транскрипт встречи\n"
                "2️⃣ Отправьте ID лида из Bitrix24\n"
                "3️⃣ Получите анализ и обновление в Bitrix\n\n"
                "<i>Бот анализирует встречу по 12 критериям и даёт рекомендации.</i>"
            )
            return jsonify({"ok": True})
        
        # Получение сессии пользователя
        session = get_session(chat_id)
        
        if not session or session['state'] != 'AWAITING_LEAD_ID':
            # Это новый транскрипт
            if len(text) < 50:
                send_message(chat_id, 
                    "❌ Транскрипт слишком короткий. "
                    "Пожалуйста, отправьте полный транскрипт встречи (минимум 50 символов)."
                )
                return jsonify({"ok": True})
            
            set_session(chat_id, 'AWAITING_LEAD_ID', text)
            send_message(chat_id, 
                "✅ <b>Транскрипт получен!</b>\n\n"
                f"Объём текста: {len(text)} символов\n\n"
                "📝 Теперь отправьте <b>ID лида</b> из Bitrix24 "
                "(например: 123 или 4567)"
            )
            
            # Уведомляем админа о новом транскрипте
            notify_admin(f"Новый транскрипт от {user_name} (chat: {chat_id}), {len(text)} символов")
            
        else:
            # Это ID лида
            lead_id = text.strip()
            
            if not validate_lead_id(lead_id):
                send_message(chat_id, 
                    "❌ Неверный формат ID лида. "
                    "ID должен быть числом (например: 123, 4567).\n\n"
                    "Попробуйте ещё раз:"
                )
                return jsonify({"ok": True})
            
            send_message(chat_id, 
                f"🔄 <b>Начинаю обработку...</b>\n\n"
                f"ID лида: {lead_id}\n"
                f"Анализирую транскрипт через Gemini AI..."
            )
            
            try:
                # Анализ через Gemini
                log.info(f"Анализ транскрипта для лида {lead_id}")
                analysis_result = analyze_transcript(session['transcript'])
                
                if not analysis_result:
                    raise Exception("Пустой результат анализа от Gemini")
                
                log.info(f"Анализ завершён, длина результата: {len(analysis_result)}")
                
                # Отправляем результат пользователю
                send_message(chat_id, f"📊 <b>АНАЛИЗ ВСТРЕЧИ (ID: {lead_id})</b>\n\n{analysis_result}")
                
                # Обновляем Bitrix только если URL настроен
                if BITRIX_WEBHOOK_URL:
                    try:
                        log.info(f"Обновление лида {lead_id} в Bitrix")
                        bitrix_result = update_lead_comment(lead_id, analysis_result[:8000])  # Ограничиваем размер
                        
                        if bitrix_result.get('result'):
                            send_message(chat_id, "✅ <b>Лид успешно обновлён в Bitrix24!</b>")
                            notify_admin(f"Успешно обработан лид {lead_id} от {user_name}")
                        else:
                            send_message(chat_id, f"⚠️ Частичная ошибка Bitrix: {bitrix_result}")
                            
                    except Exception as bitrix_error:
                        log.error(f"Ошибка обновления Bitrix: {bitrix_error}")
                        send_message(chat_id, 
                            f"❌ <b>Ошибка обновления Bitrix:</b>\n{str(bitrix_error)[:500]}\n\n"
                            "Анализ выполнен, но лид не обновлён."
                        )
                        notify_admin(f"Ошибка Bitrix для лида {lead_id}: {bitrix_error}")
                else:
                    send_message(chat_id, "⚠️ Bitrix не настроен - только анализ выполнен")
                
            except Exception as e:
                log.error(f"Ошибка анализа: {e}")
                send_message(chat_id, 
                    f"❌ <b>Ошибка анализа:</b>\n{str(e)[:500]}\n\n"
                    "Попробуйте ещё раз или обратитесь к администратору."
                )
                notify_admin(f"Ошибка анализа для лида {lead_id}: {e}")
            
            # Очищаем сессию
            clear_session(chat_id)
            
            # Предлагаем новый анализ
            send_message(chat_id, 
                "\n🔄 <b>Готов к новому анализу!</b>\n"
                "Отправьте следующий транскрипт."
            )
    
    except Exception as e:
        log.error(f"Критическая ошибка webhook: {e}")
        try:
            if 'chat_id' in locals():
                send_message(chat_id, "❌ Произошла системная ошибка. Попробуйте позже.")
        except:
            pass
        notify_admin(f"Критическая ошибка webhook: {e}")
    
    return jsonify({"ok": True})

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья приложения"""
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "webhook_url": WEBHOOK_URL
    })

@app.route('/', methods=['GET'])
def index():
    """Главная страница"""
    return jsonify({
        "service": "Telegram Gemini Analysis Bot",
        "status": "running",
        "webhook": WEBHOOK_URL
    })

def setup_webhook():
    """Настройка webhook для Telegram"""
    try:
        # Удаляем старый webhook
        delete_response = requests.post(f"{TELEGRAM_API_URL}/deleteWebhook", timeout=30)
        log.info(f"Удаление старого webhook: {delete_response.text}")
        
        time.sleep(1)
        
        # Устанавливаем новый webhook
        webhook_response = requests.post(
            f"{TELEGRAM_API_URL}/setWebhook",
            json={
                "url": WEBHOOK_URL,
                "allowed_updates": ["message"],
                "drop_pending_updates": True
            },
            timeout=30
        )
        webhook_response.raise_for_status()
        
        result = webhook_response.json()
        if result.get('ok'):
            log.info(f"✅ Webhook успешно установлен: {WEBHOOK_URL}")
            notify_admin(f"Бот перезапущен. Webhook: {WEBHOOK_URL}")
        else:
            log.error(f"❌ Ошибка установки webhook: {result}")
            
    except Exception as e:
        log.error(f"Критическая ошибка настройки webhook: {e}")
        raise

if __name__ == '__main__':
    log.info("🚀 Запуск Telegram Gemini Analysis Bot...")
    log.info(f"PORT: {PORT}")
    log.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    
    try:
        setup_webhook()
        log.info("✅ Бот готов к работе!")
        app.run(host='0.0.0.0', port=PORT, debug=False)
    except Exception as e:
        log.error(f"💥 Критическая ошибка запуска: {e}")
        raise
