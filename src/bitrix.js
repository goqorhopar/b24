// src/bitrix.js
import axios from 'axios';
import { config } from './config.js';

const FM = config.leadFieldMap || {};
const BITRIX_WEBHOOK = (config.bitrixWebhookUrl || '').replace(/\/$/, '');
const RESPONSIBLE_ID = Number(config.bitrixResponsibleId) || undefined;
const CREATED_BY_ID = Number(config.bitrixCreatedById) || RESPONSIBLE_ID;
const TASK_DEADLINE_DAYS = Number(config.bitrixTaskDefaultDeadlineDays) || 3;

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
    const { data } = await axios.post(url, payload, {
      headers: { 'Content-Type': 'application/json' }
    });
    if (data?.error) {
      const err = new Error(`${data.error}: ${data.error_description}`);
      err.details = data;
      throw err;
    }
    return data?.result;
  } catch (e) {
    logger?.error?.({ method, message: e.message, payload }, 'Bitrix API call failed');
    throw e;
  }
}

/* ===========================
   Формирование полей лида
   =========================== */
function buildLeadFields(a, transcript, sourceLabel, logger) {
  const fields = {
    COMMENTS: sanitizeText(
      [
        'Анализ встречи:',
        a.summary || '—',
        '',
        `Категория: ${a.category || '—'} (вероятность ${a.probability ?? '—'}%)`,
        '',
        `Источник обновления: ${sourceLabel || 'Telegram Bot'}`
      ].join('\n'),
      20000
    ),
    SOURCE_DESCRIPTION: sanitizeText(sourceLabel || 'Updated via Meeting Bot', 255)
  };

  // Заполняем пользовательские поля UF_* из конфига
  if (FM.UF_WHAT_SELLS && a.whatSells) fields[FM.UF_WHAT_SELLS] = sanitizeText(a.whatSells, 500);
  if (FM.UF_MEETING_HOST && a.meetingHost) fields[FM.UF_MEETING_HOST] = sanitizeText(a.meetingHost, 255);
  if (FM.UF_MEETING_PLANNED_AT && a.meetingPlannedAt) fields[FM.UF_MEETING_PLANNED_AT] = a.meetingPlannedAt; // ISO
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
  return sanitizeText(lines.join('\n'), 60000);
}

async function addActivityToLead(leadId, subject, description, logger) {
  const fields = {
    OWNER_ID: Number(leadId),
    OWNER_TYPE_ID: 1, // Lead
    TYPE_ID: 4,       // Note
    SUBJECT: sanitizeText(subject, 255),
    DESCRIPTION: sanitizeText(description, 60000),
    DESCRIPTION_TYPE: 1
  };
  return callBitrix('crm.activity.add', { fields }, logger);
}

/* ===========================
   Публичные методы
   =========================== */
export async function updateLead(leadId, analysis, transcript, source, logger) {
  if (!leadId) throw new Error('leadId обязателен');
  const fields = buildLeadFields(analysis, transcript, source, logger);
  await callBitrix('crm.lead.update', { id: String(leadId), fields }, logger);

  // Добавляем активность с журналом анализа
  try {
    const title = `Анализ встречи (категория: ${analysis?.category || '—'})`;
    const body = buildActivityBody(analysis, transcript);
    await addActivityToLead(leadId, title, body, logger);
  } catch (e) {
    logger?.warn?.({ leadId, error: e.message }, 'Не удалось добавить активность к лиду');
  }
}

export async function createTask({ title, description, leadId, source = 'Meeting Bot', responsibleId = RESPONSIBLE_ID, createdById = CREATED_BY_ID, deadline }, logger) {
  if (!leadId) throw new Error('leadId обязателен для привязки задачи');
  if (!responsibleId) throw new Error('BITRIX_RESPONSIBLE_ID обязателен');

  const d = deadline ? new Date(deadline) : new Date();
  if (!deadline) {
    d.setDate(d.getDate() + TASK_DEADLINE_DAYS
