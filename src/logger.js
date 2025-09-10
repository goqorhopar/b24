// src/logger.js
import pino from 'pino';

// Проверяем, работает ли код на Render.com (в продакшене)
const isProduction = process.env.NODE_ENV === 'production';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  // Используем красивый вывод только в разработке
  transport: isProduction ? undefined : {
    target: 'pino-pretty',
    options: {
      translateTime: 'SYS:standard',
      ignore: 'pid,hostname',
      colorize: true
    }
  },
  formatters: {
    level: (label) => ({ level: label })
  },
  timestamp: () => `,"time":"${new Date().toISOString()}"`
});

export default logger;
