import axios from 'axios';
import logger from './logger.js';

export async function updateLead(report, leadId) {
  const webhookUrl = process.env.BITRIX_WEBHOOK_URL;

  if (!webhookUrl) {
    throw new Error("❌ BITRIX_WEBHOOK_URL не задан в переменных окружения");
  }

  logger.info(`Обновляю лид ${leadId} через Bitrix24 webhook...`);

  // Извлекаем информацию из отчета
  const clientInfo = extractClientInfo(report);
  const nextSteps = extractNextSteps(report);
  const priorityAction = extractPriorityAction(report);
  const deadlines = extractDeadlines(report);
  const contacts = extractContacts(report);
  const budget = extractBudget(report);
  const probability = extractProbability(report);
  const businessInfo = extractBusinessInfo(report);
  
  // Формируем данные для обновления лида
  const payload = {
    id: leadId,
    fields: {
      TITLE: clientInfo.name || `Лид ${leadId}`,
      NAME: clientInfo.firstName || undefined,
      LAST_NAME: clientInfo.lastName || undefined,
      COMMENTS: report,
      SOURCE_DESCRIPTION: "Создано через Telegram бота",
      UF_CRM_PRODUCT: businessInfo.product || "Не определено",
      UF_CRM_CLIENT_TYPE: clientInfo.type || "Новый",
      UF_CRM_PROBABILITY: probability || 30,
      UF_CRM_BUDGET: budget || undefined,
      UF_CRM_INDUSTRY: businessInfo.industry || undefined,
      UF_CRM_DECISION_MAKER: businessInfo.decisionMaker || undefined,
      UF_CRM_TIMELINE: deadlines.overall || undefined,
      UF_CRM_NEXT_STEP: nextSteps[0] || "Обратная связь по встрече",
      UF_CRM_PRIORITY_ACTION: priorityAction || "Уточнить детали",
      ASSIGNED_BY_ID: 1, // ID ответственного менеджера
      // Дополнительные стандартные поля Bitrix24
      STATUS_ID: "NEW", // Статус лида
      CURRENCY_ID: "RUB", // Валюта
      OPENED: "Y", // Сделка открыта
    }
  };

  // Добавляем контакты если найдены
  if (contacts.phone) {
    payload.fields.PHONE = [{ VALUE: contacts.phone, VALUE_TYPE: "WORK" }];
  }
  
  if (contacts.email) {
    payload.fields.EMAIL = [{ VALUE: contacts.email, VALUE_TYPE: "WORK" }];
  }

  try {
    const res = await axios.post(`${webhookUrl}/crm.lead.update.json`, payload);
    if (res.data.error) {
      logger.error(`Bitrix24 error: ${res.data.error_description}`);
      throw new Error(res.data.error_description);
    }
    logger.info(`✅ Лид ${leadId} успешно обновлен`);
    
    // Создаем задачи
    await createTasks(leadId, clientInfo.name, webhookUrl, nextSteps, deadlines, priorityAction);
  } catch (err) {
    logger.error(`Ошибка при обновлении лида ${leadId}: ${err.message}`);
    throw err;
  }
}

// Вспомогательные функции для извлечения информации из отчета
function extractClientInfo(report) {
  const nameMatch = report.match(/Клиент:\s*([^\n]+)/);
  const name = nameMatch ? nameMatch[1].trim() : null;
  
  let firstName = null;
  let lastName = null;
  if (name) {
    const nameParts = name.split(' ');
    firstName = nameParts[0] || null;
    lastName = nameParts.length > 1 ? nameParts.slice(1).join(' ') : null;
  }
  
  let type = "Новый";
  if (report.includes("горячий клиент") || report.includes("высокая вероятность")) type = "Горячий";
  else if (report.includes("теплый клиент") || report.includes("средняя вероятность")) type = "Теплый";
  else if (report.includes("холодный клиент") || report.includes("низкая вероятность")) type = "Холодный";
  
  return { name, firstName, lastName, type };
}

