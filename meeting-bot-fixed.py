#!/usr/bin/env python3
"""
Meeting Bot - Исправленная версия для участия во встречах
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

# Selenium для автоматизации браузера
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Аудио обработка
import pyaudio
import wave
import speech_recognition as sr
from pydub import AudioSegment

# GitHub
from github import Github

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'goqorhopar/b24')

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
        if GITHUB_TOKEN:
            self.github = Github(GITHUB_TOKEN)
            self.repo = self.github.get_repo(GITHUB_REPO)
        else:
            self.github = None
            self.repo = None
        
    def setup_driver(self, headless=True):
        """Настройка Chrome драйвера"""
        options = Options()
        
        # Важные опции для работы с аудио/видео
        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--use-fake-device-for-media-stream')
        options.add_argument('--autoplay-policy=no-user-gesture-required')
        
        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        
        # Разрешения для микрофона и камеры
        prefs = {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        # Путь к ChromeDriver (автоматический поиск)
        try:
            # Пытаемся найти chromedriver в PATH
            self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            logger.error(f"Ошибка инициализации Chrome: {e}")
            # Fallback для Linux сервера
            try:
                service = Service('/usr/bin/chromedriver')
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e2:
                logger.error(f"Ошибка инициализации Chrome с сервисом: {e2}")
                raise e2
        
    def join_google_meet(self, meeting_url: str, name: str = "Meeting Bot"):
        """Присоединиться к Google Meet"""
        try:
            self.driver.get(meeting_url)
            
            # Ждем загрузки страницы
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Отключаем камеру и микрофон
            try:
                # Современные селекторы Google Meet
                camera_selectors = [
                    "[data-is-muted='false'][aria-label*='camera']",
                    "[aria-label*='Turn off camera']",
                    "[aria-label*='Turn on camera']",
                    "button[aria-label*='camera']",
                    "[jsname='BOHaEe']"  # Кнопка камеры
                ]
                
                for selector in camera_selectors:
                    try:
                        camera_btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        camera_btn.click()
                        logger.info("Камера отключена")
                        break
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Не удалось отключить камеру: {e}")
                
            try:
                # Селекторы для микрофона
                mic_selectors = [
                    "[data-is-muted='false'][aria-label*='microphone']",
                    "[aria-label*='Turn off microphone']",
                    "[aria-label*='Turn on microphone']",
                    "button[aria-label*='microphone']",
                    "[jsname='BOHaEe']"  # Кнопка микрофона
                ]
                
                for selector in mic_selectors:
                    try:
                        mic_btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        mic_btn.click()
                        logger.info("Микрофон отключен")
                        break
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Не удалось отключить микрофон: {e}")
            
            # Вводим имя
            try:
                name_selectors = [
                    "input[type='text']",
                    "input[placeholder*='name']",
                    "input[aria-label*='name']",
                    "[data-promo-anchor-id='join-form-name-input']"
                ]
                
                name_input = None
                for selector in name_selectors:
                    try:
                        name_input = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if name_input:
                    name_input.clear()
                    name_input.send_keys(name)
                    logger.info(f"Введено имя: {name}")
                else:
                    logger.warning("Не удалось найти поле для ввода имени")
                    
            except Exception as e:
                logger.warning(f"Не удалось ввести имя: {e}")
            
            # Нажимаем кнопку присоединения
            try:
                join_selectors = [
                    "button[jsname='Qx7uuf']",  # Кнопка "Join now"
                    "button[aria-label*='Join now']",
                    "button[aria-label*='Join']",
                    "button:contains('Join')",
                    "button:contains('Присоединиться')"
                ]
                
                join_clicked = False
                for selector in join_selectors:
                    try:
                        if ":contains" in selector:
                            # Используем XPath для текстового поиска
                            xpath = f"//button[contains(text(), '{selector.split(':contains(')[1].rstrip(')')}')]"
                            join_btn = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, xpath))
                            )
                        else:
                            join_btn = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        join_btn.click()
                        logger.info("Нажата кнопка присоединения")
                        join_clicked = True
                        break
                    except:
                        continue
                
                if not join_clicked:
                    # Fallback - ищем любую кнопку с текстом join
                    join_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
                    for btn in join_buttons:
                        btn_text = btn.text.lower()
                        if "join" in btn_text or "присоединиться" in btn_text or "войти" in btn_text:
                            btn.click()
                            logger.info("Нажата кнопка присоединения (fallback)")
                            break
                            
            except Exception as e:
                logger.warning(f"Не удалось нажать кнопку присоединения: {e}")
                    
            logger.info(f"Успешно присоединились к встрече: {meeting_url}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при присоединении к Google Meet: {e}")
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
