/**
 * Telegram Bot сервис
 */

const TelegramBot = require('node-telegram-bot-api')
const logger = require('../utils/logger')
const config = require('../config')

class TelegramBotService {
  constructor() {
    this.bot = null
    this.isInitialized = false
    this.messageHandlers = new Map()
    this.userStates = new Map()
  }

  async initialize() {
    try {
      if (!config.TELEGRAM_BOT_TOKEN) {
        throw new Error('TELEGRAM_BOT_TOKEN не настроен')
      }

      // Создание бота
      this.bot = new TelegramBot(config.TELEGRAM_BOT_TOKEN, {
        polling: !config.TELEGRAM_WEBHOOK_URL,
        webHook: !!config.TELEGRAM_WEBHOOK_URL,
        onlyFirstMatch: true
      })

      // Настройка webhook если указан
      if (config.TELEGRAM_WEBHOOK_URL) {
        await this.setupWebhook()
      }

      // Регистрация обработчиков
      this.setupMessageHandlers()

      this.isInitialized = true
      logger.info('✅ Telegram Bot инициализирован')
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Telegram Bot', error)
      throw error
    }
  }

  async setupWebhook() {
    try {
      const webhookUrl = `${config.TELEGRAM_WEBHOOK_URL}/webhook/telegram`
      await this.bot.setWebHook(webhookUrl, {
        secret_token: config.TELEGRAM_WEBHOOK_SECRET
      })
      logger.info(`✅ Webhook настроен: ${webhookUrl}`)
    } catch (error) {
      logger.errorWithContext('Ошибка настройки webhook', error)
      throw error
    }
  }

  setupMessageHandlers() {
    // Обработчик всех сообщений
    this.bot.on('message', async (msg) => {
      try {
        await this.handleMessage(msg)
      } catch (error) {
        logger.errorWithContext('Ошибка обработки сообщения', error, { messageId: msg.message_id })
      }
    })

    // Обработчик callback query (inline кнопки)
    this.bot.on('callback_query', async (callbackQuery) => {
      try {
        await this.handleCallbackQuery(callbackQuery)
      } catch (error) {
        logger.errorWithContext('Ошибка обработки callback query', error, { queryId: callbackQuery.id })
      }
    })

    // Обработчик ошибок
    this.bot.on('error', (error) => {
      logger.errorWithContext('Ошибка Telegram Bot', error)
    })

    // Обработчик polling error
    this.bot.on('polling_error', (error) => {
      logger.errorWithContext('Ошибка polling Telegram Bot', error)
    })
  }

  async handleMessage(msg) {
    const chatId = msg.chat.id
    const text = msg.text || ''
    const user = msg.from

    logger.info(`Получено сообщение от ${user.username || user.first_name}: ${text}`)

    // Инициализация состояния пользователя
    if (!this.userStates.has(chatId)) {
      this.userStates.set(chatId, {
        state: 'idle',
        lastActivity: new Date(),
        meetingData: null
      })
    }

    const userState = this.userStates.get(chatId)
    userState.lastActivity = new Date()

    // Обработка команд
    if (text.startsWith('/')) {
      await this.handleCommand(msg)
      return
    }

    // Обработка состояний
    await this.handleUserState(msg, userState)
  }

  async handleCommand(msg) {
    const chatId = msg.chat.id
    const text = msg.text
    const user = msg.from

    logger.audit(`Команда от пользователя ${user.username || user.first_name}: ${text}`)

    switch (text) {
      case '/start':
        await this.sendWelcomeMessage(chatId)
        break

      case '/help':
        await this.sendHelpMessage(chatId)
        break

      case '/status':
        await this.sendStatusMessage(chatId)
        break

      case '/meetings':
        await this.sendMeetingsList(chatId)
        break

      case '/cancel':
        await this.cancelCurrentOperation(chatId)
        break

      default:
        await this.bot.sendMessage(chatId, '❓ Неизвестная команда. Используйте /help для списка команд.')
    }
  }

  async handleUserState(msg, userState) {
    const chatId = msg.chat.id
    const text = msg.text

    switch (userState.state) {
      case 'idle':
        await this.handleIdleState(msg)
        break

      case 'awaiting_meeting_link':
        await this.handleMeetingLink(msg)
        break

      case 'awaiting_lead_id':
        await this.handleLeadId(msg)
        break

      case 'awaiting_confirmation':
        await this.handleConfirmation(msg)
        break

      default:
        await this.bot.sendMessage(chatId, '❓ Неизвестное состояние. Используйте /cancel для сброса.')
    }
  }

  async handleIdleState(msg) {
    const chatId = msg.chat.id
    const text = msg.text

    // Проверка на ссылку встречи
    if (this.isMeetingUrl(text)) {
      await this.startMeetingProcess(msg)
    } else {
      await this.bot.sendMessage(chatId, 
        '👋 Привет! Отправь мне ссылку на встречу, и я автоматически присоединюсь, запишу и проанализирую её.\n\n' +
        'Поддерживаемые платформы:\n' +
        '• Zoom\n' +
        '• Google Meet\n' +
        '• Microsoft Teams\n' +
        '• Контур.Толк\n' +
        '• Яндекс.Телемост'
      )
    }
  }

