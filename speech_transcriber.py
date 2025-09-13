"""
Модуль для транскрипции аудио в текст с использованием Whisper
"""
import os
import time
import logging
import threading
import queue
import tempfile
from typing import Optional, Dict, Any, Callable, List
import whisper
import torch
import numpy as np
from datetime import datetime
import json

log = logging.getLogger(__name__)

class SpeechTranscriber:
    """Класс для транскрипции аудио с использованием Whisper"""
    
    def __init__(self, 
                 model_name: str = "base",
                 device: str = "auto",
                 language: str = "ru"):
        self.model_name = model_name
        self.device = self._get_optimal_device(device)
        self.language = language
        self.model = None
        self.is_loaded = False
        self.transcription_queue = queue.Queue()
        self.is_transcribing = False
        self.transcription_thread = None
        
        # Доступные модели Whisper
        self.available_models = {
            "tiny": "39M, ~32x реального времени",
            "base": "74M, ~16x реального времени", 
            "small": "244M, ~6x реального времени",
            "medium": "769M, ~2x реального времени",
            "large": "1550M, ~1x реального времени"
        }
        
        log.info(f"Инициализация SpeechTranscriber: model={model_name}, device={self.device}")
    
    def _get_optimal_device(self, device: str) -> str:
        """Определить оптимальное устройство для вычислений"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                log.info("Обнаружен CUDA, используется GPU")
            else:
                device = "cpu"
                log.info("CUDA не обнаружен, используется CPU")
        return device
    
    def load_model(self) -> bool:
        """Загрузить модель Whisper"""
        if self.is_loaded:
            log.info("Модель уже загружена")
            return True
        
        try:
            log.info(f"Загрузка Whisper модели '{self.model_name}'...")
            
            # Проверка доступности модели
            if self.model_name not in self.available_models:
                log.warning(f"Модель '{self.model_name}' не найдена, используется 'base'")
                self.model_name = "base"
            
            # Загрузка модели
            self.model = whisper.load_model(
                self.model_name, 
                device=self.device
            )
            
            self.is_loaded = True
            log.info(f"Модель '{self.model_name}' успешно загружена на {self.device}")
            return True
            
        except Exception as e:
            log.error(f"Ошибка при загрузке модели: {e}")
            return False
    
    def transcribe_file(self, audio_file_path: str, 
                       language: Optional[str] = None,
                       task: str = "transcribe") -> Optional[Dict[str, Any]]:
        """Транскрибировать аудиофайл"""
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        try:
            log.info(f"Начало транскрипции файла: {audio_file_path}")
            
            # Проверка существования файла
            if not os.path.exists(audio_file_path):
                log.error(f"Файл не найден: {audio_file_path}")
                return None
            
            # Настройки транскрипции
            transcribe_options = {
                'language': language or self.language,
                'task': task,
                'verbose': False,
                'word_timestamps': True,
                'fp16': False if self.device == 'cpu' else True
            }
            
            # Выполнение транскрипции
            start_time = time.time()
            result = self.model.transcribe(audio_file_path, **transcribe_options)
            end_time = time.time()
            
            # Форматирование результата
            transcription_result = {
                'text': result.get('text', ''),
                'language': result.get('language', self.language),
                'duration': end_time - start_time,
                'segments': result.get('segments', []),
                'words': self._extract_words_with_timestamps(result),
                'file_path': audio_file_path,
                'timestamp': datetime.now().isoformat()
            }
            
            log.info(f"Транскрипция завершена за {transcription_result['duration']:.2f} секунд")
            log.info(f"Длина текста: {len(transcription_result['text'])} символов")
            
            return transcription_result
            
        except Exception as e:
            log.error(f"Ошибка при транскрипции файла: {e}")
            return None
    
    def transcribe_audio_data(self, audio_data: np.ndarray,
                            sample_rate: int = 16000,
                            language: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Транскрибировать аудиоданные (numpy array)"""
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        try:
            log.info("Начало транскрипции аудиоданных")
            
            # Настройки транскрипции
            transcribe_options = {
                'language': language or self.language,
                'task': 'transcribe',
                'verbose': False,
                'word_timestamps': True,
                'fp16': False if self.device == 'cpu' else True
            }
            
            # Выполнение транскрипции
            start_time = time.time()
            result = self.model.transcribe(audio_data, **transcribe_options)
            end_time = time.time()
            
            # Форматирование результата
            transcription_result = {
                'text': result.get('text', ''),
                'language': result.get('language', self.language),
                'duration': end_time - start_time,
                'segments': result.get('segments', []),
                'words': self._extract_words_with_timestamps(result),
                'sample_rate': sample_rate,
                'timestamp': datetime.now().isoformat()
            }
            
            log.info(f"Транскрипция завершена за {transcription_result['duration']:.2f} секунд")
            log.info(f"Длина текста: {len(transcription_result['text'])} символов")
            
            return transcription_result
            
        except Exception as e:
            log.error(f"Ошибка при транскрипции аудиоданных: {e}")
            return None
    
    def start_real_time_transcription(self, 
                                    audio_callback: Callable,
                                    language: Optional[str] = None) -> bool:
        """Начать транскрипцию в реальном времени"""
        if self.is_transcribing:
            log.warning("Транскрипция уже идет")
            return False
        
        try:
            self.is_transcribing = True
            self.transcription_thread = threading.Thread(
                target=self._real_time_transcription_worker,
                args=(audio_callback, language)
            )
            self.transcription_thread.daemon = True
            self.transcription_thread.start()
            
            log.info("Начата транскрипция в реальном времени")
            return True
            
        except Exception as e:
            log.error(f"Ошибка при начале транскрипции в реальном времени: {e}")
            return False
    
    def stop_real_time_transcription(self):
        """Остановить транскрипцию в реальном времени"""
        if not self.is_transcribing:
            log.warning("Транскрипция не идет")
            return
        
        try:
            self.is_transcribing = False
            
            if self.transcription_thread:
                self.transcription_thread.join(timeout=5)
                self.transcription_thread = None
            
            log.info("Транскрипция в реальном времени остановлена")
            
        except Exception as e:
            log.error(f"Ошибка при остановке транскрипции: {e}")
    
    def _real_time_transcription_worker(self, audio_callback: Callable, language: Optional[str]):
        """Рабочий поток для транскрипции в реальном времени"""
        log.debug("Запущен рабочий поток транскрипции")
        
        buffer = []
        buffer_duration = 0  # секунды
        chunk_duration = 5  # секунд
        
        while self.is_transcribing:
            try:
                # Получение аудиоданных от callback
                audio_chunk = audio_callback()
                if audio_chunk is not None:
                    buffer.append(audio_chunk)
                    buffer_duration += len(audio_chunk) / 16000  # предполагаем sample_rate = 16000
                    
                    # Если накоплено достаточно данных, транскрибируем
                    if buffer_duration >= chunk_duration:
                        audio_data = np.concatenate(buffer)
                        
                        # Транскрипция чанка
                        result = self.transcribe_audio_data(
                            audio_data, 
                            sample_rate=16000,
                            language=language
                        )
                        
                        if result and result['text'].strip():
                            # Отправка результата в очередь
                            self.transcription_queue.put(result)
                            log.debug(f"Транскрибирован чанк: {len(result['text'])} символов")
                        
                        # Очистка буфера
                        buffer = []
                        buffer_duration = 0
                
                time.sleep(0.1)
                
            except Exception as e:
                log.error(f"Ошибка в рабочем потоке транскрипции: {e}")
                time.sleep(1)
        
        log.debug("Рабочий поток транскрипции остановлен")
    
    def get_transcription_results(self) -> List[Dict[str, Any]]:
        """Получить результаты транскрипции"""
        results = []
        while not self.transcription_queue.empty():
            try:
                result = self.transcription_queue.get_nowait()
                results.append(result)
            except queue.Empty:
                break
        return results
    
    def _extract_words_with_timestamps(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлечь слова с временными метками"""
        words = []
        
        if 'segments' in result:
            for segment in result['segments']:
                if 'words' in segment:
                    for word_info in segment['words']:
                        words.append({
                            'word': word_info.get('word', ''),
                            'start': word_info.get('start', 0),
                            'end': word_info.get('end', 0),
                            'confidence': word_info.get('probability', 0)
                        })
        
        return words
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получить информацию о модели"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'is_loaded': self.is_loaded,
            'language': self.language,
            'available_models': self.available_models,
            'current_model_info': self.available_models.get(self.model_name, 'Unknown')
        }
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.stop_real_time_transcription()
        
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            log.info("Модель Whisper выгружена")

class MeetingTranscriber:
    """Класс для транскрипции встреч"""
    
    def __init__(self, 
                 model_name: str = "base",
                 language: str = "ru",
                 enable_real_time: bool = False):
        self.transcriber = SpeechTranscriber(
            model_name=model_name,
            language=language
        )
        self.enable_real_time = enable_real_time
        self.meeting_transcripts = []
        self.current_transcript = None
        
    def transcribe_meeting_audio(self, audio_file_path: str, 
                               meeting_info: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Транскрибировать аудио встречи"""
        try:
            log.info(f"Начало транскрипции встречи из файла: {audio_file_path}")
            
            # Транскрипция аудио
            transcription_result = self.transcriber.transcribe_file(audio_file_path)
            
            if not transcription_result:
                log.error("Не удалось транскрибировать аудио встречи")
                return None
            
            # Добавление информации о встрече
            meeting_transcript = {
                'meeting_info': meeting_info or {},
                'transcription': transcription_result,
                'processed_at': datetime.now().isoformat(),
                'summary': self._generate_summary(transcription_result['text'])
            }
            
            self.meeting_transcripts.append(meeting_transcript)
            self.current_transcript = meeting_transcript
            
            log.info("Транскрипция встречи успешно завершена")
            return meeting_transcript
            
        except Exception as e:
            log.error(f"Ошибка при транскрипции встречи: {e}")
            return None
    
    def start_meeting_transcription(self, 
                                  audio_callback: Callable,
                                  meeting_info: Optional[Dict[str, Any]] = None) -> bool:
        """Начать транскрипцию встречи в реальном времени"""
        if not self.enable_real_time:
            log.warning("Транскрипция в реальном времени отключена")
            return False
        
        try:
            # Инициализация текущей транскрипции
            self.current_transcript = {
                'meeting_info': meeting_info or {},
                'transcription': {
                    'text': '',
                    'segments': [],
                    'words': [],
                    'language': self.transcriber.language,
                    'timestamp': datetime.now().isoformat()
                },
                'started_at': datetime.now().isoformat(),
                'real_time_chunks': []
            }
            
            # Начало транскрипции
            success = self.transcriber.start_real_time_transcription(
                audio_callback,
                language=self.transcriber.language
            )
            
            if success:
                log.info("Начата транскрипция встречи в реальном времени")
                return True
            else:
                return False
                
        except Exception as e:
            log.error(f"Ошибка при начале транскрипции встречи: {e}")
            return False
    
    def update_real_time_transcript(self):
        """Обновить транскрипцию в реальном времени"""
        if not self.current_transcript:
            return
        
        try:
            # Получение новых результатов транскрипции
            new_chunks = self.transcriber.get_transcription_results()
            
            for chunk in new_chunks:
                self.current_transcript['real_time_chunks'].append(chunk)
                
                # Обновление полного текста
                if chunk['text'].strip():
                    self.current_transcript['transcription']['text'] += ' ' + chunk['text']
                    self.current_transcript['transcription']['segments'].extend(chunk['segments'])
                    self.current_transcript['transcription']['words'].extend(chunk['words'])
            
            # Обрезка начальных пробелов
            self.current_transcript['transcription']['text'] = self.current_transcript['transcription']['text'].strip()
            
        except Exception as e:
            log.error(f"Ошибка при обновлении транскрипции: {e}")
    
    def stop_meeting_transcription(self) -> Optional[Dict[str, Any]]:
        """Остановить транскрипцию встречи"""
        try:
            self.transcriber.stop_real_time_transcription()
            
            if self.current_transcript:
                # Финализация транскрипции
                self.current_transcript['ended_at'] = datetime.now().isoformat()
                self.current_transcript['transcription']['timestamp'] = datetime.now().isoformat()
                
                # Генерация итогового текста
                full_text = self.current_transcript['transcription']['text']
                self.current_transcript['summary'] = self._generate_summary(full_text)
                
                # Добавление в историю
                self.meeting_transcripts.append(self.current_transcript)
                
                log.info("Транскрипция встречи остановлена")
                return self.current_transcript
            else:
                log.warning("Нет активной транскрипции встречи")
                return None
                
        except Exception as e:
            log.error(f"Ошибка при остановке транскрипции встречи: {e}")
            return None
    
    def _generate_summary(self, text: str) -> str:
        """Сгенерировать краткое резюме текста"""
        if not text or len(text.strip()) < 50:
            return "Текст слишком короткий для резюме"
        
        # Простое резюме на основе первых и последних предложений
        sentences = text.split('.')
        if len(sentences) > 4:
            summary = f"{sentences[0].strip()}. {sentences[-2].strip()}."
        else:
            summary = text.strip()
        
        return summary[:500] + "..." if len(summary) > 500 else summary
    
    def get_current_transcript(self) -> Optional[Dict[str, Any]]:
        """Получить текущую транскрипцию"""
        return self.current_transcript
    
    def get_transcript_history(self) -> List[Dict[str, Any]]:
        """Получить историю транскрипций"""
        return self.meeting_transcripts
    
    def export_transcript(self, transcript: Dict[str, Any], 
                         output_format: str = "json",
                         output_file: Optional[str] = None) -> Optional[str]:
        """Экспортировать транскрипцию в файл"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"meeting_transcript_{timestamp}.{output_format}"
            
            if output_format.lower() == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(transcript, f, ensure_ascii=False, indent=2)
            
            elif output_format.lower() == "txt":
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Meeting Transcript\n")
                    f.write(f"================\n\n")
                    f.write(f"Date: {transcript.get('processed_at', 'Unknown')}\n")
                    f.write(f"Language: {transcript.get('transcription', {}).get('language', 'Unknown')}\n\n")
                    f.write(f"Transcription:\n")
                    f.write(f"------------\n")
                    f.write(transcript.get('transcription', {}).get('text', ''))
                    
                    if 'summary' in transcript:
                        f.write(f"\n\nSummary:\n")
                        f.write(f"--------\n")
                        f.write(transcript['summary'])
            
            log.info(f"Транскрипция экспортирована в файл: {output_file}")
            return output_file
            
        except Exception as e:
            log.error(f"Ошибка при экспорте транскрипции: {e}")
            return None
    
    def get_transcriber_info(self) -> Dict[str, Any]:
        """Получить информацию о транскрибере"""
        return {
            'transcriber_info': self.transcriber.get_model_info(),
            'enable_real_time': self.enable_real_time,
            'total_transcripts': len(self.meeting_transcripts),
            'has_active_transcript': self.current_transcript is not None
        }
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.transcriber.cleanup()

# Функция для создания экземпляра транскрибера
def create_meeting_transcriber(model_name: str = "base",
                             language: str = "ru",
                             enable_real_time: bool = False) -> MeetingTranscriber:
    """Создать экземпляр транскрибера встреч"""
    return MeetingTranscriber(
        model_name=model_name,
        language=language,
        enable_real_time=enable_real_time
    )
