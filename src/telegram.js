// src/telegram.js
import TelegramBot from 'node-telegram-bot-api';
import logger from './logger.js';
import { config } from './config.js';
import { runChecklist } from './gemini.js';
import { bitrixService } from './bitrix.js';

const token = config.telegramBotToken;
const userStates = new Map(); // chatId -> { step, transcript }

if (!token) {
  logger.warn('TELEGRAM_BOT_TOKEN не задан. Бот не запущен.');
  process.exit(1);
}

logger.info('🚀 Инициализация Telegram Bot...');

// Создаем бота с опциями для избежания конфликтов
const bot = new TelegramBot(token, {
  polling: {
    interval: 300,
    timeout: 10,
    limit: 100,
    autoStart: true,
    params: {
      timeout: 10
    }
  }
});

logger.info('🚀 Telegram Bot запущен в режиме polling');

// Отправляем уведомление админу при запуске
if (config.adminChatId) {
  bot.sendMessage(config.adminChatId, '🤖 Meeting Bot запущен и готов к работе!')
    .catch(err => {
      logger.error({ error: err.message }, 'Не удалось отправить уведомление админу');
    });
}

// Команда /start
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  logger.info({ chatId }, 'Команда /start получена');
  
  bot.sendMessage(
    chatId,
    '🤖 Добро пожаловать в Meeting Bot!\n\n' +
    'Отправьте транскрипт встречи для анализа, а затем ID лида в Bitrix24.\n\n' +
    '📋 Формат работы:\n' +
    '1. Отправьте транскрипт встречи\n' +
    '2. Отправьте ID лида из Bitrix24\n' +
    '3. Бот проанализирует и обновит лид'
  ).catch(err => {
    logger.error({ chatId, error: err.message }, 'Ошибка отправки сообщения');
  });
});

// Команда /help
bot.onText(/\/help/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(
    chatId,
    '📖 Помощь по Meeting Bot:\n\n' +
    '• Просто отправьте транскрипт встречи\n' +
    '• Затем отправьте числовой ID лида из Bitrix24\n' +
    '• Бот автоматически проанализирует и обновит лид\n\n' +
    '⚠️ Убедитесь, что:\n' +
    '• Транскрипт содержит достаточно информации\n' +
    '• ID лида корректен\n' +
    '• Бот имеет доступ к Bitrix24'
  ).catch(err => {
    logger.error({ chatId, error: err.message }, 'Ошибка отправки сообщения помощи');
  });
});

// Команда /status для админа
bot.onText(/\/status/, (msg) => {
  const chatId = msg.chat.id;
  
  // Проверяем, что команда от админа
  if (config.adminChatId && chatId !== config.adminChatId) {
    bot.sendMessage(chatId, '❌ Эта команда только для администратора');
    return;
  }
  
  const memoryUsage = process.memoryUsage();
  const uptime = process.uptime();
  const hours = Math.floor(uptime / 3600);
  const minutes = Math.floor((uptime % 3600) / 60);
  const seconds = Math.floor(uptime % 60);
  
  const statusMessage = `
🤖 Статус бота:
• Память: ${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB / ${Math.round(memoryUsage.heapTotal / 1024 / 1024)}MB
• Время работы: ${hours}ч ${minutes}м ${seconds}с
• Активных сессий: ${userStates.size}
• Версия: 1.0.0
• Окружение: ${process.env.NODE_ENV || 'development'}
  `.trim();
  
  bot.sendMessage(chatId, statusMessage).catch(err => {
    logger.error({ chatId, error: err.message }, 'Ошибка отправки статуса');
  });
});

