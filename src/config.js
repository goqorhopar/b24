// src/config.js

export const config = {
  // Telegram
  telegramBotToken: process.env.TELEGRAM_BOT_TOKEN,

  // Bitrix
  bitrixWebhookUrl: process.env.BITRIX_WEBHOOK_URL, // например: https://<domain>.bitrix24.ru/rest/<user>/<token>
  bitrixResponsibleId: process.env.BITRIX_RESPONSIBLE_ID, // ID ответственного за задачи
  bitrixCreatedById: process.env.BITRIX_CREATED_BY_ID || process.env.BITRIX_RESPONSIBLE_ID,
  bitrixTaskDefaultDeadlineDays: process.env.BITRIX_TASK_DEADLINE_DAYS || 3,

  // Gemini / LLM
  geminiApiKey: process.env.GEMINI_API_KEY,
  geminiModel: process.env.GEMINI_MODEL || 'gemini-1.5-pro',

  // Маппинг пользовательских полей лида (замени пустые строки на реальные UF_* коды)
  // Названия взяты с интерфейса карточки лида, который ты показал: «Что продает», «Кто проводит встречу?», «План дата встречи» и т.д.
  leadFieldMap: {
    // Примеры. Обнови значениями реальных UF_* кодов из CRM → Настройки → Настраиваемые поля
    UF_WHAT_SELLS: '',             // "Что продает"
    UF_MEETING_HOST: '',           // "Кто проводит встречу?"
    UF_MEETING_PLANNED_AT: '',     // "План дата встречи" (тип Дата/Время)
    UF_INDUSTRY: '',               // "Отрасль" (строка/список)
    UF_DECISION_MAKERS: '',        // "Ключевые лица" (строка/текст)
    UF_DECISION_TIMELINE: '',      // "Сроки принятия решения" (строка/текст)
    UF_BUDGET: '',                 // "Бюджет" (строка/число)
    UF_CATEGORY: '',               // "Категория клиента" (строка/список: A/B/C)
    UF_PRIORITY_ACTION: '',        // "Приоритетные действия" (строка/текст)
    UF_PROBABILITY: '',            // "Вероятность сделки" (число)
    UF_TONE: '',                   // "Тон беседы" (строка)
    UF_DIALOG_CONTROL: '',         // "Контроль диалога" (строка)
    UF_OBJECTIONS: ''              // "Возражения" (текст)
  }
};
