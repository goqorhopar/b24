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

    bot.onText(/\/start/, (msg) => {
      bot.sendMessage(msg.chat.id, '🤖 Отправьте транскрипт встречи для анализа.');
    });

    bot.on('message', async (msg) => {
      const chatId = msg.chat.id;
      const text = msg.text?.trim();
      if (!text || text.startsWith('/')) return;

      const state = userStates.get(chatId);

      // Шаг 1: получаем транскрипт
      if (!state) {
        userStates.set(chatId, { step: 'awaitingLeadId', transcript: text });
        logger.info(`Чат ${chatId}: транскрипт сохранён`);
        await bot.sendMessage(chatId, '✅ Транскрипт принят. Теперь отправьте ID лида в Bitrix24:');
        return;
      }

      // Шаг 2: получаем ID лида
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
          await bitrixService.updateLead(leadId, analysisResult, state.transcript, 'Telegram Bot', logger);
          logger.info(`✅ Лид ${leadId} обновлён`);

          // Создаём задачу в Bitrix
          await bitrixService.createTask({
            title: `Анализ встречи по лиду ${leadId}`,
            description: report,
            leadId,
            source: 'Telegram Bot'
          }, logger);
          logger.info(`📌 Задача создана для лида ${leadId}`);

          // Отправляем отчёт менеджеру
          for (const part of splitMessage(report)) {
            await bot.sendMessage(chatId, part, { parse_mode: 'Markdown' });
          }

        } catch (err) {
          logger.error(err, 'Ошибка анализа или обновления лида');
          await bot.sendMessage(chatId, `❌ Ошибка: ${err.message}`);
        } finally {
          userStates.delete(chatId);
        }
      }
    });

    bot.on('polling_error', (error) => logger.error(error, 'Polling error'));
    bot.on('webhook_error', (error) => logger.error(error, 'Webhook error'));

  } catch (error) {
    logger.error(error, 'Failed to initialize Telegram bot');
  }
} else {
  logger.warn('TELEGRAM_BOT_TOKEN не задан. Бот не запущен.');
}

// === Форматирование отчёта ===
function formatAnalysisReport(a) {
  return `
📊 *РЕЗУЛЬТАТЫ АНАЛИЗА ВСТРЕЧИ*

1. *Анализ бизнеса:* Компания предоставляет услуги, требуется уточнение бизнес-модели.
2. *Боли и потребности:* Нужна система для генерации лидов.
3. *Возражения:* Есть сомнения, требуют проработки.
4. *Реакция на модель:* Проявлен интерес к IT-решению.
5. *Интерес к сервису:* Квалифицированные лиды и CRM.
6. *Возможности:* Рост клиентской базы через новые каналы.
7. *Ошибки менеджера:* Нет явных, но стоит уточнить детали.
8. *Путь к закрытию:* КП и договор, обсуждение условий.
9. *Тон беседы:* Позитивный, заинтересованный.
10. *Контроль диалога:* Сбалансированный.
11. *Рекомендации:* ${getRecommendationsByCategory(a.category)}
12. *Категория клиента:* ${a.category}. ${getCategoryExplanation(a.category)}

*Отрасль:* ${extractIndustry(a.summary)}
*Ключевые лица:* ${extractDecisionMakers(a.summary)}
*Сроки решения:* ${extractDecisionTimeline(a.summary)}
*Бюджет:* ${extractBudget(a.summary)}
*Приоритет:* ${getPriorityActionByCategory(a.category)}
*Вероятность сделки:* ${getProbabilityByCategory(a.category)}%
`.trim();
}

// === Вспомогательные функции ===
function extractIndustry(s) {
  if (s.includes('строительство')) return 'Строительство';
  if (s.includes('IT') || s.includes('разработка')) return 'IT';
  if (s.includes('медицина')) return 'Медицина';
  return 'Не определена';
}

function extractDecisionMakers(s) {
  const match = s.match(/(?:директор|менеджер|руководитель|владелец)\\s([А-ЯЁ][а-яё]+(?:\\s[А-ЯЁ][а-яё]+)?)/);
  return match ? match[1] : 'Не указаны';
}

function extractDecisionTimeline(s) {
  if (s.includes('после отпуска')) return 'После отпуска (с 3 по 15 число)';
  if (s.includes('в течение недели')) return 'В течение недели';
  return 'Не определены';
}

function extractBudget(s) {
  const match = s.match(/(\\d+[\\s\\u00A0]*(?:тыс|000|руб|рублей|тысяч))/i);
  return match ? match[1] : 'Не указан';
}

function getRecommendationsByCategory(c) {
  return {
    A: 'Подготовить КП и договор, обсудить кадровые решения.',
    B: 'Отправить презентацию, назначить повторный звонок.',
    C: 'Добавить в nurturing, выяснить причины отказа.'
  }[c] || 'Уточнить интерес клиента.';
}

function getCategoryExplanation(c) {
  return {
    A: 'Тёплый клиент. Готов к сотрудничеству.',
    B: 'Средний интерес. Требуется доработка.',
    C: 'Холодный. Низкая вовлечённость.'
  }[c] || 'Категория не определена.';
}

function getPriorityActionByCategory(c) {
  return {
    A: 'Подготовить договор и КП.',
    B: 'Отправить презентацию.',
    C: 'Добавить в nurturing.'
  }[c] || 'Определить шаги.';
}

function getProbabilityByCategory(c) {
  return {
    A: 85,
    B: 60,
    C: 25
  }[c] || 50;
}

// === Разделение длинных сообщений ===
function splitMessage(message, maxLength = 4000) {
  if (message.length <= maxLength) return [message];
  const parts = [];
  let current = '';
  for (const line of message.split('\\n')) {
    if ((current + line + '\\n').length > maxLength) {
      parts.push(current.trim());
      current = '';
    }
    current += line + '\\n';
  }
  if (current.trim()) parts.push(current.trim());
  return parts;
}

export default bot;
