/**
 * Адаптер для записи аудио с системного звука
 */

const ffmpeg = require('fluent-ffmpeg')
const fs = require('fs').promises
const path = require('path')
const { spawn } = require('child_process')
const logger = require('../utils/logger')
const config = require('../config')

class AudioRecorderAdapter {
  constructor() {
    this.activeRecordings = new Map()
    this.recordingProcesses = new Map()
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Audio Recorder Adapter...')

      // Создание директорий для аудио
      await this.ensureDirectories()

      // Проверка доступности PulseAudio
      await this.checkPulseAudio()

      logger.info('✅ Audio Recorder Adapter инициализирован')
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Audio Recorder Adapter', error)
      throw error
    }
  }

  async ensureDirectories() {
    const directories = [
      config.AUDIO_DIR,
      config.TEMP_DIR,
      path.join(config.AUDIO_DIR, 'raw'),
      path.join(config.AUDIO_DIR, 'processed')
    ]

    for (const dir of directories) {
      try {
        await fs.mkdir(dir, { recursive: true })
        logger.debug(`Директория создана/проверена: ${dir}`)
      } catch (error) {
        logger.errorWithContext(`Ошибка создания директории ${dir}`, error)
        throw error
      }
    }
  }

  async checkPulseAudio() {
    try {
      // Проверка доступности PulseAudio
      const { exec } = require('child_process')
      const { promisify } = require('util')
      const execAsync = promisify(exec)

      await execAsync('pulseaudio --check')
      logger.info('✅ PulseAudio доступен')

      // Получение списка sink'ов
      const { stdout } = await execAsync('pactl list sinks short')
      logger.debug('Доступные sink\'ы:', stdout)

    } catch (error) {
      logger.warn('PulseAudio недоступен, будет использован альтернативный метод записи')
    }
  }

  async startRecording(meetingId, options = {}) {
    const {
      duration = config.AUDIO_RECORDING_DURATION,
      format = config.AUDIO_FORMAT,
      sampleRate = config.AUDIO_SAMPLE_RATE,
      channels = config.AUDIO_CHANNELS
    } = options

    try {
      logger.meeting(`Начало записи аудио для встречи ${meetingId}`, {
        duration,
        format,
        sampleRate,
        channels
      })

      // Генерация имени файла
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
      const filename = `meeting_${meetingId}_${timestamp}.${format}`
      const filepath = path.join(config.AUDIO_DIR, 'raw', filename)

      // Запуск записи
      const recordingProcess = await this.startPulseAudioRecording(filepath, {
        duration,
        sampleRate,
        channels,
        format
      })

      // Сохранение информации о записи
      this.activeRecordings.set(meetingId, {
        filepath,
        filename,
        startTime: new Date(),
        duration,
        format,
        sampleRate,
        channels,
        process: recordingProcess
      })

      this.recordingProcesses.set(meetingId, recordingProcess)

      logger.meeting(`Запись аудио начата для встречи ${meetingId}`, {
        filepath,
        duration: `${duration}ms`
      })

      return {
        success: true,
        audioPath: filepath,
        filename,
        meetingId
      }

    } catch (error) {
      logger.errorWithContext(`Ошибка начала записи для встречи ${meetingId}`, error)
      return { success: false, error: error.message }
    }
  }

  async startPulseAudioRecording(filepath, options) {
    const { duration, sampleRate, channels, format } = options

    return new Promise((resolve, reject) => {
      try {
        // Команда для записи с PulseAudio
        const command = [
          'ffmpeg',
          '-f', 'pulse',
          '-i', config.PULSEAUDIO_SINK,
          '-acodec', 'pcm_s16le',
          '-ar', sampleRate.toString(),
          '-ac', channels.toString(),
          '-t', (duration / 1000).toString(), // конвертация в секунды
          '-y', // перезаписать файл если существует
          filepath
        ]

        logger.debug(`Запуск команды записи: ${command.join(' ')}`)

        const process = spawn('ffmpeg', command.slice(1), {
          stdio: ['ignore', 'pipe', 'pipe']
        })

        let stderr = ''

        process.stderr.on('data', (data) => {
          stderr += data.toString()
        })

        process.on('close', (code) => {
          if (code === 0) {
            logger.meeting(`Запись завершена успешно: ${filepath}`)
            resolve(process)
          } else {
            logger.error(`Ошибка записи (код ${code}): ${stderr}`)
            reject(new Error(`Ошибка записи: ${stderr}`))
          }
        })

        process.on('error', (error) => {
          logger.errorWithContext('Ошибка процесса записи', error)
          reject(error)
        })

        // Таймаут для записи
        setTimeout(() => {
          if (!process.killed) {
            process.kill('SIGTERM')
            logger.meeting(`Запись остановлена по таймауту: ${filepath}`)
          }
        }, duration + 5000) // +5 секунд буфер

        resolve(process)

      } catch (error) {
        reject(error)
      }
    })
  }

  async stopRecording(meetingId) {
    try {
      const recording = this.activeRecordings.get(meetingId)
      if (!recording) {
        logger.warn(`Запись для встречи ${meetingId} не найдена`)
        return { success: false, error: 'Запись не найдена' }
      }

      const { process, filepath } = recording

      logger.meeting(`Остановка записи для встречи ${meetingId}`, { filepath })

      // Остановка процесса записи
      if (process && !process.killed) {
        process.kill('SIGTERM')
        
        // Ожидание завершения процесса
        await new Promise((resolve) => {
          process.on('close', resolve)
          setTimeout(resolve, 5000) // таймаут 5 секунд
        })
      }

      // Проверка существования файла
      try {
        await fs.access(filepath)
        const stats = await fs.stat(filepath)
        
        logger.meeting(`Запись остановлена для встречи ${meetingId}`, {
          filepath,
          size: `${Math.round(stats.size / 1024)}KB`,
          duration: `${Date.now() - recording.startTime.getTime()}ms`
        })

        // Удаление из активных записей
        this.activeRecordings.delete(meetingId)
        this.recordingProcesses.delete(meetingId)

        return {
          success: true,
          audioPath: filepath,
          size: stats.size,
          duration: Date.now() - recording.startTime.getTime()
        }

      } catch (error) {
        logger.errorWithContext(`Файл записи не найден: ${filepath}`, error)
        return { success: false, error: 'Файл записи не найден' }
      }

    } catch (error) {
      logger.errorWithContext(`Ошибка остановки записи для встречи ${meetingId}`, error)
      return { success: false, error: error.message }
    }
  }

  async processAudio(inputPath, outputPath, options = {}) {
    const {
      format = 'wav',
      sampleRate = 16000,
      channels = 1,
      bitrate = '128k'
    } = options

    try {
      logger.meeting(`Обработка аудио: ${inputPath} -> ${outputPath}`)

      return new Promise((resolve, reject) => {
        ffmpeg(inputPath)
          .audioCodec('pcm_s16le')
          .audioFrequency(sampleRate)
          .audioChannels(channels)
          .audioBitrate(bitrate)
          .format(format)
          .on('start', (commandLine) => {
            logger.debug(`FFmpeg команда: ${commandLine}`)
          })
          .on('progress', (progress) => {
            logger.debug(`Прогресс обработки: ${progress.percent}%`)
          })
          .on('end', () => {
            logger.meeting(`Обработка аудио завершена: ${outputPath}`)
            resolve({ success: true, outputPath })
          })
          .on('error', (error) => {
            logger.errorWithContext('Ошибка обработки аудио', error)
            reject(error)
          })
          .save(outputPath)
      })

    } catch (error) {
      logger.errorWithContext('Ошибка обработки аудио', error)
      return { success: false, error: error.message }
    }
  }

  async convertToWav(inputPath, outputPath) {
    return this.processAudio(inputPath, outputPath, {
      format: 'wav',
      sampleRate: 16000,
      channels: 1
    })
  }

  async getAudioInfo(filepath) {
    try {
      return new Promise((resolve, reject) => {
        ffmpeg.ffprobe(filepath, (error, metadata) => {
          if (error) {
            reject(error)
            return
          }

          const audioStream = metadata.streams.find(stream => stream.codec_type === 'audio')
          if (!audioStream) {
            reject(new Error('Аудио поток не найден'))
            return
          }

          resolve({
            duration: parseFloat(metadata.format.duration),
            size: parseInt(metadata.format.size),
            sampleRate: parseInt(audioStream.sample_rate),
            channels: parseInt(audioStream.channels),
            codec: audioStream.codec_name,
            bitrate: parseInt(metadata.format.bit_rate)
          })
        })
      })
    } catch (error) {
      logger.errorWithContext(`Ошибка получения информации об аудио: ${filepath}`, error)
      throw error
    }
  }

  async cleanupOldRecordings() {
    try {
      const cutoffDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) // 7 дней назад
      const rawDir = path.join(config.AUDIO_DIR, 'raw')
      const processedDir = path.join(config.AUDIO_DIR, 'processed')

      let deletedCount = 0

      // Очистка raw файлов
      const rawFiles = await fs.readdir(rawDir)
      for (const file of rawFiles) {
        const filepath = path.join(rawDir, file)
        const stats = await fs.stat(filepath)
        
        if (stats.mtime < cutoffDate) {
          await fs.unlink(filepath)
          deletedCount++
          logger.debug(`Удален старый файл записи: ${filepath}`)
        }
      }

      // Очистка processed файлов
      const processedFiles = await fs.readdir(processedDir)
      for (const file of processedFiles) {
        const filepath = path.join(processedDir, file)
        const stats = await fs.stat(filepath)
        
        if (stats.mtime < cutoffDate) {
          await fs.unlink(filepath)
          deletedCount++
          logger.debug(`Удален старый обработанный файл: ${filepath}`)
        }
      }

      logger.info(`Очистка аудио файлов завершена. Удалено файлов: ${deletedCount}`)

    } catch (error) {
      logger.errorWithContext('Ошибка очистки старых записей', error)
    }
  }

  async getActiveRecordings() {
    return Array.from(this.activeRecordings.values())
  }

  async getRecordingInfo(meetingId) {
    return this.activeRecordings.get(meetingId) || null
  }

  async shutdown() {
    try {
      logger.info('🛑 Остановка Audio Recorder Adapter...')

      // Остановка всех активных записей
      for (const meetingId of this.activeRecordings.keys()) {
        await this.stopRecording(meetingId)
      }

      // Завершение всех процессов
      for (const [meetingId, process] of this.recordingProcesses) {
        try {
          if (!process.killed) {
            process.kill('SIGTERM')
          }
        } catch (error) {
          logger.errorWithContext(`Ошибка завершения процесса записи ${meetingId}`, error)
        }
      }

      this.activeRecordings.clear()
      this.recordingProcesses.clear()

      logger.info('✅ Audio Recorder Adapter остановлен')
    } catch (error) {
      logger.errorWithContext('Ошибка остановки Audio Recorder Adapter', error)
    }
  }
}

module.exports = AudioRecorderAdapter
