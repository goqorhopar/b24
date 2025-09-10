import axios from 'axios';
import { config } from './config.js';

class BitrixService {
  constructor() {
    // Используем URL из ошибки в логе как базовый
    this.baseUrl = 'https://skill-to-lead.bitrix24.ru';
    this.userId = '1403';
    this.webhookKey = 'cmf3ncejqif8ny31';
    this.restUrl = `${this.baseUrl}/rest/${this.userId}/${this.webhookKey}`;
  }

  // Обновление лида результатами анализа встречи
  async updateLead(leadId, analysisResult, transcript, meetingUrl, logger) {
    try {
      logger.info(`Обновляю лид ${leadId} через Bitrix24 webhook...`);

      // Формируем базовые данные для обновления лида (только проверенные поля)
      const updateData = {
        id: leadId.toString(),
        fields: {
          // Базовые поля, которые точно существуют
          TITLE: this.extractClientName(analysisResult.summary) || `Клиент после встречи`,
          COMMENTS: this.formatLeadComment(analysisResult, transcript, meetingUrl),
          
          // Стандартные поля
          SOURCE_DESCRIPTION: "Создано через Telegram бота",
          OPENED: "Y",
          
          // Пытаемся установить статус
          STATUS_ID: this.getStatusByCategory(analysisResult.category),
          
          // Базовая информация
          CURRENCY_ID: "RUB"
        }
      };

      // Добавляем пользовательские поля только если они могут существовать
      const customFields = this.getCustomFields(analysisResult);
      
      // Осторожно добавляем кастомные поля
      Object.keys(customFields).forEach(key => {
        updateData.fields[key] = customFields[key];
      });

      logger.info({ leadId, fieldsCount: Object.keys(updateData.fields).length }, 'Подготовлены данные для обновления лида');

      // Обновляем лид
      const response = await axios.post(`${this.restUrl}/crm.lead.update.json`, updateData, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 30000
      });
      
      if (response.data && response.data.result) {
        logger.info({ leadId }, '✅ Лид успешно обновлен в Bitrix');
        
        // Пытаемся добавить активность (необязательно)
        try {
          await this.addLeadActivity(leadId, analysisResult, meetingUrl, logger);
        } catch (activityError) {
          logger.warn({ error: activityError.message }, 'Не удалось добавить активность, но лид обновлен');
        }
        
        return { success: true, leadId };
      } else {
        throw new Error(response.data?.error_description || 'Неизвестная ошибка Bitrix');
      }

    } catch (error) {
      logger.error({ 
        leadId, 
        error: error.message,
        response: error.response?.data,
        status: error.response?.status
      }, 'Ошибка при обновлении лида в Bitrix');
      
      // Если ошибка связана с полями, пробуем минимальное обновление
      if (error.response?.status === 400) {
        logger.warn('Попытка минимального обновления лида...');
        return await this.minimalLeadUpdate(leadId, analysisResult, logger);
      }
      
      throw new Error(`Ошибка обновления Bitrix: ${error.message}`);
    }
  }

  // Минимальное обновление лида только базовыми полями
  async minimalLeadUpdate(leadId, analysisResult, logger) {
    try {
      const minimalData = {
        id: leadId.toString(),
        fields: {
          COMMENTS: `Анализ встречи: ${analysisResult.summary}`,
          SOURCE_DESCRIPTION: "Обновлено через Meeting Bot"
        }
      };

      const response = await axios.post(`${this.restUrl}/crm.lead.update.json`, minimalData, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.data && response.data.result) {
        logger.info({ leadId }, '✅ Минимальное обновление лида выполнено');
        return { success: true, leadId };
      }
      
      throw new Error('Минимальное обновление не удалось');
    } catch (error) {
      logger.error({ error: error.message }, 'Минимальное обновление также не удалось');
      throw error;
    }
  }

  // Получение кастомных полей с проверкой
  getCustomFields(analysisResult) {
    const customFields = {};
    
    // Список возможных кастомных полей (добавляем только если они логичны)
    const possibleFields = {
      'UF_CRM_MEETING_SCORE': analysisResult.overallScore,
      'UF_CRM_CLIENT_CATEGORY': analysisResult.category,
      'UF_CRM_CLIENT_TYPE': 'Проанализированный',
      'UF_CRM_PROBABILITY': this.getProbabilityByCategory(analysisResult.category),
      'UF_CRM_BUDGET': this.extractBudget(analysisResult.summary),
      'UF_CRM_INDUSTRY': this.extractIndustry(analysisResult.summary),
      'UF_CRM_DECISION_MAKER': this.extractDecisionMaker(analysisResult.summary),
      'UF_CRM_NEXT_STEP': this.getNextStepByCategory(analysisResult.category),
      'UF_CRM_PRIORITY_ACTION': this.getPriorityActionByCategory(analysisResult.category)
    };

    // Добавляем только не пустые значения
    Object.keys(possibleFields).forEach(key => {
      const value = possibleFields[key];
      if (value !== null && value !== undefined && value !== '') {
        customFields[key] = value;
      }
    });

    return customFields;
  }

  // Добавление активности к лиду (упрощенная версия)
  async addLeadActivity(leadId, analysisResult, meetingUrl, logger) {
    try {
      const activityData = {
        fields: {
          OWNER_TYPE_ID: 1, // Лид
          OWNER_ID: leadId,
          TYPE_ID: 4, // Встреча
          SUBJECT: 'Анализ встречи через Meeting Bot',
          DESCRIPTION: this.formatActivityDescription(analysisResult, meetingUrl),
          COMPLETED: 'Y',
          RESPONSIBLE_ID: 1
        }
      };

      const response = await axios.post(`${this.restUrl}/crm.activity.add.json`, activityData);
      
      if (response.data && response.data.result) {
        logger.info({ leadId, activityId: response.data.result }, 'Активность добавлена к лиду');
        return response.data.result;
      }

    } catch (error) {
      logger.warn({ leadId, error: error.message }, 'Не удалось добавить активность к лиду');
      // Не бросаем исключение, так как это не критично
    }
  }

  // Извлечение имени клиента из анализа
  extractClientName(summary) {
    const nameMatch = summary.match(/[А-Я][а-я]+ [А-Я][а-я]+|[А-Я][а-я]+/);
    return nameMatch ? nameMatch[0] : null;
  }

  // Извлечение бюджета из анализа
  extractBudget(summary) {
    const budgetMatch = summary.match(/(\d+\s*(?:тыс|руб|рублей|тысяч))/i);
    return budgetMatch ? budgetMatch[0] : null;
  }

  // Извлечение отрасли из анализа
  extractIndustry(summary) {
    const industries = ['IT', 'Строительство', 'Торговля', 'Услуги', 'Производство'];
    for (const industry of industries) {
      if (summary.toLowerCase().includes(industry.toLowerCase())) {
        return industry;
      }
    }
    return null;
  }

  // Извлечение лица, принимающего решения
  extractDecisionMaker(summary) {
    if (summary.includes('директор')) return 'Директор';
    if (summary.includes('руководитель')) return 'Руководитель';
    if (summary.includes('менеджер')) return 'Менеджер';
    return 'Не определен';
  }

  // Форматирование комментария для лида (сокращенная версия)
  formatLeadComment(analysisResult, transcript, meetingUrl) {
    const date = new Date().toLocaleString('ru-RU');
    
    return `🤖 АНАЛИЗ ВСТРЕЧИ (${date})

⭐ Общая оценка: ${analysisResult.overallScore}/100
🏷️ Категория клиента: ${analysisResult.category}

💡 РЕЗЮМЕ:
${analysisResult.summary}

📝 РЕКОМЕНДАЦИИ:
${this.getRecommendationsByCategory(analysisResult.category)}

🔗 Ссылка встречи: ${meetingUrl}`.trim();
  }

  // Форматирование описания активности
  formatActivityDescription(analysisResult, meetingUrl) {
    return `Автоматический анализ встречи через Meeting Bot.

Результаты:
- Оценка: ${analysisResult.overallScore}/100
- Категория: ${analysisResult.category}
- Ссылка: ${meetingUrl}

Резюме: ${analysisResult.summary}`.trim();
  }

  // Получение статуса по категории клиента
  getStatusByCategory(category) {
    const statusMap = {
      'A': 'NEW',      // Горячий
      'B': 'NEW',      // Теплый  
      'C': 'NEW',      // Холодный
      'Теплый': 'NEW',
      'Горячий': 'NEW',
      'Холодный': 'NEW'
    };
    
    return statusMap[category] || 'NEW';
  }

  // Получение вероятности по категории
  getProbabilityByCategory(category) {
    const probabilityMap = {
      'A': 80,
      'B': 60,
      'C': 30,
      'Теплый': 60,
      'Горячий': 80,
      'Холодный': 30
    };
    
    return probabilityMap[category] || 50;
  }

  // Получение следующего шага по категории
  getNextStepByCategory(category) {
    const nextStepMap = {
      'A': 'Подготовить КП и назначить встречу',
      'B': 'Отправить презентацию и запланировать звонок',
      'C': 'Добавить в базу для nurturing',
      'Теплый': 'Отправить презентацию и запланировать звонок',
      'Горячий': 'Подготовить КП и назначить встречу',
      'Холодный': 'Добавить в базу для nurturing'
    };
    
    return nextStepMap[category] || 'Стандартная обработка';
  }

  // Получение приоритетного действия по категории
  getPriorityActionByCategory(category) {
    const actionMap = {
      'A': 'Срочно подготовить коммерческое предложение',
      'B': 'Отправить презентацию услуг',
      'C': 'Добавить в email-рассылку',
      'Теплый': 'Отправить презентацию услуг',
      'Горячий': 'Срочно подготовить коммерческое предложение',
      'Холодный': 'Добавить в email-рассылку'
    };
    
    return actionMap[category] || 'Обработать согласно стандартному процессу';
  }

  // Получение рекомендаций по категории
  getRecommendationsByCategory(category) {
    const recommendations = {
      'A': '✅ Срочно подготовить КП\n📞 Назначить встречу в течение 1-2 дней',
      'B': '📋 Отправить презентацию\n📞 Запланировать звонок через неделю', 
      'C': '📧 Добавить в рассылку\n⏰ Повторный контакт через месяц',
      'Теплый': '📋 Отправить презентацию\n📞 Запланировать звонок через неделю',
      'Горячий': '✅ Срочно подготовить КП\n📞 Назначить встречу в течение 1-2 дней',
      'Холодный': '📧 Добавить в рассылку\n⏰ Повторный контакт через месяц'
    };
    
    return recommendations[category] || 'Стандартная обработка лида';
  }
}

export const bitrixService = new BitrixService();
