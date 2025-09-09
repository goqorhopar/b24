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
  const payload = {
    id: leadId,
    fields: {
      TITLE: clientName,
      COMMENTS: report,
    }
  };

  try {
    const res = await axios.post(`${webhookUrl}/crm.lead.update.json`, payload);
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
  // Форматируем дату дедлайна (текущая дата + 3 дня)
  const deadlineDate = new Date();
  deadlineDate.setDate(deadlineDate.getDate() + 3);
  const deadlineStr = deadlineDate.toISOString().split('T')[0];
  
  // Получаем текущего пользователя вебхука
  let currentUserId = 1;
  try {
    const userRes = await axios.post(`${webhookUrl}/user.current.json`);
    if (userRes.data.result) {
      currentUserId = userRes.data.result.ID;
    }
  } catch (err) {
    logger.warn(`Не удалось получить ID пользователя: ${err.message}`);
  }

  const taskPayload = {
    fields: {
      TITLE: `Следующий шаг по лиду: ${clientName}`,
      DESCRIPTION: `Необходимо выполнить следующие действия по лиду ${leadId}. Сгенерировано автоматически из анализа встречи.`,
      CREATED_BY: currentUserId,
      RESPONSIBLE_ID: currentUserId,
      DEADLINE: deadlineStr,
      UF_CRM_TASK: [`L_${leadId}`], // Привязываем задачу к лиду
      // Дополнительные поля для лучшей совместимости
      ENTITY_TYPE: 'LEAD',
      ENTITY_ID: leadId
    }
  };

  try {
    logger.info(`Создаю задачу для лида ${leadId}: ${JSON.stringify(taskPayload)}`);
    
    const res = await axios.post(`${webhookUrl}/tasks.task.add.json`, taskPayload);
    
    if (res.data.error) {
      logger.error(`Ошибка при создании задачи: ${JSON.stringify(res.data.error)}`);
      
      // Пробуем альтернативный метод создания задачи
      await createTaskAlternative(leadId, clientName, webhookUrl, deadlineStr, currentUserId);
      return;
    }
    
    logger.info(`✅ Задача для лида ${leadId} создана: ${JSON.stringify(res.data.result)}`);
  } catch (err) {
    logger.error(`Ошибка при создании задачи для лида ${leadId}: ${err.message}`);
    
    // Пробуем альтернативный метод создания задачи
    await createTaskAlternative(leadId, clientName, webhookUrl, deadlineStr, currentUserId);
  }
}

// Альтернативный метод создания задачи (если первый не сработал)
async function createTaskAlternative(leadId, clientName, webhookUrl, deadlineStr, userId) {
  try {
    const taskPayload = {
      fields: {
        TITLE: `Следующий шаг по лиду: ${clientName}`,
        DESCRIPTION: `Необходимо выполнить следующие действия по лиду ${leadId}. Сгенерировано автоматически из анализа встречи.`,
        CREATED_BY: userId,
        RESPONSIBLE_ID: userId,
        DEADLINE: deadlineStr,
        // Альтернативный способ привязки к лиду
        UF_CRM_TASK: leadId.toString()
      }
    };
    
    const res = await axios.post(`${webhookUrl}/task.item.add.json`, taskPayload);
    
    if (res.data.error) {
      logger.error(`Ошибка при альтернативном создании задачи: ${JSON.stringify(res.data.error)}`);
      return;
    }
    
    logger.info(`✅ Задача создана альтернативным методом для лида ${leadId}`);
  } catch (err) {
    logger.error(`Ошибка при альтернативном создании задачи: ${err.message}`);
  }
}
