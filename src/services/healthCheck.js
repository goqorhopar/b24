/**
 * Сервис проверки здоровья системы
 */

const os = require('os')
const fs = require('fs').promises
const path = require('path')
const logger = require('../utils/logger')
const config = require('../config')

class HealthCheckService {
  constructor() {
    this.checks = new Map()
    this.lastCheck = null
    this.overallStatus = 'unknown'
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Health Check Service...')

      // Регистрация проверок
      this.registerChecks()

      // Первоначальная проверка
      await this.performHealthCheck()

      logger.info('✅ Health Check Service инициализирован')
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Health Check Service', error)
      throw error
    }
  }

  registerChecks() {
    // Проверка системы
    this.checks.set('system', {
      name: 'System Resources',
      check: this.checkSystemResources.bind(this),
      critical: true
    })

    // Проверка дискового пространства
    this.checks.set('disk', {
      name: 'Disk Space',
      check: this.checkDiskSpace.bind(this),
      critical: true
    })

    // Проверка памяти
    this.checks.set('memory', {
      name: 'Memory Usage',
      check: this.checkMemoryUsage.bind(this),
      critical: true
    })

    // Проверка директорий
    this.checks.set('directories', {
      name: 'Required Directories',
      check: this.checkDirectories.bind(this),
      critical: true
    })

    // Проверка конфигурации
    this.checks.set('config', {
      name: 'Configuration',
      check: this.checkConfiguration.bind(this),
      critical: true
    })

    // Проверка внешних сервисов
    this.checks.set('external', {
      name: 'External Services',
      check: this.checkExternalServices.bind(this),
      critical: false
    })
  }

  async performHealthCheck() {
    try {
      const results = {}
      let overallHealthy = true
      let criticalIssues = 0

      logger.debug('Выполнение проверки здоровья системы...')

      for (const [key, check] of this.checks) {
        try {
          const result = await check.check()
          results[key] = {
            name: check.name,
            status: result.healthy ? 'healthy' : 'unhealthy',
            message: result.message,
            details: result.details,
            critical: check.critical,
            timestamp: new Date().toISOString()
          }

          if (!result.healthy && check.critical) {
            overallHealthy = false
            criticalIssues++
          }

        } catch (error) {
          logger.errorWithContext(`Ошибка проверки ${check.name}`, error)
          results[key] = {
            name: check.name,
            status: 'error',
            message: error.message,
            critical: check.critical,
            timestamp: new Date().toISOString()
          }

          if (check.critical) {
            overallHealthy = false
            criticalIssues++
          }
        }
      }

      this.overallStatus = overallHealthy ? 'healthy' : 'unhealthy'
      this.lastCheck = {
        status: this.overallStatus,
        timestamp: new Date().toISOString(),
        checks: results,
        criticalIssues,
        totalChecks: this.checks.size
      }

      logger.debug(`Проверка здоровья завершена. Статус: ${this.overallStatus}`)

      return this.lastCheck

    } catch (error) {
      logger.errorWithContext('Ошибка выполнения проверки здоровья', error)
      this.overallStatus = 'error'
      this.lastCheck = {
        status: 'error',
        timestamp: new Date().toISOString(),
        error: error.message
      }
      return this.lastCheck
    }
  }

  async checkSystemResources() {
    try {
      const uptime = process.uptime()
      const loadAvg = os.loadavg()
      const cpuCount = os.cpus().length

      const details = {
        uptime: `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m`,
        loadAverage: loadAvg,
        cpuCount: cpuCount,
        platform: os.platform(),
        arch: os.arch(),
        nodeVersion: process.version
      }

      // Проверка загрузки CPU
      const avgLoad = loadAvg[0] / cpuCount
      const healthy = avgLoad < 2.0 // Загрузка менее 200%

      return {
        healthy,
        message: healthy ? 'Системные ресурсы в норме' : 'Высокая загрузка системы',
        details
      }

    } catch (error) {
      return {
        healthy: false,
        message: `Ошибка проверки системных ресурсов: ${error.message}`,
        details: { error: error.message }
      }
    }
  }

  async checkDiskSpace() {
    try {
      const stats = await fs.stat(config.DATA_DIR)
      const details = {
        dataDir: config.DATA_DIR,
        exists: true
      }

      // Простая проверка доступности записи
      const testFile = path.join(config.DATA_DIR, '.health_check_test')
      try {
        await fs.writeFile(testFile, 'test')
        await fs.unlink(testFile)
        details.writable = true
      } catch (error) {
        details.writable = false
        return {
          healthy: false,
          message: 'Нет доступа на запись в директорию данных',
          details
        }
      }

      return {
        healthy: true,
        message: 'Дисковое пространство доступно',
        details
      }

    } catch (error) {
      return {
        healthy: false,
        message: `Ошибка проверки дискового пространства: ${error.message}`,
        details: { error: error.message }
      }
    }
  }

  async checkMemoryUsage() {
    try {
      const memUsage = process.memoryUsage()
      const totalMem = os.totalmem()
      const freeMem = os.freemem()
      const usedMem = totalMem - freeMem

      const details = {
        processMemory: {
          rss: Math.round(memUsage.rss / 1024 / 1024), // MB
          heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024), // MB
          heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024), // MB
          external: Math.round(memUsage.external / 1024 / 1024) // MB
        },
        systemMemory: {
          total: Math.round(totalMem / 1024 / 1024), // MB
          used: Math.round(usedMem / 1024 / 1024), // MB
          free: Math.round(freeMem / 1024 / 1024), // MB
          usagePercent: Math.round((usedMem / totalMem) * 100)
        }
      }

      // Проверка использования памяти
      const memUsagePercent = (usedMem / totalMem) * 100
      const heapUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100

      const healthy = memUsagePercent < 90 && heapUsagePercent < 90

      return {
        healthy,
        message: healthy ? 'Использование памяти в норме' : 'Высокое использование памяти',
        details
      }

    } catch (error) {
      return {
        healthy: false,
        message: `Ошибка проверки памяти: ${error.message}`,
        details: { error: error.message }
      }
    }
  }

  async checkDirectories() {
    try {
      const requiredDirs = [
        config.DATA_DIR,
        config.LOGS_DIR,
        config.AUDIO_DIR,
        config.TEMP_DIR
      ]

      const details = {}
      let allExist = true

      for (const dir of requiredDirs) {
        try {
          await fs.access(dir)
          details[dir] = { exists: true, accessible: true }
        } catch (error) {
          details[dir] = { exists: false, accessible: false, error: error.message }
          allExist = false
        }
      }

      return {
        healthy: allExist,
        message: allExist ? 'Все необходимые директории доступны' : 'Некоторые директории недоступны',
        details
      }

    } catch (error) {
      return {
        healthy: false,
        message: `Ошибка проверки директорий: ${error.message}`,
        details: { error: error.message }
      }
    }
  }

  async checkConfiguration() {
    try {
      const requiredVars = [
        'TELEGRAM_BOT_TOKEN',
        'BITRIX_WEBHOOK_URL',
        'GEMINI_API_KEY'
      ]

      const details = {}
      let allConfigured = true

      for (const varName of requiredVars) {
        const value = config[varName]
        details[varName] = {
          configured: !!value,
          hasValue: value && value.length > 0
        }

        if (!value) {
          allConfigured = false
        }
      }

      // Дополнительные проверки конфигурации
      details.optionalVars = {
        OPENAI_API_KEY: !!config.OPENAI_API_KEY,
        GOOGLE_STT_API_KEY: !!config.GOOGLE_STT_API_KEY,
        AZURE_SPEECH_KEY: !!config.AZURE_SPEECH_KEY
      }

      return {
        healthy: allConfigured,
        message: allConfigured ? 'Конфигурация корректна' : 'Отсутствуют обязательные переменные окружения',
        details
      }

    } catch (error) {
      return {
        healthy: false,
        message: `Ошибка проверки конфигурации: ${error.message}`,
        details: { error: error.message }
      }
    }
  }

  async checkExternalServices() {
    try {
      const details = {}
      let allHealthy = true

      // Проверка Telegram API
      try {
        const axios = require('axios')
        const response = await axios.get(`https://api.telegram.org/bot${config.TELEGRAM_BOT_TOKEN}/getMe`, {
          timeout: 5000
        })
        details.telegram = {
          status: 'healthy',
          botName: response.data.result?.first_name || 'Unknown'
        }
      } catch (error) {
        details.telegram = {
          status: 'unhealthy',
          error: error.message
        }
        allHealthy = false
      }

      // Проверка Bitrix API
      try {
        const axios = require('axios')
        const response = await axios.post(`${config.BITRIX_WEBHOOK_URL}/crm.lead.fields.json`, {}, {
          timeout: 5000
        })
        details.bitrix = {
          status: 'healthy',
          fieldsCount: Object.keys(response.data.result || {}).length
        }
      } catch (error) {
        details.bitrix = {
          status: 'unhealthy',
          error: error.message
        }
        allHealthy = false
      }

      // Проверка Gemini API
      try {
        const { GoogleGenerativeAI } = require('google-generative-ai')
        const genAI = new GoogleGenerativeAI(config.GEMINI_API_KEY)
        const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' })
        
        // Простой тестовый запрос
        const result = await model.generateContent('Test')
        details.gemini = {
          status: 'healthy',
          model: 'gemini-1.5-flash'
        }
      } catch (error) {
        details.gemini = {
          status: 'unhealthy',
          error: error.message
        }
        allHealthy = false
      }

      return {
        healthy: allHealthy,
        message: allHealthy ? 'Все внешние сервисы доступны' : 'Некоторые внешние сервисы недоступны',
        details
      }

    } catch (error) {
      return {
        healthy: false,
        message: `Ошибка проверки внешних сервисов: ${error.message}`,
        details: { error: error.message }
      }
    }
  }

  async getStatus() {
    if (!this.lastCheck || this.isCheckStale()) {
      await this.performHealthCheck()
    }

    return this.lastCheck
  }

  isCheckStale() {
    if (!this.lastCheck) return true
    
    const checkAge = Date.now() - new Date(this.lastCheck.timestamp).getTime()
    const maxAge = config.HEALTH_CHECK_INTERVAL || 300000 // 5 минут по умолчанию
    
    return checkAge > maxAge
  }

  async getQuickStatus() {
    try {
      const memUsage = process.memoryUsage()
      const uptime = process.uptime()

      return {
        status: this.overallStatus,
        uptime: Math.floor(uptime),
        memory: Math.round(memUsage.heapUsed / 1024 / 1024), // MB
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      }
    }
  }

  async getDetailedStatus() {
    return await this.getStatus()
  }

  async forceCheck() {
    logger.info('Принудительная проверка здоровья системы...')
    return await this.performHealthCheck()
  }

  getOverallStatus() {
    return this.overallStatus
  }

  isHealthy() {
    return this.overallStatus === 'healthy'
  }

  async shutdown() {
    try {
      logger.info('🛑 Остановка Health Check Service...')
      
      this.checks.clear()
      this.lastCheck = null
      this.overallStatus = 'unknown'

      logger.info('✅ Health Check Service остановлен')
    } catch (error) {
      logger.errorWithContext('Ошибка остановки Health Check Service', error)
    }
  }
}

module.exports = HealthCheckService
