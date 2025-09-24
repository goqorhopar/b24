/**
 * Адаптер для работы с платформами встреч (Zoom, Google Meet, Teams, etc.)
 */

const puppeteer = require('puppeteer')
const logger = require('../utils/logger')
const config = require('../config')

class MeetingPlatformAdapter {
  constructor() {
    this.browser = null
    this.pages = new Map()
    this.activeMeetings = new Map()
  }

  async initialize() {
    try {
      logger.info('🚀 Инициализация Meeting Platform Adapter...')

      // Запуск браузера
      this.browser = await puppeteer.launch({
        headless: config.PUPPETEER_HEADLESS,
        slowMo: config.PUPPETEER_SLOW_MO,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu',
          '--disable-web-security',
          '--allow-running-insecure-content',
          '--disable-features=VizDisplayCompositor',
          '--use-fake-ui-for-media-stream',
          '--allow-file-access-from-files',
          '--disable-blink-features=AutomationControlled',
          '--window-size=1920,1080'
        ],
        defaultViewport: {
          width: 1920,
          height: 1080
        }
      })

      logger.info('✅ Meeting Platform Adapter инициализирован')
    } catch (error) {
      logger.errorWithContext('Ошибка инициализации Meeting Platform Adapter', error)
      throw error
    }
  }

  async joinMeeting(meetingUrl, options = {}) {
    const { displayName = 'AI Assistant', meetingId } = options
    let page = null

    try {
      logger.meeting(`Присоединение к встрече: ${meetingUrl}`, { meetingId, displayName })

      // Создание новой страницы
      page = await this.browser.newPage()
      this.pages.set(meetingId, page)

      // Настройка страницы
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
      
      // Установка разрешений для аудио/видео
      await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'permissions', {
          get: () => ({
            query: () => Promise.resolve({ state: 'granted' })
          })
        })
      })

      // Определение платформы
      const platform = this.detectPlatform(meetingUrl)
      logger.meeting(`Обнаружена платформа: ${platform}`, { meetingId })

      // Переход на страницу встречи
      await page.goto(meetingUrl, { 
        waitUntil: 'networkidle2',
        timeout: config.PUPPETEER_TIMEOUT 
      })

      // Ожидание загрузки
      await page.waitForTimeout(5000)

      // Присоединение в зависимости от платформы
      let joinResult
      switch (platform) {
        case 'zoom':
          joinResult = await this.joinZoomMeeting(page, displayName, meetingId)
          break
        case 'google-meet':
          joinResult = await this.joinGoogleMeet(page, displayName, meetingId)
          break
        case 'teams':
          joinResult = await this.joinTeamsMeeting(page, displayName, meetingId)
          break
        case 'kontur-talk':
          joinResult = await this.joinKonturTalk(page, displayName, meetingId)
          break
        case 'yandex-telemost':
          joinResult = await this.joinYandexTelemost(page, displayName, meetingId)
          break
        default:
          throw new Error(`Неподдерживаемая платформа: ${platform}`)
      }

      if (joinResult.success) {
        // Сохранение активной встречи
        this.activeMeetings.set(meetingId, {
          page,
          platform,
          url: meetingUrl,
          startTime: new Date(),
          status: 'joined'
        })

        // Отключение микрофона и камеры
        await this.muteAudioVideo(page, meetingId)

        logger.meeting(`Успешно присоединились к встрече ${platform}`, { meetingId })
      }

      return joinResult

    } catch (error) {
      logger.errorWithContext(`Ошибка присоединения к встрече ${meetingId}`, error)
      
      if (page) {
        await page.close()
        this.pages.delete(meetingId)
      }

      return { success: false, error: error.message }
    }
  }

  detectPlatform(url) {
    const urlLower = url.toLowerCase()
    
    if (urlLower.includes('zoom.us')) return 'zoom'
    if (urlLower.includes('meet.google.com')) return 'google-meet'
    if (urlLower.includes('teams.microsoft.com')) return 'teams'
    if (urlLower.includes('talk.kontur.ru')) return 'kontur-talk'
    if (urlLower.includes('telemost.yandex.ru')) return 'yandex-telemost'
    
    throw new Error(`Неподдерживаемая платформа для URL: ${url}`)
  }

  async joinZoomMeeting(page, displayName, meetingId) {
    try {
      logger.meeting('Присоединение к Zoom встрече', { meetingId })

      // Закрытие всплывающих окон
      await this.closePopups(page)

      // Ввод имени
      const nameSelectors = [
        '#inputname',
        'input[name="displayname"]',
        'input[placeholder*="name" i]',
        'input[placeholder*="имя" i]',
        'input[placeholder*="Name" i]',
        'input[placeholder*="Имя" i]'
      ]

      for (const selector of nameSelectors) {
        try {
          const nameInput = await page.waitForSelector(selector, { timeout: 3000 })
          if (nameInput) {
            await nameInput.clear()
            await nameInput.type(displayName)
            logger.meeting('Имя введено в Zoom', { meetingId, displayName })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Нажатие кнопки присоединения
      const joinSelectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button[aria-label*="Join"]',
        'button[aria-label*="Присоединиться"]',
        '.join-button',
        '#joinBtn'
      ]

      for (const selector of joinSelectors) {
        try {
          const joinButton = await page.waitForSelector(selector, { timeout: 3000 })
          if (joinButton) {
            await joinButton.click()
            logger.meeting('Кнопка присоединения нажата в Zoom', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Ожидание входа в комнату
      await page.waitForTimeout(10000)

      return { success: true, platform: 'zoom' }

    } catch (error) {
      logger.errorWithContext('Ошибка присоединения к Zoom', error, { meetingId })
      return { success: false, error: error.message }
    }
  }

  async joinGoogleMeet(page, displayName, meetingId) {
    try {
      logger.meeting('Присоединение к Google Meet', { meetingId })

      // Закрытие всплывающих окон
      await this.closePopups(page)

      // Нажатие кнопки присоединения
      const joinSelectors = [
        'button[aria-label*="Join now"]',
        'button[aria-label*="Ask to join"]',
        'button[data-is-muted="false"]',
        '.VfPpkd-LgbsSe'
      ]

      for (const selector of joinSelectors) {
        try {
          const joinButton = await page.waitForSelector(selector, { timeout: 5000 })
          if (joinButton) {
            await joinButton.click()
            logger.meeting('Кнопка присоединения нажата в Google Meet', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Ожидание входа в комнату
      await page.waitForTimeout(8000)

      return { success: true, platform: 'google-meet' }

    } catch (error) {
      logger.errorWithContext('Ошибка присоединения к Google Meet', error, { meetingId })
      return { success: false, error: error.message }
    }
  }

  async joinTeamsMeeting(page, displayName, meetingId) {
    try {
      logger.meeting('Присоединение к Teams встрече', { meetingId })

      // Закрытие всплывающих окон
      await this.closePopups(page)

      // Нажатие кнопки присоединения
      const joinSelectors = [
        'button[aria-label*="Join now"]',
        'button[aria-label*="Join meeting"]',
        '.ts-calling-join-button',
        '[data-tid="prejoin-join-button"]'
      ]

      for (const selector of joinSelectors) {
        try {
          const joinButton = await page.waitForSelector(selector, { timeout: 5000 })
          if (joinButton) {
            await joinButton.click()
            logger.meeting('Кнопка присоединения нажата в Teams', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Ожидание входа в комнату
      await page.waitForTimeout(8000)

      return { success: true, platform: 'teams' }

    } catch (error) {
      logger.errorWithContext('Ошибка присоединения к Teams', error, { meetingId })
      return { success: false, error: error.message }
    }
  }

  async joinKonturTalk(page, displayName, meetingId) {
    try {
      logger.meeting('Присоединение к Контур.Толк', { meetingId })

      // Закрытие всплывающих окон
      await this.closePopups(page)

      // Нажатие кнопки присоединения
      const joinSelectors = [
        'button[aria-label*="Войти"]',
        'button[aria-label*="Присоединиться"]',
        '.join-button',
        '.enter-button'
      ]

      for (const selector of joinSelectors) {
        try {
          const joinButton = await page.waitForSelector(selector, { timeout: 5000 })
          if (joinButton) {
            await joinButton.click()
            logger.meeting('Кнопка присоединения нажата в Контур.Толк', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Ожидание входа в комнату
      await page.waitForTimeout(8000)

      return { success: true, platform: 'kontur-talk' }

    } catch (error) {
      logger.errorWithContext('Ошибка присоединения к Контур.Толк', error, { meetingId })
      return { success: false, error: error.message }
    }
  }

  async joinYandexTelemost(page, displayName, meetingId) {
    try {
      logger.meeting('Присоединение к Яндекс.Телемост', { meetingId })

      // Закрытие всплывающих окон
      await this.closePopups(page)

      // Нажатие кнопки присоединения
      const joinSelectors = [
        'button[aria-label*="Войти"]',
        'button[aria-label*="Присоединиться"]',
        '.join-button',
        '.enter-button'
      ]

      for (const selector of joinSelectors) {
        try {
          const joinButton = await page.waitForSelector(selector, { timeout: 5000 })
          if (joinButton) {
            await joinButton.click()
            logger.meeting('Кнопка присоединения нажата в Яндекс.Телемост', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Ожидание входа в комнату
      await page.waitForTimeout(8000)

      return { success: true, platform: 'yandex-telemost' }

    } catch (error) {
      logger.errorWithContext('Ошибка присоединения к Яндекс.Телемост', error, { meetingId })
      return { success: false, error: error.message }
    }
  }

  async closePopups(page) {
    try {
      const closeSelectors = [
        'button[aria-label*="Close"]',
        'button[aria-label*="Закрыть"]',
        '.close-button',
        '.dismiss-button',
        '[data-testid="close"]'
      ]

      for (const selector of closeSelectors) {
        try {
          const closeButton = await page.waitForSelector(selector, { timeout: 2000 })
          if (closeButton) {
            await closeButton.click()
            await page.waitForTimeout(1000)
          }
        } catch (e) {
          continue
        }
      }
    } catch (error) {
      logger.debug('Ошибка закрытия попапов:', error.message)
    }
  }

  async muteAudioVideo(page, meetingId) {
    try {
      logger.meeting('Отключение аудио и видео', { meetingId })

      // Отключение микрофона
      const muteSelectors = [
        'button[aria-label*="Mute"]',
        'button[aria-label*="Unmute"]',
        'button[aria-label*="микрофон"]',
        'button[aria-label*="microphone"]',
        '.microphone-button',
        '.mute-button'
      ]

      for (const selector of muteSelectors) {
        try {
          const muteButton = await page.waitForSelector(selector, { timeout: 3000 })
          if (muteButton) {
            await muteButton.click()
            logger.meeting('Микрофон отключен', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Отключение камеры
      const videoSelectors = [
        'button[aria-label*="Stop Video"]',
        'button[aria-label*="Start Video"]',
        'button[aria-label*="камера"]',
        'button[aria-label*="camera"]',
        '.camera-button',
        '.video-button'
      ]

      for (const selector of videoSelectors) {
        try {
          const videoButton = await page.waitForSelector(selector, { timeout: 3000 })
          if (videoButton) {
            await videoButton.click()
            logger.meeting('Камера отключена', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

    } catch (error) {
      logger.errorWithContext('Ошибка отключения аудио/видео', error, { meetingId })
    }
  }

  async leaveMeeting(meetingId) {
    try {
      const meeting = this.activeMeetings.get(meetingId)
      if (!meeting) {
        logger.warn(`Встреча ${meetingId} не найдена`)
        return { success: false, error: 'Встреча не найдена' }
      }

      const { page, platform } = meeting

      logger.meeting(`Выход из встречи ${platform}`, { meetingId })

      // Поиск кнопки выхода в зависимости от платформы
      const leaveSelectors = [
        'button[aria-label*="Leave"]',
        'button[aria-label*="Выйти"]',
        'button[aria-label*="End"]',
        'button[aria-label*="Завершить"]',
        '.leave-button',
        '.end-button',
        '.hangup-button'
      ]

      for (const selector of leaveSelectors) {
        try {
          const leaveButton = await page.waitForSelector(selector, { timeout: 3000 })
          if (leaveButton) {
            await leaveButton.click()
            logger.meeting('Кнопка выхода нажата', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Подтверждение выхода если требуется
      await page.waitForTimeout(2000)
      const confirmSelectors = [
        'button[aria-label*="End Meeting"]',
        'button[aria-label*="Завершить встречу"]',
        'button[aria-label*="Leave Meeting"]',
        'button[aria-label*="Покинуть встречу"]'
      ]

      for (const selector of confirmSelectors) {
        try {
          const confirmButton = await page.waitForSelector(selector, { timeout: 3000 })
          if (confirmButton) {
            await confirmButton.click()
            logger.meeting('Выход подтвержден', { meetingId })
            break
          }
        } catch (e) {
          continue
        }
      }

      // Закрытие страницы
      await page.close()
      this.pages.delete(meetingId)
      this.activeMeetings.delete(meetingId)

      logger.meeting(`Выход из встречи ${meetingId} завершен`)
      return { success: true }

    } catch (error) {
      logger.errorWithContext(`Ошибка выхода из встречи ${meetingId}`, error)
      return { success: false, error: error.message }
    }
  }

  async isInMeeting(meetingId) {
    const meeting = this.activeMeetings.get(meetingId)
    return !!meeting && meeting.status === 'joined'
  }

  async getMeetingInfo(meetingId) {
    return this.activeMeetings.get(meetingId) || null
  }

  async shutdown() {
    try {
      logger.info('🛑 Остановка Meeting Platform Adapter...')

      // Выход из всех активных встреч
      for (const meetingId of this.activeMeetings.keys()) {
        await this.leaveMeeting(meetingId)
      }

      // Закрытие всех страниц
      for (const [meetingId, page] of this.pages) {
        try {
          await page.close()
        } catch (error) {
          logger.errorWithContext(`Ошибка закрытия страницы ${meetingId}`, error)
        }
      }

      this.pages.clear()
      this.activeMeetings.clear()

      // Закрытие браузера
      if (this.browser) {
        await this.browser.close()
      }

      logger.info('✅ Meeting Platform Adapter остановлен')
    } catch (error) {
      logger.errorWithContext('Ошибка остановки Meeting Platform Adapter', error)
    }
  }
}

module.exports = MeetingPlatformAdapter