function extractBusinessInfo(report) {
  // Определяем отрасль
  let industry = null;
  const industries = ["IT", "ритейл", "производство", "строительство", "медицина", "образование", "финансы"];
  for (const ind of industries) {
    if (report.toLowerCase().includes(ind.toLowerCase())) {
      industry = ind;
      break;
    }
  }
  
  // Определяем продукт/услугу
  let product = null;
  const productKeywords = ["продукт", "услуга", "решение", "сервис", "software", "platform", "SaaS"];
  for (const keyword of productKeywords) {
    const regex = new RegExp(`${keyword}[^.:!?]*[.:!?]`, 'i');
    const match = report.match(regex);
    if (match) {
      product = match[0];
      break;
    }
  }
  
  // Определяем лицо, принимающее решение
  let decisionMaker = null;
  const decisionKeywords = ["директор", "руководитель", "CEO", "CTO", "менеджер", "владелец"];
  for (const keyword of decisionKeywords) {
    if (report.toLowerCase().includes(keyword.toLowerCase())) {
      decisionMaker = keyword;
      break;
    }
  }
  
  return { industry, product, decisionMaker };
}

function extractNextSteps(report) {
  const nextStepsSection = report.split('СЛЕДУЮЩИЕ ШАГИ:')[1];
  if (!nextStepsSection) return ["Обратная связь по встрече"];
  
  const steps = [];
  const lines = nextStepsSection.split('\n');
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine && 
        !trimmedLine.startsWith('ПРИОРИТЕТНЫЕ ДЕЙСТВИЯ:') && 
        !trimmedLine.startsWith('ДЕДЛАЙНЫ:') &&
        !trimmedLine.startsWith('КОНТАКТЫ:') &&
        !trimmedLine.startsWith('БЮДЖЕТ:') &&
        !trimmedLine.startsWith('ВЕРОЯТНОСТЬ СДЕЛКИ:')) {
      steps.push(trimmedLine);
    }
    
    if (steps.length >= 3) break; // Берем не более 3 шагов
  }
  
  return steps.length > 0 ? steps : ["Обратная связь по встрече"];
}

function extractPriorityAction(report) {
  const prioritySection = report.split('ПРИОРИТЕТНЫЕ ДЕЙСТВИЯ:')[1];
  if (!prioritySection) return "Уточнить детали";
  
  const firstLine = prioritySection.split('\n')[0].trim();
  return firstLine || "Уточнить детали";
}

function extractDeadlines(report) {
  const deadlinesSection = report.split('ДЕДЛАЙНЫ:')[1];
  if (!deadlinesSection) return { overall: "Не определен" };
  
  const deadlines = {};
  const lines = deadlinesSection.split('\n');
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine && 
        !trimmedLine.startsWith('КОНТАКТЫ:') && 
        !trimmedLine.startsWith('БЮДЖЕТ:') &&
        !trimmedLine.startsWith('ВЕРОЯТНОСТЬ СДЕЛКИ:')) {
      
      if (trimmedLine.includes("общий") || trimmedLine.includes("основной")) {
        deadlines.overall = trimmedLine;
      } else if (trimmedLine.includes("следующий шаг")) {
        deadlines.nextStep = trimmedLine;
      } else if (trimmedLine.includes("решение")) {
        deadlines.decision = trimmedLine;
      }
    }
  }
  
  return deadlines;
}

function extractContacts(report) {
  const contactsSection = report.split('КОНТАКТЫ:')[1];
  if (!contactsSection) return { phone: null, email: null };
  
  let phone = null;
  let email = null;
  
  const phoneMatch = contactsSection.match(/(\+7|8)[\s(]?(\d{3})[\s)]?(\d{3})[\s-]?(\d{2})[\s-]?(\d{2})/);
  if (phoneMatch) phone = phoneMatch[0];
  
  const emailMatch = contactsSection.match(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i);
  if (emailMatch) email = emailMatch[0];
  
  return { phone, email };
}

function extractBudget(report) {
  const budgetSection = report.split('БЮДЖЕТ:')[1];
  if (budgetSection) {
    const budgetMatch = budgetSection.match(/(\d+[\d\s]*(руб|р|USD|\$|€|EUR|тыс|млн|трлн))/i);
    if (budgetMatch) return budgetMatch[0];
  }
  
  // Ищем бюджет в основном тексте
  const budgetRegex = /(\d+[\d\s]*(руб|р|USD|\$|€|EUR|тыс|млн|трлн))/gi;
  const budgetMatches = report.match(budgetRegex);
  return budgetMatches ? budgetMatches[0] : null;
}

