/**
 * Адаптер для анализа транскриптов через Gemini AI
 */

const { GoogleGenerativeAI } = require('google-generative-ai')
const logger = require('../utils/logger')
const config = require('../config')

class GeminiAnalyzerAdapter {
  constructor() {
    this.gemini = null
    this.model = null
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Gemini Analyzer Adapter...')

      if (!config.GEMINI_API_KEY) {
        throw new Error('GEMINI_API_KEY не настроен')
      }

      // Инициализация Gemini AI
      this.gemini = new GoogleGenerativeAI(config.GEMINI_API_KEY)
      this.model = this.gemini.getGenerativeModel({ model: 'gemini-1.5-flash' })

      logger.info('✅ Gemini Analyzer Adapter инициализирован')
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Gemini Analyzer Adapter', error)
      throw error
    }
  }

  async analyze(transcript, options = {}) {
    const {
      includeTasks = true,
      includeLeadUpdate = true,
      language = 'ru'
    } = options

    try {
      logger.meeting('Начало анализа транскрипта через Gemini', {
        transcriptLength: transcript.length,
        language
      })

      // Подготовка промпта для анализа
      const prompt = this.buildAnalysisPrompt(transcript, { includeTasks, includeLeadUpdate, language })

      // Запрос к Gemini
      const result = await this.model.generateContent(prompt)
      const response = await result.response
      const analysisText = response.text()

      // Парсинг ответа
      const analysis = this.parseAnalysisResponse(analysisText)

      logger.meeting('Анализ транскрипта завершен', {
        hasLead: !!analysis.lead,
        tasksCount: analysis.tasks?.length || 0,
        confidence: analysis.confidence
      })

      return {
        success: true,
        analysis,
        rawResponse: analysisText
      }

    } catch (error) {
      logger.errorWithContext('Ошибка анализа через Gemini', error)
      return { success: false, error: error.message }
    }
  }

  buildAnalysisPrompt(transcript, options) {
    const { includeTasks, includeLeadUpdate, language } = options

    const basePrompt = `
Ты - AI-ассистент для анализа деловых встреч и звонков. Проанализируй следующий транскрипт встречи и извлеки структурированную информацию.

ТРАНСКРИПТ ВСТРЕЧИ:
${transcript}

ЗАДАЧИ:
1. Проанализируй содержание встречи
2. Извлеки ключевую информацию о клиенте и его потребностях
3. Определи следующие шаги и действия
4. Оцени качество лида и вероятность сделки

ОТВЕТ ДОЛЖЕН БЫТЬ В СТРОГОМ JSON ФОРМАТЕ:
`

    const leadPrompt = includeLeadUpdate ? `
ЛИД (обновление существующего лида в CRM):
{
  "lead": {
    "title": "Краткое название лида",
    "company_title": "Название компании клиента",
    "client_name": "Имя клиента",
    "client_last_name": "Фамилия клиента",
    "source_description": "Как клиент узнал о нас",
    "key_request": "Основной запрос клиента",
    "pains_text": "Проблемы и боли клиента",
    "budget_value": "Бюджет (число)",
    "budget_currency": "Валюта (RUB/USD/EUR)",
    "timeline_text": "Сроки реализации",
    "sentiment": "Настроение клиента (positive/neutral/negative)",
    "is_lpr": true/false,
    "meeting_scheduled": true/false,
    "meeting_done": true/false,
    "kp_done_text": "Да/Нет",
    "lpr_confirmed_text": "Да/Нет",
    "our_product_text": "Что мы продаем",
    "client_type_text": "Тип клиента",
    "wow_effect": "WOW-эффект для клиента",
    "product": "Продукт/услуга",
    "task_formulation": "Формулировка задачи",
    "ad_budget": "Рекламный бюджет",
    "closing_comment": "Комментарий по закрытию",
    "meeting_responsible_id": "ID ответственного за встречу",
    "meeting_date": "YYYY-MM-DD",
    "planned_meeting_date": "YYYY-MM-DD HH:MM:SS"
  }
}
` : ''

    const tasksPrompt = includeTasks ? `
ЗАДАЧИ (создание задач в CRM):
{
  "tasks": [
    {
      "title": "Название задачи",
      "description": "Описание задачи",
      "priority": "high/medium/low",
      "deadline_days": 3,
      "responsible_id": "ID ответственного"
    }
  ]
}
` : ''

    const analysisPrompt = `
АНАЛИЗ:
{
  "analysis": {
    "summary": "Краткое резюме встречи",
    "key_points": ["Ключевой момент 1", "Ключевой момент 2"],
    "next_steps": ["Следующий шаг 1", "Следующий шаг 2"],
    "lead_quality": "high/medium/low",
    "deal_probability": 0.8,
    "confidence": 0.9,
    "recommendations": ["Рекомендация 1", "Рекомендация 2"]
  }
}
`

    const endPrompt = `
ВАЖНО:
- Отвечай ТОЛЬКО валидным JSON
- Все поля обязательны
- Используй русский язык для текстовых полей
- Будь точным и конкретным
- Если информация отсутствует, используй null
- Даты в формате YYYY-MM-DD или YYYY-MM-DD HH:MM:SS
- Числа без кавычек
- Булевы значения как true/false
`

    return basePrompt + leadPrompt + tasksPrompt + analysisPrompt + endPrompt
  }

  parseAnalysisResponse(responseText) {
    try {
      // Попытка найти JSON в ответе
      const jsonMatch = responseText.match(/\{[\s\S]*\}/)
      if (!jsonMatch) {
        throw new Error('JSON не найден в ответе')
      }

      const jsonText = jsonMatch[0]
      const parsed = JSON.parse(jsonText)

      // Валидация структуры
      this.validateAnalysisStructure(parsed)

      return parsed

    } catch (error) {
      logger.errorWithContext('Ошибка парсинга ответа Gemini', error, {
        responseText: responseText.substring(0, 500)
      })

      // Возврат базовой структуры в случае ошибки
      return this.getDefaultAnalysis()
    }
  }

  validateAnalysisStructure(analysis) {
    const requiredFields = ['analysis']
    
    for (const field of requiredFields) {
      if (!analysis[field]) {
        throw new Error(`Отсутствует обязательное поле: ${field}`)
      }
    }

    // Валидация анализа
    if (!analysis.analysis.summary) {
      analysis.analysis.summary = 'Анализ недоступен'
    }

    if (!analysis.analysis.confidence) {
      analysis.analysis.confidence = 0.5
    }

    // Валидация лида
    if (analysis.lead) {
      if (!analysis.lead.title) {
        analysis.lead.title = 'Лид из встречи'
      }
    }

    // Валидация задач
    if (analysis.tasks && !Array.isArray(analysis.tasks)) {
      analysis.tasks = []
    }
  }

  getDefaultAnalysis() {
    return {
      analysis: {
        summary: 'Анализ недоступен из-за ошибки парсинга',
        key_points: [],
        next_steps: [],
        lead_quality: 'medium',
        deal_probability: 0.5,
        confidence: 0.3,
        recommendations: ['Требуется ручная проверка']
      },
      lead: null,
      tasks: []
    }
  }

  async analyzeWithContext(transcript, context = {}) {
    try {
      logger.meeting('Анализ с контекстом', { contextKeys: Object.keys(context) })

      const contextPrompt = this.buildContextualPrompt(transcript, context)
      const result = await this.model.generateContent(contextPrompt)
      const response = await result.response
      const analysisText = response.text()

      const analysis = this.parseAnalysisResponse(analysisText)

      return {
        success: true,
        analysis,
        rawResponse: analysisText
      }

    } catch (error) {
      logger.errorWithContext('Ошибка контекстного анализа', error)
      return { success: false, error: error.message }
    }
  }

  buildContextualPrompt(transcript, context) {
    const { leadInfo, companyInfo, previousMeetings } = context

    let contextInfo = ''

    if (leadInfo) {
      contextInfo += `\nИНФОРМАЦИЯ О ЛИДЕ:\n${JSON.stringify(leadInfo, null, 2)}\n`
    }

    if (companyInfo) {
      contextInfo += `\nИНФОРМАЦИЯ О КОМПАНИИ:\n${JSON.stringify(companyInfo, null, 2)}\n`
    }

    if (previousMeetings && previousMeetings.length > 0) {
      contextInfo += `\nПРЕДЫДУЩИЕ ВСТРЕЧИ:\n${JSON.stringify(previousMeetings, null, 2)}\n`
    }

    return this.buildAnalysisPrompt(transcript, { includeTasks: true, includeLeadUpdate: true }) + contextInfo
  }

  async generateSummary(transcript, maxLength = 500) {
    try {
      const prompt = `
Создай краткое резюме следующего транскрипта встречи (максимум ${maxLength} символов):

${transcript}

Резюме должно включать:
- Основную тему встречи
- Ключевые решения
- Следующие шаги
- Важные детали

Отвечай на русском языке.
`

      const result = await this.model.generateContent(prompt)
      const response = await result.response
      const summary = response.text()

      return {
        success: true,
        summary: summary.trim()
      }

    } catch (error) {
      logger.errorWithContext('Ошибка генерации резюме', error)
      return { success: false, error: error.message }
    }
  }

  async extractKeyPoints(transcript) {
    try {
      const prompt = `
Извлеки ключевые моменты из следующего транскрипта встречи:

${transcript}

Верни список ключевых моментов в формате JSON:
{
  "key_points": [
    {
      "point": "Ключевой момент",
      "importance": "high/medium/low",
      "category": "budget/timeline/requirements/objections/next_steps"
    }
  ]
}
`

      const result = await this.model.generateContent(prompt)
      const response = await result.response
      const keyPointsText = response.text()

      const jsonMatch = keyPointsText.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        const keyPoints = JSON.parse(jsonMatch[0])
        return {
          success: true,
          keyPoints: keyPoints.key_points || []
        }
      }

      return {
        success: false,
        error: 'Не удалось извлечь ключевые моменты'
      }

    } catch (error) {
      logger.errorWithContext('Ошибка извлечения ключевых моментов', error)
      return { success: false, error: error.message }
    }
  }

  async detectSentiment(transcript) {
    try {
      const prompt = `
Определи настроение клиента в следующем транскрипте встречи:

${transcript}

Верни результат в формате JSON:
{
  "sentiment": "positive/neutral/negative",
  "confidence": 0.9,
  "emotions": ["заинтересованность", "сомнения", "энтузиазм"],
  "reasoning": "Обоснование определения настроения"
}
`

      const result = await this.model.generateContent(prompt)
      const response = await result.response
      const sentimentText = response.text()

      const jsonMatch = sentimentText.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        const sentiment = JSON.parse(jsonMatch[0])
        return {
          success: true,
          sentiment
        }
      }

      return {
        success: false,
        error: 'Не удалось определить настроение'
      }

    } catch (error) {
      logger.errorWithContext('Ошибка определения настроения', error)
      return { success: false, error: error.message }
    }
  }

  async getModelInfo() {
    try {
      // Получение информации о модели
      return {
        model: 'gemini-1.5-flash',
        provider: 'google',
        maxTokens: 8192,
        supportedLanguages: ['ru', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh'],
        capabilities: [
          'text_analysis',
          'sentiment_analysis',
          'entity_extraction',
          'summarization',
          'task_generation'
        ]
      }
    } catch (error) {
      logger.errorWithContext('Ошибка получения информации о модели', error)
      return null
    }
  }

  async shutdown() {
    try {
      logger.info('🛑 Остановка Gemini Analyzer Adapter...')

      this.gemini = null
      this.model = null

      logger.info('✅ Gemini Analyzer Adapter остановлен')
    } catch (error) {
      logger.errorWithContext('Ошибка остановки Gemini Analyzer Adapter', error)
    }
  }
}

module.exports = GeminiAnalyzerAdapter
