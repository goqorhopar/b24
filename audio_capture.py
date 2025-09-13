"""
Модуль захвата аудио с экрана/браузера для транскрипции встреч
"""
import os
import time
import logging
import threading
import queue
import wave
import tempfile
import subprocess
from typing import Optional, Callable, Dict, Any
import numpy as np
import sounddevice as sd
import soundfile as sf
import pyaudio
from datetime import datetime

log = logging.getLogger(__name__)

class AudioCapture:
    """Класс для захвата аудио с системных устройств или экрана"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 audio_format: int = pyaudio.paInt16):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio_format = audio_format
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.temp_files = []
        
    def get_audio_devices(self) -> Dict[str, Any]:
        """Получить список доступных аудиоустройств"""
        devices = {
            'input': [],
            'output': [],
            'loopback': []
        }
        
        try:
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                
                if device_info['maxInputChannels'] > 0:
                    devices['input'].append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
                
                if device_info['maxOutputChannels'] > 0:
                    devices['output'].append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxOutputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
                
                # Проверка на loopback устройства (для захвата системного звука)
                if 'loopback' in device_info['name'].lower() or 'stereo mix' in device_info['name'].lower():
                    devices['loopback'].append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
        
        except Exception as e:
            log.error(f"Ошибка при получении списка устройств: {e}")
        
        return devices
    
    def find_best_loopback_device(self) -> Optional[int]:
        """Найти лучшее loopback устройство для захвата системного звука"""
        devices = self.get_audio_devices()
        
        # Приоритет: устройства с пометкой loopback
        for device in devices['loopback']:
            log.info(f"Найдено loopback устройство: {device['name']} (индекс: {device['index']})")
            return device['index']
        
        # Если нет loopback, ищем стерео микшер
        for device in devices['input']:
            if 'stereo mix' in device['name'].lower() or 'mix' in device['name'].lower():
                log.info(f"Найдено устройство Stereo Mix: {device['name']} (индекс: {device['index']})")
                return device['index']
        
        # Если ничего не найдено, используем устройство по умолчанию
        try:
            default_device = self.audio.get_default_input_device_info()
            log.info(f"Используем устройство по умолчанию: {default_device['name']} (индекс: {default_device['index']})")
            return default_device['index']
        except Exception as e:
            log.error(f"Не удалось получить устройство по умолчанию: {e}")
            return None
    
    def start_recording(self, device_index: Optional[int] = None) -> bool:
        """Начать запись аудио"""
        if self.is_recording:
            log.warning("Запись уже идет")
            return False
        
        try:
            if device_index is None:
                device_index = self.find_best_loopback_device()
            
            if device_index is None:
                log.error("Не найдено подходящее аудиоустройство")
                return False
            
            # Настройка потока записи
            self.stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._recording_worker)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            log.info(f"Начата запись аудио с устройства {device_index}")
            return True
            
        except Exception as e:
            log.error(f"Ошибка при начале записи: {e}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """Остановить запись и вернуть путь к файлу"""
        if not self.is_recording:
            log.warning("Запись не идет")
            return None
        
        try:
            self.is_recording = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            if self.recording_thread:
                self.recording_thread.join(timeout=5)
                self.recording_thread = None
            
            # Сохранение записанных данных
            audio_data = []
            while not self.audio_queue.empty():
                audio_data.append(self.audio_queue.get())
            
            if audio_data:
                # Создание временного файла
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=".wav", 
                    delete=False,
                    prefix=f"meeting_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                )
                
                # Сохранение в WAV файл
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(audio_data))
                
                self.temp_files.append(temp_file.name)
                log.info(f"Запись остановлена, файл сохранен: {temp_file.name}")
                return temp_file.name
            else:
                log.warning("Нет записанных аудиоданных")
                return None
                
        except Exception as e:
            log.error(f"Ошибка при остановке записи: {e}")
            return None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback функция для захвата аудио"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def _recording_worker(self):
        """Рабочий поток для обработки аудио"""
        log.debug("Запущен рабочий поток записи аудио")
        
        while self.is_recording:
            time.sleep(0.1)
        
        log.debug("Рабочий поток записи аудио остановлен")
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.stop_recording()
        
        # Удаление временных файлов
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    log.debug(f"Удален временный файл: {temp_file}")
            except Exception as e:
                log.error(f"Ошибка при удалении временного файла {temp_file}: {e}")
        
        self.temp_files.clear()
        
        if self.audio:
            self.audio.terminate()
            log.info("PyAudio ресурс освобожден")

class ScreenAudioCapture:
    """Класс для захвата аудио с экрана (через FFmpeg)"""
    
    def __init__(self):
        self.ffmpeg_process = None
        self.temp_file = None
        self.is_recording = False
        
    def start_recording(self, output_file: Optional[str] = None) -> bool:
        """Начать запись аудио с экрана"""
        if self.is_recording:
            log.warning("Запись уже идет")
            return False
        
        try:
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"screen_audio_{timestamp}.wav"
            
            self.temp_file = output_file
            
            # Команда FFmpeg для захвата системного аудио
            # Для Windows
            if os.name == 'nt':
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-f', 'dshow',
                    '-i', 'audio=virtual-audio-capturer',
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    '-y',
                    output_file
                ]
            else:
                # Для Linux/Mac
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-f', 'pulse',
                    '-i', 'default',
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    '-y',
                    output_file
                ]
            
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.is_recording = True
            log.info(f"Начата запись аудио с экрана в файл: {output_file}")
            return True
            
        except Exception as e:
            log.error(f"Ошибка при начале записи экрана: {e}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """Остановить запись и вернуть путь к файлу"""
        if not self.is_recording:
            log.warning("Запись не идет")
            return None
        
        try:
            self.is_recording = False
            
            if self.ffmpeg_process:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=10)
                self.ffmpeg_process = None
            
            if self.temp_file and os.path.exists(self.temp_file):
                log.info(f"Запись экрана остановлена, файл: {self.temp_file}")
                return self.temp_file
            else:
                log.warning("Файл записи не найден")
                return None
                
        except Exception as e:
            log.error(f"Ошибка при остановке записи экрана: {e}")
            return None

class BrowserAudioCapture:
    """Класс для захвата аудио конкретного браузера"""
    
    def __init__(self):
        self.audio_capture = AudioCapture()
        
    def start_browser_audio_capture(self, browser_name: str = "chrome") -> bool:
        """Начать захват аудио конкретного браузера"""
        try:
            devices = self.audio_capture.get_audio_devices()
            
            # Поиск устройства браузера
            browser_device = None
            for device in devices['output']:
                if browser_name.lower() in device['name'].lower():
                    # Для захвата аудио браузера нам нужно loopback устройство
                    # В Windows это может быть "Stereo Mix" или подобное
                    log.info(f"Найден браузер: {device['name']}")
                    break
            
            # Начинаем запись с лучшего доступного устройства
            return self.audio_capture.start_recording()
            
        except Exception as e:
            log.error(f"Ошибка при начале захвата аудио браузера: {e}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """Остановить запись"""
        return self.audio_capture.stop_recording()
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.audio_capture.cleanup()

class MeetingAudioRecorder:
    """Основной класс для записи аудио встреч"""
    
    def __init__(self, recording_method: str = "auto"):
        self.recording_method = recording_method
        self.audio_capture = None
        self.screen_capture = None
        self.browser_capture = None
        self.current_file = None
        
        # Выбор метода записи
        if recording_method == "system":
            self.audio_capture = AudioCapture()
        elif recording_method == "screen":
            self.screen_capture = ScreenAudioCapture()
        elif recording_method == "browser":
            self.browser_capture = BrowserAudioCapture()
        else:  # auto
            # Пробуем разные методы в порядке приоритета
            self.audio_capture = AudioCapture()
    
    def start_meeting_recording(self, meeting_url: Optional[str] = None) -> bool:
        """Начать запись встречи"""
        try:
            # Определение метода записи на основе платформы
            if self.recording_method == "auto":
                if meeting_url:
                    if 'zoom' in meeting_url.lower():
                        # Для Zoom пробуем системный звук
                        return self.audio_capture.start_recording() if self.audio_capture else False
                    elif 'meet.google.com' in meeting_url.lower():
                        # Для Google Meet пробуем захват браузера
                        return self.browser_capture.start_browser_audio_capture() if self.browser_capture else False
                    else:
                        # Для остальных платформ - системный звук
                        return self.audio_capture.start_recording() if self.audio_capture else False
                else:
                    # Если URL не указан, пробуем системный звук
                    return self.audio_capture.start_recording() if self.audio_capture else False
            
            # Для конкретных методов
            elif self.recording_method == "system":
                return self.audio_capture.start_recording() if self.audio_capture else False
            elif self.recording_method == "screen":
                return self.screen_capture.start_recording() if self.screen_capture else False
            elif self.recording_method == "browser":
                return self.browser_capture.start_browser_audio_capture() if self.browser_capture else False
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при начале записи встречи: {e}")
            return False
    
    def stop_meeting_recording(self) -> Optional[str]:
        """Остановить запись встречи"""
        try:
            if self.audio_capture:
                self.current_file = self.audio_capture.stop_recording()
            elif self.screen_capture:
                self.current_file = self.screen_capture.stop_recording()
            elif self.browser_capture:
                self.current_file = self.browser_capture.stop_recording()
            
            return self.current_file
            
        except Exception as e:
            log.error(f"Ошибка при остановке записи встречи: {e}")
            return None
    
    def get_audio_devices_info(self) -> Dict[str, Any]:
        """Получить информацию об аудиоустройствах"""
        if self.audio_capture:
            return self.audio_capture.get_audio_devices()
        return {'input': [], 'output': [], 'loopback': []}
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.audio_capture:
            self.audio_capture.cleanup()
        if self.screen_capture:
            self.screen_capture.stop_recording()
        if self.browser_capture:
            self.browser_capture.cleanup()

# Функция для создания экземпляра рекордера
def create_meeting_recorder(recording_method: str = "auto") -> MeetingAudioRecorder:
    """Создать экземпляр рекордера встреч"""
    return MeetingAudioRecorder(recording_method=recording_method)