  async startMeetingProcess(msg) {
    const chatId = msg.chat.id
    const text = msg.text
    const user = msg.from

    try {
      // Обновление состояния
      const userState = this.userStates.get(chatId)
      userState.state = 'awaiting_meeting_link'
      userState.meetingData = {
        url: text,
        user: user,
        startTime: new Date()
      }

      // Отправка подтверждения
      await this.bot.sendMessage(chatId, 
        '🚀 Получил ссылку на встречу! Начинаю процесс...\n\n' +
        '📋 Что я сделаю:\n' +
        '1. Присоединюсь к встрече\n' +
        '2. Запишу аудио\n' +
        '3. Сделаю транскрипцию\n' +
        '4. Проведу анализ через AI\n' +
        '5. Обновлю лид в Bitrix\n\n' +
        '⏳ Пожалуйста, подождите...'
      )

      // Запуск процесса встречи
      await this.triggerMeetingProcess(chatId, text, user)

    } catch (error) {
      logger.errorWithContext('Ошибка запуска процесса встречи', error, { chatId, url: text })
      await this.bot.sendMessage(chatId, '❌ Ошибка при запуске процесса встречи. Попробуйте позже.')
      this.resetUserState(chatId)
    }
  }

  async triggerMeetingProcess(chatId, meetingUrl, user) {
    // Эмитируем событие для оркестратора встреч
    if (this.meetingOrchestrator) {
      await this.meetingOrchestrator.processMeeting(chatId, meetingUrl, user)
    }
  }

  async handleMeetingLink(msg) {
    // Обработка уже запущенного процесса встречи
    const chatId = msg.chat.id
    await this.bot.sendMessage(chatId, '⏳ Встреча уже обрабатывается. Пожалуйста, дождитесь завершения.')
  }

  async handleLeadId(msg) {
    const chatId = msg.chat.id
    const text = msg.text

    if (!/^\d+$/.test(text)) {
      await this.bot.sendMessage(chatId, '❗ Введите корректный ID лида (только цифры).')
      return
    }

    const leadId = parseInt(text)
    const userState = this.userStates.get(chatId)

    if (!userState.meetingData) {
      await this.bot.sendMessage(chatId, '❌ Данные встречи не найдены. Начните заново.')
      this.resetUserState(chatId)
      return
    }

    try {
      await this.bot.sendMessage(chatId, `🔗 Обновляю лид ${leadId} на основе анализа встречи...`)

      // Обновление лида в Bitrix
      if (this.meetingOrchestrator) {
        await this.meetingOrchestrator.updateLead(chatId, leadId, userState.meetingData)
      }

      await this.bot.sendMessage(chatId, '✅ Лид успешно обновлен!')
      this.resetUserState(chatId)

    } catch (error) {
      logger.errorWithContext('Ошибка обновления лида', error, { chatId, leadId })
      await this.bot.sendMessage(chatId, `❌ Ошибка при обновлении лида ${leadId}: ${error.message}`)
    }
  }

  async handleConfirmation(msg) {
    const chatId = msg.chat.id
    const text = msg.text.toLowerCase()

    if (text === 'да' || text === 'yes' || text === 'y') {
      // Подтверждение получено
      await this.bot.sendMessage(chatId, '✅ Подтверждение получено. Продолжаю...')
      // Логика подтверждения
    } else if (text === 'нет' || text === 'no' || text === 'n') {
      await this.bot.sendMessage(chatId, '❌ Операция отменена.')
      this.resetUserState(chatId)
    } else {
      await this.bot.sendMessage(chatId, '❗ Пожалуйста, ответьте "да" или "нет".')
    }
  }

  async handleCallbackQuery(callbackQuery) {
    const chatId = callbackQuery.message.chat.id
    const data = callbackQuery.data

    try {
      await this.bot.answerCallbackQuery(callbackQuery.id)

      // Обработка inline кнопок
      switch (data) {
        case 'confirm_meeting':
          await this.handleMeetingConfirmation(chatId)
          break

        case 'cancel_meeting':
          await this.cancelCurrentOperation(chatId)
          break

        default:
          logger.warn(`Неизвестный callback query: ${data}`)
      }
    } catch (error) {
      logger.errorWithContext('Ошибка обработки callback query', error, { data })
    }
  }

  // Вспомогательные методы
  isMeetingUrl(text) {
    const meetingPatterns = [
      /zoom\.us\/j\/\d+/i,
      /meet\.google\.com\/[a-z0-9-]+/i,
      /teams\.microsoft\.com\/l\/meetup-join/i,
      /talk\.kontur\.ru/i,
      /telemost\.yandex\.ru/i
    ]

    return meetingPatterns.some(pattern => pattern.test(text))
  }

