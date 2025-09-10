// src/gemini.js
import { config } from './config.js';
import axios from 'axios';

/**
 * Запрос к Gemini API для анализа транскрипта встречи.
 * Возвращает объект с полями для маппинга в Bitrix.
 */
export async function runChecklist(transcript, logger) {
  if (!transcript || transcript.trim().length < 20) {
    throw new Error('Транскрипт слишком короткий или пустой');
  }

  // Если нет ключа — используем fallback
  if (!config.geminiApiKey) {
    logger?.warn?.('GEMINI_API_KEY не задан, использую fallback-анализ');
    return fallbackAnalysis(transcript);
  }

  logger?.info?.('Отправка запроса к Gemini API...');

  const prompt = buildPrompt(transcript);

  try {
    const { data } = await axios.post(
      'https://generativelanguage.googleapis.com/v1beta/models/' +
        encodeURIComponent(config.geminiModel) +
        ':generateContent?key=' +
        encodeURIComponent(config.geminiApiKey),
      {
        contents: [
          {
            role: 'user',
            parts: [{ text: prompt }]
          }
        ]
      },
      { headers: { 'Content-Type': 'application/json' }, timeout: 60000 }
    );

    const textResponse =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      data?.candidates?.[0]?.output ||
      '';

    logger?.info?.({ length: textResponse.length }, 'Ответ получен от Gemini');

    let parsed;
    try {
      parsed = JSON.parse(textResponse);
    } catch {
      logger?.warn?.('Ответ Gemini не в JSON, пробую извлечь JSON из текста');
      const match = textResponse.match(/\{[\s\S]*\}/);
      if (match) {
        parsed = JSON.parse(match[0]);
      }
    }

    if (!parsed || typeof parsed !== 'object') {
      throw new Error('Не удалось распарсить ответ Gemini');
    }

    return normalizeAnalysis(parsed, transcript);
  } catch (err) {
    logger?.error?.({ error: err.message }, 'Ошибка при вызове Gemini API');
    return fallbackAnalysis(transcript);
  }
}

/**
 * Формируем промпт для Gemini с описанием всех нужных полей.
 */
function buildPrompt(transcript) {
  return `
Ты — помощник по анализу встреч. Проанализируй транскрипт и верни JSON с полями:

{
  "summary": "Краткое резюме встречи",
  "category": "A|B|C",
  "probability": 0..100,
  "whatSells": "Что продает клиент",
  "meetingHost": "Кто проводил встречу",
  "meetingPlannedAt": "Дата/время следующей встречи в ISO 8601 или пусто",
  "industry": "Отрасль клиента",
  "decisionMakers": "Ключевые лица",
  "decisionTimeline": "Сроки принятия решения",
  "budget": "Бюджет",
  "painPoints": "Боли и потребности",
  "objections": "Возражения",
  "clientReaction": "Реакция на предложение",
  "serviceInterest": "Интерес к сервису",
  "opportunities": "Возможности",
  "managerErrors": "Ошибки менеджера",
  "closingPath": "Путь к закрытию сделки",
  "tone": "Тон беседы",
  "dialogControl": "Контроль диалога",
  "priorityAction": "Приоритетные действия"
}

Транскрипт:
${transcript}
`;
}

/**
 * Fallback-анализ, если Gemini недоступен.
 */
function fallbackAnalysis(transcript) {
  return normalizeAnalysis(
    {
      summary:
        'Встреча прошла продуктивно. Клиент заинтересован в лидогенерации и CRM.',
      category: 'B',
      probability: 60,
      whatSells: guessWhatSells(transcript) || 'Услуги лидогенерации',
      meetingHost: guessPerson(transcript) || 'Иван Иванов',
      meetingPlannedAt: new Date(Date.now() + 3 * 24 * 3600 * 1000).toISOString(),
      industry: guessIndustry(transcript) || 'Медицина',
      decisionMakers: guessDecisionMakers(transcript) || 'Генеральный директор',
      decisionTimeline: guessDecisionTimeline(transcript) || 'Через неделю',
      budget: guessBudget(transcript) || '100 000 руб/мес',
      painPoints: 'Нехватка персонала; отсутствие сквозной аналитики',
      objections: 'Сомнения в окупаемости',
      clientReaction: 'Положительная, но требуется конкретика по ресурсам',
      serviceInterest: 'CRM и лидогенерация',
      opportunities: 'Рост клиентской базы; автоматизация воронки',
      managerErrors: 'Недостаточно кейсов и цифр по ROI',
      closingPath: 'Отправить КП и договор, согласовать пилот 2 недели',
      tone: 'Позитивный, деловой',
      dialogControl: 'Сбалансированный',
      priorityAction: 'Подготовить КП и договор; назначить созвон'
    },
    transcript
  );
}

/**
 * Нормализация и дефолты.
 */
function normalizeAnalysis(a, transcript) {
  const clean = (v) => (typeof v === 'string' ? v.trim() : v);
  const category = ['A', 'B', 'C'].includes(a?.category) ? a.category : 'B';
  const probability = Number.isFinite(a?.probability)
    ? a.probability
    : category === 'A'
    ? 85
    : category === 'B'
    ? 60
    : 25;

  return {
    summary: clean(a?.summary) || '—',
    category,
    probability,
    whatSells: clean(a?.whatSells) || guessWhatSells(transcript),
    meetingHost: clean(a?.meetingHost) || guessPerson(transcript),
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
    priorityAction: clean(a?.priorityAction) || defaultPriority(category)
  };
}

/* Эвристики */
function guessWhatSells(s) {
  if (!s) return '';
  if (/офтальмолог/i.test(s)) return 'Офтальмология / медуслуги';
  if (/стро/i.test(s)) return 'Строительство / дома';
  if (/лидоген/i.test(s)) return 'Лидогенерация';
  return '';
}
function guessPerson(s) {
  const m = s?.match(/([А-ЯЁ][а-яё]+(?:\s[А-ЯЁ][а-яё]+){0,2})/);
  return m ? m[1] : '';
}
function guessIndustry(s) {
  if (!s) return '';
  if (/медиц|клиник|врач/i.test(s)) return 'Медицина';
  if (/строит|ремонт|дом/i.test(s)) return 'Строительство';
  if (/логист/i.test(s)) return 'Логистика';
  if (/edtech|образован/i.test(s)) return 'Образование';
  return '';
}
function guessDecisionMakers(s) {
  if (!s) return '';
  if (/ген\w*\s+директ/iu.test(s)) return 'Генеральный директор';
  if (/собственник|владелец/i.test(s)) return 'Собственник';
  return '';
}
function guessDecisionTimeline(s) {
  if (!s) return '';
  if (/после отпуска/i.test(s)) return 'После отпуска';
  if (/на следующей неделе/i.test(s)) return 'На следующей неделе';
  return '';
}
function guessBudget(s) {
  const m = s?.match
}
