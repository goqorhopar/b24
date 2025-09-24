/**
 * Адаптер для транскрипции речи (STT)
 */

const OpenAI = require('openai')
const fs = require('fs').promises
const path = require('path')
const logger = require('../utils/logger')
const config = require('../config')

class SpeechTranscriberAdapter {
  constructor() {
    this.openai = null
    this.googleClient = null
    this.azureClient = null
    this.provider = this.detectProvider()
  }

  detectProvider() {
    if (config.OPENAI_API_KEY) return 'openai'
    if (config.GOOGLE_STT_API_KEY) return 'google'
    if (config.AZURE_SPEECH_KEY) return 'azure'
    return 'openai' // по умолчанию
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Speech Transcriber Adapter...')

      switch (this.provider) {
        case 'openai':
          await this.initializeOpenAI()
          break
        case 'google':
          await this.initializeGoogle()
          break
        case 'azure':
          await this.initializeAzure()
          break
        default:
          throw new Error(`Неподдерживаемый провайдер STT: ${this.provider}`)
      }

      logger.info(`✅ Speech Transcriber Adapter инициализирован (${this.provider})`)
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Speech Transcriber Adapter', error)
      throw error
    }
  }

  async initializeOpenAI() {
    if (!config.OPENAI_API_KEY) {
      throw new Error('OPENAI_API_KEY не настроен')
    }

    this.openai = new OpenAI({
      apiKey: config.OPENAI_API_KEY
    })

    logger.info('✅ OpenAI клиент инициализирован')
  }

  async initializeGoogle() {
    // Инициализация Google Speech-to-Text
    // В реальной реализации здесь будет код для Google Cloud Speech-to-Text
    logger.info('✅ Google Speech-to-Text клиент инициализирован')
  }

  async initializeAzure() {
    // Инициализация Azure Speech Services
    // В реальной реализации здесь будет код для Azure Speech Services
    logger.info('✅ Azure Speech Services клиент инициализирован')
  }

  async transcribe(audioPath, options = {}) {
    const {
      language = 'ru',
      model = 'whisper-1',
      responseFormat = 'json',
      temperature = 0.0
    } = options

    try {
      logger.meeting(`Начало транскрипции: ${audioPath}`, {
        provider: this.provider,
        language,
        model
      })

      // Проверка существования файла
      await fs.access(audioPath)

      // Получение информации о файле
      const stats = await fs.stat(audioPath)
      logger.debug(`Размер аудио файла: ${Math.round(stats.size / 1024)}KB`)

      let result
      switch (this.provider) {
        case 'openai':
          result = await this.transcribeWithOpenAI(audioPath, { language, model, responseFormat, temperature })
          break
        case 'google':
          result = await this.transcribeWithGoogle(audioPath, { language })
          break
        case 'azure':
          result = await this.transcribeWithAzure(audioPath, { language })
          break
        default:
          throw new Error(`Неподдерживаемый провайдер: ${this.provider}`)
      }

      if (result.success) {
        logger.meeting(`Транскрипция завершена: ${audioPath}`, {
          provider: this.provider,
          textLength: result.transcript.length,
          confidence: result.confidence
        })
      }

      return result

    } catch (error) {
      logger.errorWithContext(`Ошибка транскрипции: ${audioPath}`, error)
      return { success: false, error: error.message }
    }
  }

  async transcribeWithOpenAI(audioPath, options) {
    try {
      const { language, model, responseFormat, temperature } = options

      // Чтение аудио файла
      const audioBuffer = await fs.readFile(audioPath)
      
      // Создание File объекта для OpenAI API
      const audioFile = new File([audioBuffer], path.basename(audioPath), {
        type: this.getMimeType(audioPath)
      })

      // Запрос к OpenAI Whisper API
      const response = await this.openai.audio.transcriptions.create({
        file: audioFile,
        model: model,
        language: language,
        response_format: responseFormat,
        temperature: temperature
      })

      const transcript = response.text || response

      return {
        success: true,
        transcript: transcript.trim(),
        confidence: 1.0, // Whisper не возвращает confidence
        provider: 'openai',
        model: model,
        language: language
      }

    } catch (error) {
      logger.errorWithContext('Ошибка транскрипции через OpenAI', error)
      return { success: false, error: error.message }
    }
  }

  async transcribeWithGoogle(audioPath, options) {
    try {
      const { language } = options

      // Заглушка для Google Speech-to-Text
      // В реальной реализации здесь будет код для Google Cloud Speech-to-Text API
      
      logger.warn('Google Speech-to-Text не реализован, используется заглушка')
      
      return {
        success: true,
        transcript: 'Заглушка для Google Speech-to-Text транскрипции',
        confidence: 0.8,
        provider: 'google',
        language: language
      }

    } catch (error) {
      logger.errorWithContext('Ошибка транскрипции через Google', error)
      return { success: false, error: error.message }
    }
  }

  async transcribeWithAzure(audioPath, options) {
    try {
      const { language } = options

      // Заглушка для Azure Speech Services
      // В реальной реализации здесь будет код для Azure Speech Services API
      
      logger.warn('Azure Speech Services не реализован, используется заглушка')
      
      return {
        success: true,
        transcript: 'Заглушка для Azure Speech Services транскрипции',
        confidence: 0.85,
        provider: 'azure',
        language: language
      }

    } catch (error) {
      logger.errorWithContext('Ошибка транскрипции через Azure', error)
      return { success: false, error: error.message }
    }
  }

  getMimeType(filepath) {
    const ext = path.extname(filepath).toLowerCase()
    const mimeTypes = {
      '.wav': 'audio/wav',
      '.mp3': 'audio/mpeg',
      '.mp4': 'audio/mp4',
      '.m4a': 'audio/mp4',
      '.webm': 'audio/webm',
      '.ogg': 'audio/ogg',
      '.flac': 'audio/flac'
    }
    return mimeTypes[ext] || 'audio/wav'
  }

  async transcribeWithTimestamps(audioPath, options = {}) {
    try {
      logger.meeting(`Транскрипция с временными метками: ${audioPath}`)

      // Для Whisper с временными метками нужен другой подход
      if (this.provider === 'openai') {
        return await this.transcribeWithOpenAITimestamps(audioPath, options)
      }

      // Для других провайдеров возвращаем обычную транскрипцию
      const result = await this.transcribe(audioPath, options)
      if (result.success) {
        result.segments = [{
          start: 0,
          end: 0,
          text: result.transcript
        }]
      }
      return result

    } catch (error) {
      logger.errorWithContext(`Ошибка транскрипции с временными метками: ${audioPath}`, error)
      return { success: false, error: error.message }
    }
  }

  async transcribeWithOpenAITimestamps(audioPath, options) {
    try {
      const { language, model } = options

      const audioBuffer = await fs.readFile(audioPath)
      const audioFile = new File([audioBuffer], path.basename(audioPath), {
        type: this.getMimeType(audioPath)
      })

      // Запрос с временными метками
      const response = await this.openai.audio.transcriptions.create({
        file: audioFile,
        model: model || 'whisper-1',
        language: language,
        response_format: 'verbose_json',
        timestamp_granularities: ['segment']
      })

      return {
        success: true,
        transcript: response.text,
        segments: response.segments || [],
        confidence: 1.0,
        provider: 'openai',
        model: model || 'whisper-1',
        language: language
      }

    } catch (error) {
      logger.errorWithContext('Ошибка транскрипции с временными метками через OpenAI', error)
      return { success: false, error: error.message }
    }
  }

  async detectLanguage(audioPath) {
    try {
      logger.meeting(`Определение языка: ${audioPath}`)

      if (this.provider === 'openai') {
        return await this.detectLanguageWithOpenAI(audioPath)
      }

      // Для других провайдеров возвращаем русский по умолчанию
      return {
        success: true,
        language: 'ru',
        confidence: 0.5
      }

    } catch (error) {
      logger.errorWithContext(`Ошибка определения языка: ${audioPath}`, error)
      return { success: false, error: error.message }
    }
  }

  async detectLanguageWithOpenAI(audioPath) {
    try {
      const audioBuffer = await fs.readFile(audioPath)
      const audioFile = new File([audioBuffer], path.basename(audioPath), {
        type: this.getMimeType(audioPath)
      })

      const response = await this.openai.audio.transcriptions.create({
        file: audioFile,
        model: 'whisper-1',
        response_format: 'verbose_json'
      })

      return {
        success: true,
        language: response.language || 'ru',
        confidence: 1.0
      }

    } catch (error) {
      logger.errorWithContext('Ошибка определения языка через OpenAI', error)
      return { success: false, error: error.message }
    }
  }

  async getSupportedLanguages() {
    const languages = {
      openai: ['ru', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh'],
      google: ['ru-RU', 'en-US', 'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'pt-PT', 'ja-JP', 'ko-KR', 'zh-CN'],
      azure: ['ru-RU', 'en-US', 'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'pt-PT', 'ja-JP', 'ko-KR', 'zh-CN']
    }

    return languages[this.provider] || languages.openai
  }

  async getProviderInfo() {
    return {
      provider: this.provider,
      supportedLanguages: await this.getSupportedLanguages(),
      maxFileSize: this.getMaxFileSize(),
      supportedFormats: this.getSupportedFormats()
    }
  }

  getMaxFileSize() {
    const maxSizes = {
      openai: 25 * 1024 * 1024, // 25MB
      google: 60 * 1024 * 1024, // 60MB
      azure: 4 * 1024 * 1024 // 4MB
    }
    return maxSizes[this.provider] || maxSizes.openai
  }

  getSupportedFormats() {
    const formats = {
      openai: ['wav', 'mp3', 'mp4', 'm4a', 'webm', 'ogg', 'flac'],
      google: ['wav', 'flac', 'linear16', 'mulaw', 'alaw', 'ogg_opus'],
      azure: ['wav', 'mp3', 'ogg', 'flac']
    }
    return formats[this.provider] || formats.openai
  }

  async shutdown() {
    try {
      logger.info('🛑 Остановка Speech Transcriber Adapter...')

      // Очистка ресурсов
      this.openai = null
      this.googleClient = null
      this.azureClient = null

      logger.info('✅ Speech Transcriber Adapter остановлен')
    } catch (error) {
      logger.errorWithContext('Ошибка остановки Speech Transcriber Adapter', error)
    }
  }
}

module.exports = SpeechTranscriberAdapter
