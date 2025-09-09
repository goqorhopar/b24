import axios from 'axios';
import logger from './logger.js';

export async function updateLead(report, leadId) {
  const webhookUrl = process.env.BITRIX_WEBHOOK_URL;

  if (!webhookUrl) {
    throw new Error("❌ BITRIX_WEBHOOK_URL не задан в переменных окружения");
  }

  logger.info(`Обновляю лид ${leadId} через Bitrix24 webhook...`);

  const url = `${webhookUrl}/crm.lead.update.json`;

  const payload = {
    id: leadId,
    fields: {
      COMMENTS: report
    }
  };

  try {
    const res = await axios.post(url, payload);
    if (res.data.error) {
      logger.error(`Bitrix24 error: ${res.data.error_description}`);
      throw new Error(res.data.error_description);
    }
    logger.info(`✅ Лид ${leadId} успешно обновлен`);
  } catch (err) {
    logger.error(`Ошибка при обновлении лида ${leadId}: ${err.message}`);
    throw err;
  }
}
