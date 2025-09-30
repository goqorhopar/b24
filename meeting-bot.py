#!/usr/bin/env python3
"""
Meeting Bot - Улучшенная версия для работы на VPS
Поддержка: Google Meet, Zoom, Яндекс Телемост, Контур.Толк
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import subprocess
import tempfile
import re
import time
from pathlib import Path

# Selenium для автоматизации браузера
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Whisper для транскрипции
from faster_whisper import WhisperModel

# GitHub
from github import Github

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'goqorhopar/b24')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')
RECORD_DIR = os.getenv('RECORD_DIR', '/tmp/recordings')
MEETING_TIMEOUT_MIN = int(os.getenv('MEETING_TIMEOUT_MIN', '180'))  # 3 часа по умолчанию

# Создаем директорию для записей
Path(RECORD_DIR).mkdir(parents=True, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MeetingBot:
    """Основной класс для работы с встречами"""
    
    def __init__(self):
        self.driver = None
        self.recording = False
        self.audio_file = None
        self.transcript = []
        self.recording_process = None
        self.meeting_url = None
        self.start_time = None
        
        # Инициализация GitHub
        if GITHUB_TOKEN:
            try:
                self.github = Github(GITHUB_TOKEN)
                self.repo = self.github.get_repo(GITHUB_REPO)
                logger.info("GitHub репозиторий подключен")
            except Exception as e:
                logger.error(f"Ошибка подключения к GitHub: {e}")
                self.github = None
                self.repo = None
        else:
            self.github = None
            self.repo = None
            logger.warning("GitHub токен не настроен")
        
        # Инициализация Whisper модели
        try:
            logger.info(f"Загрузка Whisper модели: {WHISPER_MODEL}")
            self.whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            logger.info("Whisper модель загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки Whisper: {e}")
            self.whisper_model = None
        
    def setup_driver(self, headless=True):
        """Настройка Chrome драйвера для VPS"""
        options = Options()
        
        # Критичные настройки для headless режима
        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-extensions')
        
        # Настройки для медиа
        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--use-fake-device-for-media-stream')
        options.add_argument('--autoplay-policy=no-user-gesture-required')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Размер окна
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Разрешения для микрофона и камеры
        prefs = {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Инициализация драйвера
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome драйвер инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Chrome: {e}")
            raise
        
    def detect_meeting_type(self, url: str) -> str:
        """Определить тип встречи по URL"""
        url_lower = url.lower()
        if 'meet.google.com' in url_lower:
            return 'google_meet'
        elif 'zoom.us' in url_lower or 'zoom.com' in url_lower:
            return 'zoom'
        elif 'telemost.yandex' in url_lower:
            return 'yandex'
        elif 'talk.contour.ru' in url_lower or 'contour.ru' in url_lower:
            return 'contour'
        elif 'teams.microsoft.com' in url_lower:
            return 'teams'
        else:
            return 'unknown'
    
    def join_google_meet(self, meeting_url: str, name: str = "Meeting Bot"):
        """Присоединиться к Google Meet с улучшенной логикой"""
        try:
            logger.info(f"Открываем Google Meet: {meeting_url}")
            self.driver.get(meeting_url)
            self.meeting_url = meeting_url
            
            # Ждем загрузки страницы
            time.sleep(5)
            
            # Проверяем, не требуется ли вход в аккаунт
            if "accounts.google.com" in self.driver.current_url:
                logger.warning("Требуется вход в Google аккаунт - встреча может быть закрытой")
                return False
            
            # Отключаем камеру (новые селекторы 2024-2025)
            camera_disabled = False
            camera_selectors = [
                "button[aria-label*='camera' i][data-is-muted='false']",
                "button[aria-label*='Turn off camera' i]",
                "div[jscontroller][jsaction*='camera'] button",
                "button[jsname='BOHaEe']",
            ]
            
            for selector in camera_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        aria_label = el.get_attribute('aria-label') or ''
                        if 'camera' in aria_label.lower():
                            el.click()
                            logger.info("Камера отключена")
                            camera_disabled = True
                            time.sleep(0.5)
                            break
                    if camera_disabled:
                        break
                except Exception as e:
                    logger.debug(f"Попытка отключить камеру через {selector}: {e}")
            
            # Отключаем микрофон
            mic_disabled = False
            mic_selectors = [
                "button[aria-label*='microphone' i][data-is-muted='false']",
                "button[aria-label*='Turn off microphone' i]",
                "div[jscontroller][jsaction*='microphone'] button",
            ]
            
            for selector in mic_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        aria_label = el.get_attribute('aria-label') or ''
                        if 'microphone' in aria_label.lower() or 'mic' in aria_label.lower():
                            el.click()
                            logger.info("Микрофон отключен")
                            mic_disabled = True
                            time.sleep(0.5)
                            break
                    if mic_disabled:
                        break
                except Exception as e:
                    logger.debug(f"Попытка отключить микрофон через {selector}: {e}")
            
            # Ищем поле ввода имени (если есть)
            try:
                name_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                for inp in name_inputs:
                    placeholder = (inp.get_attribute('placeholder') or '').lower()
                    aria_label = (inp.get_attribute('aria-label') or '').lower()
                    if 'name' in placeholder or 'имя' in placeholder or 'name' in aria_label:
                        inp.clear()
                        inp.send_keys(name)
                        logger.info(f"Введено имя: {name}")
                        time.sleep(0.5)
                        break
            except Exception as e:
                logger.debug(f"Не удалось ввести имя: {e}")
            
            # Нажимаем кнопку присоединения
            join_clicked = False
            join_patterns = [
                ('css', "button[jsname='Qx7uuf']"),
                ('css', "button[aria-label*='Join now' i]"),
                ('css', "button[aria-label*='Ask to join' i]"),
                ('xpath', "//button[contains(translate(., 'JOIN', 'join'), 'join')]"),
                ('xpath', "//button[contains(., 'Присоединиться')]"),
                ('xpath', "//span[contains(translate(., 'JOIN', 'join'), 'join')]/parent::button"),
            ]
            
            for method, selector in join_patterns:
                try:
                    if method == 'css':
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    else:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            logger.info("Нажата кнопка присоединения")
                            join_clicked = True
                            time.sleep(3)
                            break
                    if join_clicked:
                        break
                except Exception as e:
                    logger.debug(f"Попытка нажать кнопку {selector}: {e}")
            
            if not join_clicked:
                # Последняя попытка - ищем любую кнопку с текстом
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    text = btn.text.lower()
                    if any(word in text for word in ['join', 'присоединиться', 'войти']):
                        try:
                            btn.click()
                            logger.info(f"Нажата кнопка: {btn.text}")
                            join_clicked = True
                            break
                        except:
                            pass
            
            if join_clicked:
                logger.info(f"✅ Успешно присоединились к Google Meet: {meeting_url}")
                return True
            else:
                logger.warning("⚠️ Не удалось найти кнопку присоединения")
                # Но остаемся на странице - возможно, уже внутри
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка при присоединении к Google Meet: {e}")
            return False
            
    def join_zoom_meeting(self, meeting_id: str, password: Optional[str] = None, name: str = "Meeting Bot"):
        """Присоединиться к Zoom встрече через веб-клиент"""
        try:
            zoom_url = f"https://zoom.us/wc/{meeting_id}/join"
            self.driver.get(zoom_url)
            
            # Вводим имя
            name_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "inputname"))
            )
            name_input.send_keys(name)
            
            # Если есть пароль
            if password:
                password_input = self.driver.find_element(By.ID, "inputpasscode")
                password_input.send_keys(password)
            
            # Присоединяемся
            join_btn = self.driver.find_element(By.ID, "joinBtn")
            join_btn.click()
            
            logger.info(f"Успешно присоединились к Zoom встрече: {meeting_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при присоединении к Zoom: {e}")
            return False
            
    def join_yandex_telemost(self, meeting_url: str, name: str = "Meeting Bot"):
        """Присоединиться к Яндекс Телемост"""
        try:
            self.driver.get(meeting_url)
            
            # Ждем загрузки
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Вводим имя если требуется
            try:
                name_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                )
                name_input.clear()
                name_input.send_keys(name)
            except:
                pass
            
            # Отключаем камеру и микрофон
            controls = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for control in controls:
                aria_label = control.get_attribute("aria-label")
                if aria_label and ("камера" in aria_label.lower() or "микрофон" in aria_label.lower()):
                    control.click()
            
            # Присоединяемся
            join_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for btn in join_buttons:
                if "войти" in btn.text.lower() or "присоединиться" in btn.text.lower():
                    btn.click()
                    break
                    
            logger.info(f"Успешно присоединились к Яндекс Телемост: {meeting_url}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при присоединении к Яндекс Телемост: {e}")
            return False
    
    def start_recording(self):
        """Начать запись аудио с системы"""
        try:
            # Используем PulseAudio для захвата системного аудио
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.audio_file = f"/tmp/meeting_{timestamp}.wav"
            
            # Запускаем запись через ffmpeg
            self.recording_process = subprocess.Popen([
                'ffmpeg',
                '-f', 'pulse',
                '-i', 'default',  # или 'alsa_output.pci-0000_00_1f.3.analog-stereo.monitor'
                '-ac', '2',
                '-ar', '44100',
                '-y',
                self.audio_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.recording = True
            logger.info(f"Начата запись аудио: {self.audio_file}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при начале записи: {e}")
            return False
    
    def stop_recording(self):
        """Остановить запись"""
        try:
            if self.recording and self.recording_process:
                self.recording_process.terminate()
                self.recording_process.wait()
                self.recording = False
                logger.info("Запись остановлена")
                return True
        except Exception as e:
            logger.error(f"Ошибка при остановке записи: {e}")
            return False
    
    def transcribe_audio(self):
        """Транскрибировать аудио файл"""
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                logger.error("Аудио файл не найден")
                return None
                
            recognizer = sr.Recognizer()
            
            # Конвертируем в формат для speech_recognition
            audio = AudioSegment.from_wav(self.audio_file)
            audio = audio.set_channels(1)  # Моно
            audio = audio.set_frame_rate(16000)  # 16kHz
            
            temp_file = "/tmp/temp_audio.wav"
            audio.export(temp_file, format="wav")
            
            # Распознаем речь
            with sr.AudioFile(temp_file) as source:
                audio_data = recognizer.record(source)
                
            # Используем Google Speech Recognition
            try:
                text = recognizer.recognize_google(audio_data, language="ru-RU")
                self.transcript.append({
                    "timestamp": datetime.now().isoformat(),
                    "text": text
                })
                logger.info("Транскрипция завершена")
                return text
            except sr.UnknownValueError:
                logger.warning("Не удалось распознать речь")
                return "Не удалось распознать речь"
            except sr.RequestError as e:
                logger.error(f"Ошибка сервиса распознавания: {e}")
                return f"Ошибка: {e}"
                
        except Exception as e:
            logger.error(f"Ошибка при транскрипции: {e}")
            return None
    
    def save_to_github(self, content: str, filename: str):
        """Сохранить транскрипт в GitHub"""
        try:
            if not self.repo:
                logger.warning("GitHub репозиторий не настроен")
                return False
                
            path = f"transcripts/{filename}"
            
            # Проверяем существует ли файл
            try:
                file = self.repo.get_contents(path)
                # Обновляем существующий файл
                self.repo.update_file(
                    path,
                    f"Update transcript {filename}",
                    content,
                    file.sha
                )
            except:
                # Создаем новый файл
                self.repo.create_file(
                    path,
                    f"Add transcript {filename}",
                    content
                )
            
            logger.info(f"Файл сохранен в GitHub: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в GitHub: {e}")
            return False
    
    def leave_meeting(self):
        """Покинуть встречу"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            logger.info("Покинули встречу")
        except Exception as e:
            logger.error(f"Ошибка при выходе из встречи: {e}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.leave_meeting()
        if self.recording:
            self.stop_recording()
        if self.audio_file and os.path.exists(self.audio_file):
            os.remove(self.audio_file)


# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("🎥 Google Meet", callback_data='google_meet')],
        [InlineKeyboardButton("💻 Zoom", callback_data='zoom')],
        [InlineKeyboardButton("📹 Яндекс Телемост", callback_data='yandex')],
        [InlineKeyboardButton("📊 Статус", callback_data='status')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 Бот для автоматического участия во встречах\n\n"
        "Выберите тип встречи:",
        reply_markup=reply_markup
    )

async def handle_meeting_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик URL встречи"""
    url = update.message.text
    user_id = update.effective_user.id
    
    # Определяем тип встречи
    meeting_type = None
    if 'meet.google.com' in url:
        meeting_type = 'google_meet'
    elif 'zoom.us' in url:
        meeting_type = 'zoom'
    elif 'telemost.yandex' in url:
        meeting_type = 'yandex'
    
    if not meeting_type:
        await update.message.reply_text("❌ Не удалось определить тип встречи. Поддерживаются: Google Meet, Zoom, Яндекс Телемост")
        return
    
    await update.message.reply_text(f"⏳ Подключаюсь к встрече...")
    
    # Создаем бота и подключаемся
    bot = None
    try:
        bot = MeetingBot()
        bot.setup_driver(headless=True)
        
        success = False
        if meeting_type == 'google_meet':
            success = bot.join_google_meet(url)
        elif meeting_type == 'zoom':
            # Извлекаем ID встречи из URL
            meeting_id = url.split('/')[-1].split('?')[0]
            success = bot.join_zoom_meeting(meeting_id)
        elif meeting_type == 'yandex':
            success = bot.join_yandex_telemost(url)
        
        if success:
            await update.message.reply_text("✅ Успешно подключился к встрече!")
            
            # Начинаем запись
            if bot.start_recording():
                await update.message.reply_text("🎙️ Запись началась...")
                
                # Сохраняем контекст
                context.user_data['bot'] = bot
                context.user_data['recording'] = True
                
                # Отправляем кнопки управления
                keyboard = [
                    [InlineKeyboardButton("⏹️ Остановить запись", callback_data='stop_recording')],
                    [InlineKeyboardButton("🚪 Покинуть встречу", callback_data='leave_meeting')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Управление встречей:", reply_markup=reply_markup)
            else:
                await update.message.reply_text("⚠️ Подключился к встрече, но не удалось начать запись")
        else:
            await update.message.reply_text("❌ Не удалось подключиться к встрече. Проверьте URL и попробуйте снова.")
            if bot:
                bot.cleanup()
                
    except Exception as e:
        logger.error(f"Критическая ошибка при подключении к встрече: {e}")
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
        if bot:
            bot.cleanup()

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'stop_recording':
        bot = context.user_data.get('bot')
        if bot and bot.recording:
            bot.stop_recording()
            await query.edit_message_text("⏸️ Запись остановлена. Начинаю транскрипцию...")
            
            # Транскрибируем
            transcript = bot.transcribe_audio()
            
            if transcript:
                # Сохраняем в GitHub
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"transcript_{timestamp}.txt"
                
                if bot.save_to_github(transcript, filename):
                    await query.message.reply_text(f"✅ Транскрипт сохранен в GitHub:\n`{filename}`", parse_mode='Markdown')
                
                # Отправляем транскрипт пользователю
                await query.message.reply_document(
                    document=transcript.encode('utf-8'),
                    filename=filename,
                    caption="📝 Транскрипт встречи"
                )
            else:
                await query.message.reply_text("❌ Не удалось создать транскрипт")
    
    elif query.data == 'leave_meeting':
        bot = context.user_data.get('bot')
        if bot:
            bot.cleanup()
            context.user_data.clear()
            await query.edit_message_text("👋 Покинул встречу")
    
    elif query.data == 'status':
        bot = context.user_data.get('bot')
        if bot and bot.recording:
            await query.edit_message_text("🟢 Бот активен и записывает встречу")
        else:
            await query.edit_message_text("🔴 Бот не активен")

def main():
    """Главная функция"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meeting_url))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
