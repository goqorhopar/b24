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
  const taskPayload = {
    fields: {
      TITLE: `Следующий шаг по лиду: ${clientName}`,
      DESCRIPTION: `Необходимо выполнить следующие действия по лиду ${leadId}`,
      CREATED_BY: 1, // ID пользователя, который создает задачу
      RESPONSIBLE_ID: 1, // ID ответственного
      DEADLINE: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // +3 дня
      UF_CRM_TASK: [`L_${leadId}`] // Привязываем задачу к лиду
    }
  };

  try {
    const res = await axios.post(`${webhookUrl}/tasks.task.add.json`, taskPayload);
    if (res.data.error) {
      logger.error(`Ошибка при создании задачи: ${res.data.error_description}`);
      return;
    }
    logger.info(`✅ Задача для лида ${leadId} создана`);
  } catch (err) {
    logger.error(`Ошибка при создании задачи для лида ${leadId}: ${err.message}`);
  }
}
