// src/gemini.js

import axios from 'axios';
import { config } from './config.js';

/**
 * runChecklist — анализ транскрипта.
 * Возвращает структурированный объект a:
 * {
 *   summary, category, score,
 *   whatSells, meetingHost, meetingPlannedAt,
 *   industry, decisionMakers, decisionTimeline, budget,
 *   painPoints, objections, clientReaction, serviceInterest, opportunities,
 *   managerErrors, closingPath, tone, dialogControl,
 *   priorityAction, probability
 * }
 */
export async function runChecklist(transcript, logger) {
  if (!config.geminiApiKey) throw new Error('GEMINI_API_KEY is not set');

  logger?.info?.('Отправка запроса к Gemini API...');
  // Здесь можно использовать свой шлюз/клиент. Ниже — эмуляция запроса:
  const prompt = buildPrompt(transcript);

  // Эмуляция (замени на реальный вызов Geminи)
  const data = await fakeGeminiCall(prompt);

  // Пост-обработка и разумные дефолты
  const a = normalizeAnalysis(data, transcript);
  logger?.info?.({ textLength: a.summary?.length || 0 }, 'Получен ответ от Gemini');

  // Для удобства логов:
  logger?.info?.({ score: a.score, category: a.category }, 'Анализ успешно выполнен');
  return a;
}

function buildPrompt(transcript) {
  return `Проанализируй транскрипт встречи и верни JSON с полями:
{
  "summary": "...",
  "category": "A|B|C",
  "score": 0..100,
  "whatSells": "...",
  "meetingHost": "...",
  "meetingPlannedAt": "YYYY-MM-DDTHH:mm:ssZ | пусто",
  "industry": "...",
  "decisionMakers": "...",
  "decisionTimeline": "...",
  "budget": "...",
  "painPoints": "...",
  "objections": "...",
  "clientReaction": "...",
  "serviceInterest": "...",
  "opportunities": "...",
  "managerErrors": "...",
  "closingPath": "...",
  "tone": "...",
  "dialogControl": "...",
  "priorityAction": "...",
  "probability": 0..100
}
Транскрипт:
${transcript}`;
}

// Временно: имитация ответа (замени на фактический вызов Gemini)
async function fakeGeminiCall(prompt) {
  await new Promise(r => setTimeout(r, 1200));
  return {
    summary: 'Встреча прошла продуктивно. Клиент проявил интерес к лидогенерации и CRM.',
    category: 'B',
    score: 78,
    whatSells: 'Услуги лидогенерации и CRM-автоматизации',
    meetingHost: 'Виктор Зорин',
    meetingPlannedAt: toISO(nextWorkdayAtHour(10)), // пример
    industry: 'Медицина',
    decisionMakers: 'Генеральный директор; Главный врач',
    decisionTimeline: 'После отпуска, на следующей неделе',
    budget: 'от 100 000 руб/мес',
    painPoints: 'Нехватка персонала для обработки лидов; отсутствие единой CRM',
    objections: 'Сомнения в окупаемости; Вопросы по ресурсам',
    clientReaction: 'Интерес с осторожностью, нужна проработка кадров',
    serviceInterest: 'Квалифицированные лиды, CRM-интеграция',
    opportunities: 'Стабильный поток заявок; Автоматизация воронки',
    managerErrors: 'Не дожали по срокам; мало кейсов',
    closingPath: 'Отправить КП и договор, обсудить ресурсы, согласовать пилот',
    tone: 'Позитивный, деловой',
    dialogControl: 'Сбалансированный',
    priorityAction: 'Подготовить КП, назначить Zoom, согласовать пилот на 2 недели',
    probability: 60
  };
}

function normalizeAnalysis(a, transcript) {
  const clean = v => (typeof v === 'string' ? v.trim() : v);
  const category = ['A', 'B', 'C'].includes(a?.category) ? a.category : 'B';
  const score = Number.isFinite(a?.score) ? a.score : (category === 'A' ? 85 : category === 'B' ? 60 : 25);

  return {
    summary: clean(a?.summary) || '—',
    category,
    score,
    whatSells: clean(a?.whatSells) || guessWhatSells(transcript),
    meetingHost: clean(a?.meetingHost) || guessMeetingHost(transcript),
    meetingPlannedAt: isoOrEmpty(a?.meetingPlannedAt),
    industry: clean(a?.industry) || guessIndustry(transcript),
    decisionMakers: clean(a?.decisionMakers) || guessDecisionMakers(transcript),
    decisionTimeline: clean(a?.decisionTimeline) || guessDecisionTimeline(transcript),
    budget: clean(a?.budget) || guessBudget(transcript),
    painPoints: clean(a?.painPoints) || '—',
    objections: clean(a?.objections) || '—',
    clientReaction: clean(a?.clientReaction) || '—',
    serviceInterest: clean(a?.serviceInterest) || '—',
    opportunities: clean(a?.opportunities) || '—',
    managerErrors: clean(a?.managerErrors) || '—',
    closingPath: clean(a?.closingPath) || '—',
    tone: clean(a?.tone) || '—',
    dialogControl: clean(a?.dialogControl) || '—',
    priorityAction: clean(a?.priorityAction) || defaultPriority(category),
    probability: Number.isFinite(a?.probability) ? a.probability : defaultProbability(category)
  };
}

// Хелперы для извлечения, если LLM не дал явно
function guessWhatSells(s) {
  if (!s) return '';
  if (/офтальмолог/i.test(s)) return 'Офтальмология / медуслуги';
  if (/стро/i.test(s)) return 'Строительство / дома';
  if (/лидоген/i.test(s)) return 'Лидогенерация';
  return '';
}

function guessMeetingHost(s) {
  const m = s?.match(/(Виктор\s+Зорин)/i);
  return m ? m[1] : '';
}

function guessIndustry(s) {
  if (!s) return '';
  if (/медиц|клиник|врач/i.test(s)) return 'Медицина';
  if (/строит|срубы|дома/i.test(s)) return 'Строительство';
  if (/логист/i.test(s)) return 'Логистика';
  return '';
}

function guessDecisionMakers(s) {
  if (!s) return '';
  if (/ген(еральн\w*)\s+директ/iu.test(s)) return 'Генеральный директор';
  return '';
}

function guessDecisionTimeline(s) {
  if (!s) return '';
  if (/после отпуска/i.test(s)) return 'После отпуска';
  if (/на следующей неделе/i.test(s)) return 'На следующей неделе';
  return '';
}

function guessBudget(s) {
  const m = s?.match(/(\d[\d\s\u00A0]*(?:тыс|000|руб|руб\.|рублей|тысяч))/i);
  return m ? m[1] : '';
}

function defaultPriority(c) {
  return c === 'A' || c === 'B' ? 'Подготовить КП и договор, назначить Zoom' : 'Добавить в nurturing и вернуться позже';
}

function defaultProbability(c) {
  return c === 'A' ? 85 : c === 'B' ? 60 : 25;
}

function toISO(d) {
  if (!d) return '';
  return new Date(d).toISOString();
}

function nextWorkdayAtHour(h) {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(h, 0, 0, 0);
  return d;
}

function isoOrEmpty(v) {
  const t = v && new Date(v);
  return t && !isNaN(t) ? t.toISOString() : '';
}
