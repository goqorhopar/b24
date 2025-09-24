/**
 * Адаптер для работы с Bitrix24 API
 */

const axios = require('axios')
const logger = require('../utils/logger')
const config = require('../config')

class BitrixClientAdapter {
  constructor() {
    this.webhookUrl = null
    this.responsibleId = null
    this.createdById = null
    this.taskDeadlineDays = null
    this.requestTimeout = 30000
    this.maxRetries = 3
    this.retryDelay = 2000
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Bitrix Client Adapter...')

      if (!config.BITRIX_WEBHOOK_URL) {
        throw new Error('BITRIX_WEBHOOK_URL не настроен')
      }

      this.webhookUrl = config.BITRIX_WEBHOOK_URL
      this.responsibleId = config.BITRIX_RESPONSIBLE_ID
      this.createdById = config.BITRIX_CREATED_BY_ID
      this.taskDeadlineDays = config.BITRIX_TASK_DEADLINE_DAYS

      // Проверка подключения
      await this.testConnection()

      logger.info('✅ Bitrix Client Adapter инициализирован')
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Bitrix Client Adapter', error)
      throw error
    }
  }

  async testConnection() {
    try {
      const response = await this.makeRequest('crm.lead.fields.json', {})
      logger.info('✅ Подключение к Bitrix24 успешно')
      return true
    } catch (error) {
      logger.errorWithContext('Ошибка подключения к Bitrix24', error)
      throw error
    }
  }

  async makeRequest(method, data, retries = this.maxRetries) {
    const url = `${this.webhookUrl}/${method}`
    
    logger.debug(`Bitrix запрос: ${method}`, { data: JSON.stringify(data).substring(0, 500) })

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await axios.post(url, data, {
          timeout: this.requestTimeout,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        })

        const result = response.data

        // Проверка на ошибки Bitrix API
        if (result.error) {
          const errorMsg = result.error_description || result.error
          logger.error(`Bitrix API ошибка: ${errorMsg}`)
          throw new Error(`${method}: ${errorMsg}`)
        }

        logger.debug(`Bitrix ответ: ${method}`, { result: JSON.stringify(result).substring(0, 1000) })
        return result

      } catch (error) {
        logger.warn(`Попытка ${attempt}/${retries} для ${method} неудачна: ${error.message}`)
        
        if (attempt === retries) {
          throw error
        }

        // Задержка перед повтором
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt))
      }
    }
  }

  async getLeadInfo(leadId) {
    try {
      logger.integration('bitrix', `Получение информации о лиде ${leadId}`)

      const response = await this.makeRequest('crm.lead.get.json', {
        id: leadId
      })

      return {
        success: true,
        lead: response.result
      }

    } catch (error) {
      logger.errorWithContext(`Ошибка получения лида ${leadId}`, error)
      return { success: false, error: error.message }
    }
  }

  async updateLead(leadId, analysis, context = {}) {
    try {
      logger.integration('bitrix', `Обновление лида ${leadId}`, { analysisKeys: Object.keys(analysis) })

      // Подготовка полей для обновления
      const fields = this.prepareLeadFields(analysis, context)

      // Обновление лида
      const response = await this.makeRequest('crm.lead.update.json', {
        id: leadId,
        fields: fields,
        params: {
          REGISTER_SONET_EVENT: 'Y'
        }
      })

      // Обновление комментария
      if (analysis.analysis?.summary || context.transcript) {
        await this.updateLeadComment(leadId, analysis, context)
      }

      logger.integration('bitrix', `Лид ${leadId} обновлен`, { updatedFields: Object.keys(fields) })

      return {
        success: true,
        leadId: leadId,
        updatedFields: Object.keys(fields),
        response: response.result
      }

    } catch (error) {
      logger.errorWithContext(`Ошибка обновления лида ${leadId}`, error)
      return { success: false, error: error.message }
    }
  }

  prepareLeadFields(analysis, context) {
    const fields = {}

    // Основные поля лида
    if (analysis.lead) {
      const lead = analysis.lead

      // Стандартные поля
      if (lead.title) fields.TITLE = lead.title
      if (lead.company_title) fields.COMPANY_TITLE = lead.company_title
      if (lead.client_name) fields.NAME = lead.client_name
      if (lead.client_last_name) fields.LAST_NAME = lead.client_last_name
      if (lead.source_description) fields.SOURCE_DESCRIPTION = lead.source_description

      // Кастомные поля (UF_CRM_*)
      if (lead.key_request) fields.UF_CRM_1754665062 = lead.key_request // WOW-эффект
      if (lead.product) fields.UF_CRM_1579102568584 = lead.product // Что продает
      if (lead.task_formulation) fields.UF_CRM_1592909799043 = lead.task_formulation // Как сформулирована задача
      if (lead.ad_budget) fields.UF_CRM_1592910027 = lead.ad_budget // Рекламный бюджет
      if (lead.is_lpr !== undefined) fields.UF_CRM_1754651857 = lead.is_lpr ? '1' : '0' // Вышли на ЛПР?
      if (lead.meeting_scheduled !== undefined) fields.UF_CRM_1754651891 = lead.meeting_scheduled ? '1' : '0' // Назначили встречу?
      if (lead.meeting_done !== undefined) fields.UF_CRM_1754651937 = lead.meeting_done ? '1' : '0' // Провели встречу?
      if (lead.closing_comment) fields.UF_CRM_1592911226916 = lead.closing_comment // Комментарий по закрытию
      if (lead.meeting_responsible_id) fields.UF_CRM_1756298185 = lead.meeting_responsible_id // Кто проводит встречу?
      if (lead.meeting_date) fields.UF_CRM_1755862426686 = lead.meeting_date // Дата факт. проведения встречи
      if (lead.planned_meeting_date) fields.UF_CRM_1757408917 = lead.planned_meeting_date // План дата встречи

      // Перечисления (нужно получить ID по названию)
      if (lead.client_type_text) {
        const clientTypeId = this.getEnumId('UF_CRM_1547738289', lead.client_type_text)
        if (clientTypeId) fields.UF_CRM_1547738289 = clientTypeId
      }

      if (lead.bad_reason_text) {
        const badReasonId = this.getEnumId('UF_CRM_1555492157080', lead.bad_reason_text)
        if (badReasonId) fields.UF_CRM_1555492157080 = badReasonId
      }

      if (lead.kp_done_text) {
        const kpDoneId = this.getEnumId('UF_CRM_1754652099', lead.kp_done_text)
        if (kpDoneId) fields.UF_CRM_1754652099 = kpDoneId
      }

      if (lead.lpr_confirmed_text) {
        const lprConfirmedId = this.getEnumId('UF_CRM_1755007163632', lead.lpr_confirmed_text)
        if (lprConfirmedId) fields.UF_CRM_1755007163632 = lprConfirmedId
      }

      if (lead.source_text) {
        const sourceId = this.getEnumId('UF_CRM_1648714327', lead.source_text)
        if (sourceId) fields.UF_CRM_1648714327 = sourceId
      }

      if (lead.our_product_text) {
        const productId = this.getEnumId('UF_CRM_1741622365', lead.our_product_text)
        if (productId) fields.UF_CRM_1741622365 = productId
      }
    }

    return fields
  }

  getEnumId(fieldCode, value) {
    // Заглушка для получения ID перечисления
    // В реальной реализации здесь будет кэширование и запрос к API
    logger.debug(`Получение ID для перечисления ${fieldCode}: ${value}`)
    return null
  }

  async updateLeadComment(leadId, analysis, context) {
    try {
      const commentParts = []

      // Добавление анализа
      if (analysis.analysis?.summary) {
        commentParts.push(`**Анализ встречи:**\n${analysis.analysis.summary}`)
      }

      // Добавление ключевых моментов
      if (analysis.analysis?.key_points && analysis.analysis.key_points.length > 0) {
        commentParts.push(`**Ключевые моменты:**\n${analysis.analysis.key_points.map(point => `• ${point}`).join('\n')}`)
      }

      // Добавление следующих шагов
      if (analysis.analysis?.next_steps && analysis.analysis.next_steps.length > 0) {
        commentParts.push(`**Следующие шаги:**\n${analysis.analysis.next_steps.map(step => `• ${step}`).join('\n')}`)
      }

      // Добавление транскрипта
      if (context.transcript) {
        commentParts.push(`**Транскрипт встречи:**\n${context.transcript}`)
      }

      // Добавление рекомендаций
      if (analysis.analysis?.recommendations && analysis.analysis.recommendations.length > 0) {
        commentParts.push(`**Рекомендации:**\n${analysis.analysis.recommendations.map(rec => `• ${rec}`).join('\n')}`)
      }

      const comment = commentParts.join('\n\n')

      // Обновление комментария
      await this.makeRequest('crm.lead.update.json', {
        id: leadId,
        fields: {
          COMMENTS: comment
        },
        params: {
          REGISTER_SONET_EVENT: 'Y'
        }
      })

      logger.integration('bitrix', `Комментарий лида ${leadId} обновлен`)

    } catch (error) {
      logger.errorWithContext(`Ошибка обновления комментария лида ${leadId}`, error)
    }
  }

  async createTasks(leadId, analysis) {
    try {
      logger.integration('bitrix', `Создание задач для лида ${leadId}`)

      const tasks = []
      const deadline = new Date()
      deadline.setDate(deadline.getDate() + this.taskDeadlineDays)

      // Создание стандартных задач
      const standardTasks = this.generateStandardTasks(leadId, analysis, deadline)

      for (const taskData of standardTasks) {
        try {
          const response = await this.makeRequest('tasks.task.add.json', {
            fields: taskData
          })

          if (response.result) {
            const taskId = response.result.task?.id || response.result.id
            tasks.push({
              id: taskId,
              title: taskData.TITLE,
              status: 'created'
            })
          }

        } catch (error) {
          logger.errorWithContext(`Ошибка создания задачи: ${taskData.TITLE}`, error)
        }
      }

      // Создание задач из анализа
      if (analysis.tasks && Array.isArray(analysis.tasks)) {
        for (const task of analysis.tasks) {
          try {
            const taskData = this.prepareTaskFields(leadId, task, deadline)
            const response = await this.makeRequest('tasks.task.add.json', {
              fields: taskData
            })

            if (response.result) {
              const taskId = response.result.task?.id || response.result.id
              tasks.push({
                id: taskId,
                title: taskData.TITLE,
                status: 'created'
              })
            }

          } catch (error) {
            logger.errorWithContext(`Ошибка создания задачи из анализа: ${task.title}`, error)
          }
        }
      }

      logger.integration('bitrix', `Создано задач для лида ${leadId}: ${tasks.length}`)

      return {
        success: true,
        createdTasks: tasks
      }

    } catch (error) {
      logger.errorWithContext(`Ошибка создания задач для лида ${leadId}`, error)
      return { success: false, error: error.message, createdTasks: [] }
    }
  }

  generateStandardTasks(leadId, analysis, deadline) {
    const tasks = []

    // Задача 1: Первичная обработка
    tasks.push({
      TITLE: `[Лид ${leadId}] Шаг 1: Первичная обработка и верификация`,
      DESCRIPTION: 'Проверить корректность данных по лиду, заполненных ботом. Уточнить у клиента недостающие данные при необходимости. Подтвердить контакт.',
      RESPONSIBLE_ID: this.responsibleId,
      DEADLINE: deadline.toISOString().replace('T', ' ').substring(0, 19),
      PRIORITY: 2,
      UF_CRM_TASK: [`L_${leadId}`]
    })

    // Задача 2: Подготовка КП
    const kpDeadline = new Date(deadline)
    kpDeadline.setDate(kpDeadline.getDate() + 2)

    tasks.push({
      TITLE: `[Лид ${leadId}] Шаг 2: Подготовка коммерческого предложения`,
      DESCRIPTION: `На основе данных из лида и транскрипта подготовить КП, сфокусировавшись на решении проблем: ${analysis.lead?.pains_text || 'не указаны'}. Согласовать с отделом продукта.`,
      RESPONSIBLE_ID: this.responsibleId,
      DEADLINE: kpDeadline.toISOString().replace('T', ' ').substring(0, 19),
      PRIORITY: 2,
      UF_CRM_TASK: [`L_${leadId}`]
    })

    // Задача 3: Организация демо
    const demoDeadline = new Date(deadline)
    demoDeadline.setDate(demoDeadline.getDate() + 3)

    const clientName = analysis.lead ? `${analysis.lead.client_name || ''} ${analysis.lead.client_last_name || ''}`.trim() : 'клиента'

    tasks.push({
      TITLE: `[Лид ${leadId}] Шаг 3: Организация демо-звонка`,
      DESCRIPTION: `Связаться с ${clientName} и назначить демонстрацию продукта на удобное время. Ответить на вопросы.`,
      RESPONSIBLE_ID: this.responsibleId,
      DEADLINE: demoDeadline.toISOString().replace('T', ' ').substring(0, 19),
      PRIORITY: 2,
      UF_CRM_TASK: [`L_${leadId}`]
    })

    return tasks
  }

  prepareTaskFields(leadId, task, defaultDeadline) {
    const deadline = task.deadline_days 
      ? new Date(Date.now() + task.deadline_days * 24 * 60 * 60 * 1000)
      : defaultDeadline

    const priorityMap = {
      'high': 3,
      'medium': 2,
      'low': 1
    }

    return {
      TITLE: `[Лид ${leadId}] ${task.title}`,
      DESCRIPTION: task.description || '',
      RESPONSIBLE_ID: task.responsible_id || this.responsibleId,
      DEADLINE: deadline.toISOString().replace('T', ' ').substring(0, 19),
      PRIORITY: priorityMap[task.priority] || 2,
      UF_CRM_TASK: [`L_${leadId}`]
    }
  }

  async getLeadFields() {
    try {
      const response = await this.makeRequest('crm.lead.fields.json', {})
      return {
        success: true,
        fields: response.result
      }
    } catch (error) {
      logger.errorWithContext('Ошибка получения полей лида', error)
      return { success: false, error: error.message }
    }
  }

  async getTaskInfo(taskId) {
    try {
      const response = await this.makeRequest('tasks.task.get', {
        taskId: taskId
      })
      return {
        success: true,
        task: response.result
      }
    } catch (error) {
      logger.errorWithContext(`Ошибка получения задачи ${taskId}`, error)
      return { success: false, error: error.message }
    }
  }

  async getConnectionInfo() {
    try {
      const fieldsResponse = await this.getLeadFields()
      
      return {
        success: true,
        webhookConfigured: !!this.webhookUrl,
        connectionTest: fieldsResponse.success,
        availableFields: fieldsResponse.success ? Object.keys(fieldsResponse.fields).length : 0,
        customFields: fieldsResponse.success ? Object.keys(fieldsResponse.fields).filter(field => field.startsWith('UF_')).length : 0,
        responsibleId: this.responsibleId,
        createdById: this.createdById,
        taskDeadlineDays: this.taskDeadlineDays
      }
    } catch (error) {
      logger.errorWithContext('Ошибка получения информации о подключении', error)
      return { success: false, error: error.message }
    }
  }

  async shutdown() {
    try {
      logger.info('🛑 Остановка Bitrix Client Adapter...')

      this.webhookUrl = null
      this.responsibleId = null
      this.createdById = null
      this.taskDeadlineDays = null

      logger.info('✅ Bitrix Client Adapter остановлен')
    } catch (error) {
      logger.errorWithContext('Ошибка остановки Bitrix Client Adapter', error)
    }
  }
}

module.exports = BitrixClientAdapter
