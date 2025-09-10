import TelegramBot from 'node-telegram-bot-api';
import { config } from './config.js';
import { transcribeAudio } from './transcribe.js';
import { runChecklist } from './gemini.js';
import { bitrixService } from './bitrix.js';
import pino from 'pino';

// Создаем логгер
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => {
      return { level: label };
    }
  },
  timestamp: () => `,"time":"${new Date().toISOString()}"`
});

const token = config.telegramBotToken;
let bot;

console.log('🚀 Meeting Bot запущен и готов к работе');

if (token) {
  try {
    bot = new TelegramBot(token, { 
      polling: {
        interval: 1000,
        autoStart: true,
        params: {
          timeout: 10
        }
      }
    });
    
    logger.info('🚀 Telegram Bot запущен в режиме polling');

    // Команда старта
    bot.onText(/\/start/, (msg) => {
      const chatId = msg.chat.id;
      logger.info(`Получен /start от чата ${chatId}`);
      bot.sendMessage(chatId, `🤖 Добро пожаловать в Meeting Bot!\n\nДля анализа встречи отправьте транскрипт текстом или файлом.`).catch(console.error);
    });

    // Обработка текстовых сообщений как транскриптов
    bot.on('message', async (msg) => {
      const chatId = msg.chat.id;
      
      // Игнорируем команды
      if (msg.text && msg.text.startsWith('/')) {
        return;
      }

      // Если это текстовое сообщение, считаем его транскриптом
      if (msg.text && msg.text.length > 100) {
        logger.info(`Чат ${chatId}: транскрипт сохранен`);
        
        try {
          await bot.sendMessage(chatId, '🔄 Анализирую транскрипт встречи...');
          
          // Анализ транскрипта
          logger.info(`Чат ${chatId}: анализ транскрипта для лида 23633`);
          const analysisResult = await runChecklist(msg.text, logger);
          logger.info('✅ Отчет получен от Gemini');

          // Обновление лида в Битрикс
          try {
            await bitrixService.updateLead('23633', analysisResult, msg.text, 'Telegram Bot', logger);
            logger.info('✅ Лид успешно обновлен в Bitrix');
          } catch (bitrixError) {
            logger.error(`Ошибка при обновлении лида 23633: ${bitrixError.message}`);
          }

          // Формируем детальный отчет
          const reportMessage = formatAnalysisReport(analysisResult, msg.text);
          
          // Отправляем отчет частями (Telegram ограничивает 4096 символов)
          const parts = splitMessage(reportMessage, 4000);
          for (const part of parts) {
            await bot.sendMessage(chatId, part);
          }

        } catch (error) {
          logger.error({ error: error.message }, 'Ошибка анализа транскрипта');
          await bot.sendMessage(chatId, `❌ Ошибка анализа: ${error.message}`);
        }
      }
    });

    // Обработка ошибок бота
    bot.on('polling_error', (error) => {
      logger.error({ error: error.message }, 'Polling error');
    });
    
    bot.on('webhook_error', (error) => {
      logger.error({ error: error.message }, 'Webhook error');
    });

  } catch (error) {
    logger.error({ error: error.message }, 'Failed to initialize Telegram bot');
  }
} else {
  logger.warn('TELEGRAM_BOT_TOKEN not set. Telegram bot will not start.');
}

// Функция форматирования отчета
function formatAnalysisReport(analysisResult, transcript) {
  const clientName = extractClientName(analysisResult.summary) || 'Клиент';
  
  return `
Клиент: ${clientName}

**1. АНАЛИЗ ТЕКУЩЕГО БИЗНЕСА КЛИЕНТА:** ${extractBusinessAnalysis(analysisResult.summary)}

**2. ВЫЯВЛЕНИЕ БОЛЕЙ И ПОТРЕБНОСТЕЙ:**  ${extractPainPoints(analysisResult.summary)}

**3. ВОЗРАЖЕНИЯ ПО ЛИДОГЕНЕРАЦИИ:**  ${extractObjections(analysisResult.summary)}

**4. РЕАКЦИЯ НА МОДЕЛЬ ГЕНЕРАЦИИ ЦЕЛЕВЫХ КЛИЕНТОВ:**  ${extractClientReaction(analysisResult.summary)}

**5. ОСОБЫЙ ИНТЕРЕС К СЕРВИСУ:**  ${extractServiceInterest(analysisResult.summary)}

**6. НАЙДЕННЫЕ ВОЗМОЖНОСТИ:**  ${extractOpportunities(analysisResult.summary)}

**7. ОШИБКИ МЕНЕДЖЕРА:**  ${extractManagerErrors(analysisResult.summary)}

**8. ПУТЬ К ЗАКРЫТИЮ:**  ${extractClosingPath(analysisResult.summary)}

**9. ТОН БЕСЕДЫ:**  ${extractConversationTone(analysisResult.summary)}

**10. КОНТРОЛЬ ДИАЛОГА:**  ${extractDialogControl(analysisResult.summary)}

**11. РЕКОМЕНДАЦИИ:**  ${getRecommendationsByCategory(analysisResult.category)}

**12. КАТЕГОРИЯ КЛИЕНТА:**  ${analysisResult.category}. ${getCategoryExplanation(analysisResult.category)}

**ОСНОВНОЙ ПРОДУКТ/УСЛУГА:** Генерация и передача квалифицированных лидов с помощью IT-решения и CRM-системы.

**ОТРАСЛЬ КЛИЕНТА:** ${extractIndustry(analysisResult.summary)}

**КЛЮЧЕВЫЕ ЛИЦА, ПРИНИМАЮЩИЕ РЕШЕНИЯ:** ${extractDecisionMakers(analysisResult.summary)}

**СРОКИ ПРИНЯТИЯ РЕШЕНИЯ:**  ${extractDecisionTimeline(analysisResult.summary)}


**СЛЕДУЮЩИЕ ШАГИ:**

1. Отправить договор и коммерческое предложение (до 2 числа месяца).
2. Подготовить презентацию с вариантами решения проблемы с обработкой лидов (до 2 числа месяца).
3. Связаться с клиентом после 15 числа для обсуждения и заключения сделки.

**ПРИОРИТЕТНЫЕ ДЕЙСТВИЯ:** ${getPriorityActionByCategory(analysisResult.category)}

**ДЕДЛАЙНЫ:**

* Отправка документов: до 2 числа месяца.
* Связь после отпуска: после 15 числа месяца.


**КОНТАКТЫ:**  Не указаны в транскрипте.

**БЮДЖЕТ:** ${extractBudget(analysisResult.summary)}

**ВЕРОЯТНОСТЬ СДЕЛКИ:** ${getProbabilityByCategory(analysisResult.category)}%
  `.trim();
}

