// src/config.js

// Проверка обязательных переменных окружения
const requiredEnvVars = ['TELEGRAM_BOT_TOKEN', 'BITRIX_WEBHOOK_URL', 'GEMINI_API_KEY', 'BITRIX_RESPONSIBLE_ID'];
const missingEnvVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingEnvVars.length > 0) {
  console.error(`❌ Отсутствуют обязательные переменные окружения: ${missingEnvVars.join(', ')}`);
  process.exit(1);
}

// BITRIX_RESPONSIBLE_ID - обязательный для создания задач
const responsibleId = Number(process.env.BITRIX_RESPONSIBLE_ID);
if (isNaN(responsibleId)) {
  console.error('❌ BITRIX_RESPONSIBLE_ID должен быть числом');
  process.exit(1);
}

const deadlineDays = Number(process.env.BITRIX_TASK_DEADLINE_DAYS || 3);
if (isNaN(deadlineDays) || deadlineDays <= 0) {
  console.error('❌ BITRIX_TASK_DEADLINE_DAYS должен быть положительным числом');
  process.exit(1);
}

// Порт для сервера
const port = Number(process.env.PORT || 3000);

// ADMIN_CHAT_ID - опциональный, для уведомлений администратора
const adminChatId = process.env.ADMIN_CHAT_ID ? Number(process.env.ADMIN_CHAT_ID) : null;

/*
  НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:

  1. Telegram Bot Token - получить у @BotFather
  TELEGRAM_BOT_TOKEN=your_telegram_bot_token

  2. Bitrix24 Webhook URL - создать входящий вебхук в Bitrix24
  BITRIX_WEBHOOK_URL=https://your_domain.bitrix24.ru/rest/1/your_webhook_token

  3. Bitrix Responsible User ID - ID пользователя для назначения задач (ОБЯЗАТЕЛЬНО)
  BITRIX_RESPONSIBLE_ID=123

  4. Gemini API Key - получить в Google AI Studio
  GEMINI_API_KEY=your_gemini_api_key

  5. Admin Chat ID - ID чата для уведомлений администратора
  ADMIN_CHAT_ID=123456789

  6. Опционально: переопределите коды полей лида, если они отличаются в вашем Bitrix24
  UF_WHAT_SELLS=UF_CRM_CUSTOM_FIELD
  UF_MEETING_HOST=UF_CRM_ANOTHER_FIELD
  ...
*/

export const config = {
  /* ===========================
     🔹 Server
     =========================== */
  port: port,

  /* ===========================
     🔹 Telegram
     =========================== */
  // Токен Telegram-бота от @BotFather
  telegramBotToken: process.env.TELEGRAM_BOT_TOKEN,

  // ID чата администратора для уведомлений
  adminChatId: adminChatId,

  /* ===========================
     🔹 Bitrix24
     =========================== */
  // Полный URL входящего вебхука Bitrix24
  bitrixWebhookUrl: process.env.BITRIX_WEBHOOK_URL,

  // ID пользователя, на кого будут назначаться задачи (ОБЯЗАТЕЛЬНО)
  bitrixResponsibleId: responsibleId,

  // ID пользователя, от имени которого будут создаваться задачи (по умолчанию = ответственному)
  bitrixCreatedById: process.env.BITRIX_CREATED_BY_ID ? Number(process.env.BITRIX_CREATED_BY_ID) : responsibleId,

  // Количество дней по умолчанию до дедлайна задачи
  bitrixTaskDefaultDeadlineDays: deadlineDays,

  /* ===========================
     🔹 Gemini / LLM
     =========================== */
  // API-ключ Gemini
  geminiApiKey: process.env.GEMINI_API_KEY,

  // Модель Gemini
  geminiModel: process.env.GEMINI_MODEL || 'gemini-1.5-flash',

  /* ===========================
     🔹 Маппинг пользовательских полей лида
     =========================== */
  // Здесь указываем реальные UF_* коды из Bitrix24, чтобы бот мог заполнять эти поля напрямую
  leadFieldMap: {
    UF_WHAT_SELLS: process.env.UF_WHAT_SELLS || 'UF_CRM_1726143451',         // Что продает
    UF_MEETING_HOST: process.env.UF_MEETING_HOST || 'UF_CRM_1726143462',       // Кто проводит встречу?
    UF_MEETING_PLANNED_AT: process.env.UF_MEETING_PLANNED_AT || 'UF_CRM_1726143473', // План дата встречи (datetime)
    UF_INDUSTRY: process.env.UF_INDUSTRY || 'UF_CRM_1726143484',           // Отрасль
    UF_DECISION_MAKERS: process.env.UF_DECISION_MAKERS || 'UF_CRM_1726143495',    // Ключевые лица
    UF_DECISION_TIMELINE: process.env.UF_DECISION_TIMELINE || 'UF_CRM_1726143506',  // Сроки принятия решения
    UF_BUDGET: process.env.UF_BUDGET || 'UF_CRM_1726143517',             // Бюджет
    UF_CATEGORY: process.env.UF_CATEGORY || 'UF_CRM_1726143528',           // Категория клиента (A/B/C)
    UF_PRIORITY_ACTION: process.env.UF_PRIORITY_ACTION || 'UF_CRM_1726143539',    // Приоритетные действий
    UF_PROBABILITY: process.env.UF_PROBABILITY || 'UF_CRM_1726143550',        // Вероятность сделки (число)
    UF_TONE: process.env.UF_TONE || 'UF_CRM_1726143561',               // Тон беседы
    UF_DIALOG_CONTROL: process.env.UF_DIALOG_CONTROL || 'UF_CRM_1726143572',     // Контроль диалога
    UF_OBJECTIONS: process.env.UF_OBJECTIONS || 'UF_CRM_1726143583'          // Возражения
  }
};