// Обработка всех сообщений
bot.on('message', async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text?.trim();
  const username = msg.from?.username || msg.from?.first_name || 'unknown';
  
  if (!text || text.startsWith('/')) return;

  logger.info({ chatId, username, textLength: text.length }, 'Получено сообщение');

  const state = userStates.get(chatId);

  // Шаг 1: принимаем транскрипт
  if (!state) {
    if (text.length < 50) {
      bot.sendMessage(chatId, '❌ Транскрипт слишком короткий. Минимум 50 символов.');
      return;
    }
    
    userStates.set(chatId, { step: 'awaitingLeadId', transcript: text });
    logger.info({ chatId, transcriptLength: text.length }, 'Транскрипт сохранён');
    
    await bot.sendMessage(chatId, 
      '✅ Транскрипт принят (' + text.length + ' символов).\n' +
      'Теперь отправьте числовой ID лида в Bitrix24:'
    );
    return;
  }

  // Шаг 2: ждём ID лида
  if (state.step === 'awaitingLeadId') {
    if (!/^[0-9]+$/.test(text)) {
      await bot.sendMessage(chatId, '❌ ID лида должен быть числом. Попробуйте снова:');
      return;
    }

    const leadId = text;
    logger.info({ chatId, leadId }, 'Получен ID лида');

    try {
      await bot.sendMessage(chatId, '🔄 Анализирую транскрипт...');
      const analysis = await runChecklist(state.transcript, logger);

      // Формируем отчёт
      const report = formatAnalysisReport(analysis);

      // Обновляем лид
      await bot.sendMessage(chatId, '📝 Обновляю лид в Bitrix24...');
      await bitrixService.updateLead(leadId, analysis, state.transcript, 'Telegram Bot', logger);
      logger.info({ leadId }, '✅ Лид обновлён в Bitrix');

      // Создаём задачу
      await bot.sendMessage(chatId, '📌 Создаю задачу...');
      const taskTitle = `Анализ встречи по лиду ${leadId} (${analysis.category || '—'})`;
      const { taskId } = await bitrixService.createTask({
        title: taskTitle,
        description: report,
        leadId,
        source: 'Telegram Bot'
      }, logger);
      
      logger.info({ leadId, taskId }, '✅ Задача создана и привязана к лиду');

      // Отправляем отчёт менеджеру
      await bot.sendMessage(chatId, '📊 Отчет готов:');
      
      for (const part of splitMessage(report)) {
        await bot.sendMessage(chatId, part, { parse_mode: 'Markdown' });
      }
      
      await bot.sendMessage(chatId, 
        '✅ Готово!\n' +
        '• Лид #' + leadId + ' обновлен в Bitrix24\n' +
        '• Задача #' + taskId + ' создана\n' +
        '• Ответственный: пользователь #' + config.bitrixResponsibleId
      );
      
      // Уведомляем админа о successful обработке
      if (config.adminChatId) {
        const adminMessage = `✅ Успешная обработка лида #${leadId}
Чат: ${chatId}
Пользователь: ${username}
Длина транскрипта: ${state.transcript.length} символов
Задача: #${taskId}`;
        
        bot.sendMessage(config.adminChatId, adminMessage)
          .catch(err => logger.error({ error: err.message }, 'Не удалось уведомить админа'));
      }
      
    } catch (err) {
      logger.error({ chatId, error: err.message, stack: err.stack }, 'Ошибка анализа или обновления лида');
      
      let errorMessage = `❌ Ошибка: ${err.message}`;
      if (err.message.includes('BITRIX_WEBHOOK_URL')) {
        errorMessage += '\n\n⚠️ Проверьте настройки Bitrix24 Webhook';
      } else if (err.message.includes('не найден') || err.message.includes('404')) {
        errorMessage += '\n\n⚠️ Лид с таким ID не найден в Bitrix24';
      }
      
      await bot.sendMessage(chatId, errorMessage);
      
      // Уведомляем админа об ошибке
      if (config.adminChatId) {
        const errorAdminMessage = `❌ Ошибка обработки лида
Чат: ${chatId}
Пользователь: ${username}
Ошибка: ${err.message}
Транскрипт: ${state.transcript.substring(0, 100)}...`;
        
        bot.sendMessage(config.adminChatId, errorAdminMessage)
          .catch(adminErr => logger.error({ error: adminErr.message }, 'Не удалось уведомить админа об ошибке'));
      }
    } finally {
      userStates.delete(chatId);
      logger.info({ chatId }, 'Процесс завершён, состояние сброшено');
    }
  }
});