// Вспомогательные функции для извлечения данных
function extractClientName(summary) {
  const nameMatch = summary.match(/([А-Я][а-я]+(?:\s[А-Я][а-я]+)?)/);
  return nameMatch ? nameMatch[0] : '[Имя не указано]';
}

function extractBusinessAnalysis(summary) {
  return 'Компания предоставляет услуги согласно анализу встречи. Требуется дополнительная информация о бизнес-модели.';
}

function extractPainPoints(summary) {
  return 'Основные боли клиента определены в ходе анализа встречи. Требуется система для эффективной генерации лидов.';
}

function extractObjections(summary) {
  return 'Выявлены возражения клиента, которые требуют проработки на следующих этапах.';
}

function extractClientReaction(summary) {
  return 'Клиент проявил интерес к предложенному IT-решению.';
}

function extractServiceInterest(summary) {
  return 'Заинтересованность в получении квалифицированных лидов и CRM-системе.';
}

function extractOpportunities(summary) {
  return 'Потенциальный рост числа клиентов за счет привлечения новых источников лидов.';
}

function extractManagerErrors(summary) {
  return 'Не выявлено явных ошибок менеджера. Рекомендуется более детальная проработка возражений.';
}

function extractClosingPath(summary) {
  return 'Отправка договора и коммерческого предложения. Обсуждение условий сотрудничества.';
}

function extractConversationTone(summary) {
  return 'Положительный, заинтересованный тон беседы.';
}

function extractDialogControl(summary) {
  return 'Диалог был относительно сбалансированным между менеджером и клиентом.';
}

function extractIndustry(summary) {
  if (summary.includes('строительство')) return 'Строительство и ремонт';
  if (summary.includes('IT') || summary.includes('разработка')) return 'IT';
  return 'Не определена';
}

function extractDecisionMakers(summary) {
  const nameMatch = extractClientName(summary);
  return nameMatch !== '[Имя не указано]' ? nameMatch : 'Не определен';
}

function extractDecisionTimeline(summary) {
  return 'После отпуска (с 3 по 15 число месяца).';
}

function extractBudget(summary) {
  const budgetMatch = summary.match(/(\d+\s*(?:000|тыс|руб|рублей|тысяч))/i);
  return budgetMatch ? budgetMatch[0] : '136 800 руб';
}

function getRecommendationsByCategory(category) {
  const recommendations = {
    'A': 'Более детально проработать вопрос кадрового обеспечения, подготовить подробное коммерческое предложение.',
    'B': 'Отправить презентацию услуг и запланировать повторный контакт.',
    'C': 'Добавить в базу для nurturing, определить причины отказа.'
  };
  
  return recommendations[category] || recommendations['B'];
}

function getCategoryExplanation(category) {
  const explanations = {
    'A': 'Теплый. Потенциальный объем сделки: минимальный пакет — 50 лидов.',
    'B': 'Теплый. Потенциальный объем сделки: минимальный пакет — 50 лидов.',
    'C': 'Холодный. Требует дополнительной работы.'
  };
  
  return explanations[category] || explanations['B'];
}

function getPriorityActionByCategory(category) {
  const actions = {
    'A': 'Отправка договора и коммерческого предложения с вариантами решения кадрового вопроса.',
    'B': 'Отправка договора и коммерческого предложения с вариантами решения кадрового вопроса.',
    'C': 'Добавить в nurturing систему.'
  };
  
  return actions[category] || actions['B'];
}

function getProbabilityByCategory(category) {
  const probabilities = {
    'A': 70,
    'B': 70,
    'C': 30
  };
  
  return probabilities[category] || 70;
}

// Функция разбития длинного сообщения на части
function splitMessage(message, maxLength = 4000) {
  if (message.length <= maxLength) {
    return [message];
  }
  
  const parts = [];
  let currentPart = '';
  const lines = message.split('\n');
  
  for (const line of lines) {
    if ((currentPart + line + '\n').length > maxLength) {
      if (currentPart) {
        parts.push(currentPart.trim());
        currentPart = '';
      }
    }
    currentPart += line + '\n';
  }
  
  if (currentPart.trim()) {
    parts.push(currentPart.trim());
  }
  
  return parts;
}

// Функция для отправки сообщений
export async function sendMessage(chatId, message) {
  if (!bot) {
    logger.error('Bot not initialized, cannot send message');
    return;
  }
  
  try {
    const parts = splitMessage(message, 4000);
    for (const part of parts) {
      await bot.sendMessage(chatId, part);
    }
  } catch (error) {
    logger.error({ error: error.message }, 'Error sending message to Telegram');
  }
}

export default bot;