  async sendWelcomeMessage(chatId) {
    const message = 
      '🤖 **Meeting Bot Assistant**\n\n' +
      'Я автоматический ассистент для встреч. Мои возможности:\n\n' +
      '🎯 **Автоматическое участие в встречах**\n' +
      '🎙️ **Запись и транскрипция аудио**\n' +
      '🧠 **Анализ через AI (Gemini)**\n' +
      '📊 **Обновление лидов в Bitrix24**\n' +
      '📋 **Создание задач автоматически**\n\n' +
      'Просто отправь мне ссылку на встречу!'

    await this.bot.sendMessage(chatId, message, { parse_mode: 'Markdown' })
  }

  async sendHelpMessage(chatId) {
    const message = 
      '📖 **Справка по командам:**\n\n' +
      '/start - Начать работу с ботом\n' +
      '/help - Показать эту справку\n' +
      '/status - Статус системы\n' +
      '/meetings - Список встреч\n' +
      '/cancel - Отменить текущую операцию\n\n' +
      '**Как использовать:**\n' +
      '1. Отправь ссылку на встречу\n' +
      '2. Дождись завершения анализа\n' +
      '3. Введи ID лида для обновления\n\n' +
      '**Поддерживаемые платформы:**\n' +
      '• Zoom, Google Meet, Teams\n' +
      '• Контур.Толк, Яндекс.Телемост'

    await this.bot.sendMessage(chatId, message, { parse_mode: 'Markdown' })
  }

  async sendStatusMessage(chatId) {
    const uptime = process.uptime()
    const memoryUsage = process.memoryUsage()
    
    const message = 
      '📊 **Статус системы:**\n\n' +
      `⏱️ Время работы: ${Math.floor(uptime / 3600)}ч ${Math.floor((uptime % 3600) / 60)}м\n` +
      `💾 Память: ${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB\n` +
      `🔄 Версия: ${require('../../package.json').version}\n` +
      `🌐 Окружение: ${config.NODE_ENV}\n\n` +
      '✅ Все системы работают нормально'

    await this.bot.sendMessage(chatId, message, { parse_mode: 'Markdown' })
  }

  async sendMeetingsList(chatId) {
    // Получение списка встреч из базы данных
    try {
      const meetings = await this.getUserMeetings(chatId)
      
      if (meetings.length === 0) {
        await this.bot.sendMessage(chatId, '📋 У вас пока нет встреч.')
        return
      }

      let message = '📋 **Ваши встречи:**\n\n'
      meetings.forEach((meeting, index) => {
        message += `${index + 1}. ${meeting.platform} - ${meeting.status}\n`
        message += `   📅 ${meeting.createdAt}\n\n`
      })

      await this.bot.sendMessage(chatId, message, { parse_mode: 'Markdown' })
    } catch (error) {
      logger.errorWithContext('Ошибка получения списка встреч', error, { chatId })
      await this.bot.sendMessage(chatId, '❌ Ошибка при получении списка встреч.')
    }
  }

  async cancelCurrentOperation(chatId) {
    this.resetUserState(chatId)
    await this.bot.sendMessage(chatId, '✅ Операция отменена. Вы можете начать заново.')
  }

  resetUserState(chatId) {
    this.userStates.set(chatId, {
      state: 'idle',
      lastActivity: new Date(),
      meetingData: null
    })
  }

  async getUserMeetings(chatId) {
    // Заглушка - в реальной реализации будет запрос к базе данных
    return []
  }

  // Публичные методы для взаимодействия с другими сервисами
  async sendMessage(chatId, text, options = {}) {
    try {
      return await this.bot.sendMessage(chatId, text, options)
    } catch (error) {
      logger.errorWithContext('Ошибка отправки сообщения', error, { chatId })
      throw error
    }
  }

  async sendDocument(chatId, document, options = {}) {
    try {
      return await this.bot.sendDocument(chatId, document, options)
    } catch (error) {
      logger.errorWithContext('Ошибка отправки документа', error, { chatId })
      throw error
    }
  }

  async editMessageText(chatId, messageId, text, options = {}) {
    try {
      return await this.bot.editMessageText(text, {
        chat_id: chatId,
        message_id: messageId,
        ...options
      })
    } catch (error) {
      logger.errorWithContext('Ошибка редактирования сообщения', error, { chatId, messageId })
      throw error
    }
  }

  // Метод для обработки webhook
  async handleWebhook(update) {
    if (update.message) {
      await this.handleMessage(update.message)
    } else if (update.callback_query) {
      await this.handleCallbackQuery(update.callback_query)
    }
  }

  // Установка ссылки на оркестратор встреч
  setMeetingOrchestrator(orchestrator) {
    this.meetingOrchestrator = orchestrator
  }

  // Graceful shutdown
  async shutdown() {
    try {
      if (this.bot) {
        await this.bot.stopPolling()
        if (config.TELEGRAM_WEBHOOK_URL) {
          await this.bot.deleteWebHook()
        }
        logger.info('✅ Telegram Bot остановлен')
      }
    } catch (error) {
      logger.errorWithContext('Ошибка остановки Telegram Bot', error)
    }
  }
}

module.exports = TelegramBotService