// Обработка ошибок polling
bot.on('polling_error', (error) => {
  logger.error({ 
    error: error.message, 
    code: error.code,
    response: error.response?.body 
  }, 'Polling error');
  
  // Уведомляем админа об ошибке polling
  if (config.adminChatId) {
    bot.sendMessage(config.adminChatId, `❌ Ошибка polling: ${error.message}`)
      .catch(err => logger.error({ error: err.message }, 'Не удалось уведомить админа об ошибке polling'));
  }
});

bot.on('webhook_error', (error) => {
  logger.error({ error: error.message }, 'Webhook error');
});

// Обработка остановки бота
process.on('SIGTERM', () => {
  logger.info('Останавливаем Telegram Bot...');
  bot.stopPolling();
  
  // Уведомляем админа об остановке
  if (config.adminChatId) {
    bot.sendMessage(config.adminChatId, '🛑 Бот остановлен (SIGTERM)')
      .catch(err => logger.error({ error: err.message }, 'Не удалось уведомить админа об остановке'));
  }
});

process.on('SIGINT', () => {
  logger.info('Останавливаем Telegram Bot...');
  bot.stopPolling();
  
  // Уведомляем админа об остановке
  if (config.adminChatId) {
    bot.sendMessage(config.adminChatId, '🛑 Бот остановлен (SIGINT)')
      .catch(err => logger.error({ error: err.message }, 'Не удалось уведомить админа об остановке'));
  }
});

/**
 * Форматирование отчёта для менеджера
 */
function formatAnalysisReport(a) {
  return `
📊 *РЕЗУЛЬТАТЫ АНАЛИЗА ВСТРЕЧИ*

*Категория клиента:* ${a.category || '—'} (вероятность ${a.probability ?? '—'}%)

*Отрасль:* ${a.industry || '—'}
*Что продает:* ${a.whatSells || '—'}
*Ключевые лица:* ${a.decisionMakers || '—'}
*Сроки решения:* ${a.decisionTimeline || '—'}
*Бюджет:* ${a.budget || '—'}

*Основные боли и потребности:*
${a.painPoints || '—'}

*Возражения клиента:*
${a.objections || '—'}

*Реакция на предложение:*
${a.clientReaction || '—'}

*Интерес к сервису:*
${a.serviceInterest || '—'}

*Найденные возможности:*
${a.opportunities || '—'}

*Ошибки менеджера:*
${a.managerErrors || '—'}

*Путь к закрытию:*
${a.closingPath || '—'}

*Тон беседы:* ${a.tone || '—'}
*Контроль диалога:* ${a.dialogControl || '—'}

*Приоритетные действия:*
${a.priorityAction || '—'}

*Кто проводил встречу:* ${a.meetingHost || '—'}
*Плановая дата следующей встречи:* ${a.meetingPlannedAt ? new Date(a.meetingPlannedAt).toLocaleDateString('ru-RU') : '—'}

🧾 *Краткая сводка:*
${a.summary || '—'}
`.trim();
}

/**
 * Разделение длинных сообщений для Telegram
 */
function splitMessage(message, maxLength = 4000) {
  if (message.length <= maxLength) return [message];
  const parts = [];
  let current = '';
  
  const lines = message.split('\n');
  for (const line of lines) {
    if ((current + line + '\n').length > maxLength) {
      if (current.trim()) parts.push(current.trim());
      current = line + '\n';
    } else {
      current += line + '\n';
    }
  }
  
  if (current.trim()) parts.push(current.trim());
  return parts;
}

export default bot;
