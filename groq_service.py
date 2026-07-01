import json
import re
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, WORDS_PER_LESSON

client = Groq(api_key=GROQ_API_KEY)


def _ask_json(prompt: str) -> dict:
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "Ту як муаллими забон ҳастӣ. ФАҚАТ бо JSON холис ҷавоб деҳ, бе ҷумлаи иловагӣ, бе ```."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    text = resp.choices[0].message.content.strip()
    text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def generate_lesson(lesson_number: int, language: str) -> dict:
    lang_name = "русӣ" if language == "ru" else "англисӣ"
    prompt = f"""
Барои дарси {lesson_number} забони {lang_name} рӯйхати {WORDS_PER_LESSON} калимаи нав тартиб деҳ
(сатҳи мутобиқ ба рақами дарс - чи қадаре дарс баландтар, калимаҳо каме мураккабтар).
Ҳар калима бо тарҷумаи тоҷикӣ ва як мисоли ҳукм (бо тарҷумаи он) ҳамроҳ бошад.
Формат:
{{"words": [{{"word": "...", "translation": "...", "example": "...", "example_translation": "..."}}]}}
"""
    return _ask_json(prompt)


def generate_quiz(words: list, test_type: str) -> dict:
    words_str = ", ".join(w["word"] for w in words)
    n_questions = min(len(words), 10) if test_type == "mini" else min(len(words), 20)
    prompt = f"""
Дар асоси калимаҳои зерин {n_questions} саволи тести чандинтанобаро тартиб деҳ (4 вариант ҳар савол, як ҷавоби дуруст):
Калимаҳо: {words_str}
Формат:
{{"questions": [{{"question": "...", "options": ["...", "...", "...", "..."], "correct_index": 0}}]}}
"""
    return _ask_json(prompt)