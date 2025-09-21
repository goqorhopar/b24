# 🧪 Как проверить работу бота

## ✅ Быстрая проверка (уже выполнена)

Запустите простой тест:
```bash
python simple_test.py
```

**Результат:** ✅ 5/5 тестов пройдено - бот готов к настройке!

## 🔧 Полная настройка и проверка

### 1. Создайте файл `.env`

Создайте файл `.env` в корневой папке проекта со следующим содержимым:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=ваш_токен_бота
ADMIN_CHAT_ID=ваш_chat_id

# Gemini AI
GEMINI_API_KEY=ваш_gemini_api_ключ
GEMINI_MODEL=gemini-1.5-flash

# Bitrix24
BITRIX_WEBHOOK_URL=ваш_webhook_url
BITRIX_RESPONSIBLE_ID=ваш_id_ответственного
BITRIX_CREATED_BY_ID=ваш_id_создателя

# Настройки
MEETING_DURATION_MINUTES=30
AUDIO_QUALITY=high
LOG_LEVEL=INFO
NODE_ENV=development
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Запустите полный тест

```bash
python test_meeting_bot.py
```

### 4. Запустите бота

```bash
python main.py
```

## 🧪 Тестирование компонентов

### Тест детектора платформ
```python
from platform_detector import MeetingPlatformDetector

detector = MeetingPlatformDetector()
url = "https://zoom.us/j/123456789"
platform = detector.detect_platform_from_url(url)
print(f"Платформа: {platform['platform_name']}")
```

### Тест автоматизации встреч
```python
from aggressive_meeting_automation import AggressiveMeetingAutomation

automation = AggressiveMeetingAutomation()
# Тест определения платформы
platform = automation._detect_platform_from_url("https://zoom.us/j/123456789")
print(f"Платформа: {platform}")
```

### Тест транскрипции
```python
from speech_transcriber import SpeechTranscriber

transcriber = SpeechTranscriber()
# Транскрипция файла (если есть)
result = transcriber.transcribe_file("test_audio.wav")
print(f"Транскрипт: {result['text']}")
```

## 🚀 Тестирование в Telegram

### 1. Запустите бота
```bash
python main.py
```

### 2. Отправьте команды боту
- `/start` - начать работу
- `/help` - показать справку
- `/status` - проверить статус

### 3. Отправьте ссылку на встречу
```
https://zoom.us/j/123456789
```

### 4. Проверьте процесс
Бот должен:
1. ✅ Определить платформу (Zoom)
2. ✅ Присоединиться к встрече
3. ✅ Записать аудио
4. ✅ Транскрибировать речь
5. ✅ Проанализировать через Gemini
6. ✅ Отправить анализ в чат
7. ✅ Запросить ID лида
8. ✅ Обновить лид в Bitrix24

## 🔍 Проверка логов

### Просмотр логов в реальном времени
```bash
tail -f bot.log
```

### Поиск ошибок
```bash
grep "ERROR" bot.log
```

### Поиск успешных операций
```bash
grep "✅" bot.log
```

## 🐛 Устранение проблем

### Ошибка "GEMINI_API_KEY не найден"
- Проверьте файл `.env`
- Убедитесь, что переменная `GEMINI_API_KEY` установлена

### Ошибка "Chrome WebDriver не найден"
- Установите Chrome браузер
- Установите ChromeDriver: `pip install webdriver-manager`

### Ошибка "Whisper модель не загружена"
- Проверьте интернет-соединение
- Убедитесь, что `GEMINI_API_KEY` корректный

### Ошибка "Bitrix24 API недоступен"
- Проверьте `BITRIX_WEBHOOK_URL`
- Убедитесь, что URL корректный и доступен

## 📊 Мониторинг работы

### Проверка активных встреч
```python
from meeting_link_processor import MeetingLinkProcessor

processor = MeetingLinkProcessor()
print(f"Активных встреч: {len(processor.active_meetings)}")
```

### Проверка статуса компонентов
```python
# Проверка транскрипции
from speech_transcriber import SpeechTranscriber
transcriber = SpeechTranscriber()
print(f"Модель загружена: {transcriber.model is not None}")

# Проверка автоматизации
from aggressive_meeting_automation import AggressiveMeetingAutomation
automation = AggressiveMeetingAutomation()
print(f"WebDriver готов: {automation.driver is not None}")
```

## 🎯 Критерии успешной работы

✅ **Все компоненты инициализированы**
✅ **Детектор платформ работает**
✅ **Автоматизация встреч готова**
✅ **Транскрипция настроена**
✅ **Анализ через Gemini работает**
✅ **Интеграция с Bitrix24 активна**
✅ **Telegram бот отвечает на команды**

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f bot.log`
2. Запустите тесты: `python simple_test.py`
3. Проверьте переменные окружения
4. Убедитесь в доступности всех сервисов

---

**Статус:** ✅ Готов к использованию  
**Последняя проверка:** Все тесты пройдены успешно
