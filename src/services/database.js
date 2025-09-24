/**
 * Сервис базы данных
 */

const sqlite3 = require('sqlite3').verbose()
const path = require('path')
const fs = require('fs').promises
const logger = require('../utils/logger')
const config = require('../config')

class DatabaseService {
  constructor() {
    this.db = null
    this.dbPath = config.DATABASE_URL.replace('sqlite:', '')
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Database Service...')

      // Создание директории для базы данных
      const dbDir = path.dirname(this.dbPath)
      await fs.mkdir(dbDir, { recursive: true })

      // Подключение к базе данных
      this.db = new sqlite3.Database(this.dbPath)

      // Создание таблиц
      await this.createTables()

      logger.info('✅ Database Service инициализирован')
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Database Service', error)
      throw error
    }
  }

  async createTables() {
    const tables = [
      // Таблица встреч
      `CREATE TABLE IF NOT EXISTS meetings (
        id TEXT PRIMARY KEY,
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        username TEXT,
        url TEXT NOT NULL,
        platform TEXT,
        status TEXT NOT NULL DEFAULT 'starting',
        audio_path TEXT,
        transcript TEXT,
        analysis TEXT,
        error TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        joined_at DATETIME,
        recording_started_at DATETIME,
        transcription_completed_at DATETIME,
        analysis_completed_at DATETIME,
        completed_at DATETIME
      )`,

      // Таблица логов
      `CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        category TEXT,
        meeting_id TEXT,
        chat_id INTEGER,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`,

      // Таблица аудио файлов
      `CREATE TABLE IF NOT EXISTS audio_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        size INTEGER,
        duration INTEGER,
        format TEXT,
        sample_rate INTEGER,
        channels INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (meeting_id) REFERENCES meetings (id)
      )`,

      // Таблица задач
      `CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        lead_id TEXT,
        task_id TEXT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'created',
        priority TEXT DEFAULT 'medium',
        responsible_id TEXT,
        deadline DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        FOREIGN KEY (meeting_id) REFERENCES meetings (id)
      )`,

      // Таблица пользователей
      `CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        is_bot BOOLEAN DEFAULT 0,
        language_code TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
      )`,

      // Таблица настроек
      `CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`
    ]

    for (const table of tables) {
      await this.run(table)
    }

    // Создание индексов
    await this.createIndexes()

    logger.info('✅ Таблицы базы данных созданы')
  }

  async createIndexes() {
    const indexes = [
      'CREATE INDEX IF NOT EXISTS idx_meetings_chat_id ON meetings(chat_id)',
      'CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status)',
      'CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings(created_at)',
      'CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)',
      'CREATE INDEX IF NOT EXISTS idx_logs_meeting_id ON logs(meeting_id)',
      'CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at)',
      'CREATE INDEX IF NOT EXISTS idx_audio_files_meeting_id ON audio_files(meeting_id)',
      'CREATE INDEX IF NOT EXISTS idx_tasks_meeting_id ON tasks(meeting_id)',
      'CREATE INDEX IF NOT EXISTS idx_tasks_lead_id ON tasks(lead_id)',
      'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)'
    ]

    for (const index of indexes) {
      await this.run(index)
    }

    logger.info('✅ Индексы базы данных созданы')
  }

  async run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function(error) {
        if (error) {
          reject(error)
        } else {
          resolve({ id: this.lastID, changes: this.changes })
        }
      })
    })
  }

  async get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (error, row) => {
        if (error) {
          reject(error)
        } else {
          resolve(row)
        }
      })
    })
  }

  async all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (error, rows) => {
        if (error) {
          reject(error)
        } else {
          resolve(rows)
        }
      })
    })
  }

  // Методы для работы с встречами
  async createMeeting(meetingData) {
    try {
      const {
        id,
        chatId,
        userId,
        username,
        url,
        platform = null,
        status = 'starting'
      } = meetingData

      const sql = `
        INSERT INTO meetings (id, chat_id, user_id, username, url, platform, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `

      await this.run(sql, [id, chatId, userId, username, url, platform, status])

      logger.meeting(`Встреча создана в базе данных: ${id}`)
      return { success: true, id }
    } catch (error) {
      logger.errorWithContext(`Ошибка создания встречи: ${meetingData.id}`, error)
      return { success: false, error: error.message }
    }
  }

  async updateMeeting(meetingId, updateData) {
    try {
      const fields = []
      const values = []

      Object.keys(updateData).forEach(key => {
        if (updateData[key] !== undefined) {
          fields.push(`${key} = ?`)
          values.push(updateData[key])
        }
      })

      if (fields.length === 0) {
        return { success: true }
      }

      fields.push('updated_at = CURRENT_TIMESTAMP')
      values.push(meetingId)

      const sql = `UPDATE meetings SET ${fields.join(', ')} WHERE id = ?`

      await this.run(sql, values)

      logger.meeting(`Встреча обновлена в базе данных: ${meetingId}`)
      return { success: true }
    } catch (error) {
      logger.errorWithContext(`Ошибка обновления встречи: ${meetingId}`, error)
      return { success: false, error: error.message }
    }
  }

  async getMeeting(meetingId) {
    try {
      const sql = 'SELECT * FROM meetings WHERE id = ?'
      const meeting = await this.get(sql, [meetingId])
      return meeting
    } catch (error) {
      logger.errorWithContext(`Ошибка получения встречи: ${meetingId}`, error)
      return null
    }
  }

  async getMeetings(chatId = null, limit = 50, offset = 0) {
    try {
      let sql = 'SELECT * FROM meetings'
      const params = []

      if (chatId) {
        sql += ' WHERE chat_id = ?'
        params.push(chatId)
      }

      sql += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
      params.push(limit, offset)

      const meetings = await this.all(sql, params)
      return meetings
    } catch (error) {
      logger.errorWithContext('Ошибка получения списка встреч', error)
      return []
    }
  }

  async getMeetingsByStatus(status, limit = 100) {
    try {
      const sql = 'SELECT * FROM meetings WHERE status = ? ORDER BY created_at DESC LIMIT ?'
      const meetings = await this.all(sql, [status, limit])
      return meetings
    } catch (error) {
      logger.errorWithContext(`Ошибка получения встреч по статусу: ${status}`, error)
      return []
    }
  }

  // Методы для работы с логами
  async log(level, message, category = null, meetingId = null, chatId = null, metadata = null) {
    try {
      const sql = `
        INSERT INTO logs (level, message, category, meeting_id, chat_id, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
      `

      const metadataStr = metadata ? JSON.stringify(metadata) : null
      await this.run(sql, [level, message, category, meetingId, chatId, metadataStr])

    } catch (error) {
      logger.errorWithContext('Ошибка записи лога в базу данных', error)
    }
  }

  async getLogs(level = null, meetingId = null, limit = 100, offset = 0) {
    try {
      let sql = 'SELECT * FROM logs'
      const params = []
      const conditions = []

      if (level) {
        conditions.push('level = ?')
        params.push(level)
      }

      if (meetingId) {
        conditions.push('meeting_id = ?')
        params.push(meetingId)
      }

      if (conditions.length > 0) {
        sql += ' WHERE ' + conditions.join(' AND ')
      }

      sql += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
      params.push(limit, offset)

      const logs = await this.all(sql, params)
      return logs
    } catch (error) {
      logger.errorWithContext('Ошибка получения логов', error)
      return []
    }
  }

  // Методы для работы с аудио файлами
  async saveAudioFile(audioData) {
    try {
      const {
        meetingId,
        filename,
        filepath,
        size,
        duration,
        format,
        sampleRate,
        channels
      } = audioData

      const sql = `
        INSERT INTO audio_files (meeting_id, filename, filepath, size, duration, format, sample_rate, channels)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `

      await this.run(sql, [meetingId, filename, filepath, size, duration, format, sampleRate, channels])

      logger.meeting(`Аудио файл сохранен в базе данных: ${filename}`)
      return { success: true }
    } catch (error) {
      logger.errorWithContext(`Ошибка сохранения аудио файла: ${audioData.filename}`, error)
      return { success: false, error: error.message }
    }
  }

  async getAudioFiles(meetingId) {
    try {
      const sql = 'SELECT * FROM audio_files WHERE meeting_id = ? ORDER BY created_at DESC'
      const files = await this.all(sql, [meetingId])
      return files
    } catch (error) {
      logger.errorWithContext(`Ошибка получения аудио файлов для встречи: ${meetingId}`, error)
      return []
    }
  }

  // Методы для работы с задачами
  async createTask(taskData) {
    try {
      const {
        meetingId,
        leadId,
        taskId,
        title,
        description,
        status = 'created',
        priority = 'medium',
        responsibleId,
        deadline
      } = taskData

      const sql = `
        INSERT INTO tasks (meeting_id, lead_id, task_id, title, description, status, priority, responsible_id, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `

      await this.run(sql, [meetingId, leadId, taskId, title, description, status, priority, responsibleId, deadline])

      logger.meeting(`Задача создана в базе данных: ${title}`)
      return { success: true }
    } catch (error) {
      logger.errorWithContext(`Ошибка создания задачи: ${taskData.title}`, error)
      return { success: false, error: error.message }
    }
  }

  async getTasks(meetingId = null, leadId = null) {
    try {
      let sql = 'SELECT * FROM tasks'
      const params = []
      const conditions = []

      if (meetingId) {
        conditions.push('meeting_id = ?')
        params.push(meetingId)
      }

      if (leadId) {
        conditions.push('lead_id = ?')
        params.push(leadId)
      }

      if (conditions.length > 0) {
        sql += ' WHERE ' + conditions.join(' AND ')
      }

      sql += ' ORDER BY created_at DESC'

      const tasks = await this.all(sql, params)
      return tasks
    } catch (error) {
      logger.errorWithContext('Ошибка получения задач', error)
      return []
    }
  }

  // Методы для работы с пользователями
  async saveUser(userData) {
    try {
      const {
        id,
        username,
        firstName,
        lastName,
        isBot = false,
        languageCode
      } = userData

      const sql = `
        INSERT OR REPLACE INTO users (id, username, first_name, last_name, is_bot, language_code, last_activity)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
      `

      await this.run(sql, [id, username, firstName, lastName, isBot, languageCode])

      return { success: true }
    } catch (error) {
      logger.errorWithContext(`Ошибка сохранения пользователя: ${userData.id}`, error)
      return { success: false, error: error.message }
    }
  }

  async getUser(userId) {
    try {
      const sql = 'SELECT * FROM users WHERE id = ?'
      const user = await this.get(sql, [userId])
      return user
    } catch (error) {
      logger.errorWithContext(`Ошибка получения пользователя: ${userId}`, error)
      return null
    }
  }

  // Методы для работы с настройками
  async setSetting(key, value, description = null) {
    try {
      const sql = `
        INSERT OR REPLACE INTO settings (key, value, description, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
      `

      await this.run(sql, [key, value, description])
      return { success: true }
    } catch (error) {
      logger.errorWithContext(`Ошибка сохранения настройки: ${key}`, error)
      return { success: false, error: error.message }
    }
  }

  async getSetting(key) {
    try {
      const sql = 'SELECT value FROM settings WHERE key = ?'
      const result = await this.get(sql, [key])
      return result ? result.value : null
    } catch (error) {
      logger.errorWithContext(`Ошибка получения настройки: ${key}`, error)
      return null
    }
  }

  // Методы очистки
  async cleanupOldLogs(cutoffDate) {
    try {
      const sql = 'DELETE FROM logs WHERE created_at < ?'
      const result = await this.run(sql, [cutoffDate.toISOString()])
      
      logger.info(`Очищено логов: ${result.changes}`)
      return result.changes
    } catch (error) {
      logger.errorWithContext('Ошибка очистки старых логов', error)
      return 0
    }
  }

  async cleanupOldMeetings(cutoffDate) {
    try {
      const sql = 'DELETE FROM meetings WHERE created_at < ? AND status IN ("completed", "failed")'
      const result = await this.run(sql, [cutoffDate.toISOString()])
      
      logger.info(`Очищено встреч: ${result.changes}`)
      return result.changes
    } catch (error) {
      logger.errorWithContext('Ошибка очистки старых встреч', error)
      return 0
    }
  }

  async cleanupOldAudioFiles(cutoffDate) {
    try {
      const sql = 'DELETE FROM audio_files WHERE created_at < ?'
      const result = await this.run(sql, [cutoffDate.toISOString()])
      
      logger.info(`Очищено аудио файлов: ${result.changes}`)
      return result.changes
    } catch (error) {
      logger.errorWithContext('Ошибка очистки старых аудио файлов', error)
      return 0
    }
  }

  // Статистика
  async getStatistics() {
    try {
      const stats = {}

      // Количество встреч по статусам
      const meetingStats = await this.all(`
        SELECT status, COUNT(*) as count 
        FROM meetings 
        GROUP BY status
      `)
      stats.meetings = meetingStats

      // Количество логов по уровням
      const logStats = await this.all(`
        SELECT level, COUNT(*) as count 
        FROM logs 
        GROUP BY level
      `)
      stats.logs = logStats

      // Количество задач по статусам
      const taskStats = await this.all(`
        SELECT status, COUNT(*) as count 
        FROM tasks 
        GROUP BY status
      `)
      stats.tasks = taskStats

      // Общее количество пользователей
      const userCount = await this.get('SELECT COUNT(*) as count FROM users')
      stats.users = userCount.count

      return stats
    } catch (error) {
      logger.errorWithContext('Ошибка получения статистики', error)
      return {}
    }
  }

  async close() {
    return new Promise((resolve, reject) => {
      if (this.db) {
        this.db.close((error) => {
          if (error) {
            logger.errorWithContext('Ошибка закрытия базы данных', error)
            reject(error)
          } else {
            logger.info('✅ База данных закрыта')
            resolve()
          }
        })
      } else {
        resolve()
      }
    })
  }
}

module.exports = DatabaseService
