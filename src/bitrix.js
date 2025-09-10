// src/bitrix.js

import axios from 'axios';
import { config } from './config.js';

const BITRIX_WEBHOOK = (config.bitrixWebhookUrl || '').replace(/\/$/, '');
const RESPONSIBLE_ID = Number(config.bitrixResponsibleId) || undefined;
const CREATED_BY_ID = Number(config.bitrixCreatedById) || RESPONSIBLE_ID;
const TASK_DEADLINE_DAYS = Number(config.bitrixTaskDefaultDeadlineDays) || 3;
const FM = config.leadFieldMap || {}; // UF_* mapping

function assertConfig(logger) {
  if (!BITRIX_WEBHOOK) {
    const msg = 'Bitrix webhook URL is not configured (config.bitrixWebhookUrl)';
    logger?.error?.(msg);
    throw new Error(msg);
  }
}

async function callBitrix(method, payload, logger) {
  assertConfig(logger);
  const url = `${BITRIX_WEBHOOK}/${method}.json`;
  try {
    const { data } = await axios.post(url, payload, {
      headers: { 'Content-Type': 'application/json', 'User-Agent': 'MeetingBot/1.0' },
      timeout: 30000
    });

    if (data?.error) {
      const err = new Error(`${data.error}: ${data.error_description || 'Unknown error'}`);
      err.code = data.error;
      err.details = data;
      throw err;
    }
    return data?.result;
  } catch (error) {
    const status = error.response?.status;
    const desc = error.response?.data?.error_description || error.message;
    logger?.error?.({ method, status, error: desc }, 'Bitrix API call failed');
    throw error;
  }
}

function sanitizeText(text, max = 60000) {
  if (!text) return '';
  const normalized = String(text).replace(/\u0000/g, '').trim();
  return normalized.length > max ? normalized.slice(0, max - 3) + '...' : normalized;
}

function parseNumber(val) {
  if (val == null) return undefined;
  const m = String(val).replace(/[^\d.,]/g, '').replace(',', '.');
  const n = Number(m);
  return Number.isFinite(n) ? n : undefined;
}

function buildLeadFields(analysis, transcript, sourceLabel, logger) {
  const fields = {
    COMMENTS: sanitizeText(
      [
        'Анализ встречи:',
        analysis.summary || '—',
        '',
        `Категория: ${analysis.category || '—'} (вероятность ${analysis.probability ?? '—'}%)`,
        '',
        `Источник обновления: ${sourceLabel || 'Telegram Bot'}`
      ].join('\n'),
      20000
    ),
    SOURCE_DESCRIPTION: sanitizeText(sourceLabel || 'Updated via Meeting Bot', 255)
  };

  // Маппим пользовательские поля, если указаны UF_* в конфиге
  // Названия взяты из твоей карточки: «Что продает», «Кто проводит встречу?», «План дата встречи» и др.
  if (FM.UF_WHAT_SELLS && analysis.whatSells) fields[FM.UF_WHAT_SELLS] = sanitizeText(analysis.whatSells, 2000);
  if (FM.UF_MEETING_HOST && analysis.meetingHost) fields[FM.UF_MEETING_HOST] = sanitizeText(analysis.meetingHost, 255);
  if (FM.UF_MEETING_PLANNED_AT && analysis.meetingPlannedAt) fields[FM.UF_MEETING_PLANNED_AT] = analysis.meetingPlannedAt;
  if (FM.UF_INDUSTRY && analysis.industry) fields[FM.UF_INDUSTRY] = sanitizeText(analysis.industry, 255);
  if (FM.UF_DECISION_MAKERS && analysis.decisionMakers) fields[FM.UF_DECISION_MAKERS] = sanitizeText(analysis.decisionMakers, 2000);
  if (FM.UF_DECISION_TIMELINE && analysis.decisionTimeline) fields[FM.UF_DECISION_TIMELINE] = sanitizeText(analysis.decisionTimeline, 1000);
  if (FM.UF_BUDGET && analysis.budget) fields[FM.UF_BUDGET] = sanitizeText(analysis.budget, 255);
  if (FM.UF_CATEGORY && analysis.category) fields[FM.UF_CATEGORY] = sanitizeText(analysis.category, 10);
  if (FM.UF_PRIORITY_ACTION && analysis.priorityAction) fields[FM.UF_PRIORITY_ACTION] = sanitizeText(analysis.priorityAction, 2000);
  if (FM.UF_PROBABILITY && (analysis.probability != null)) fields[FM.UF_PROBABILITY] = parseNumber(analysis.probability);
  if (FM.UF_TONE && analysis.tone) fields[FM.UF_TONE] = sanitizeText(analysis.tone, 255);
  if (FM.UF_DIALOG_CONTROL && analysis.dialogControl) fields[FM.UF_DIALOG_CONTROL] = sanitizeText(analysis.dialogControl, 255);
  if (FM.UF_OBJECTIONS && analysis.objections) fields[FM.UF_OBJECTIONS] = sanitizeText(analysis.objections, 60000);

  logger?.info?.({ fieldsCount: Object.keys(fields).length }, 'Подготовлены данные для обновления лида');
  return fields;
}

