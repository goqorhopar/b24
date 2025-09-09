import TelegramBot from 'node-telegram-bot-api';
import express from 'express';
import logger from './logger.js';
import { analyzeTranscript } from './checklist.js';
import { updateLead } from './bitrix.js';

const app = express();
app.use(express.json());

const bot = new TelegramBot(process.env.TELEGRAM_TOKEN);
const PORT = process.env.PORT || 3000;

// Устанавливаем webhook при запуске
async function setupWebhook() {
  try {
    const webhookUrl = `${process.env.RENDER_EXTERNAL_URL}/bot${process.env.TELEGRAM_TOKEN}`;
    await bot.setWebHook(webhookUrl);
    logger.info(`Webhook установлен: ${webhookUrl}`);
  } catch (error) {
    logger.error(`Ошибка установки webhook: ${error.message}`);
  }
}

// Обработчик webhook
app.post(`/bot${process.env.TELEGRAM_TOKEN}`, (req, res) => {
  bot.processUpdate(req.body);
  res.sendStatus(200);
});

// Временное хранилище данных по каждому чату
const context = {};

bot.on('message', async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text?.trim();

  if (!text) return;

  try {
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
        await bot.sendMessage(chatId, `📋 Отчет по встрече:\n\n${report.substring(0, 4000)}...`);
        
        // Добавляем задержку перед обновлением лида
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        await updateLead(report, leadId);
        await bot.sendMessage(chatId, `🔥 Лид #${leadId} обновлен в Bitrix24 с полной информацией и задачами!`);
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
  } catch (error) {
    logger.error(`Error processing message: ${error.message}`);
  }
});

// Запускаем сервер
app.listen(PORT, async () => {
  logger.info(`🚀 Сервер запущен на порту ${PORT}`);
  await setupWebhook();
});

// Обработчик закрытия процесса
process.on('SIGINT', () => {
  logger.info('Останавливаем бота...');
  process.exit();
});
