import { GoogleGenerativeAI } from "@google/generative-ai";
import logger from "./logger.js";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

export async function analyzeTranscript(transcript) {
  // Экранируем обратные кавычки в транскрипте
  const safeTranscript = transcript.replace(/`/g, "'");
  
  const prompt = "Ты - эксперт по продажам и переговорам. Анализируешь транскрипции встреч и " +
    "выдаешь структурированные саммари.\n\n" +
    "В начале ответа всегда указывай имя клиента в формате: \"Клиент: [Имя Фамилия]\"\n\n" +
    "ЗАДАЧА:\n" +
    "Проанализировать транскрипт и выдать отчет по 12 пунктам:\n\n" +
    "1. АНАЛИЗ ТЕКУЩЕГО БИЗНЕСА КЛИЕНТA\n" +
    "2. ВЫЯВЛЕНИЕ БОЛЕЙ И ПОТРЕБНОСТЕЙ\n" +
    "3. ВОЗРАЖЕНИЯ ПО ЛИДОГЕНЕРАЦИИ\n" +
    "4. РЕАКЦИЯ НА МОДЕЛЬ ГЕНЕРАЦИИ ЦЕЛЕВЫХ КЛИЕНТОВ\n" +
    "5. ОСОБЫЙ ИНТЕРЕС К СЕРВИСУ\n" +
    "6. НАЙДЕННЫЕ ВОЗМОЖНОСТИ\n" +
    "7. ОШИБКИ МЕНЕДЖЕРА\n" +
    "8. ПУТЬ К ЗАКРЫТИЮ\n" +
    "9. ТОН БЕСЕДЫ\n" +
    "10. КОНТРОЛЬ ДИАЛОГА\n" +
    "11. РЕКОМЕНДАЦИИ\n" +
    "12. КАТЕГОРИЯ КЛИЕНТА\n\n" +
    "ТРАНСКРИПТ:\n" +
    safeTranscript + "\n\n" +
    "ФОРМАТ ВЫВОДА:\n" +
    "Структурированный отчет по каждому пункту с конкретными примерами из транскрипта.\n" +
    "Без воды, только факты и рекомендации.";

  try {
    const result = await model.generateContent(prompt);
    const text = result.response.text();
    logger.info("✅ Отчет получен от Gemini");
    return text;
  } catch (err) {
    logger.error(`Ошибка при анализе Gemini: ${err.message}`);
    throw err;
  }
}
