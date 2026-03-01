import re
import json
from groq import Groq
from app.models.schemas import WordDoubtResponse
from app.core.config import settings

def explain_word(word: str, context: str = "") -> WordDoubtResponse:
    # Set 60s timeout
    client = Groq(api_key=settings.groq_api_key, timeout=60.0)
    clean_word = word.strip()

    ctx_instr = f'Context: "{context}"' if context else "No context provided."
    prompt = (
        f'Explain the word: "{clean_word}". {ctx_instr}\n'
        f'Return ONLY a JSON object with keys: word, word_type, meaning, '
        f'simple_explanation, example_sentences, synonyms, antonyms, origin.'
    )

    try:
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return WordDoubtResponse(**data)
    except Exception as e:
        print(f"Word assist error: {e}")

    # Fallback to prevent validation error
    return WordDoubtResponse(
        word=clean_word,
        word_type="unknown",
        meaning="Service temporarily unavailable.",
        simple_explanation="We couldn't reach the dictionary service.",
        example_sentences=[],
        synonyms=[],
        antonyms=[],
        origin=""
    )