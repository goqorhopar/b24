/**
 * Главный файл бота-ассистента встреч
 * Автономный бот для автоматического участия в онлайн-встречах
 */

const express = require('express')
const helmet = require('helmet')
const cors = require('cors')
const compression = require('compression')
const rateLimit = require('express-rate-limit')
const cron = require('node-cron')
const path = require('path')

const logger = require('./utils/logger')
const config = require('./config')
const TelegramBot = require('./services/telegramBot')
const MeetingOrchestrator = require('./services/meetingOrchestrator')
const HealthCheck = require('./services/healthCheck')
const Database = require('./services/database')

class MeetingBotApp {
  constructor() {
    this.app = express()
    this.telegramBot = null
    this.meetingOrchestrator = null
    this.healthCheck = null
    this.database = null
    this.isShuttingDown = false
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Meeting Bot Assistant...')

      // Инициализация базы данных
      this.database = new Database()
      await this.database.initialize()
      logger.info('✅ База данных инициализирована')

      // Инициализация Telegram бота
      this.telegramBot = new TelegramBot()
      await this.telegramBot.initialize()
      logger.info('✅ Telegram бот инициализирован')

      // Инициализация оркестратора встреч
      this.meetingOrchestrator = new MeetingOrchestrator(this.telegramBot)
      await this.meetingOrchestrator.initialize()
      logger.info('✅ Оркестратор встреч инициализирован')

      // Инициализация health check
      this.healthCheck = new HealthCheck()
      await this.healthCheck.initialize()
      logger.info('✅ Health check инициализирован')

      // Настройка Express приложения
      this.setupExpress()

      // Настройка cron задач
      this.setupCronJobs()

      // Настройка graceful shutdown
      this.setupGracefulShutdown()

      logger.info('🎉 Meeting Bot Assistant успешно инициализирован!')
    } catch (error) {
      logger.error('❌ Ошибка инициализации:', error)
      throw error
    }
  }

  setupExpress() {
    // Безопасность
    this.app.use(helmet())
    this.app.use(cors())
    this.app.use(compression())

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 минут
      max: 100, // максимум 100 запросов с одного IP
      message: 'Слишком много запросов с этого IP, попробуйте позже'
    })
    this.app.use(limiter)

    // Парсинг JSON
    this.app.use(express.json({ limit: '10mb' }))
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }))

    // Статические файлы
    this.app.use('/static', express.static(path.join(__dirname, '../public')))

    // Маршруты
    this.setupRoutes()

    // Обработка ошибок
    this.app.use(this.errorHandler)
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', async (req, res) => {
      try {
        const health = await this.healthCheck.getStatus()
        res.status(health.status === 'healthy' ? 200 : 503).json(health)
      } catch (error) {
        logger.error('Ошибка health check:', error)
        res.status(503).json({
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          error: error.message
        })
      }
    })

    // Webhook для Telegram
    this.app.post('/webhook/telegram', async (req, res) => {
      try {
        if (this.telegramBot) {
          await this.telegramBot.handleWebhook(req.body)
        }
        res.status(200).json({ ok: true })
      } catch (error) {
        logger.error('Ошибка обработки webhook:', error)
        res.status(500).json({ error: error.message })
      }
    })

    // API для управления ботом
    this.app.get('/api/status', (req, res) => {
      res.json({
        status: 'running',
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
        version: require('../package.json').version
      })
    })

    this.app.get('/api/meetings', async (req, res) => {
      try {
        const meetings = await this.database.getMeetings()
        res.json(meetings)
      } catch (error) {
        logger.error('Ошибка получения встреч:', error)
        res.status(500).json({ error: error.message })
      }
    })

    // Корневой маршрут
    this.app.get('/', (req, res) => {
      res.json({
        name: 'Meeting Bot Assistant',
        version: require('../package.json').version,
        status: 'running',
        endpoints: {
          health: '/health',
          webhook: '/webhook/telegram',
          api: '/api/status'
        }
      })
    })
  }

  setupCronJobs() {
    // Очистка старых логов каждые 24 часа
    cron.schedule('0 2 * * *', async () => {
      try {
        logger.info('🧹 Запуск очистки старых логов...')
        await this.cleanupOldLogs()
        logger.info('✅ Очистка логов завершена')
      } catch (error) {
        logger.error('❌ Ошибка очистки логов:', error)
      }
    })

    // Проверка здоровья системы каждые 5 минут
    cron.schedule('*/5 * * * *', async () => {
      try {
        const health = await this.healthCheck.getStatus()
        if (health.status !== 'healthy') {
          logger.warn('⚠️ Проблемы со здоровьем системы:', health)
        }
      } catch (error) {
        logger.error('❌ Ошибка проверки здоровья:', error)
      }
    })

    logger.info('✅ Cron задачи настроены')
  }

  setupGracefulShutdown() {
    const shutdown = async (signal) => {
      if (this.isShuttingDown) return
      this.isShuttingDown = true

      logger.info(`🛑 Получен сигнал ${signal}, начинаем graceful shutdown...`)

      try {
        // Остановка сервера
        if (this.server) {
          await new Promise((resolve) => {
            this.server.close(resolve)
          })
          logger.info('✅ HTTP сервер остановлен')
        }

        // Остановка Telegram бота
        if (this.telegramBot) {
          await this.telegramBot.shutdown()
          logger.info('✅ Telegram бот остановлен')
        }

        // Остановка оркестратора встреч
        if (this.meetingOrchestrator) {
          await this.meetingOrchestrator.shutdown()
          logger.info('✅ Оркестратор встреч остановлен')
        }

        // Закрытие базы данных
        if (this.database) {
          await this.database.close()
          logger.info('✅ База данных закрыта')
        }

        logger.info('🎉 Graceful shutdown завершен')
        process.exit(0)
      } catch (error) {
        logger.error('❌ Ошибка при shutdown:', error)
        process.exit(1)
      }
    }

    process.on('SIGTERM', () => shutdown('SIGTERM'))
    process.on('SIGINT', () => shutdown('SIGINT'))
    process.on('SIGUSR2', () => shutdown('SIGUSR2')) // nodemon restart
  }

  async cleanupOldLogs() {
    // Очистка логов старше 7 дней
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    await this.database.cleanupOldLogs(sevenDaysAgo)
  }

  errorHandler(err, req, res, next) {
    logger.error('Ошибка Express:', err)
    
    if (res.headersSent) {
      return next(err)
    }

    res.status(500).json({
      error: 'Внутренняя ошибка сервера',
      timestamp: new Date().toISOString()
    })
  }

  async start() {
    try {
      await this.initialize()

      const port = config.PORT || 3000
      this.server = this.app.listen(port, '0.0.0.0', () => {
        logger.info(`🌐 HTTP сервер запущен на порту ${port}`)
        logger.info(`📊 Health check: http://localhost:${port}/health`)
        logger.info(`🤖 Webhook: http://localhost:${port}/webhook/telegram`)
      })
    } catch (error) {
      logger.error('❌ Ошибка запуска приложения:', error)
      process.exit(1)
    }
  }
}

// Запуск приложения
if (require.main === module) {
  const app = new MeetingBotApp()
  app.start().catch((error) => {
    logger.error('❌ Критическая ошибка:', error)
    process.exit(1)
  })
}

module.exports = MeetingBotApp
