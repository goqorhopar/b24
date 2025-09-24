/**
 * Оркестратор встреч - основной сервис для управления процессом встреч
 */

const logger = require('../utils/logger')
const config = require('../config')
const MeetingPlatform = require('../adapters/meetingPlatform')
const AudioRecorder = require('../adapters/audioRecorder')
const SpeechTranscriber = require('../adapters/speechTranscriber')
const GeminiAnalyzer = require('../adapters/geminiAnalyzer')
const BitrixClient = require('../adapters/bitrixClient')
const Database = require('./database')

class MeetingOrchestrator {
  constructor(telegramBot) {
    this.telegramBot = telegramBot
    this.meetingPlatform = null
    this.audioRecorder = null
    this.speechTranscriber = null
    this.geminiAnalyzer = null
    this.bitrixClient = null
    this.database = null
    this.activeMeetings = new Map()
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Meeting Orchestrator...')

      // Инициализация компонентов
      this.meetingPlatform = new MeetingPlatform()
      await this.meetingPlatform.initialize()

      this.audioRecorder = new AudioRecorder()
      await this.audioRecorder.initialize()

      this.speechTranscriber = new SpeechTranscriber()
      await this.speechTranscriber.initialize()

      this.geminiAnalyzer = new GeminiAnalyzer()
      await this.geminiAnalyzer.initialize()

      this.bitrixClient = new BitrixClient()
      await this.bitrixClient.initialize()

      this.database = new Database()
      await this.database.initialize()

      // Установка ссылки на оркестратор в Telegram боте
      if (this.telegramBot) {
        this.telegramBot.setMeetingOrchestrator(this)
      }

      logger.info('✅ Meeting Orchestrator инициализирован')
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Meeting Orchestrator', error)
      throw error
    }
  }

  async processMeeting(chatId, meetingUrl, user) {
    const meetingId = this.generateMeetingId()
    
    try {
      logger.meeting(`Начинаем обработку встречи ${meetingId}`, {
        chatId,
        meetingUrl,
        userId: user.id,
        username: user.username
      })

      // Создание записи встречи в базе данных
      const meeting = await this.database.createMeeting({
        id: meetingId,
        chatId,
        url: meetingUrl,
        userId: user.id,
        username: user.username,
        status: 'starting'
      })

      // Сохранение в активных встречах
      this.activeMeetings.set(meetingId, {
        ...meeting,
        startTime: new Date(),
        user
      })

      // Уведомление пользователя
      await this.telegramBot.sendMessage(chatId, 
        '🎯 **Этап 1/5: Присоединение к встрече**\n\n' +
        'Подключаюсь к встрече...'
      )

      // Этап 1: Присоединение к встрече
      const joinResult = await this.joinMeeting(meetingId, meetingUrl, user)
      if (!joinResult.success) {
        throw new Error(`Не удалось присоединиться к встрече: ${joinResult.error}`)
      }

      await this.telegramBot.sendMessage(chatId, 
        '✅ Присоединился к встрече!\n\n' +
        '🎙️ **Этап 2/5: Запись аудио**\n\n' +
        'Начинаю запись...'
      )

      // Этап 2: Запись аудио
      const recordingResult = await this.recordAudio(meetingId)
      if (!recordingResult.success) {
        throw new Error(`Ошибка записи аудио: ${recordingResult.error}`)
      }

      await this.telegramBot.sendMessage(chatId, 
        '✅ Аудио записано!\n\n' +
        '📝 **Этап 3/5: Транскрипция**\n\n' +
        'Обрабатываю аудио...'
      )

      // Этап 3: Транскрипция
      const transcriptionResult = await this.transcribeAudio(meetingId, recordingResult.audioPath)
      if (!transcriptionResult.success) {
        throw new Error(`Ошибка транскрипции: ${transcriptionResult.error}`)
      }

      await this.telegramBot.sendMessage(chatId, 
        '✅ Транскрипция готова!\n\n' +
        '🧠 **Этап 4/5: Анализ через AI**\n\n' +
        'Анализирую содержание...'
      )

      // Этап 4: Анализ через Gemini
      const analysisResult = await this.analyzeTranscript(meetingId, transcriptionResult.transcript)
      if (!analysisResult.success) {
        throw new Error(`Ошибка анализа: ${analysisResult.error}`)
      }

      await this.telegramBot.sendMessage(chatId, 
        '✅ Анализ завершен!\n\n' +
        '📊 **Этап 5/5: Готово к обновлению Bitrix**\n\n' +
        'Введите ID лида для обновления:'
      )

      // Обновление статуса встречи
      await this.database.updateMeeting(meetingId, {
        status: 'completed',
        audioPath: recordingResult.audioPath,
        transcript: transcriptionResult.transcript,
        analysis: analysisResult.analysis,
        completedAt: new Date()
      })

      // Обновление состояния пользователя
      const userState = this.telegramBot.userStates.get(chatId)
      if (userState) {
        userState.state = 'awaiting_lead_id'
        userState.meetingData = {
          meetingId,
          analysis: analysisResult.analysis,
          transcript: transcriptionResult.transcript
        }
      }

      logger.meeting(`Встреча ${meetingId} успешно завершена`, {
        chatId,
        duration: Date.now() - this.activeMeetings.get(meetingId).startTime.getTime()
      })

    } catch (error) {
      logger.errorWithContext(`Ошибка обработки встречи ${meetingId}`, error, {
        chatId,
        meetingUrl
      })

      // Обновление статуса на ошибку
      await this.database.updateMeeting(meetingId, {
        status: 'failed',
        error: error.message,
        completedAt: new Date()
      })

      // Уведомление пользователя об ошибке
      await this.telegramBot.sendMessage(chatId, 
        `❌ **Ошибка при обработке встречи**\n\n` +
        `Ошибка: ${error.message}\n\n` +
        `Попробуйте позже или обратитесь к администратору.`
      )

      // Сброс состояния пользователя
      this.telegramBot.resetUserState(chatId)
    } finally {
      // Очистка активной встречи
      this.activeMeetings.delete(meetingId)
    }
  }

  async joinMeeting(meetingId, meetingUrl, user) {
    try {
      logger.meeting(`Присоединение к встрече ${meetingId}`, { meetingUrl })

      const result = await this.meetingPlatform.joinMeeting(meetingUrl, {
        displayName: `Ассистент ${user.first_name || user.username || 'Григория'}`,
        meetingId
      })

      if (result.success) {
        await this.database.updateMeeting(meetingId, {
          status: 'joined',
          platform: result.platform,
          joinedAt: new Date()
        })
      }

      return result
    } catch (error) {
      logger.errorWithContext(`Ошибка присоединения к встрече ${meetingId}`, error)
      return { success: false, error: error.message }
    }
  }

  async recordAudio(meetingId) {
    try {
      logger.meeting(`Начало записи аудио для встречи ${meetingId}`)

      const result = await this.audioRecorder.startRecording(meetingId, {
        duration: config.AUDIO_RECORDING_DURATION,
        format: config.AUDIO_FORMAT,
        sampleRate: config.AUDIO_SAMPLE_RATE,
        channels: config.AUDIO_CHANNELS
      })

      if (result.success) {
        await this.database.updateMeeting(meetingId, {
          status: 'recording',
          recordingStartedAt: new Date()
        })
      }

      return result
    } catch (error) {
      logger.errorWithContext(`Ошибка записи аудио для встречи ${meetingId}`, error)
      return { success: false, error: error.message }
    }
  }

  async transcribeAudio(meetingId, audioPath) {
    try {
      logger.meeting(`Транскрипция аудио для встречи ${meetingId}`, { audioPath })

      const result = await this.speechTranscriber.transcribe(audioPath)

      if (result.success) {
        await this.database.updateMeeting(meetingId, {
          status: 'transcribed',
          transcript: result.transcript,
          transcriptionCompletedAt: new Date()
        })
      }

      return result
    } catch (error) {
      logger.errorWithContext(`Ошибка транскрипции для встречи ${meetingId}`, error)
      return { success: false, error: error.message }
    }
  }

  async analyzeTranscript(meetingId, transcript) {
    try {
      logger.meeting(`Анализ транскрипта для встречи ${meetingId}`)

      const result = await this.geminiAnalyzer.analyze(transcript)

      if (result.success) {
        await this.database.updateMeeting(meetingId, {
          status: 'analyzed',
          analysis: result.analysis,
          analysisCompletedAt: new Date()
        })
      }

      return result
    } catch (error) {
      logger.errorWithContext(`Ошибка анализа для встречи ${meetingId}`, error)
      return { success: false, error: error.message }
    }
  }

  async updateLead(chatId, leadId, meetingData) {
    try {
      logger.meeting(`Обновление лида ${leadId} для чата ${chatId}`)

      const result = await this.bitrixClient.updateLead(leadId, meetingData.analysis, {
        transcript: meetingData.transcript,
        meetingId: meetingData.meetingId
      })

      if (result.success) {
        // Создание задач
        const tasksResult = await this.bitrixClient.createTasks(leadId, meetingData.analysis)
        
        await this.telegramBot.sendMessage(chatId, 
          '✅ **Лид успешно обновлен!**\n\n' +
          `📊 Обновлены поля: ${result.updatedFields.join(', ')}\n` +
          `📝 Создано задач: ${tasksResult.createdTasks.length}\n\n` +
          '🎉 Процесс завершен успешно!'
        )

        logger.audit(`Лид ${leadId} обновлен через бота`, {
          chatId,
          meetingId: meetingData.meetingId,
          updatedFields: result.updatedFields,
          createdTasks: tasksResult.createdTasks.length
        })
      }

      return result
    } catch (error) {
      logger.errorWithContext(`Ошибка обновления лида ${leadId}`, error, { chatId })
      throw error
    }
  }

  generateMeetingId() {
    return `meeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  async getMeetingStatus(meetingId) {
    const meeting = this.activeMeetings.get(meetingId)
    if (meeting) {
      return meeting.status
    }

    const dbMeeting = await this.database.getMeeting(meetingId)
    return dbMeeting ? dbMeeting.status : 'not_found'
  }

  async getActiveMeetings() {
    return Array.from(this.activeMeetings.values())
  }

  async cleanupOldMeetings() {
    try {
      const cutoffDate = new Date(Date.now() - 24 * 60 * 60 * 1000) // 24 часа назад
      await this.database.cleanupOldMeetings(cutoffDate)
      logger.info('✅ Очистка старых встреч завершена')
    } catch (error) {
      logger.errorWithContext('Ошибка очистки старых встреч', error)
    }
  }

  async shutdown() {
    try {
      logger.info('🛑 Остановка Meeting Orchestrator...')

      // Остановка всех активных встреч
      for (const [meetingId, meeting] of this.activeMeetings) {
        try {
          await this.meetingPlatform.leaveMeeting(meetingId)
          await this.audioRecorder.stopRecording(meetingId)
        } catch (error) {
          logger.errorWithContext(`Ошибка остановки встречи ${meetingId}`, error)
        }
      }

      // Очистка активных встреч
      this.activeMeetings.clear()

      // Остановка компонентов
      if (this.meetingPlatform) {
        await this.meetingPlatform.shutdown()
      }

      if (this.audioRecorder) {
        await this.audioRecorder.shutdown()
      }

      if (this.speechTranscriber) {
        await this.speechTranscriber.shutdown()
      }

      if (this.geminiAnalyzer) {
        await this.geminiAnalyzer.shutdown()
      }

      if (this.bitrixClient) {
        await this.bitrixClient.shutdown()
      }

      logger.info('✅ Meeting Orchestrator остановлен')
    } catch (error) {
      logger.errorWithContext('Ошибка остановки Meeting Orchestrator', error)
    }
  }
}

module.exports = MeetingOrchestrator
