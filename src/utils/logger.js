/**
 * Настройка логирования с Winston
 */

const winston = require('winston')
const path = require('path')
const fs = require('fs')
const config = require('../config')

// Создание директории для логов если не существует
const logsDir = config.LOGS_DIR
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true })
}

// Формат логов
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.prettyPrint()
)

// Формат для консоли
const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({
    format: 'HH:mm:ss'
  }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let msg = `${timestamp} [${level}]: ${message}`
    if (Object.keys(meta).length > 0) {
      msg += ` ${JSON.stringify(meta)}`
    }
    return msg
  })
)

// Создание логгера
const logger = winston.createLogger({
  level: config.LOG_LEVEL,
  format: logFormat,
  defaultMeta: {
    service: 'meeting-bot',
    version: require('../../package.json').version
  },
  transports: [
    // Файл для всех логов
    new winston.transports.File({
      filename: path.join(logsDir, 'meeting-bot.log'),
      maxsize: config.LOG_MAX_SIZE,
      maxFiles: config.LOG_MAX_FILES,
      tailable: true
    }),

    // Файл только для ошибок
    new winston.transports.File({
      filename: path.join(logsDir, 'error.log'),
      level: 'error',
      maxsize: config.LOG_MAX_SIZE,
      maxFiles: config.LOG_MAX_FILES,
      tailable: true
    }),

    // Файл для аудита (важные события)
    new winston.transports.File({
      filename: path.join(logsDir, 'audit.log'),
      level: 'info',
      maxsize: config.LOG_MAX_SIZE,
      maxFiles: config.LOG_MAX_FILES,
      tailable: true,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    })
  ],

  // Обработка необработанных исключений
  exceptionHandlers: [
    new winston.transports.File({
      filename: path.join(logsDir, 'exceptions.log'),
      maxsize: config.LOG_MAX_SIZE,
      maxFiles: config.LOG_MAX_FILES
    })
  ],

  // Обработка необработанных промисов
  rejectionHandlers: [
    new winston.transports.File({
      filename: path.join(logsDir, 'rejections.log'),
      maxsize: config.LOG_MAX_SIZE,
      maxFiles: config.LOG_MAX_FILES
    })
  ]
})

// Добавление консольного транспорта для разработки
if (config.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: consoleFormat
  }))
}

// Методы для аудита
logger.audit = (message, meta = {}) => {
  logger.info(message, {
    ...meta,
    audit: true,
    timestamp: new Date().toISOString()
  })
}

// Метод для логирования встреч
logger.meeting = (message, meta = {}) => {
  logger.info(message, {
    ...meta,
    category: 'meeting',
    timestamp: new Date().toISOString()
  })
}

// Метод для логирования ошибок с контекстом
logger.errorWithContext = (message, error, context = {}) => {
  logger.error(message, {
    error: {
      message: error.message,
      stack: error.stack,
      name: error.name
    },
    context,
    timestamp: new Date().toISOString()
  })
}

// Метод для логирования производительности
logger.performance = (operation, duration, meta = {}) => {
  logger.info(`Performance: ${operation}`, {
    ...meta,
    category: 'performance',
    duration: `${duration}ms`,
    timestamp: new Date().toISOString()
  })
}

// Метод для логирования безопасности
logger.security = (message, meta = {}) => {
  logger.warn(message, {
    ...meta,
    category: 'security',
    timestamp: new Date().toISOString()
  })
}

// Метод для логирования интеграций
logger.integration = (service, message, meta = {}) => {
  logger.info(message, {
    ...meta,
    category: 'integration',
    service,
    timestamp: new Date().toISOString()
  })
}

// Graceful shutdown
process.on('SIGINT', () => {
  logger.info('Получен SIGINT, закрываем логгер...')
  logger.end()
})

process.on('SIGTERM', () => {
  logger.info('Получен SIGTERM, закрываем логгер...')
  logger.end()
})

module.exports = logger
