// src/index.js
import express from 'express';
import pino from 'pino';
import { config } from './config.js';

// Простая конфигурация логгера
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => {
      return { level: label };
    }
  },
  timestamp: () => `,"time":"${new Date().toISOString()}"`
});

const app = express();
app.use(express.json({ limit: '10mb' }));

// Healthcheck
app.get('/health', (_, res) => {
  logger.info('Health check requested');
  res.status(200).json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    service: 'Meeting Bot',
    version: '1.0.0',
    config: {
      hasTelegramToken: !!config.telegramBotToken,
      hasBitrixWebhook: !!config.bitrixWebhookUrl,
      hasGeminiKey: !!config.geminiApiKey,
      responsibleId: config.bitrixResponsibleId,
      port: config.port
    }
  });
});

// Простой endpoint для проверки работы
app.get('/', (_, res) => {
  res.json({ 
    message: 'Meeting Bot is running',
    endpoints: ['/health'],
    status: 'active'
  });
});

// Обработка ошибок
app.use((error, req, res, next) => {
  logger.error({ error: error.message, stack: error.stack }, 'Server error');
  res.status(500).json({ error: 'Internal server error' });
});

// Запускаем сервер
const server = app.listen(config.port, '0.0.0.0', () => {
  logger.info(`🚀 Meeting Bot запущен и готов к работе`);
  logger.info(`🚀 Сервер запущен на порту ${config.port}`);
  logger.info(`🌐 Health check: http://localhost:${config.port}/health`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

// Обработка необработанных ошибок
process.on('uncaughtException', (error) => {
  logger.error({ error: error.message, stack: error.stack }, 'Uncaught exception');
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error({ reason, promise }, 'Unhandled rejection');
  process.exit(1);
});

export default app;
