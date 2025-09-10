export const config = {
  port: process.env.PORT || 3000,
  chromiumPath: process.env.CHROME_BIN || '/usr/bin/google-chrome-stable',
  geminiApiKey: process.env.GEMINI_API_KEY,
  recording: {
    outDir: process.env.REC_DIR || '/tmp/recordings',
    maxSeconds: Number(process.env.REC_MAX_SECONDS || 3600)
  },
  telegramBotToken: process.env.TELEGRAM_BOT_TOKEN,
  adminChatId: process.env.ADMIN_CHAT_ID,
  webhookUrl: process.env.RENDER_EXTERNAL_URL || 'https://b24.onrender.com',
  
  // Настройки Битрикс24 (из логов)
  bitrix: {
    // Базовый URL Битрикс24
    baseUrl: 'https://skill-to-lead.bitrix24.ru',
    
    // ID пользователя для webhook
    userId: '1403',
    
    // Ключ webhook
    webhookKey: 'cmf3ncejqif8ny31',
    
    // ID ответственного за лиды
    responsibleId: process.env.BITRIX_RESPONSIBLE_ID || '1',
    
    // Дополнительные настройки
    timeout: 30000, // 30 секунд таймаут
    retryAttempts: 3, // Количество попыток
    
    // Маппинг статусов
    statusMapping: {
      'NEW': 'NEW',
      'IN_PROCESS': 'IN_PROCESS', 
      'PROCESSED': 'PROCESSED',
      'JUNK': 'JUNK'
    },
    
    // Стандартные поля для безопасного обновления
    safeFields: [
      'TITLE',
      'NAME', 
      'LAST_NAME',
      'COMMENTS',
      'STATUS_ID',
      'SOURCE_DESCRIPTION',
      'CURRENCY_ID',
      'OPENED',
      'ASSIGNED_BY_ID'
    ]
  }
};
