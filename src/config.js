// src/config.js

export const config = {
  /* ===========================
     🔹 Telegram
     =========================== */
  // Токен Telegram-бота от @BotFather
  telegramBotToken: process.env.TELEGRAM_BOT_TOKEN,

  /* ===========================
     🔹 Bitrix24
     =========================== */
  // Полный URL входящего вебхука Bitrix24
  // Пример: https://skill-to-lead.bitrix24.ru/rest/1403/<webhook_token>
  bitrixWebhookUrl: process.env.BITRIX_WEBHOOK_URL,

  // ID пользователя, на кого будут назначаться задачи
  bitrixResponsibleId: process.env.BITRIX_RESPONSIBLE_ID,

  // ID пользователя, от имени которого будут создаваться задачи (по умолчанию = ответственному)
  bitrixCreatedById: process.env.BITRIX_CREATED_BY_ID || process.env.BITRIX_RESPONSIBLE_ID,

  // Количество дней по умолчанию до дедлайна задачи
  bitrixTaskDefaultDeadlineDays: Number(process.env.BITRIX_TASK_DEADLINE_DAYS || 3),

  /* ===========================
     🔹 Gemini / LLM
     =========================== */
  // API-ключ Gemini
  geminiApiKey: process.env.GEMINI_API_KEY,

  // Модель Gemini
  geminiModel: process.env.GEMINI_MODEL || 'gemini-1.5-pro',

  /* ===========================
     🔹 Маппинг пользовательских полей лида
     =========================== */
  // Здесь указываем реальные UF_* коды из Bitrix24, чтобы бот мог заполнять эти поля напрямую
  leadFieldMap: {
    UF_WHAT_SELLS: 'UF_CRM_1726143451',         // Что продает
    UF_MEETING_HOST: 'UF_CRM_1726143462',       // Кто проводит встречу?
    UF_MEETING_PLANNED_AT: 'UF_CRM_1726143473', // План дата встречи (datetime)
    UF_INDUSTRY: 'UF_CRM_1726143484',           // Отрасль
    UF_DECISION_MAKERS: 'UF_CRM_1726143495',    // Ключевые лица
    UF_DECISION_TIMELINE: 'UF_CRM_1726143506',  // Сроки принятия решения
    UF_BUDGET: 'UF_CRM_1726143517',             // Бюджет
    UF_CATEGORY: 'UF_CRM_1726143528',           // Категория клиента (A/B/C)
    UF_PRIORITY_ACTION: 'UF_CRM_1726143539',    // Приоритетные действия
    UF_PROBABILITY: 'UF_CRM_1726143550',        // Вероятность сделки (число)
    UF_TONE: 'UF_CRM_1726143561',               // Тон беседы
    UF_DIALOG_CONTROL: 'UF_CRM_1726143572',     // Контроль диалога
    UF_OBJECTIONS: 'UF_CRM_1726143583'          // Возражения
  }
};
