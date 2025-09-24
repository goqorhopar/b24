/**
 * Конфигурация приложения
 */

require('dotenv').config()

const config = {
  // Основные настройки
  NODE_ENV: process.env.NODE_ENV || 'development',
  PORT: parseInt(process.env.PORT) || 3000,
  HOST: process.env.HOST || '0.0.0.0',

  // Telegram Bot
  TELEGRAM_BOT_TOKEN: process.env.TELEGRAM_BOT_TOKEN,
  TELEGRAM_WEBHOOK_URL: process.env.TELEGRAM_WEBHOOK_URL,
  TELEGRAM_WEBHOOK_SECRET: process.env.TELEGRAM_WEBHOOK_SECRET,

  // Bitrix24
  BITRIX_WEBHOOK_URL: process.env.BITRIX_WEBHOOK_URL,
  BITRIX_RESPONSIBLE_ID: process.env.BITRIX_RESPONSIBLE_ID || '1',
  BITRIX_CREATED_BY_ID: process.env.BITRIX_CREATED_BY_ID || '1',
  BITRIX_TASK_DEADLINE_DAYS: parseInt(process.env.BITRIX_TASK_DEADLINE_DAYS) || 3,

  // Gemini AI
  GEMINI_API_KEY: process.env.GEMINI_API_KEY,

  // OpenAI (для Whisper STT)
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,

  // Альтернативные STT сервисы
  GOOGLE_STT_API_KEY: process.env.GOOGLE_STT_API_KEY,
  AZURE_SPEECH_KEY: process.env.AZURE_SPEECH_KEY,
  AZURE_SPEECH_REGION: process.env.AZURE_SPEECH_REGION,

  // Puppeteer настройки
  PUPPETEER_HEADLESS: process.env.PUPPETEER_HEADLESS !== 'false',
  PUPPETEER_SLOW_MO: parseInt(process.env.PUPPETEER_SLOW_MO) || 0,
  PUPPETEER_TIMEOUT: parseInt(process.env.PUPPETEER_TIMEOUT) || 30000,

  // Аудио настройки
  AUDIO_RECORDING_DURATION: parseInt(process.env.AUDIO_RECORDING_DURATION) || 3600, // 1 час
  AUDIO_FORMAT: process.env.AUDIO_FORMAT || 'wav',
  AUDIO_SAMPLE_RATE: parseInt(process.env.AUDIO_SAMPLE_RATE) || 16000,
  AUDIO_CHANNELS: parseInt(process.env.AUDIO_CHANNELS) || 1,

  // PulseAudio настройки
  PULSEAUDIO_SINK: process.env.PULSEAUDIO_SINK || 'meeting_bot_sink',
  PULSEAUDIO_SOURCE: process.env.PULSEAUDIO_SOURCE || 'meeting_bot_source',

  // Пути к файлам
  DATA_DIR: process.env.DATA_DIR || '/data',
  LOGS_DIR: process.env.LOGS_DIR || '/var/log/meetingbot',
  AUDIO_DIR: process.env.AUDIO_DIR || '/data/audio',
  TEMP_DIR: process.env.TEMP_DIR || '/tmp',

  // Логирование
  LOG_LEVEL: process.env.LOG_LEVEL || 'info',
  LOG_MAX_SIZE: process.env.LOG_MAX_SIZE || '10m',
  LOG_MAX_FILES: parseInt(process.env.LOG_MAX_FILES) || 5,

  // База данных
  DATABASE_URL: process.env.DATABASE_URL || 'sqlite:./data/meetingbot.db',
  DATABASE_POOL_SIZE: parseInt(process.env.DATABASE_POOL_SIZE) || 10,

  // Безопасность
  JWT_SECRET: process.env.JWT_SECRET || 'your-secret-key',
  API_RATE_LIMIT: parseInt(process.env.API_RATE_LIMIT) || 100,
  API_RATE_WINDOW: parseInt(process.env.API_RATE_WINDOW) || 900000, // 15 минут

  // Встречи
  MEETING_TIMEOUT: parseInt(process.env.MEETING_TIMEOUT) || 3600000, // 1 час
  MEETING_RETRY_ATTEMPTS: parseInt(process.env.MEETING_RETRY_ATTEMPTS) || 3,
  MEETING_RETRY_DELAY: parseInt(process.env.MEETING_RETRY_DELAY) || 5000,

  // Уведомления
  NOTIFICATION_TELEGRAM_CHAT_ID: process.env.NOTIFICATION_TELEGRAM_CHAT_ID,
  NOTIFICATION_ENABLED: process.env.NOTIFICATION_ENABLED === 'true',

  // Мониторинг
  HEALTH_CHECK_INTERVAL: parseInt(process.env.HEALTH_CHECK_INTERVAL) || 300000, // 5 минут
  METRICS_ENABLED: process.env.METRICS_ENABLED === 'true',

  // Docker
  DOCKER_MODE: process.env.DOCKER_MODE === 'true',
  CONTAINER_NAME: process.env.CONTAINER_NAME || 'meeting-bot',

  // Разработка
  DEBUG: process.env.DEBUG === 'true',
  MOCK_SERVICES: process.env.MOCK_SERVICES === 'true'
}

// Валидация обязательных переменных
const requiredVars = [
  'TELEGRAM_BOT_TOKEN',
  'BITRIX_WEBHOOK_URL',
  'GEMINI_API_KEY'
]

const missingVars = requiredVars.filter(varName => !config[varName])

if (missingVars.length > 0) {
  console.error('❌ Отсутствуют обязательные переменные окружения:')
  missingVars.forEach(varName => {
    console.error(`   - ${varName}`)
  })
  process.exit(1)
}

// Дополнительные настройки для разных окружений
if (config.NODE_ENV === 'production') {
  config.LOG_LEVEL = 'warn'
  config.PUPPETEER_HEADLESS = true
  config.DEBUG = false
}

if (config.NODE_ENV === 'development') {
  config.LOG_LEVEL = 'debug'
  config.PUPPETEER_HEADLESS = false
  config.DEBUG = true
}

// Экспорт конфигурации
module.exports = config
