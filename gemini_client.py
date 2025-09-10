import os
import logging
import time
from typing import Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Настройка логирования
log = logging.getLogger(__name__)

# Конфигурация Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
MAX_RETRIES = 3
RETRY_DELAY = 2

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY не найден в переменных окружения!")

# Инициализация Gemini
genai.configure(api_key=GEMINI_API_KEY)

def get_analysis_prompt() -> str:
    """Получение детального промпта для анализа"""
    return """
Ты эксперт по продажам с 20+ летним опытом. Проанализируй транскрипт встречи с клиентом по следующим критериям:

**ОБЯЗАТЕЛЬНАЯ СТРУКТУРА АНАЛИЗА:**

🏢 **1. АНАЛИЗ БИЗНЕСА КЛИЕНТА**
- Какой у клиента бизнес, сфера деятельности
- Размер компании, количество сотрудников
- Текущая ситуация в бизнесе
- Ключевые вызовы и задачи

💔 **2. БОЛИ И ПРОБЛЕМЫ**
- Основные болевые точки клиента
- Проблемы, которые он хочет решить
- Последствия нерешённых проблем
- Срочность решения

❌ **3. ВОЗРАЖЕНИЯ КЛИЕНТА**
- Какие возражения озвучил клиент
- Скрытые возражения (что не сказал прямо)
- Причины сомнений
- Страхи и опасения

🎭 **4. РЕАКЦИЯ И ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ**
- Общее настроение клиента
- Уровень заинтересованности
- Эмоциональные реакции на предложения
- Готовность к изменениям

⭐ **5. УРОВЕНЬ ИНТЕРЕСА**
- Насколько клиент заинтересован (1-10)
- Что его больше всего заинтересовало
- Какие вопросы задавал
- Признаки готовности покупать

💰 **6. ВОЗМОЖНОСТИ И БЮДЖЕТ**
- Есть ли у клиента бюджет
- Кто принимает решения о покупке
- Временные рамки для решения
- Конкуренты, которых рассматривает

⚠️ **7. ОШИБКИ МЕНЕДЖЕРА**
- Что менеджер делал неправильно
- Упущенные возможности
- Неправильные вопросы или ответы
- Что можно было сделать лучше

🎯 **8. ПУТЬ К ЗАКРЫТИЮ СДЕЛКИ**
- Что нужно для закрытия
- Какие шаги предпринять
- Кого ещё привлечь к переговорам
- Временные рамки

🗣️ **9. ТОН И СТИЛЬ ОБЩЕНИЯ**
- Как проходило общение
- Уровень доверия
- Профессионализм менеджера
- Качество коммуникации

🎮 **10. КОНТРОЛЬ ВСТРЕЧИ**
- Кто контролировал ход встречи
- Умел ли менеджер направлять разговор
- Структурированность встречи
- Достигнуты ли цели встречи

📋 **11. КОНКРЕТНЫЕ РЕКОМЕНДАЦИИ**
- 3-5 конкретных действий для менеджера
- Что сказать клиенту при следующем контакте
- Как преодолеть возражения
- Какие материалы подготовить

📊 **12. ИТОГОВАЯ КАТЕГОРИЯ И NEXT STEPS**

**КАТЕГОРИЯ КЛИЕНТА:**
- **A** (Горячий) - готов покупать, есть бюджет, принимает решения
- **B** (Тёплый) - заинтересован, но нужна дополнительная работа  
- **C** (Холодный) - слабый интерес или нет возможности покупать

**3 КОНКРЕТНЫХ ШАГА:**
1. [Первое действие с датой]
2. [Второе действие с датой] 
3. [Третье действие с датой]

---

**ВАЖНО:** 
- Используй ЦИТАТЫ из транскрипта для подтверждения выводов
- Будь конкретным, избегай общих фраз
- Оценивай объективно, указывай на ошибки
- Давай только реалистичные рекомендации
- Анализируй с точки зрения опытного продажника

Проанализируй следующий транскрипт:
"""

