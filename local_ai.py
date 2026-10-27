"""Необязательный локальный языковой помощник через Ollama с безопасной деградацией."""
from dataclasses import dataclass
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://localhost:11434"


@dataclass
class LocalAIStatus:
    """Статус доступности локальной языковой модели."""
    available: bool
    models: list[str]
    status_code: str  # 'ready', 'no_models', 'unreachable', 'disabled'
    message: str
    details: str = ""


def get_local_ai_status(base_url: str = DEFAULT_BASE_URL, timeout: float = 3.0) -> LocalAIStatus:
    """Безопасно проверяет доступность сервиса Ollama без выбрасывания исключений."""
    request = Request(f"{base_url.rstrip('/')}/api/tags", method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            models = [m.get("name", "") for m in payload.get("models", []) if m.get("name")]
            if models:
                return LocalAIStatus(
                    available=True,
                    models=models,
                    status_code="ready",
                    message="Локальный ИИ готов к работе.",
                    details=f"Обнаружено моделей: {len(models)}."
                )
            return LocalAIStatus(
                available=False,
                models=[],
                status_code="no_models",
                message="Сервис Ollama запущен, но в нём не загружены модели.",
                details="Требуется загрузка модели для текстовых пояснений."
            )
    except Exception as exc:
        return LocalAIStatus(
            available=False,
            models=[],
            status_code="unreachable",
            message="Локальный ИИ (Ollama) не подключён.",
            details="Базовые функции поиска, карты связей, анализа рисков и машинного обучения работают в полном объёме автономно."
        )


def list_local_models(base_url: str = DEFAULT_BASE_URL) -> list[str]:
    """Возвращает установленные в Ollama модели; при ошибке возвращает пустой список."""
    status = get_local_ai_status(base_url, timeout=1.5)
    return status.models


def ask_local_model(prompt: str, model: str, base_url: str = DEFAULT_BASE_URL, timeout: int = 120) -> str:
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
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(f"Модель «{model}» не найдена в Ollama.") from exc
        raise RuntimeError(f"Ollama вернул HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Не удалось получить ответ от локальной модели Ollama. Проверьте статус сервиса.") from exc

    answer = payload.get("response", "").strip()
    if not answer:
        raise RuntimeError("Локальная модель вернула пустой ответ.")
    return answer


def make_evidence_prompt(question: str, drug_a: str, drug_b: str, level: str | None) -> str:
    """Готовит строгий контекст из факта DDInter и вопроса пользователя для исключения галлюцинаций."""
    if level is None:
        evidence = (
            f"Для пары {drug_a} — {drug_b} запись в академической базе DDInter не найдена. "
            "Отсутствие записи не подтверждает безопасность и не доказывает отсутствие взаимодействия."
        )
    else:
        evidence = f"Для пары {drug_a} — {drug_b} в базе DDInter зафиксирована запись с уровнем опасности: {level}."

    return f"""Ты — учебный ассистент по анализу научной базы данных DDInter. Отвечай по-русски и строго по делу.
Используй только переданный научный факт. Не придумывай клинические симптомы, дозировки и исходы, которых нет в факте.
Не ставь диагноз, не давай персональных рекомендаций пациенту. Ясно разделяй факт из базы и клиническую практику.
Если записи нет в базе, обязательно укажи, что это не гарантирует безопасность сочетания.

Факт из базы DDInter: {evidence}
Вопрос пользователя: {question}

Дай объективный ответ в 2-4 предложениях: что конкретно известно из базы и почему окончательное решение принимает врач или клинический фармаколог."""


def generate_structured_explanation(drug_a: str, drug_b: str, level: str | None) -> dict[str, str]:
    """Детерминированное доказательное пояснение статуса DDInter без обращения к сторонней LLM."""
    if level is None:
        return {
            "summary": f"В текущей версии базы DDInter пара «{drug_a}» + «{drug_b}» не зарегистрирована.",
            "clinical_meaning": "Отсутствие записи в исследовательской базе не является доказательством безопасности сочетания.",
            "recommendation": "Проконсультируйтесь с лечащим врачом или фармацевтом перед совместным приёмом."
        }

    level_explanations = {
        "Major": {
            "summary": f"Для пары «{drug_a}» + «{drug_b}» в DDInter присвоен наивысший уровень риска (Major).",
            "clinical_meaning": "В литературе зафиксированы клинически значимые взаимодействия, способные вызвать серьёзные побочные реакции или срыв терапии.",
            "recommendation": "Требуется повышенное внимание, оценка соотношения риск/польза и рассмотрение альтернативных препаратов врачом."
        },
        "Moderate": {
            "summary": f"Для пары «{drug_a}» + «{drug_b}» зафиксирован умеренный уровень риска (Moderate).",
            "clinical_meaning": "Взаимодействие описано в исследованиях, может потребовать коррекции дозировки или мониторинга лабораторных показателей.",
            "recommendation": "Сообщите врачу обо всех принимаемых препаратах для подбора индивидуального режима приёма."
        },
        "Minor": {
            "summary": f"Для пары «{drug_a}» + «{drug_b}» зафиксирован незначительный уровень риска (Minor).",
            "clinical_meaning": "Взаимодействие имеет ограниченную клиническую значимость или проявляется в редких индивидуальных случаях.",
            "recommendation": "Специальных мер обычно не требуется, однако при появлении необычных симптомов обратитесь к врачу."
        },
        "Unknown": {
            "summary": f"Для пары «{drug_a}» + «{drug_b}» в источнике DDInter уровень тяжести указан как Unknown.",
            "clinical_meaning": "Факт взаимодействия отмечен в научных публикациях, однако авторы базы не классифицировали его строго по шкале тяжести.",
            "recommendation": "Необходимо опираться на официальную инструкцию к препаратам и консультацию специалиста."
        }
    }
    return level_explanations.get(level, {
        "summary": f"Уровень взаимодействия: {level}.",
        "clinical_meaning": "Сведения приведены из базы DDInter.",
        "recommendation": "Проконсультируйтесь со специалистом."
    })
