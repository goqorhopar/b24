from playwright.sync_api import sync_playwright
import json
import os

COOKIES_PATH = "cookies.json"

class MeetingBotPlaywright:
    def transcribe_audio(self):
        try:
            from faster_whisper import WhisperModel
            audio_file = getattr(self, "audio_file", None)
            if not audio_file or not os.path.exists(audio_file):
                print("Аудио файл не найден для транскрипции!")
                return
            print("Запускаю транскрипцию...")
            model = WhisperModel("medium", device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_file, language="ru", beam_size=5, vad_filter=True)
            transcript = []
            for segment in segments:
                transcript.append(segment.text.strip())
            transcript_text = "\n".join(transcript)
            transcript_file = audio_file.replace(".wav", "_transcript.txt")
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            print(f"Транскрипция завершена! Файл: {transcript_file}")
        except Exception as e:
            print(f"Ошибка транскрипции: {e}")
    def __init__(self, meeting_url):
        self.meeting_url = meeting_url
        self.browser = None
        self.context = None
        self.page = None

    def load_cookies(self):
        if os.path.exists(COOKIES_PATH):
            return COOKIES_PATH
        return None

    def start_audio_recording(self, audio_file="meeting_audio.wav"):
        import subprocess
        self.audio_file = audio_file
        # Попробуем PulseAudio и ALSA
        commands = [
            ["ffmpeg", "-f", "pulse", "-i", "default", "-ac", "2", "-ar", "16000", "-y", self.audio_file],
            ["ffmpeg", "-f", "alsa", "-i", "default", "-ac", "2", "-ar", "16000", "-y", self.audio_file]
        ]
        for cmd in commands:
            try:
                self.recording_process = subprocess.Popen(cmd)
                print(f"Запись аудио начата: {' '.join(cmd)}")
                return
            except Exception as e:
                print(f"Ошибка запуска ffmpeg: {e}")
        print("Не удалось запустить запись аудио!")

    def stop_audio_recording(self):
        if hasattr(self, "recording_process") and self.recording_process:
            self.recording_process.terminate()
            self.recording_process.wait()
            print(f"Запись аудио остановлена. Файл: {getattr(self, 'audio_file', None)}")

    def join_meeting(self):
        with sync_playwright() as p:
            self.browser = p.chromium.launch(headless=False)
            cookies_file = self.load_cookies()
            if cookies_file:
                self.context = self.browser.new_context(storage_state=cookies_file)
            else:
                self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.page.goto(self.meeting_url)
            # Пример для Google Meet
            if "meet.google.com" in self.meeting_url:
                try:
                    self.page.wait_for_selector("text=Join now", timeout=15000)
                    self.page.click("text=Join now")
                except Exception as e:
                    print(f"Ошибка входа в Google Meet: {e}")
            # Пример для Zoom (если открыт для гостя)
            elif "zoom.us" in self.meeting_url:
                try:
                    self.page.wait_for_selector("text=Join from Your Browser", timeout=20000)
                    self.page.click("text=Join from Your Browser")
                except Exception as e:
                    print(f"Ошибка входа в Zoom: {e}")
            # Пример для Яндекс Телемост
            elif "telemost.yandex" in self.meeting_url:
                # Добавить логику входа
                pass
            # Пример для Контур Толк
            elif "contour.ru" in self.meeting_url:
                # Добавить логику входа
                pass
            print("Бот внутри встречи!")
            self.start_audio_recording()
            input("Нажмите Enter для выхода...")
            self.stop_audio_recording()
            self.transcribe_audio()
            self.browser.close()

if __name__ == "__main__":
    url = input("Вставьте ссылку на встречу: ")
    bot = MeetingBotPlaywright(url)
    bot.join_meeting()
