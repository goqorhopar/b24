import os, logging, requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from db import init_db, set_session, get_session, clear_session
from gemini_client import analyze_transcript
from bitrix import update_lead_comment

load_dotenv()
logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO').upper())
log = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API = f"https://api.telegram.org/bot{TOKEN}"
APP_URL = os.getenv('RENDER_EXTERNAL_URL')
PORT = int(os.getenv('PORT', '3000'))

if not TOKEN or not APP_URL:
    raise RuntimeError("TELEGRAM_BOT_TOKEN и RENDER_EXTERNAL_URL обязательны!")

init_db()
app = Flask(__name__)

def send(chat, text):
    requests.post(f"{API}/sendMessage", json={"chat_id": chat, "text": text[:4000], "parse_mode":"HTML"})

@app.route('/webhook', methods=['POST'])
def webhook():
    d = request.get_json()
    msg = d.get('message')
    if not msg: return jsonify(ok=True)
    chat = msg['chat']['id']
    text = msg.get('text','').strip()
    if not text: return jsonify(ok=True)

    s = get_session(chat)
    if not s:
        set_session(chat, 'AWAITING_LEAD_ID', text)
        send(chat, "Транскрипт принят. Пришлите ID лида.")
    else:
        if s['state'] == 'AWAITING_LEAD_ID':
            lead_id = text
            send(chat, f"ID {lead_id} получен. Анализирую...")
            try:
                report = analyze_transcript(s['transcript'])
                for i in range(0, len(report), 3800):
                    send(chat, report[i:i+3800])
                try:
                    update_lead_comment(lead_id, report[:9000])
                    send(chat, "Лид обновлён в Bitrix ✅")
                except Exception as e:
                    send(chat, f"Bitrix ошибка: {e}")
            except Exception as e:
                send(chat, f"Ошибка анализа: {e}")
            clear_session(chat)
        else:
            set_session(chat, 'AWAITING_LEAD_ID', text)
            send(chat, "Принял новый транскрипт. Пришлите ID.")

    return jsonify(ok=True)

@app.route('/')
def index(): return "OK"

def set_webhook():
    r = requests.get(f"{API}/setWebhook", params={"url": APP_URL.rstrip('/')+'/webhook'})
    log.info("Webhook set: %s", r.text)

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=PORT)
