import os, google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

def analyze_transcript(transcript: str) -> str:
    system_prompt = (
        "Ты эксперт по продажам. Проанализируй встречу по 12 пунктам: "
        "1) Анализ бизнеса 2) Боли 3) Возражения 4) Реакция 5) Интерес "
        "6) Возможности 7) Ошибки менеджера 8) Путь к закрытию 9) Тон "
        "10) Контроль 11) Рекомендации 12) Категория. "
        "Дай краткий отчёт с цитатами и итоговую категорию A/B/C + 3 шага next step."
    )
    model = genai.GenerativeModel(MODEL)
    r = model.generate_content([system_prompt, transcript],
        generation_config=genai.GenerationConfig(max_output_tokens=1200, temperature=0))
    return r.text or str(r)
