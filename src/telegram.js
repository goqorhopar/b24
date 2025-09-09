import TelegramBot from 'node-telegram-bot-api';
import logger from './logger.js';
import { analyzeTranscript } from './checklist.js';
import { updateLead } from './bitrix.js';

const bot = new TelegramBot(process.env.TELEGRAM_TOKEN, { polling: true });

// Временное хранилище данных по каждому чату
const context = {};

bot.on('message', async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text?.trim();

  if (!text) return;

  // Если сообщение — это число → считаем ID лида
  if (/^\d+$/.test(text)) {
    if (!context[chatId]?.transcript) {
      await bot.sendMessage(chatId, "⚠️ Сначала отправь транскрипт встречи, затем ID лида.");
      return;
    }

    const leadId = text;
    const transcript = context[chatId].transcript;

    await bot.sendMessage(chatId, `✅ Получен ID лида: ${leadId}. Запускаю анализ транскрипта...`);
    logger.info(`Чат ${chatId}: анализ транскрипта для лида ${leadId}`);

    try {
      const report = await analyzeTranscript(transcript);
      await bot.sendMessage(chatId, `📋 Отчет по встрече:\n\n${report}`);

      await updateLead(report, leadId);
      await bot.sendMessage(chatId, `🔥 Лид #${leadId} обновлен в Bitrix24`);
    } catch (err) {
      logger.error(err);
      await bot.sendMessage(chatId, "❌ Ошибка при обработке транскрипта или обновлении лида.");
    }

    // очистка контекста после завершения
    delete context[chatId];
    return;
  }

  // Если сообщение длинное → сохраняем как транскрипт
  if (text.length > 200) {
    context[chatId] = { transcript: text };
    await bot.sendMessage(chatId, "📄 Транскрипт сохранен. Теперь отправь ID лида отдельным сообщением.");
    logger.info(`Чат ${chatId}: транскрипт сохранен`);
    return;
  }

  // Если сообщение не подходит
  await bot.sendMessage(chatId, "Отправь сначала полный транскрипт встречи, затем ID лида отдельным сообщением.");
});
