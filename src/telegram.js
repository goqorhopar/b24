// src/telegram.js

import TelegramBot from 'node-telegram-bot-api';
import { config } from './config.js';
import { runChecklist } from './gemini.js';
import { bitrixService } from './bitrix.js';
import pino from 'pino';

// Логгер
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: { level: (label) => ({ level: label }) },
  timestamp: () => `,"time":"${new Date().toISOString()}"`
});

const token = config.telegramBotToken;
let bot;

// Состояния: chatId -> { step, transcript }
const userStates = new Map();

console.log('🚀 Meeting Bot запущен и готов к работе');

if (token) {
  try {
    bot = new TelegramBot(token, { polling: true });
    logger.info('🚀 Telegram Bot запущен в режиме polling');
    logger.info('📱 Telegram Bot активен');
    logger.info('🌐 Health check: http://localhost:3000/health');

    // /start
    bot.onText(/\/start/, (msg) => {
      bot.sendMessage(msg.chat.id, '🤖 Отправьте транскрипт встречи для анализа.');
    });

    bot.on('message', async (msg) => {
      const chatId = msg.chat.id;
      const text = msg.text?.trim();
      if (!text || text.startsWith('/')) return;

      const state = userStates.get(chatId);

      // Шаг 1: транскрипт
      if (!state) {
        userStates.set(chatId, { step: 'awaitingLeadId', transcript: text });
        logger.info(`Чат ${chatId}: транскрипт сохранён`);
        await bot.sendMessage(chatId, '✅ Транскрипт принят. Теперь отправьте ID лида в Bitrix24:');
        return;
      }

      // Шаг 2: ID лида → анализ → обновление → задача
      if (state.step === 'awaitingLeadId') {
        if (!/^[0-9]+$/.test(text)) {
          await bot.sendMessage(chatId, '❌ ID лида должен быть числом. Попробуйте снова:');
          return;
        }

        const leadId = text;
        logger.info(`Чат ${chatId}: получен ID лида ${leadId}`);

        try {
          await bot.sendMessage(chatId, '🔄 Анализирую транскрипт...');
          const analysisResult = await runChecklist(state.transcript, logger);

          // Формируем отчёт
          const report = formatAnalysisReport(analysisResult);

          // Обновляем лид
          logger.info(`Обновляю лид ${leadId} через Bitrix24 webhook...`);
          await bitrixService.updateLead(leadId, analysisResult, state.transcript, 'Telegram Bot', logger);
          logger.info({ leadId }, '✅ Лид успешно обновлён в Bitrix');

          // Создаём задачу
          try {
            const taskTitle = `Анализ встречи по лиду ${leadId} (${analysisResult.category || '—'})`;
            const { taskId } = await bitrixService.createTask({
              title: taskTitle,
              description: report,
              leadId,
              source: 'Telegram Bot'
            }, logger);
            logger.info({ leadId, taskId }, '📌 Задача создана и привязана к лиду');
          } catch (taskErr) {
            logger.warn({ leadId, error: taskErr.message }, 'Не удалось создать задачу');
          }

          // Отправляем отчёт менеджеру
          for (const part of splitMessage(report)) {
            await bot.sendMessage(chatId, part, { parse_mode: 'Markdown' });
          }

        } catch (err) {
          logger.error({ err }, 'Ошибка анализа или обновления лида');
          await bot.sendMessage(chatId, `❌ Ошибка: ${err.message}`);
        } finally {
          userStates.delete(chatId);
          logger.info(`Чат ${chatId}: процесс завершён, состояние сброшено`);
        }
      }
    });

    bot.on('polling_error', (error) => logger.error({ error }, 'Polling error'));
    bot.on('webhook_error', (error) => logger.error({ error }, 'Webhook error'));

  } catch (error) {
    logger.error({ error }, 'Failed to initialize Telegram bot');
  }
} else {
  logger.warn('TELEGRAM_BOT_TOKEN не задан. Бот не запущен.');
}

// Красивый отчёт для менеджера
function formatAnalysisReport(a) {
  return `
📊 *РЕЗУЛЬТАТЫ АНАЛИЗА ВСТРЕЧИ*

1. *Анализ бизнеса:* ${a.businessAnalysis || 'Компания предоставляет услуги; требуется уточнение бизнес-модели.'}
2. *Боли и потребности:* ${a.painPoints || '—'}
3. *Возражения:* ${a.objections || '—'}
4. *Реакция на модель:* ${a.clientReaction || '—'}
5. *Особый интерес к сервису:* ${a.serviceInterest || '—'}
6. *Найденные возможности:* ${a.opportunities || '—'}
7. *Ошибки менеджера:* ${a.managerErrors || '—'}
8. *Путь к закрытию:* ${a.closingPath || '—'}
9. *Тон беседы:* ${a.tone || '—'}
10. *Контроль диалога:* ${a.dialogControl || '—'}
11. *Рекомендации:* ${a.recommendations || a.priorityAction || '—'}
12. *Категория клиента:* ${a.category || '—'} (вероятность ${a.probability ?? '—'}%)

*Отрасль:* ${a.industry || '—'}
*Ключевые лица:* ${a.decisionMakers || '—'}
*Сроки решения:* ${a.decisionTimeline || '—'}
*Бюджет:* ${a.budget || '—'}
*Приоритет:* ${a.priorityAction || '—'}

🧾 *Сводка:*
${a.summary || '—'}
`.trim();
}

// Разделение длинных сообщений
function splitMessage(message, maxLength = 4000) {
  if (message.length <= maxLength) return [message];
  const parts = [];
  let current = '';
  for (const line of message.split('\n')) {
    if ((current + line + '\n').length > maxLength) {
      parts.push(current.trim());
      current = '';
    }
    current += line + '\n';
  }
  if (current.trim()) parts.push(current.trim());
  return parts;
}

export default bot;
