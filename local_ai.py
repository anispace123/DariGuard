"""Необязательный локальный языковой помощник через бесплатный Ollama."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://localhost:11434"


def list_local_models(base_url: str = DEFAULT_BASE_URL) -> list[str]:
    """Возвращает установленные в Ollama модели; ничего не отправляет в сеть."""
    request = Request(f"{base_url.rstrip('/')}/api/tags", method="GET")
    try:
        with urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, HTTPError, json.JSONDecodeError) as exc:
        raise ConnectionError("Ollama не отвечает. Запустите приложение Ollama и повторите проверку.") from exc
    return [model.get("name", "") for model in payload.get("models", []) if model.get("name")]


def ask_local_model(prompt: str, model: str, base_url: str = DEFAULT_BASE_URL) -> str:
    """Запрашивает локальную модель без облачного API и платного ключа."""
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(f"Модель «{model}» не найдена локально. Установите её командой `ollama pull {model}`.") from exc
        raise RuntimeError(f"Ollama вернул HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Не удалось получить ответ от локальной модели Ollama.") from exc
    answer = payload.get("response", "").strip()
    if not answer:
        raise RuntimeError("Локальная модель вернула пустой ответ. Попробуйте задать вопрос короче.")
    return answer


def make_evidence_prompt(question: str, drug_a: str, drug_b: str, level: str | None) -> str:
    """Готовит ограниченный контекст из факта DDInter и вопроса пользователя."""
    if level is None:
        evidence = (
            f"Для пары {drug_a} — {drug_b} запись в переданном наборе DDInter не найдена. "
            "Отсутствие записи не подтверждает безопасность и не доказывает отсутствие взаимодействия."
        )
    else:
        evidence = f"Для пары {drug_a} — {drug_b} в переданном наборе есть запись DDInter, уровень: {level}."
    return f"""Ты — учебный помощник по чтению базы данных DDInter. Отвечай по-русски и простыми словами.
Используй только переданный факт DDInter. Не добавляй механизмы, симптомы, частоту, лечение или иные медицинские факты, которых нет в контексте.
Не ставь диагноз, не оценивай риск конкретного пациента, не рекомендуй начинать, отменять или менять лекарства.
Ясно отличай запись базы от клинического вывода. Если вопрос требует медицинского решения, посоветуй обсудить его с врачом или фармацевтом.
Если записи нет, прямо скажи, что это не означает безопасность сочетания.

Факт из данных приложения: {evidence}
Источник факта: загруженные пользователем CSV DDInter.
Вопрос пользователя: {question}

Дай краткий ответ, отдельно перечисли, что известно из данных и чего из них заключить нельзя."""