function buildActivityBody(a, transcript) {
  const parts = [];
  const add = s => parts.push(s);
  add('РЕЗУЛЬТАТЫ АНАЛИЗА ВСТРЕЧИ');
  add('');
  add(`1) Анализ бизнеса: ${a.businessAnalysis || 'Компания предоставляет услуги; требуется уточнение бизнес-модели.'}`);
  add(`2) Боли и потребности: ${a.painPoints || '—'}`);
  add(`3) Возражения: ${a.objections || '—'}`);
  add(`4) Реакция на модель: ${a.clientReaction || '—'}`);
  add(`5) Интерес к сервису: ${a.serviceInterest || '—'}`);
  add(`6) Возможности: ${a.opportunities || '—'}`);
  add(`7) Ошибки менеджера: ${a.managerErrors || '—'}`);
  add(`8) Путь к закрытию: ${a.closingPath || '—'}`);
  add(`9) Тон беседы: ${a.tone || '—'}`);
  add(`10) Контроль диалога: ${a.dialogControl || '—'}`);
  add(`11) Рекомендации: ${a.recommendations || a.priorityAction || '—'}`);
  add(`12) Категория клиента: ${a.category || '—'} (вероятность ${a.probability ?? '—'}%)`);
  add('');
  add(`Отрасль: ${a.industry || '—'}`);
  add(`Ключевые лица: ${a.decisionMakers || '—'}`);
  add(`Сроки решения: ${a.decisionTimeline || '—'}`);
  add(`Бюджет: ${a.budget || '—'}`);
  add(`Приоритет: ${a.priorityAction || '—'}`);
  add('');
  add('Сводка:');
  add(sanitizeText(a.summary || '—', 15000));
  add('');
  add('Оригинальный транскрипт (фрагмент):');
  add(sanitizeText(transcript || '—', 8000));
  return sanitizeText(parts.join('\n'), 60000);
}

async function addActivityToLead(leadId, subject, description, logger) {
  const fields = {
    OWNER_ID: Number(leadId),
    OWNER_TYPE_ID: 1, // 1 = Lead
    TYPE_ID: 4,       // 4 = Заметка
    COMMUNICATIONS: [],
    SUBJECT: sanitizeText(subject, 255),
    DESCRIPTION: sanitizeText(description, 60000),
    DESCRIPTION_TYPE: 1 // 1 = text
  };
  return callBitrix('crm.activity.add', { fields }, logger);
}

export async function updateLead(leadId, analysis, transcript, source, logger) {
  if (!leadId) throw new Error('leadId is required');
  const fields = buildLeadFields(analysis, transcript, source, logger);

  try {
    await callBitrix('crm.lead.update', { id: String(leadId), fields }, logger);
    // Активность с журналом анализа (не критично, если упадёт)
    try {
      const title = `Анализ встречи (категория: ${analysis?.category || '—'})`;
      const body = buildActivityBody(analysis, transcript);
      await addActivityToLead(leadId, title, body, logger);
    } catch (actErr) {
      logger?.warn?.({ leadId, error: actErr.message }, 'Не удалось добавить активность к лиду');
    }
    return { ok: true };
  } catch (error) {
    // Fallback: минимальное обновление
    logger?.warn?.('Попытка минимального обновления лида...');
    try {
      await callBitrix('crm.lead.update', {
        id: String(leadId),
        fields: { COMMENTS: sanitizeText(analysis?.summary || 'Автообновление: краткое примечание', 20000) }
      }, logger);
      return { ok: true, minimal: true };
    } catch (e2) {
      throw e2;
    }
  }
}

export async function createTask(params, logger) {
  const {
    title,
    description,
    leadId,
    source = 'Meeting Bot',
    responsibleId = RESPONSIBLE_ID,
    createdById = CREATED_BY_ID,
    deadline // ISO string | Date | undefined
  } = params || {};

  if (!leadId) throw new Error('leadId is required for task linking');
  if (!responsibleId) throw new Error('config.bitrixResponsibleId is required for task assignment');

  const deadlineDate = (() => {
    if (deadline) return new Date(deadline);
    const d = new Date();
    d.setDate(d.getDate() + TASK_DEADLINE_DAYS);
    d.setHours(19, 0, 0, 0);
    return d;
  })();

  const fields = {
    TITLE: sanitizeText(title || `Анализ встречи по лиду ${leadId}`, 255),
    DESCRIPTION: sanitizeText(`${description || ''}\n\nИсточник: ${source}`, 59000),
    RESPONSIBLE_ID: Number(responsibleId),
    CREATED_BY: Number(createdById || responsibleId),
    UF_CRM_TASK: [`L_${leadId}`],
    DEADLINE: deadlineDate.toISOString()
  };

  const result = await callBitrix('tasks.task.add', { fields }, logger);
  const taskId = result?.task?.id || result?.taskId || result;
  return { taskId };
}

export const bitrixService = {
  updateLead,
  createTask,
  addActivityToLead
};
