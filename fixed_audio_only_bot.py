#!/usr/bin/env python3
import os
import sys
import time
import datetime
import subprocess
import asyncio
import logging
from pathlib import Path
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from faster_whisper import WhisperModel
from playwright.async_api import async_playwright

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RECORD_DIR = Path(os.getenv("RECORD_DIR", "/recordings"))
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "medium")
MEETING_TIMEOUT_MIN = int(os.getenv("MEETING_TIMEOUT_MIN", "3"))

class AudioOnlyMeetingBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.whisper_model = None
        self.recording_process = None
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 **Audio Meeting Bot активен!**\n\n"
            "✅ **Возможности:**\n"
            "• Присоединение к встречам\n"
            "• Запись только аудио\n"
            "• Транскрипция речи\n"
            "• Google Meet, Zoom, Яндекс\n\n"
            "🔗 **Отправьте ссылку на встречу**"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        
        if any(platform in text.lower() for platform in ['meet.google.com', 'zoom.us', 'telemost.yandex.ru', 'talk.kontur.ru']):
            await update.message.reply_text(
                f"🎯 **Встреча обнаружена!**\n\n"
                f"🔗 **URL:** {text}\n\n"
                f"🚀 **Начинаю обработку...**\n"
                f"⏳ Записываю аудио {MEETING_TIMEOUT_MIN} минут"
            )
            
            try:
                result = await self.process_meeting(text)
                
                if result:
                    await update.message.reply_text(
                        "✅ **Встреча обработана!**\n\n"
                        f"📝 **Транскрипт:**\n{result['transcript'][:1000]}...\n\n"
                        f"🎙️ **Аудио:** {result['audio_file']}\n"
                        f"⏱️ **Длительность:** {result['duration']} мин"
                    )
                else:
                    await update.message.reply_text("❌ Ошибка при обработке встречи")
                    
            except Exception as e:
                logger.error(f"Ошибка обработки встречи: {e}")
                await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        else:
            await update.message.reply_text(
                "❌ Не удалось распознать ссылку на встречу.\n\n"
                "Отправьте корректную ссылку на:\n"
                "• Google Meet\n"
                "• Zoom\n"
                "• Яндекс Телемост\n"
                "• Контур.Толк"
            )
    
    async def process_meeting(self, meeting_url: str):
        try:
            # 1. Присоединяемся к встрече
            await self.join_meeting(meeting_url)
            
            # 2. Записываем только аудио
            audio_file = await self.record_audio_only()
            
            # 3. Транскрипция
            transcript = self.transcribe_audio(audio_file)
            
            return {
                'transcript': transcript,
                'audio_file': audio_file,
                'duration': MEETING_TIMEOUT_MIN
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки встречи: {e}")
            return None
    
    async def join_meeting(self, meeting_url: str):
        """Улучшенное присоединение к встрече"""
        playwright = await async_playwright().start()
        
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--mute-audio",
                "--autoplay-policy=no-user-gesture-required",
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["microphone", "camera"],
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        
        try:
            await page.goto(meeting_url, wait_until="load", timeout=30000)
            await asyncio.sleep(5)  # Ждем загрузки
            
            # Отключаем камеру и микрофон
            try:
                await page.evaluate("""
                    // Отключаем камеру
                    const cameraButtons = document.querySelectorAll('[aria-label*="camera"], [aria-label*="Turn off camera"]');
                    for (let btn of cameraButtons) {
                        if (btn.getAttribute('aria-label')?.includes('Turn off') || btn.getAttribute('data-is-muted') === 'false') {
                            btn.click();
                            break;
                        }
                    }
                    
                    // Отключаем микрофон
                    const micButtons = document.querySelectorAll('[aria-label*="microphone"], [aria-label*="Turn off microphone"]');
                    for (let btn of micButtons) {
                        if (btn.getAttribute('aria-label')?.includes('Turn off') || btn.getAttribute('data-is-muted') === 'false') {
                            btn.click();
                            break;
                        }
                    }
                """)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Не удалось отключить камеру/микрофон: {e}")
            
            # Вводим имя
            try:
                await page.fill('input[type="text"]', "Meeting Bot")
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Не удалось ввести имя: {e}")
            
            # Присоединяемся к встрече
            join_selectors = [
                'button:has-text("Присоединиться")',
                'button:has-text("Join now")',
                'button:has-text("Join")',
                'button:has-text("Войти")',
                '[jsname="Qx7uuf"]',
                'button[aria-label*="Join"]'
            ]
            
            joined = False
            for selector in join_selectors:
                try:
                    await page.click(selector, timeout=5000)
                    logger.info(f"Нажата кнопка присоединения: {selector}")
                    joined = True
                    break
                except:
                    continue
            
            if not joined:
                # Fallback - ищем любую кнопку с текстом join
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.text_content()
                    if text and any(word in text.lower() for word in ['join', 'присоединиться', 'войти']):
                        await button.click()
                        logger.info(f"Нажата кнопка (fallback): {text}")
                        joined = True
                        break
            
            if joined:
                await asyncio.sleep(3)  # Ждем присоединения
                logger.info("Успешно присоединился к встрече")
            else:
                logger.warning("Не удалось найти кнопку присоединения")
                
        except Exception as e:
            logger.error(f"Ошибка при присоединении к встрече: {e}")
        finally:
            await context.close()
            await browser.close()
            await playwright.stop()
    
    async def record_audio_only(self):
        """Улучшенная запись аудио"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = RECORD_DIR / f"audio_{timestamp}.wav"
        
        # Создаем директорию если не существует
        audio_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Проверяем PulseAudio
        try:
            result = subprocess.run(['pulseaudio', '--check'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.info("Запускаю PulseAudio...")
                subprocess.run(['pulseaudio', '--start'], check=False)
                await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Проблема с PulseAudio: {e}")
        
        # Получаем список доступных источников
        try:
            result = subprocess.run(['pactl', 'list', 'short', 'sources'], capture_output=True, text=True)
            sources = result.stdout.strip().split('\n')
            logger.info(f"Доступные источники: {sources}")
            
            # Ищем monitor источник
            monitor_source = None
            for source in sources:
                if 'monitor' in source:
                    monitor_source = source.split()[1]
                    break
            
            if not monitor_source:
                monitor_source = 'default'
                
            logger.info(f"Используем источник: {monitor_source}")
            
        except Exception as e:
            logger.warning(f"Не удалось получить список источников: {e}")
            monitor_source = 'default'
        
        # Запись аудио
        cmd = [
            'ffmpeg', '-y',
            '-f', 'pulse',
            '-i', monitor_source,
            '-ac', '1',
            '-ar', '16000',
            '-t', str(MEETING_TIMEOUT_MIN * 60),
            '-loglevel', 'error',
            str(audio_file)
        ]
        
        logger.info(f"Записываю аудио: {' '.join(cmd)}")
        
        try:
            self.recording_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Ждем завершения записи
            await asyncio.sleep(MEETING_TIMEOUT_MIN * 60)
            
            if self.recording_process:
                self.recording_process.terminate()
                self.recording_process.wait()
                
            # Проверяем что файл создался
            if audio_file.exists() and audio_file.stat().st_size > 0:
                logger.info(f"Запись завершена: {audio_file} ({audio_file.stat().st_size} bytes)")
                return audio_file
            else:
                logger.error("Файл записи не создался или пустой")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка записи аудио: {e}")
            if self.recording_process:
                self.recording_process.terminate()
            return None
    
    def transcribe_audio(self, audio_file: Path):
        """Транскрипция аудио"""
        if not audio_file or not audio_file.exists():
            logger.error("Аудио файл не найден")
            return "Аудио файл не найден"
        
        try:
            if not self.whisper_model:
                logger.info("Загружаю модель Whisper...")
                self.whisper_model = WhisperModel(WHISPER_MODEL_NAME, device="cpu", compute_type="int8")
            
            logger.info(f"Начинаю транскрипцию: {audio_file}")
            segments, info = self.whisper_model.transcribe(
                str(audio_file), 
                language="ru", 
                vad=True,
                word_timestamps=True
            )
            
            text_parts = []
            for seg in segments:
                if seg.text.strip():
                    text_parts.append(f"[{seg.start:.1f}s] {seg.text.strip()}")
            
            text = "\n".join(text_parts)
            logger.info(f"Транскрипция завершена: {len(text)} символов")
            return text
            
        except Exception as e:
            logger.error(f"Ошибка транскрипции: {e}")
            return f"Ошибка транскрипции: {str(e)}"

def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен")
        return
    
    bot = AudioOnlyMeetingBot()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    logger.info("🚀 Запуск Audio Meeting Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
