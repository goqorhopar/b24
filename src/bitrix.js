// src/bitrix.js
import axios from 'axios';
import { config } from './config.js';

const FM = config.leadFieldMap || {};
const BITRIX_WEBHOOK = (config.bitrixWebhookUrl || '').replace(/\/$/, '');
const RESPONSIBLE_ID = config.bitrixResponsibleId;
const CREATED_BY_ID = config.bitrixCreatedById || RESPONSIBLE_ID;
const TASK_DEADLINE_DAYS = config.bitrixTaskDefaultDeadlineDays;

// Валидация конфигурации
if (!BITRIX_WEBHOOK) {
  throw new Error('BITRIX_WEBHOOK_URL не настроен');
}

if (!RESPONSIBLE_ID) {
  console.warn('⚠️ BITRIX_RESPONSIBLE_ID не задан. Задачи не будут создаваться.');
}

/* ===========================
   Вспомогательные функции
   =========================== */
function sanitizeText(text, max = 60000) {
  if (!text) return '';
  const t = String(text).replace(/\u0000/g, '').trim();
  return t.length > max ? t.slice(0, max - 3) + '...' : t;
}

function parseNumber(val) {
  if (val == null) return undefined;
  const n = Number(String(val).replace(/[^\d.,]/g, '').replace(',', '.'));
  return Number.isFinite(n) ? n : undefined;
}

async function callBitrix(method, payload, logger) {
  const url = `${BITRIX_WEBHOOK}/${method}.json`;
  
  try {
    logger?.debug?.({ method, payload }, 'Bitrix API call');
    const { data } = await axios.post(url, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000
    });
    
    if (data?.error) {
      const err = new Error(`${data.error}: ${data.error_description}`);
      err.details = data;
      throw err;
    }
    
    return data?.result;
  } catch (e) {
    const errorMsg = e.response?.data?.error_description || e.message;
    logger?.error?.({ 
      method, 
      message: errorMsg,
      url,
      payload: JSON.stringify(payload).substring(0, 500)
    }, 'Bitrix API call failed');
    
    throw new Error(`Bitrix API ошибка: ${errorMsg}`);
  }
}

/* ===========================
   Формирование полей лида
   =========================== */
function buildLeadFields(a, transcript, sourceLabel, logger) {
  if (!a || typeof a !== 'object') {
    throw new Error('Анализ встречи должен быть объектом');
  }

  const fields = {
    COMMENTS: sanitizeText(
      [
        '🤖 Анализ встречи (автоматический):',
        '────────────────────────',
        a.summary || '—',
        '',
        `📊 Категория: ${a.category || '—'} (вероятность ${a.probability ?? '—'}%)`,
        `🏢 Отрасль: ${a.industry || '—'}`,
        `👥 Ключевые лица: ${a.decisionMakers || '—'}`,
        `⏰ Сроки решения: ${a.decisionTimeline || '—'}`,
        `💰 Бюджет: ${a.budget || '—'}`,
        '',
        `🔧 Источник: ${sourceLabel || 'Telegram Bot'}`,
        `🕒 Время анализа: ${new Date().toLocaleString('ru-RU')}`
      ].join('\n'),
      20000
    ),
    SOURCE_DESCRIPTION: sanitizeText(sourceLabel || 'Updated via Meeting Bot', 255)
  };

  // Динамическое заполнение пользовательских полей
  if (FM.UF_WHAT_SELLS && a.whatSells) fields[FM.UF_WHAT_SELLS] = sanitizeText(a.whatSells, 500);
  if (FM.UF_MEETING_HOST && a.meetingHost) fields[FM.UF_MEETING_HOST] = sanitizeText(a.meetingHost, 255);
  if (FM.UF_MEETING_PLANNED_AT && a.meetingPlannedAt) fields[FM.UF_MEETING_PLANNED_AT] = a.meetingPlannedAt;
  if (FM.UF_INDUSTRY && a.industry) fields[FM.UF_INDUSTRY] = sanitizeText(a.industry, 255);
  if (FM.UF_DECISION_MAKERS && a.decisionMakers) fields[FM.UF_DECISION_MAKERS] = sanitizeText(a.decisionMakers, 4000);
  if (FM.UF_DECISION_TIMELINE && a.decisionTimeline) fields[FM.UF_DECISION_TIMELINE] = sanitizeText(a.decisionTimeline, 1000);
  if (FM.UF_BUDGET && a.budget) fields[FM.UF_BUDGET] = sanitizeText(a.budget, 255);
  if (FM.UF_CATEGORY && a.category) fields[FM.UF_CATEGORY] = sanitizeText(a.category, 10);
  if (FM.UF_PRIORITY_ACTION && a.priorityAction) fields[FM.UF_PRIORITY_ACTION] = sanitizeText(a.priorityAction, 4000);
  if (FM.UF_PROBABILITY && (a.probability != null)) {
    const p = parseNumber(a.probability);
    if (p != null) fields[FM.UF_PROBABILITY] = p;
  }
  if (FM.UF_TONE && a.tone) fields[FM.UF_TONE] = sanitizeText(a.tone, 255);
  if (FM.UF_DIALOG_CONTROL && a.dialogControl) fields[FM.UF_DIALOG_CONTROL] = sanitizeText(a.dialogControl, 255);
  if (FM.UF_OBJECTIONS && a.objections) fields[FM.UF_OBJECTIONS] = sanitizeText(a.objections, 60000);

  logger?.info?.({ fieldsCount: Object.keys(fields).length }, 'Подготовлены поля для обновления лида');
  return fields;
}

/* ===========================
   Формирование активности
   =========================== */
