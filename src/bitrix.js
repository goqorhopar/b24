import axios from 'axios';
import logger from './logger.js';

export async function updateLead(report, leadId) {
  const webhookUrl = process.env.BITRIX_WEBHOOK_URL;

  if (!webhookUrl) {
    throw new Error("❌ BITRIX_WEBHOOK_URL не задан в переменных окружения");
  }

  logger.info(`Обновляю лид ${leadId} через Bitrix24 webhook...`);

  // Извлекаем имя клиента из отчета
  const firstLine = report.split('\n')[0];
  const clientName = firstLine.startsWith('Клиент:') ? firstLine.replace('Клиент:', '').trim() : `Лид ${leadId}`;
  
  // Формируем данные для обновления лида
  const leadPayload = {
    id: leadId,
    fields: {
      TITLE: clientName,
      COMMENTS: report,
    }
  };

  try {
    const res = await axios.post(`${webhookUrl}/crm.lead.update.json`, leadPayload);
    if (res.data.error) {
      logger.error(`Bitrix24 error: ${res.data.error_description}`);
      throw new Error(res.data.error_description);
    }
    logger.info(`✅ Лид ${leadId} успешно обновлен`);
    
    // Создаем задачу
    await createTask(leadId, clientName, webhookUrl);
  } catch (err) {
    logger.error(`Ошибка при обновлении лида ${leadId}: ${err.message}`);
    throw err;
  }
}

async function createTask(leadId, clientName, webhookUrl) {
  // Получаем ID текущего пользователя
  let currentUserId = 1;
  try {
    const userRes = await axios.post(`${webhookUrl}/user.current.json`);
    if (userRes.data.result && !userRes.data.error) {
      currentUserId = userRes.data.result.ID;
      logger.info(`Текущий пользователь ID: ${currentUserId}`);
    }
  } catch (err) {
    logger.warn(`Не удалось получить ID пользователя: ${err.message}`);
  }

  // Создаем дату дедлайна (текущая дата + 3 дня)
  const deadlineDate = new Date();
  deadlineDate.setDate(deadlineDate.getDate() + 3);
  const deadlineStr = deadlineDate.toISOString().split('T')[0];

  // Формируем данные для создания задачи
  const taskData = {
    fields: {
      TITLE: `Следующий шаг по лиду: ${clientName}`,
      DESCRIPTION: `Автоматически созданная задача по результатам анализа встречи с клиентом. Лид: ${leadId}`,
      CREATED_BY: currentUserId,
      RESPONSIBLE_ID: currentUserId,
      DEADLINE: deadlineStr,
      PRIORITY: 2, // Средний приоритет
      UF_CRM_TASK: [`L_${leadId}`], // Привязка к лиду
      // Дополнительные поля для лучшего отображения
      TAGS: ['встреча', 'анализ'],
      ALLOW_CHANGE_DEADLINE: 'Y'
    }
  };

  try {
    logger.info(`Создаю задачу для лида ${leadId}...`);
    
    // Пробуем разные методы API для создания задачи
    let res;
    try {
      // Первый метод (основной)
      res = await axios.post(`${webhookUrl}/tasks.task.add.json`, taskData);
    } catch (err) {
      // Второй метод (альтернативный)
      logger.warn(`Первый метод не сработал, пробую альтернативный: ${err.message}`);
      res = await axios.post(`${webhookUrl}/task.item.add.json`, taskData);
    }
    
    if (res.data.error) {
      logger.error(`Ошибка при создании задачи: ${JSON.stringify(res.data.error)}`);
      
      // Пробуем упрощенный вариант без привязки к лиду
      const simpleTaskData = {...taskData};
      delete simpleTaskData.fields.UF_CRM_TASK;
      
      const simpleRes = await axios.post(`${webhookUrl}/tasks.task.add.json`, simpleTaskData);
      if (simpleRes.data.error) {
        logger.error(`Ошибка при создании упрощенной задачи: ${JSON.stringify(simpleRes.data.error)}`);
        return;
      }
      
      logger.info(`✅ Упрощенная задача для лида ${leadId} создана`);
      return;
    }
    
    logger.info(`✅ Задача для лида ${leadId} создана: ${JSON.stringify(res.data.result)}`);
  } catch (err) {
    logger.error(`Ошибка при создании задачи для лида ${leadId}: ${err.message}`);
  }
}