function extractProbability(report) {
  const probabilitySection = report.split('ВЕРОЯТНОСТЬ СДЕЛКИ:')[1];
  if (probabilitySection) {
    const percentMatch = probabilitySection.match(/(\d+)%/);
    if (percentMatch) return parseInt(percentMatch[1]);
  }
  
  // Оцениваем вероятность по тексту
  if (report.includes("высокая вероятность")) return 80;
  if (report.includes("средняя вероятность")) return 50;
  if (report.includes("низкая вероятность")) return 20;
  return 30;
}

async function createTasks(leadId, clientName, webhookUrl, nextSteps, deadlines, priorityAction) {
  // Получаем ID текущего пользователя
  let currentUserId = 1;
  try {
    const userRes = await axios.post(`${webhookUrl}/user.current.json`);
    if (userRes.data.result && !userRes.data.error) {
      currentUserId = userRes.data.result.ID;
    }
  } catch (err) {
    logger.warn(`Не удалось получить ID пользователя: ${err.message}`);
  }

  // Создаем основную задачу
  await createMainTask(leadId, clientName, webhookUrl, priorityAction, deadlines, currentUserId);
  
  // Создаем дополнительные задачи для следующих шагов
  for (let i = 0; i < Math.min(nextSteps.length, 3); i++) {
    await createAdditionalTask(leadId, clientName, webhookUrl, nextSteps[i], i + 1, currentUserId);
  }
}

async function createMainTask(leadId, clientName, webhookUrl, priorityAction, deadlines, userId) {
  const deadlineDate = new Date();
  deadlineDate.setDate(deadlineDate.getDate() + 2); // +2 дня для приоритетной задачи
  
  const taskData = {
    fields: {
      TITLE: `Приоритет: ${priorityAction} - ${clientName || `Лид ${leadId}`}`,
      DESCRIPTION: `Приоритетное действие по лиду ${leadId}.
Клиент: ${clientName || `Лид ${leadId}`}
Основное действие: ${priorityAction}
Сроки: ${deadlines.overall || "Не определены"}

Задача создана автоматически на основе анализа встречи.`,
      CREATED_BY: userId,
      RESPONSIBLE_ID: userId,
      DEADLINE: deadlineDate.toISOString().split('T')[0],
      PRIORITY: 1, // Высокий приоритет
      UF_CRM_TASK: [`L_${leadId}`],
      TAGS: ['встреча', 'анализ', 'приоритет'],
    }
  };

  try {
    const res = await axios.post(`${webhookUrl}/tasks.task.add.json`, taskData);
    if (res.data.error) {
      logger.error(`Ошибка при создании основной задачи: ${JSON.stringify(res.data.error)}`);
      return;
    }
    logger.info(`✅ Основная задача для лида ${leadId} создана: ${priorityAction}`);
  } catch (err) {
    logger.error(`Ошибка при создании основной задачи для лида ${leadId}: ${err.message}`);
  }
}

async function createAdditionalTask(leadId, clientName, webhookUrl, nextStep, stepNumber, userId) {
  const deadlineDate = new Date();
  deadlineDate.setDate(deadlineDate.getDate() + stepNumber * 3); // +3, +6, +9 дней
  
  const taskData = {
    fields: {
      TITLE: `Шаг ${stepNumber}: ${nextStep} - ${clientName || `Лид ${leadId}`}`,
      DESCRIPTION: `Дополнительное действие по лиду ${leadId}.
Клиент: ${clientName || `Лид ${leadId}`}
Действие: ${nextStep}

Задача создана автоматически на основе анализа встречи.`,
      CREATED_BY: userId,
      RESPONSIBLE_ID: userId,
      DEADLINE: deadlineDate.toISOString().split('T')[0],
      PRIORITY: 2, // Средний приоритет
      UF_CRM_TASK: [`L_${leadId}`],
      TAGS: ['встреча', 'анализ', `шаг${stepNumber}`],
    }
  };

  try {
    const res = await axios.post(`${webhookUrl}/tasks.task.add.json`, taskData);
    if (res.data.error) {
      logger.error(`Ошибка при создании дополнительной задачи: ${JSON.stringify(res.data.error)}`);
      return;
    }
    logger.info(`✅ Дополнительная задача ${stepNumber} для лида ${leadId} создана: ${nextStep}`);
  } catch (err) {
    logger.error(`Ошибка при создании дополнительной задачи для лида ${leadId}: ${err.message}`);
  }
}
