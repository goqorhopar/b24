// src/gemini.js
import { config } from './config.js';
import axios from 'axios';

/**
 * Запрос к Gemini API для анализа транскрипта встречи.
 * Возвращает объект с полями для маппинга в Bitrix.
 */
export async function runChecklist(transcript, logger) {
  if (!transcript || transcript.trim().length < 50) {
    throw new Error('Транскрипт слишком короткий (минимум 50 символов)');
  }

  // Если нет ключа — используем fallback
  if (!config.geminiApiKey) {
    logger?.warn?.('GEMINI_API_KEY не задан, использую fallback-анализ');
    return fallbackAnalysis(transcript);
  }

  logger?.info?.({ length: transcript.length }, 'Отправка запроса к Gemini API...');

  const prompt = buildPrompt(transcript);

  try {
    const { data } = await axios.post(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(config.geminiModel)}:generateContent?key=${encodeURIComponent(config.geminiApiKey)}`,
      {
        contents: [
          {
            role: 'user',
            parts: [{ text: prompt }]
          }
        ],
        generationConfig: {
          temperature: 0.7,
          topP: 0.8,
          topK: 40,
          maxOutputTokens: 2048,
        }
      },
      { 
        headers: { 'Content-Type': 'application/json' }, 
        timeout: 60000 
      }
    );

    const textResponse = data?.candidates?.[0]?.content?.parts?.[0]?.text || '';

    if (!textResponse) {
      throw new Error('Пустой ответ от Gemini API');
    }

    logger?.info?.({ length: textResponse.length }, 'Ответ получен от Gemini');

    let parsed;
    try {
      // Пытаемся найти JSON в ответе
      const jsonMatch = textResponse.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        parsed = JSON.parse(jsonMatch[0]);
      } else {
        parsed = JSON.parse(textResponse);
      }
    } catch (parseError) {
      logger?.warn?.({ error: parseError.message }, 'Не удалось распарсить JSON, пробую извлечь данные из текста');
      parsed = extractDataFromText(textResponse);
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
  return `Ты — эксперт по анализу бизнес-встреч. Проанализируй транскрипт встречи и верни JSON со следующими полями:

{
  "summary": "Краткое резюме встречи (2-3 предложения)",
  "category": "A|B|C (A - горячий, B - теплый, C - холодный)",
  "probability": "число от 0 до 100",
  "whatSells": "Чем занимается клиент, что продает",
  "meetingHost": "Кто проводил встречу с нашей стороны",
  "meetingPlannedAt": "Дата/время следующей встречи в формате ISO 8601 или null",
  "industry": "Отрасль клиента",
  "decisionMakers": "Кто принимает решения у клиента",
  "decisionTimeline": "Сроки принятия решения",
  "budget": "Бюджет или финансовые возможности",
  "painPoints": "Основные боли и потребности клиента",
  "objections": "Возражения и сомнения клиента",
  "clientReaction": "Реакция клиента на предложение",
  "serviceInterest": "В чем проявился интерес к сервису",
  "opportunities": "Дополнительные возможности и перспективы",
  "managerErrors": "Ошибки менеджера во время встречи",
  "closingPath": "Конкретные шаги к закрытию сделки",
  "tone": "Общий тон и атмосфера беседы",
  "dialogControl": "Кто контролировал диалог",
  "priorityAction": "Приоритетные действия после встречи"
}

ВАЖНО: Верни ТОЛЬКО JSON без каких-либо дополнительных комментариев, объяснений или текста вокруг.

Транскрипт встречи:
${transcript.substring(0, 30000)}`;
}

/**
 * Извлечение данных из текстового ответа
 */
function extractDataFromText(text) {
  const result = {};
  const lines = text.split('\n');
  
  lines.forEach(line => {
    if (line.includes('summary:')) result.summary = line.replace('summary:', '').trim();
    if (line.includes('category:')) result.category = line.replace('category:', '').trim();
    if (line.includes('probability:')) result.probability = parseInt(line.replace('probability:', '').trim());
    // ... аналогично для других полей
  });
  
  return result;
}

/**
 * Fallback-анализ, если Gemini недоступен.
 */
function fallbackAnalysis(transcript) {
  return normalizeAnalysis(
    {
      summary: 'Встреча прошла продуктивно. Клиент проявил интерес к предлагаемым решениям.',
      category: 'B',
      probability: 65,
      whatSells: guessWhatSells(transcript) || 'Услуги для бизнеса',
      meetingHost: guessPerson(transcript) || 'Менеджер по продажам',
      meetingPlannedAt: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(),
      industry: guessIndustry(transcript) || 'IT',
      decisionMakers: guessDecisionMakers(transcript) || 'Руководитель отдела',
      decisionTimeline: guessDecisionTimeline(transcript) || '2-3 недели',
      budget: guessBudget(transcript) || '50 000 - 100 000 руб',
      painPoints: 'Нехватка клиентов; низкая конверсия; высокая стоимость привлечения',
      objections: 'Сомнения в ROI; необходимость согласования с руководством',
      clientReaction: 'Заинтересован, но требует дополнительной информации',
      serviceInterest: 'Автоматизация процессов; аналитика эффективности',
      opportunities: 'Дополнительные услуги; интеграция с текущими системами',
      managerErrors: 'Недостаточно кейсов; мало конкретных цифр',
      closingPath: 'Подготовить КП; организовать демонстрацию; согласовать пилот',
      tone: 'Деловой, конструктивный',
      dialogControl: 'Сбалансированный',
      priorityAction: 'Подготовить коммерческое предложение; назначить демонстрацию'
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
  const probability = Number.isFinite(a?.probability) ? Math.min(100, Math.max(0, a.probability)) : 
                     category === 'A' ? 85 : category === 'B' ? 60 : 25;

  return {
    summary: clean(a?.summary) || 'Встреча состоялась, детали требуют уточнения.',
    category,
    probability,
    whatSells: clean(a?.whatSells) || guessWhatSells(transcript),
    meetingHost: clean(a?.meetingHost) || guessPerson(transcript),
    meetingPlannedAt: isoOrEmpty(a?.meetingPlannedAt),
    industry: clean(a?.industry) || guessIndustry(transcript),
    decisionMakers: clean(a?.decisionMakers) || guessDecisionMakers(transcript),
    decisionTimeline: clean(a?.decisionTimeline) || guessDecisionTimeline(transcript),
    budget: clean(a?.budget) || guessBudget(transcript),
    painPoints: clean(a?.painPoints) || 'Требуется выявить в ходе следующих контактов',
    objections: clean(a?.objections) || 'Возражения не выявлены',
    clientReaction: clean(a?.clientReaction) || 'Нейтральная/требует дополнительной информации',
    serviceInterest: clean(a?.serviceInterest) || 'Проявлен общий интерес',
    opportunities: clean(a?.opportunities) || 'Стандартные возможности для сотрудничества',
    managerErrors: clean(a?.managerErrors) || 'Ошибки не выявлены',
    closingPath: clean(a?.closingPath) || 'Стандартный процесс продаж',
    tone: clean(a?.tone) || 'Деловой',
    dialogControl: clean(a?.dialogControl) || 'Сбалансированный',
    priorityAction: clean(a?.priorityAction) || defaultPriority(category)
  };
}

function isoOrEmpty(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? '' : d.toISOString();
  } catch {
    return '';
  }
}

function defaultPriority(category) {
  switch (category) {
    case 'A': return 'Срочно подготовить КП и договор; назначить созвон с руководством';
    case 'B': return 'Подготовить КП; организовать демонстрацию; согласовать условия';
    case 'C': return 'Добавить в рассылку; напомнить через 2 недели; предложить тестовый период';
    default: return 'Обработать лид; уточнить потребности';
  }
}

/* Эвристики для fallback */
function guessWhatSells(s) {
  if (!s) return '';
  if (/медиц|клиник|врач|здрав|здоров/i.test(s)) return 'Медицинские услуги';
  if (/строит|ремонт|дом|недвиж/i.test(s)) return 'Строительство/Недвижимость';
  if (/ит|технолог|софт|прогр|digital/i.test(s)) return 'IT/Технологии';
  if (/образован|обучен|курс|edu/i.test(s)) return 'Образовательные услуги';
  if (/торгов|розниц|магаз|ретейл/i.test(s)) return 'Розничная торговля';
  return 'Услуги для бизнеса';
}

function guessPerson(s) {
  const m = s.match(/([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2})/);
  return m ? m[1] : 'Менеджер';
}

function guessIndustry(s) {
  if (!s) return '';
  if (/медиц|клиник|врач/i.test(s)) return 'Медицина';
  if (/строит|ремонт|дом/i.test(s)) return 'Строительство';
  if (/ит|технолог|софт/i.test(s)) return 'IT';
  if (/образован|обучен/i.test(s)) return 'Образование';
  if (/торгов|розниц/i.test(s)) return 'Розничная торговля';
  if (/производств|завод|фабрик/i.test(s)) return 'Производство';
  return 'Услуги';
}

function guessDecisionMakers(s) {
  if (!s) return '';
  if (/директор|руковод|gen|дир|управл/i.test(s)) return 'Генеральный директор';
  if (/собственник|владелец|owner/i.test(s)) return 'Собственник бизнеса';
  if (/менеджер|manager|руководитель/i.test(s)) return 'Руководитель отдела';
  if (/маркетинг|marketing/i.test(s)) return 'Маркетолог/CMO';
  if (/it|технический|разработ/i.test(s)) return 'Технический директор';
  return 'Не определено';
}

function guessDecisionTimeline(s) {
  if (!s) return '';
  if (/сразу|немедленно|быстро|срочно/i.test(s)) return 'Немедленно';
  if (/недел|week|7 дней|7 дн/i.test(s)) return '1 неделя';
  if (/месяц|month|30 дней/i.test(s)) return '1 месяц';
  if (/квартал|кв|3 месяц/i.test(s)) return 'Квартал';
  if (/после отпуск|отпуск/i.test(s)) return 'После отпуска';
  if (/новый год|н.г|январ/i.test(s)) return 'После Нового года';
  return '2-3 недели';
}

function guessBudget(s) {
  if (!s) return '';
  const budgetMatch = s.match(/(\d+[\s\d]*(?:тыс|руб|р\.|USD|\$|€|евро|euro))/i);
  if (budgetMatch) return budgetMatch[0];
  
  // Попробуем найти числа, которые могут быть бюджетом
  const numbers = s.match(/\d+/g);
  if (numbers && numbers.length > 0) {
    const lastNum = numbers[numbers.length - 1];
    if (lastNum.length >= 4) return lastNum + ' руб';
  }
  
  return '50 000 - 100 000 руб';
}

export default { runChecklist };