function buildActivityBody(a, transcript) {
  const lines = [];
  const add = s => lines.push(s);
  
  add('🤖 АВТОМАТИЧЕСКИЙ АНАЛИЗ ВСТРЕЧИ');
  add('────────────────────────');
  add('');
  add(`📊 Категория клиента: ${a.category || '—'} (вероятность ${a.probability ?? '—'}%)`);
  add(`🏢 Отрасль: ${a.industry || '—'}`);
  add(`👥 Ключевые лица: ${a.decisionMakers || '—'}`);
  add(`⏰ Сроки решения: ${a.decisionTimeline || '—'}`);
  add(`💰 Бюджет: ${a.budget || '—'}`);
  add('');
  add('🎯 Основные боли и потребности:');
  add(a.painPoints || '—');
  add('');
  add('❗ Возражения:');
  add(a.objections || '—');
  add('');
  add('😊 Реакция на предложение:');
  add(a.clientReaction || '—');
  add('');
  add('⭐ Интерес к сервису:');
  add(a.serviceInterest || '—');
  add('');
  add('🚀 Возможности:');
  add(a.opportunities || '—');
  add('');
  add('📝 Приоритетные действия:');
  add(a.priorityAction || '—');
  add('');
  add('🧾 Краткая сводка:');
  add(a.summary || '—');
  add('');
  add('────────────────────────');
  add('📄 ОРИГИНАЛЬНЫЙ ТРАНСКРИПТ (ФРАГМЕНТ):');
  add(sanitizeText(transcript || '—', 8000));
  
  return sanitizeText(lines.join('\n'), 60000);
}

async function addActivityToLead(leadId, subject, description, logger) {
  const fields = {
    OWNER_ID: Number(leadId),
    OWNER_TYPE_ID: 1, // 1 = Сделка/Лид
    TYPE_ID: 2, // 2 = Звонок
    SUBJECT: sanitizeText(subject, 255),
    DESCRIPTION: sanitizeText(description, 60000),
    DESCRIPTION_TYPE: 1, // 1 = HTML, 2 = Plain text
    COMPLETED: 'Y',
    PRIORITY: 2 // 1 - низкая, 2 - средняя, 3 - высокая
  };
  
  return callBitrix('crm.activity.add', { fields }, logger);
}

/* ===========================
   Публичные методы
   =========================== */
export async function updateLead(leadId, analysis, transcript, source, logger) {
  if (!leadId) throw new Error('leadId обязателен');
  
  logger?.info?.({ leadId }, 'Начинаю обновление лида');
  
  const fields = buildLeadFields(analysis, transcript, source, logger);
  const result = await callBitrix('crm.lead.update', { id: String(leadId), fields }, logger);
  
  try {
    const title = `Анализ встречи (${analysis?.category || 'не определена'})`;
    const body = buildActivityBody(analysis, transcript);
    await addActivityToLead(leadId, title, body, logger);
    logger?.info?.({ leadId }, 'Активность добавлена к лиду');
  } catch (e) {
    logger?.warn?.({ leadId, error: e.message }, 'Не удалось добавить активность к лиду');
  }
  
  return result;
}

export async function createTask(
  { title, description, leadId, source = 'Meeting Bot', responsibleId = RESPONSIBLE_ID, createdById = CREATED_BY_ID, deadline },
  logger
) {
  if (!leadId) throw new Error('leadId обязателен для привязки задачи');
  if (!responsibleId) {
    logger?.warn?.('BITRIX_RESPONSIBLE_ID не задан, пропускаем создание задачи');
    return { taskId: null };
  }

  let d = deadline ? new Date(deadline) : new Date();
  if (!deadline) {
    d.setDate(d.getDate() + TASK_DEADLINE_DAYS);
    d.setHours(19, 0, 0, 0); // 19:00 по местному времени
  }

  const fields = {
    TITLE: sanitizeText(title || `Анализ встречи по лиду ${leadId}`, 255),
    DESCRIPTION: sanitizeText(`${description || ''}\n\n📎 Источник: ${source}`, 59000),
    RESPONSIBLE_ID: Number(responsibleId),
    CREATED_BY: Number(createdById || responsibleId),
    UF_CRM_TASK: [`L_${leadId}`],
    DEADLINE: d.toISOString().replace('Z', ''),
    PRIORITY: 2, // 1 - низкая, 2 - средняя, 3 - высокая
    GROUP_ID: 0 // Основная группа задач
  };

  const result = await callBitrix('tasks.task.add', { fields }, logger);
  const taskId = result?.task?.id || result?.taskId || result;
  
  if (taskId) {
    logger?.info?.({ leadId, taskId }, 'Задача создана и привязана к лиду');
    
    // Добавляем комментарий к задаче
    try {
      await callBitrix('task.commentitem.add', {
        TASKID: taskId,
        FIELDS: {
          POST_MESSAGE: `✅ Задача создана автоматически на основе анализа встречи по лиду ${leadId}`
        }
      }, logger);
    } catch (commentError) {
      logger?.warn?.({ taskId, error: commentError.message }, 'Не удалось добавить комментарий к задаче');
    }
  }
  
  return { taskId };
}

// Дополнительные методы для работы с Bitrix
export async function getLead(leadId, logger) {
  if (!leadId) throw new Error('leadId обязателен');
  return callBitrix('crm.lead.get', { id: String(leadId) }, logger);
}

export async function searchLeads(query, logger) {
  if (!query) throw new Error('Поисковый запрос обязателен');
  return callBitrix('crm.lead.list', {
    filter: { '%TITLE': `%${query}%` },
    select: ['ID', 'TITLE', 'NAME', 'LAST_NAME', 'STATUS_ID']
  }, logger);
}

export const bitrixService = { 
  updateLead, 
  createTask, 
  getLead, 
  searchLeads 
};