def analyze_transcript(transcript: str) -> str:
    """Анализ транскрипта встречи через Gemini AI"""
    
    if not transcript or len(transcript.strip()) < 10:
        raise ValueError("Транскрипт слишком короткий или пустой")
    
    log.info(f"Начинаю анализ транскрипта, длина: {len(transcript)} символов")
    
    retries = 0
    last_error = None
    
    while retries < MAX_RETRIES:
        try:
            # Получаем модель
            model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Формируем полный промпт
            full_prompt = get_analysis_prompt() + "\n\n" + transcript
            
            # Конфигурация генерации
            generation_config = genai.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.1,  # Низкая температура для стабильности
                top_p=0.8,
                top_k=40
            )
            
            log.info("Отправляю запрос к Gemini API...")
            start_time = time.time()
            
            # Генерируем ответ
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            processing_time = time.time() - start_time
            log.info(f"Gemini API ответил за {processing_time:.2f} секунд")
            
            # Проверяем, что есть текст в ответе
            if not response.text:
                raise ValueError("Gemini вернул пустой ответ")
            
            result = response.text.strip()
            
            # Дополнительная валидация результата
            if len(result) < 100:
                raise ValueError("Слишком короткий ответ от Gemini")
            
            # Проверяем наличие ключевых разделов
            required_sections = ["АНАЛИЗ БИЗНЕСА", "БОЛИ", "КАТЕГОРИЯ"]
            missing_sections = [section for section in required_sections 
                              if section not in result.upper()]
            
            if missing_sections:
                log.warning(f"В анализе отсутствуют разделы: {missing_sections}")
            
            log.info(f"Анализ успешно завершён, длина результата: {len(result)} символов")
            return result
            
        except Exception as e:
            retries += 1
            last_error = e
            log.warning(f"Попытка {retries}/{MAX_RETRIES} неудачна: {str(e)}")
            
            if retries < MAX_RETRIES:
                log.info(f"Повторная попытка через {RETRY_DELAY} секунд...")
                time.sleep(RETRY_DELAY)
            else:
                log.error(f"Все попытки исчерпаны. Последняя ошибка: {str(e)}")
                break
    
    # Если все попытки провалились
    error_msg = f"Не удалось проанализировать транскрипт после {MAX_RETRIES} попыток. Ошибка: {str(last_error)}"
    log.error(error_msg)
    raise Exception(error_msg)

def test_gemini_connection() -> bool:
    """Тестирование соединения с Gemini API"""
    try:
        log.info("Тестирование соединения с Gemini API...")
        
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            "Ответь одним словом 'работает', если ты меня понимаешь.",
            generation_config=genai.GenerationConfig(max_output_tokens=10)
        )
        
        if response.text and "работает" in response.text.lower():
            log.info("✅ Соединение с Gemini API работает")
            return True
        else:
            log.warning("⚠️ Неожиданный ответ от Gemini API")
            return False
            
    except Exception as e:
        log.error(f"❌ Ошибка соединения с Gemini API: {e}")
        return False

def get_model_info() -> dict:
    """Получение информации о модели"""
    try:
        models = genai.list_models()
        current_model = None
        
        for model in models:
            if MODEL_NAME in model.name:
                current_model = {
                    'name': model.name,
                    'display_name': model.display_name,
                    'description': model.description,
                    'input_token_limit': getattr(model, 'input_token_limit', 'Не указан'),
                    'output_token_limit': getattr(model, 'output_token_limit', 'Не указан')
                }
                break
        
        return current_model or {'error': f'Модель {MODEL_NAME} не найдена'}
        
    except Exception as e:
        log.error(f"Ошибка получения информации о модели: {e}")
        return {'error': str(e)}

# Проверка соединения при импорте модуля
if __name__ != '__main__':
    try:
        # Небольшая задержка для инициализации
        import threading
        
        def delayed_test():
            time.sleep(2)
            test_gemini_connection()
        
        # Запускаем тест в отдельном потоке, чтобы не блокировать запуск
        threading.Thread(target=delayed_test, daemon=True).start()
        
    except Exception as e:
        log.warning(f"Не удалось запустить тест соединения: {e}")

# Дополнительные функции для мониторинга

def analyze_with_metrics(transcript: str) -> tuple[str, dict]:
    """Анализ с метриками производительности"""
    start_time = time.time()
    
    try:
        result = analyze_transcript(transcript)
        processing_time = time.time() - start_time
        
        metrics = {
            'processing_time': processing_time,
            'transcript_length': len(transcript),
            'result_length': len(result),
            'success': True,
            'error': None
        }
        
        return result, metrics
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        metrics = {
            'processing_time': processing_time,
            'transcript_length': len(transcript),
            'result_length': 0,
            'success': False,
            'error': str(e)
        }
        
        # Исправленная строка: используем правильный синтаксис Python 3
        raise Exception(f"Ошибка анализа с метриками: {str(e)}") from e

def get_usage_stats() -> dict:
    """Получение статистики использования API"""
    # Примечание: Gemini API пока не предоставляет детальную статистику использования
    # Здесь можно добавить логику для отслеживания локальной статистики
    return {
        'model': MODEL_NAME,
        'api_key_set': bool(GEMINI_API_KEY),
        'max_retries': MAX_RETRIES,
        'retry_delay': RETRY_DELAY,
        'note': 'Детальная статистика API недоступна'
    }
