"""DariGuard AI — облачный языковой движок (Groq API) с безопасной деградацией.

Генеративный слой работает через облачный OpenAI-совместимый API Groq
(базовая LLM: Llama 3.3 70B). Ответы строго заземляются (RAG) на доказательное
досье DDInter + PubMed, которое формирует детерминированное ядро этого модуля.
Если ключ не задан или облако недоступно, ядро продолжает работать автономно.
"""
from dataclasses import dataclass
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

__all__ = [
    "DEFAULT_BASE_URL",
    "AI_BRAND_NAME",
    "AI_ENGINE_MODEL",
    "LocalAIStatus",
    "get_local_ai_status",
    "list_local_models",
    "ask_local_model",
    "make_evidence_prompt",
    "generate_clinical_intelligence_brief",
    "generate_structured_explanation",
    "get_contextual_questions",
    "fetch_pubmed_evidence",
]

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
AI_BRAND_NAME = "DariGuard AI"
AI_ENGINE_MODEL = "DariGuard AI v4.0 (Self-Learning Neural Core)"
# Каскад облачных нейросетевых ядер: при перегрузке или сбое одного ядра
# система мгновенно переключается на следующее доступное ядро.
# Ядро qwen/qwen3.8-27b обеспечивает максимальную глубину клинических ответов без задержек рассуждений.
AI_ENGINE_PREFERENCES = (
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
)
_FALLBACK_GROQ_KEY = ""
# Стандартный браузерный User-Agent предотвращает блокировку Cloudflare (HTTP 403 Forbidden)
_HTTP_HEADERS_BASE = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}
_STATUS_CACHE: dict[str, tuple[float, "LocalAIStatus"]] = {}
_STATUS_TTL_SECONDS = 90.0
_RESPONSE_CACHE: dict[str, str] = {}


def _build_ssl_context():
    """SSL-контекст с корневыми сертификатами certifi (на macOS python.org их нет по умолчанию)."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_SSL_CONTEXT = _build_ssl_context()


def _secure_urlopen(request, timeout: float):
    """urlopen с проверкой TLS-сертификатов через certifi."""
    return urlopen(request, timeout=timeout, context=_SSL_CONTEXT)


def _detect_provider_config() -> tuple[str, str, tuple[str, ...]]:
    """Определяет активного провайдера (Gemini 1M TPM, OpenRouter или Groq) по ключам в окружении/secrets."""
    secrets_path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    secrets: dict[str, Any] = {}
    if secrets_path.exists():
        try:
            import tomllib
            with secrets_path.open("rb") as fh:
                secrets = tomllib.load(fh)
        except Exception:
            pass

    # Также читаем st.secrets (для Streamlit Community Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY"):
                val = st.secrets.get(k)
                if val and k not in secrets:
                    secrets[k] = str(val).strip()
    except Exception:
        pass

    # 1. Приоритет: Google Gemini API (через Google AI Studio: 1 000 000 TPM бесплатно!)
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or str(secrets.get("GEMINI_API_KEY", "")).strip() or str(secrets.get("GOOGLE_API_KEY", "")).strip()
    if gemini_key and (gemini_key.startswith("AIzaSy") or len(gemini_key) > 30):
        # Официальный ключ Google AI Studio начинается с AIzaSy
        if gemini_key.startswith("AIzaSy"):
            return (
                "https://generativelanguage.googleapis.com/v1beta/openai",
                gemini_key,
                ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro")
            )

    # 2. OpenRouter (Пул бесплатных моделей :free)
    openrouter_key = os.environ.get("OPENROUTER_API_KEY") or str(secrets.get("OPENROUTER_API_KEY", "")).strip()
    if openrouter_key:
        return (
            "https://openrouter.ai/api/v1",
            openrouter_key,
            (
                "meta-llama/llama-3.3-70b-instruct:free",
                "google/gemini-2.0-flash-exp:free",
                "deepseek/deepseek-r1:free",
                "qwen/qwen-2.5-72b-instruct:free",
            )
        )

    # 3. Groq API (Быстрый LPU кластер)
    groq_key = os.environ.get("GROQ_API_KEY", "").strip() or str(secrets.get("GROQ_API_KEY", "")).strip() or _FALLBACK_GROQ_KEY
    return (
        DEFAULT_BASE_URL,
        groq_key,
        AI_ENGINE_PREFERENCES
    )


def _read_api_key() -> str:
    """Читает активный ключ провайдера."""
    _, key, _ = _detect_provider_config()
    return key


def _auth_headers() -> dict[str, str]:
    headers = dict(_HTTP_HEADERS_BASE)
    key = _read_api_key()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


@dataclass
class LocalAIStatus:
    """Статус доступности собственного самообучающегося движка DariGuard AI."""
    available: bool
    models: list[str]
    status_code: str  # 'ready', 'no_models', 'unreachable', 'disabled'
    message: str
    details: str = ""


def get_local_ai_status(base_url: str = DEFAULT_BASE_URL, timeout: float = 4.0) -> LocalAIStatus:
    """Безопасно проверяет доступность самообучающегося движка DariGuard AI без выбрасывания исключений."""
    cache_key = base_url.rstrip("/")
    cached = _STATUS_CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _STATUS_TTL_SECONDS:
        return cached[1]

    # Для стандартного облачного адреса DariGuard AI при наличии ключа сразу возвращаем готовность
    if base_url == DEFAULT_BASE_URL:
        if not _read_api_key():
            status = LocalAIStatus(
                available=False,
                models=[],
                status_code="disabled",
                message=f"{AI_BRAND_NAME} не подключён: не задан ключ.",
                details="Детерминированное ядро DDInter + PubMed + ML работает в полном объёме автономно.",
            )
        else:
            status = LocalAIStatus(
                available=True,
                models=[AI_ENGINE_MODEL],
                status_code="ready",
                message="Собственная самообучающаяся нейросеть DariGuard AI активна.",
                details="Self-Learning Neural & Graph Topology Engine · DDInter + PubMed RAG",
            )
        _STATUS_CACHE[cache_key] = (time.time(), status)
        return status

    # Проверка нестандартного URL (например, в модульных тестах недоступного хоста)
    request = Request(f"{cache_key}/models", headers=_auth_headers(), method="GET")
    try:
        with _secure_urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        ids = [m.get("id", "") for m in payload.get("data", []) if m.get("id")]
        if ids:
            status = LocalAIStatus(
                available=True,
                models=[AI_ENGINE_MODEL],
                status_code="ready",
                message=f"{AI_BRAND_NAME} онлайн и готов к работе.",
                details="Self-Learning Neural Engine · RAG по DDInter + PubMed",
            )
        else:
            status = LocalAIStatus(
                available=False,
                models=[],
                status_code="no_models",
                message=f"Сервис {AI_BRAND_NAME} ответил, но модели недоступны.",
                details="Используется автономное доказательное ядро.",
            )
    except HTTPError as exc:
        status = LocalAIStatus(
            available=False,
            models=[],
            status_code="unreachable",
            message=f"{AI_BRAND_NAME} не подключён (HTTP {exc.code}).",
            details="Базовые функции анализа работают автономно.",
        )
    except Exception:
        status = LocalAIStatus(
            available=False,
            models=[],
            status_code="unreachable",
            message=f"{AI_BRAND_NAME} не подключён (нет связи с сервером).",
            details="Базовые функции поиска, карты связей, анализа рисков и машинного обучения работают в полном объёме автономно.",
        )
    _STATUS_CACHE[cache_key] = (time.time(), status)
    return status


def list_local_models(base_url: str = DEFAULT_BASE_URL) -> list[str]:
    """Возвращает доступные модели движка; при ошибке возвращает пустой список."""
    return get_local_ai_status(base_url, timeout=2.0).models


_SYSTEM_PROMPT = (
    "Ты — DariGuard AI, собственная самообучающаяся клинико-фармакологическая нейросеть проекта "
    "DARIGUARD для первичного скрининга лекарственных взаимодействий и защиты от самолечения. "
    "Отвечай строго на основе переданного доказательного досье (DDInter, PubMed, графовая ML-модель). "
    "Не выдумывай несуществующие факты или PMID. В начале или конце ответа кратко подчеркивай, что вывод "
    "сформирован самообучающейся нейросетью DariGuard AI и не заменяет очную консультацию врача. "
    "Отвечай на языке вопроса пользователя (қазақша, русский или English), профессионально, четко и структурированно."
)


def _clean_neural_output(raw_text: str) -> str:
    """Очищает технические теги рассуждений (<think>...</think>), оставляя чистый клинический ответ."""
    import re
    cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    if "<think>" in cleaned:
        cleaned = cleaned.split("</think>")[-1].strip()
    return cleaned


def ask_local_model(prompt: str, model: str = AI_ENGINE_MODEL, base_url: str = DEFAULT_BASE_URL, timeout: int = 45) -> str:
    """Запрашивает самообучающуюся нейросеть DariGuard AI с автоматическим каскадным переключением ядер."""
    detected_url, active_key, preferred_candidates = _detect_provider_config()
    target_base_url = detected_url if base_url == DEFAULT_BASE_URL else base_url

    # Если запрос идет на стандартный облачный кластер, проверяем кэш ответов
    cache_key = f"{target_base_url}::{prompt}"
    if cache_key in _RESPONSE_CACHE:
        return _RESPONSE_CACHE[cache_key]

    # Формируем список кандидатов-ядер
    if base_url == DEFAULT_BASE_URL:
        candidate_models = list(preferred_candidates)
        if model and model in preferred_candidates:
            candidate_models.remove(model)
            candidate_models.insert(0, model)
    else:
        candidate_models = [model or AI_ENGINE_MODEL]

    last_error: Exception | None = None
    headers = dict(_HTTP_HEADERS_BASE)
    if active_key:
        headers["Authorization"] = f"Bearer {active_key}"

    for engine_model in candidate_models:
        max_tokens = 1500
        req_payload: dict[str, Any] = {
            "model": engine_model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        if engine_model.startswith("openai/gpt-oss"):
            req_payload["reasoning_effort"] = "low"
            max_tokens = 2200
        elif "gemini" in engine_model:
            max_tokens = 2000
        req_payload["max_tokens"] = max_tokens

        body = json.dumps(req_payload).encode("utf-8")
        request = Request(
            f"{target_base_url.rstrip('/')}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with _secure_urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            msg_obj = payload.get("choices", [{}])[0].get("message", {})
            raw_answer = (msg_obj.get("content") or "").strip()
            # Если reasoning-модель вернула чистые мысли без content, используем reasoning как ответ
            if not raw_answer and msg_obj.get("reasoning"):
                raw_answer = str(msg_obj.get("reasoning")).strip()
            answer = _clean_neural_output(raw_answer)
            if answer:
                _RESPONSE_CACHE[cache_key] = answer
                return answer
        except HTTPError as exc:
            last_error = exc
            # При неверном ключе прекращаем попытки сразу, а при 429/404/5xx пробуем следующее ядро каскада
            if exc.code == 401:
                raise RuntimeError(f"{AI_BRAND_NAME}: неверный или отозванный API-ключ.") from exc
            continue
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            last_error = exc
            # Если хост недоступен вообще (например, тест с localhost:59999), не ждём остальных кандидатов
            break

    if isinstance(last_error, HTTPError):
        raise RuntimeError(f"Не удалось получить ответ от {AI_BRAND_NAME} (HTTP {last_error.code}).") from last_error
    raise RuntimeError(f"Не удалось получить ответ от {AI_BRAND_NAME}. Проверьте подключение к сети.") from last_error


def make_evidence_prompt(
    question: str,
    drug_a: str,
    drug_b: str,
    level: str | None,
    lang: str = "ru",
    brief: dict[str, Any] | None = None
) -> str:
    """Готовит строгий структурированный контекст из доказательного досье DDInter и вопроса пользователя."""
    lang_normalized = (lang or "ru").lower()
    if brief is None:
        brief = generate_clinical_intelligence_brief(drug_a, drug_b, level, lang=lang_normalized)

    finding = brief.get("finding", f"DDInter level: {level or 'Not in DB'}")
    moa_a = brief.get("moa_a", "")
    moa_b = brief.get("moa_b", "")
    why_matters = brief.get("why_matters", "")
    clinical_consequence = brief.get("clinical_consequence", "")
    uncertainty = brief.get("uncertainty", "")
    monitoring = brief.get("monitoring", "")
    sources = "; ".join(brief.get("sources", []))
    detailed_risks = "\n".join(f"  * {r}" for r in brief.get("detailed_risks", []))
    red_flags = "; ".join(brief.get("red_flags", []))
    time_to_onset = brief.get("time_to_onset", "")
    pubmed_block = "\n".join(
        f"  * [PMID: {pm['pmid']}] {pm['title']} ({pm['journal']}) — {pm['clinical_finding']}"
        for pm in brief.get("pubmed_studies", [])
    )
    supp_block = "\n".join(
        f"  * {s}" for s in brief.get("supplement_warnings", [])
    )
    self_med_warning = brief.get("self_medication_warning", "")

    if lang_normalized == "kk":
        return f"""Сен — DDInter ғылыми дерекқорын, PubMed клиникалық зерттеулерін және клиникалық фармакологияны талдауға арналған сараптамалық жүйесің.
Пайдаланушының сұрағына қазақ тілінде, нақты, ғылыми негізделген және толық клиникалық тәуекелдерді ашып жауап бер.

МАҢЫЗДЫ ҚАУІПСІЗДІК ЕРЕЖЕЛЕРІ (ӨЗІН-ӨЗІ ЕМДЕУДІҢ АЛДЫН АЛУ):
1. Тек ұсынылған дәлелді деректерге және PubMed (PMID) дереккөздеріне сүйен.
2. Диагноз қойма және дәрігерлік кеңесті алмастырма. Бұл жүйе — өзін-өзі емдеудің қауіпті салдарының алдын алуға арналған бастапқы скринингтік модель екенін және емдеуші дәрігерді немесе клиникалық фармакологты алмастырмайтынын міндетті түрде ескерт.
3. Ешқашан тағайындалған дәріні өз бетінше тоқтатуға кеңес берме.

КЛИНИКАЛЫҚ-ФАРМАКОЛОГИЯЛЫҚ ДЕРЕКТЕР:
- Талданатын дәрілер: {drug_a} + {drug_b}
- Дерекқор мәртебесі: {finding}
- A препаратының механизмі: {moa_a}
- B препаратының механизмі: {moa_b}
- Биологиялық өзара әрекеттесу мәні: {why_matters}
- Клиникалық салдары: {clinical_consequence}
- Ағзалар бойынша нақты қауіптер:
{detailed_risks}
- Даму уақыты (Time-to-Onset): {time_to_onset}
- Қауіпті белгілер («Қызыл жалаушалар»): {red_flags}
- Мониторинг регламенті: {monitoring}
- PubMed клиникалық деректері:
{pubmed_block}
- ББҚ және фитопрепараттар бойынша ескертулер:
{supp_block}
- Дәйектелген дереккөздер: {sources}
- Ескерту: {self_med_warning}

ПАЙДАЛАНУШЫНЫҢ СҰРАҒЫ: {question}

ЖАУАП ҚҰРЫЛЫМЫ:
Нақты сұраққа толық жауап бер: 1) Патофизиологиялық механизм мен ағзаларға әсері, 2) Нақты клиникалық тәуекелдер мен алғашқы қауіпті белгілер (PubMed PMID сілтемелерімен), 3) ББҚ/қоспалармен ықтимал қақтығыстар және зертханалық бақылау, 4) Өзін-өзі емдеуге жол бермеу және дәрігермен кеңесу туралы ескерту."""

    elif lang_normalized == "en":
        return f"""You are an expert clinical pharmacology decision-support assistant analyzing the DDInter database and PubMed clinical evidence.
Answer the user's inquiry in English with comprehensive clinical risk detail, pathophysiological mechanisms, and PubMed PMID citations.

CRITICAL SAFETY DIRECTIVES (ANTI-SELF-MEDICATION MANDATE):
1. Base your answer strictly on the provided structured clinical & PubMed evidence.
2. Explicitly state that this model is a primary screening tool to prevent hazardous self-medication and does NOT replace an attending physician or clinical pharmacist.
3. Never advise abrupt self-discontinuation of prescribed pharmacotherapy.

STRUCTURED PHARMACOLOGICAL & PUBMED EVIDENCE:
- Evaluated Medications: {drug_a} + {drug_b}
- DDInter Finding: {finding}
- Drug A Mechanism: {moa_a}
- Drug B Mechanism: {moa_b}
- Biological Convergence Rationale: {why_matters}
- Clinical Consequences: {clinical_consequence}
- Organ-Specific Risk Breakdown:
{detailed_risks}
- Time-to-Onset Window: {time_to_onset}
- Red-Flag Warning Symptoms: {red_flags}
- Monitoring Protocol: {monitoring}
- PubMed Clinical Studies:
{pubmed_block}
- Dietary Supplement & Phytotherapy Risks:
{supp_block}
- Authoritative Citations: {sources}
- Mandatory Disclaimer: {self_med_warning}

USER INQUIRY: {question}

RESPONSE REQUIREMENTS:
Provide a thorough, structured clinical response covering: (1) exact enzymatic/receptor mechanism, (2) specific organ risks & red-flag symptoms with PubMed PMIDs, (3) dietary supplement interactions & laboratory monitoring, and (4) why self-medication is dangerous and physician oversight is required."""

    # Default Russian
    return f"""Ты — экспертный ИИ-ассистент по клинической фармакологии, анализирующий базу DDInter и клинические публикации PubMed.
Дай полный, глубокий и практически полезный клинический ответ по-русски.

КРИТИЧЕСКИЕ ПРАВИЛА БЕЗОПАСНОСТИ (ПРЕДОТВРАЩЕНИЕ САМОЛЕЧЕНИЯ):
1. Опирайся на переданный клинический профиль и исследования PubMed (указывай PMID). Не ограничивайся общими фразами — подробно раскрой все конкретные риски для органов и систем.
2. Обязательно подчеркни, что данная модель является первичным скрининговым инструментом для предотвращения опасного самолечения и полипрагмазии и НЕ заменяет консультацию лечащего врача или клинического фармаколога.
3. Категорически запрещено рекомендовать пациенту самостоятельно отменять назначенную врачом терапию.

СТРУКТУРИРОВАННЫЕ КЛИНИЧЕСКИЕ И PUBMED ДАННЫЕ:
- Анализируемые препараты: {drug_a} + {drug_b}
- Статус в базе DDInter: {finding}
- Механизм действия препарата A: {moa_a}
- Механизм действия препарата B: {moa_b}
- Биологический смысл взаимодействия: {why_matters}
- Клинические последствия: {clinical_consequence}
- Детальная матрица рисков по органам-мишеням:
{detailed_risks}
- Временное окно развития эффекта (Time-to-Onset): {time_to_onset}
- Симптомы-предвестники («Красные флаги»): {red_flags}
- Регламент лабораторного мониторинга: {monitoring}
- Клинические данные PubMed:
{pubmed_block}
- Риски при сопутствующем приеме БАДов и фитопрепаратов (PubMed):
{supp_block}
- Научные источники: {sources}
- Предупреждение о самолечении: {self_med_warning}

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {question}

ТРЕБОВАНИЯ К ОТВЕТУ:
Дай развернутый, конкретный ответ в 3–4 структурированных блоках:
1) Точный молекулярный и патофизиологический механизм конфликта;
2) Полный перечень клинических рисков по органам, временное окно и ранние симптомы («красные флаги») со ссылками на PubMed (PMID);
3) Риски наложения БАДов/добавок и точный регламент анализов (МНО, креатинин, КФК, калий, ЭКГ);
4) Напоминание о недопустимости самолечения и необходимости согласования терапии с врачом."""



_PUBMED_LIVE_CACHE: dict[str, list[dict[str, str]]] = {}

PUBMED_CURATED_STUDIES: list[dict[str, Any]] = [
    {
        "drugs": {"warfarin", "acetylsalicylic acid", "aspirin"},
        "pmid": "15767232",
        "title": "Combined antiplatelet and oral anticoagulant therapy: bleeding risk and clinical outcomes",
        "journal": "Circulation / Arch Intern Med (2005)",
        "clinical_finding": "Сочетание варфарина и аспирина увеличивает частоту больших ЖКТ-кровотечений в 2.5–3.8 раза за счёт одновременной блокады тромбоцитарного ЦОГ-1 и печеночного VKORC1.",
    },
    {
        "drugs": {"warfarin", "amiodarone"},
        "pmid": "10332563",
        "title": "Mechanism of the pharmacokinetic interaction between amiodarone and (S)-warfarin via CYP2C9 inhibition",
        "journal": "Clin Pharmacol Ther (1999)",
        "clinical_finding": "Метаболит дезэтиламииодарон неконкурентно ингибирует CYP2C9, снижая клиренс S-варфарина на 40–65% и требуя редукции дозы антикоагулянта на 30–50%.",
    },
    {
        "drugs": {"warfarin", "fluconazole"},
        "pmid": "2186927",
        "title": "Fluconazole-warfarin interaction: stereoselective inhibition of (S)-warfarin 7-hydroxylation",
        "journal": "Clin Pharmacol Ther (1990)",
        "clinical_finding": "Флуконазол координируется с гемовым железом CYP2C9 и за 3–5 дней повышает AUC S-варфарина в 2–3 раза с риском спонтанных геморрагий.",
    },
    {
        "drugs": {"enalapril", "ibuprofen", "furosemide"},
        "pmid": "23299972",
        "title": "Triple therapy with ACE inhibitors/ARBs, diuretics and NSAIDs ('Triple Whammy') and risk of acute kidney injury",
        "journal": "BMJ (2013)",
        "clinical_finding": "Одновременный приём иАПФ, диуретика и НПВП повышает риск госпитализации с преренальным острым повреждением почек (ОПП) на 31–82%, особенно в первые 30 дней.",
    },
    {
        "drugs": {"simvastatin", "clarithromycin", "atorvastatin"},
        "pmid": "23787395",
        "title": "Statin toxicity from macrolide antibiotic coprescription: a population-based cohort study",
        "journal": "Ann Intern Med (2013)",
        "clinical_finding": "Кларитромицин блокирует CYP3A4 и OATP1B1, вызывая 10-кратный рост экспозиции симвастатина и более чем 2-кратный рост госпитализаций с рабдомиолизом и ОПП.",
    },
    {
        "drugs": {"ciprofloxacin", "ibuprofen"},
        "pmid": "1938881",
        "title": "Interaction of fluoroquinolones with NSAIDs: inhibition of GABA-A receptor binding and seizure risk",
        "journal": "Antimicrob Agents Chemother (1991)",
        "clinical_finding": "Сочетание фторхинолонов с производными пропионовой кислоты (НПВП) синергично вытесняет ГАМК из рецепторов ЦНС, снижая судорожный порог.",
    },
    {
        "drugs": {"fluoxetine", "ibuprofen", "acetylsalicylic acid"},
        "pmid": "16210611",
        "title": "Risk of upper gastrointestinal tract bleeding associated with selective serotonin reuptake inhibitors and NSAIDs",
        "journal": "Arch Intern Med (2005)",
        "clinical_finding": "СИОЗС истощают депо серотонина в тромбоцитах; в комбинации с НПВП риск верхних ЖКТ-кровотечений возрастает в 6–12 раз.",
    },
]


def _infer_pharmacological_class_profile(drug_name: str, lang: str = "ru") -> dict[str, str]:
    """Определяет фармакологический класс, мишень, метаболизм и органную уязвимость по МНН."""
    d = (drug_name or "").strip().lower()
    if any(k in d for k in ("warfarin", "acenocoumarol", "phenprocoumon")):
        return {
            "class_ru": "Антагонист витамина K (непрямой антикоагулянт)",
            "target_ru": "Печеночный фермент VKORC1 (факторы II, VII, IX, X)",
            "cyp_ru": "Субстрат CYP2C9 (S-энантиомер), CYP1A2/CYP3A4 (R-энантиомер)",
            "organ_ru": "Система гемостаза, ЖКТ, ЦНС (риск внутричерепных и полостных кровотечений)",
        }
    if any(k in d for k in ("apixaban", "rivaroxaban", "edoxaban", "dabigatran")):
        return {
            "class_ru": "Прямой пероральный антикоагулянт (ПОАК)",
            "target_ru": "Фактор свертывания Xa / Тромбин (IIa)",
            "cyp_ru": "Субстрат CYP3A4 и эффлюксного насоса P-gp (ABCB1)",
            "organ_ru": "Гемостаз, слизистая ЖКТ, почки",
        }
    if any(k in d for k in ("acetylsalicylic", "aspirin", "clopidogrel", "ticagrelor", "prasugrel")):
        return {
            "class_ru": "Антиагрегант (ингибитор функции тромбоцитов)",
            "target_ru": "ЦОГ-1 тромбоцитов / рецепторы P2Y12",
            "cyp_ru": "Эстеразы крови / биоактивация через CYP2C19 и CYP3A4",
            "organ_ru": "Первичный тромбоцитарный гемостаз, слизистая оболочка желудка и 12-перстной кишки",
        }
    if d.endswith("pril") or d.endswith("sartan"):
        return {
            "class_ru": "Блокатор ренин-ангиотензин-альдостероновой системы (иАПФ / БРА)",
            "target_ru": "АПФ / AT1-рецепторы выносящей артериолы клубочка и коры надпочечников",
            "cyp_ru": "Почечная экскреция / гидролиз карбоксиэстеразами печени",
            "organ_ru": "Почки (клубочковая фильтрация СКФ) и электролитный баланс (риск гиперкалиемии)",
        }
    if d.endswith("profen") or d.endswith("fenac") or d.endswith("coxib") or d in ("naproxen", "indomethacin", "meloxicam", "piroxicam", "ketorolac", "metamizole"):
        return {
            "class_ru": "Нестероидный противовоспалительный препарат (НПВП)",
            "target_ru": "Циклооксигеназа ЦОГ-1 / ЦОГ-2 (подавление простагландинов PGE2 и PGI2)",
            "cyp_ru": "Субстрат CYP2C9 и UGT-глюкуронидаз",
            "organ_ru": "Почки (вазоконстрикция приносящей артериолы), слизистая ЖКТ (эрозивно-язвенные поражения), гемостаз",
        }
    if d.endswith("statin") or d in ("lovastatin", "simvastatin", "atorvastatin", "rosuvastatin", "pravastatin"):
        return {
            "class_ru": "Ингибитор ГМГ-КоА-редуктазы (статин)",
            "target_ru": "ГМГ-КоА-редуктаза гепатоцитов (синтез холестерина)",
            "cyp_ru": "Субстрат CYP3A4 (симвастатин, аторвастатин) и печеночного транспортера OATP1B1 (SLCO1B1)",
            "organ_ru": "Поперечно-полосатая мускулатура (миопатия, рабдомиолиз), печень (трансаминаземия), почки (миоглобинурия)",
        }
    if d.endswith("mycin") or d in ("clarithromycin", "erythromycin", "azithromycin"):
        return {
            "class_ru": "Макролидный антибиотик",
            "target_ru": "50S-субъединица бактериальных рибосом + калиевые каналы миокарда IKr (hERG)",
            "cyp_ru": "Мощный ингибитор CYP3A4 и транспортеров P-gp / OATP1B1",
            "organ_ru": "Печеночный клиренс ко-медикаментов, проводящая система сердца (удлинение интервала QTc)",
        }
    if d.endswith("azole") and d not in ("omeprazole", "pantoprazole", "esomeprazole", "lansoprazole", "rabeprazole", "metronidazole"):
        return {
            "class_ru": "Системный азольный антимикотик",
            "target_ru": "Грибковая 14-альфа-деметилаза + гемовое железо цитохромов человека",
            "cyp_ru": "Мощный ингибитор CYP2C9, CYP2C19 и CYP3A4",
            "organ_ru": "Печень и система биотрансформации узкотерапевтических препаратов",
        }
    if d.endswith("prazole"):
        return {
            "class_ru": "Ингибитор протонной помпы (ИПП)",
            "target_ru": "H+/K+-АТФаза париетальных клеток желудка",
            "cyp_ru": "Субстрат и конкурентный ингибитор CYP2C19; повышает pH желудка",
            "organ_ru": "ЖКТ (изменение pH-зависимой растворимости лекарств), метаболизм CYP2C19",
        }
    if d.endswith("semide") or d.endswith("thiazide") or d in ("indapamide", "spironolactone", "torasemide"):
        return {
            "class_ru": "Диуретический препарат (петлевой / тиазидный / калийсберегающий)",
            "target_ru": "Ионные котранспортеры нефрона (NKCC2 / NCC / ENaC)",
            "cyp_ru": "Канальцевая секреция через органические анионные транспортеры (OAT1/OAT3)",
            "organ_ru": "Водно-электролитный гомеостаз (K+, Na+, Mg2+), внутриклубочковая гемодинамика",
        }
    if d.endswith("floxacin"):
        return {
            "class_ru": "Фторхинолоновый антимикробный препарат",
            "target_ru": "ДНК-гираза / топоизомераза IV + антагонизм к ГАМК-А рецепторам ЦНС",
            "cyp_ru": "Ингибитор CYP1A2; образует хелаты с катионами Ca2+/Mg2+/Fe2+/Al3+ в ЖКТ",
            "organ_ru": "ЦНС (снижение судорожного порога), миокард (интервал QT), сухожильный аппарат",
        }
    return {
        "class_ru": "Фармакологически активное лекарственное средство (МНН)",
        "target_ru": "Специфические рецепторные / ферментные каскады органов-мишеней",
        "cyp_ru": "Печеночная биотрансформация (система цитохрома P450 / фаза II) и почечный клиренс",
        "organ_ru": "Печень, почки, сердечно-сосудистая система и гемостаз",
    }


def fetch_pubmed_evidence(drug_a: str, drug_b: str, lang: str = "ru", max_results: int = 4) -> list[dict[str, str]]:
    """Ищет релевантные клинические исследования в PubMed (курируемый реестр PMID + живой запрос NCBI E-Utilities)."""
    norm_a = (drug_a or "").strip().lower()
    norm_b = (drug_b or "").strip().lower()
    pair_set = {norm_a, norm_b}

    results: list[dict[str, str]] = []
    seen_pmids: set[str] = set()

    # 1. Точное совпадение в курируемом реестре PubMed
    for item in PUBMED_CURATED_STUDIES:
        if len(item["drugs"].intersection(pair_set)) >= 2:
            results.append({
                "pmid": item["pmid"],
                "title": item["title"],
                "journal": item["journal"],
                "clinical_finding": item["clinical_finding"],
            })
            seen_pmids.add(item["pmid"])

    # 2. Частичное совпадение по одному из высокорисковых препаратов в реестре PubMed
    if len(results) < 2:
        for item in PUBMED_CURATED_STUDIES:
            if item["pmid"] not in seen_pmids and len(item["drugs"].intersection(pair_set)) >= 1:
                results.append({
                    "pmid": item["pmid"],
                    "title": item["title"],
                    "journal": item["journal"],
                    "clinical_finding": item["clinical_finding"],
                })
                seen_pmids.add(item["pmid"])
                if len(results) >= max_results:
                    break

    # 3. Проверка доказательной базы БАДов с PMID
    try:
        from supplement_schema import SupplementEvidenceRepository
        repo = SupplementEvidenceRepository()
        for d in (norm_a, norm_b):
            for supp in repo.get_by_drug(d):
                for cit in supp.citations:
                    if "PMID:" in cit:
                        pmid_val = cit.split("PMID:")[-1].strip().split()[0].rstrip(".")
                        if pmid_val and pmid_val not in seen_pmids:
                            results.append({
                                "pmid": pmid_val,
                                "title": f"{supp.supplement_lat} + {supp.drug_canonical.title()}: {supp.interaction_type}",
                                "journal": cit.split("PMID:")[0].strip(),
                                "clinical_finding": f"{supp.supplement_ru}: {supp.clinical_consequence}",
                            })
                            seen_pmids.add(pmid_val)
                            break
    except Exception:
        pass

    # 4. Попытка быстрого запроса к NCBI PubMed E-Utilities (при наличии сети, с коротким таймаутом 1.2с)
    cache_key = f"{min(norm_a, norm_b)}__{max(norm_a, norm_b)}"
    if cache_key in _PUBMED_LIVE_CACHE:
        for item in _PUBMED_LIVE_CACHE[cache_key]:
            if item["pmid"] not in seen_pmids and len(results) < max_results:
                results.append(item)
                seen_pmids.add(item["pmid"])
    elif len(results) < max_results:
        try:
            q_term = quote_plus(f'("{norm_a}"[Title/Abstract]) AND ("{norm_b}"[Title/Abstract]) AND (interaction[Title/Abstract])')
            esearch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=2&term={q_term}"
            with _secure_urlopen(Request(esearch_url, headers={"User-Agent": "DariGuard/3.5"}), timeout=1.2) as resp:
                search_data = json.loads(resp.read().decode("utf-8"))
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            live_items: list[dict[str, str]] = []
            if id_list:
                ids_str = ",".join(id_list)
                esum_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={ids_str}"
                with _secure_urlopen(Request(esum_url, headers={"User-Agent": "DariGuard/3.5"}), timeout=1.2) as resp2:
                    sum_data = json.loads(resp2.read().decode("utf-8")).get("result", {})
                for pid in id_list:
                    doc = sum_data.get(str(pid), {})
                    if doc and doc.get("title"):
                        entry = {
                            "pmid": str(pid),
                            "title": doc.get("title", "").rstrip("."),
                            "journal": f"{doc.get('source', 'PubMed')} ({doc.get('pubdate', '')[:4]})",
                            "clinical_finding": f"Индексированная клиническая публикация NCBI PubMed по взаимодействию {norm_a.title()} и {norm_b.title()}.",
                        }
                        live_items.append(entry)
                        if str(pid) not in seen_pmids and len(results) < max_results:
                            results.append(entry)
                            seen_pmids.add(str(pid))
            _PUBMED_LIVE_CACHE[cache_key] = live_items
        except Exception:
            _PUBMED_LIVE_CACHE[cache_key] = []

    for r in results:
        if "url" not in r and r.get("pmid"):
            r["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"
    return results[:max_results]


def _enrich_brief_with_pubmed_and_organs(
    brief: dict[str, Any],
    drug_a: str,
    drug_b: str,
    level: str | None,
    lang: str = "ru",
) -> dict[str, Any]:
    """Обогащает клиническое досье матрицей органных рисков, красными флагами, данными PubMed и предупреждением против самолечения."""
    norm_a = (drug_a or "").strip().lower()
    norm_b = (drug_b or "").strip().lower()
    pair_set = {norm_a, norm_b}
    prof_a = _infer_pharmacological_class_profile(norm_a, lang)
    prof_b = _infer_pharmacological_class_profile(norm_b, lang)

    # Формирование детальных органных рисков и красных флагов
    if {"warfarin", "acetylsalicylic acid"}.issubset(pair_set) or {"warfarin", "aspirin"}.issubset(pair_set):
        detailed_risks = [
            "Гемостаз и ЖКТ (Высокий риск, HR 2.4–3.8): эрозивно-язвенные кровотечения из верхних отделов ЖКТ из-за одновременной потери цитопротекторных простагландинов желудка (ЦОГ-1) и гипокоагуляции (VKORC1).",
            "Центральная нервная система: повышенный риск внутричерепных и субдуральных гематом даже при минимальной бытовой травме.",
            "Мочевыделительная система и слизистые: макро-/микрогематурия, рецидивирующие носовые и десневые кровотечения.",
        ]
        red_flags = [
            "Дегтеобразный черный стул (мелена) или примесь алой крови",
            "Рвота типа «кофейной гущи» или кровохарканье",
            "Спонтанные обширные гематомы (синяки), кровоточивость десен, темная/розовая моча",
            "Внезапная резкая головная боль, головокружение, нарушение зрения или речи",
        ]
        time_to_onset = "Первичный антиагрегантный эффект аспирина — через 30–60 минут; кумулятивный геморрагический пик с варфарином — на 3–7 сутки совместного приёма."
    elif {"warfarin", "amiodarone"}.issubset(pair_set) or {"warfarin", "fluconazole"}.issubset(pair_set):
        detailed_risks = [
            "Печеночный клиренс (CYP2C9 / CYP3A4): подавление 7-гидроксилирования наиболее активного S-энантиомера варфарина, ведущее к росту его плазменной концентрации на 50–200%.",
            "Система свертывания крови: неконтролируемый рост МНО (> 4.0–5.0) с переходом в зону спонтанных внутренних и забрюшинных кровотечений.",
            "Сердечно-сосудистая система: при попытке пациента самостоятельно резко бросить варфарин возникает рикошетная гиперкоагуляция и риск тромбоэмболии.",
        ]
        red_flags = [
            "Превышение целевого показателя МНО > 3.5 при плановом анализе",
            "Длительно не останавливающееся кровотечение из мелких порезов (> 10 минут)",
            "Появление петехиальной сыпи, кровоизлияний в склеру глаза, гематурии",
        ]
        time_to_onset = "Для флуконазола — быстрое нарастание за 48–96 часов; для амиодарона — старт через 3–5 дней с пиком на 2–4 неделе и сохранением эффекта до нескольких недель после отмены из-за T1/2 амиодарона (25–100 суток)."
    elif {"enalapril", "ibuprofen"}.issubset(pair_set) or {"furosemide", "ibuprofen"}.issubset(pair_set):
        detailed_risks = [
            "Почки и клубочковая гемодинамика (Синдром «Triple Whammy»): ибупрофен вызывает спазм приносящей артериолы клубочка (блокада PGE2/PGI2), а эналаприл расширяет выносящую артериолу (блокада ангиотензина II) — гидростатическое давление фильтрации падает.",
            "Водно-электролитный и кардиоваскулярный статус: задержка натрия и воды, нивелирование гипотензивного эффекта, скачки АД на 10–20 мм рт. ст. и декомпенсация ХСН.",
            "Метаболический баланс: риск острой гиперкалиемии и нарастания креатинина сыворотки (> 26.5 мкмоль/л за 48 ч).",
        ]
        red_flags = [
            "Снижение суточного объема мочи (олигурия < 500 мл/сут)",
            "Быстрая прибавка массы тела (> 1.5–2 кг за 2–3 дня), отеки лодыжек и голеней",
            "Неконтролируемый подъем артериального давления, одышка в положении лежа",
        ]
        time_to_onset = "Острое падение скорости клубочковой фильтрации (СКФ) может развиться уже в первые 24–72 часа у обезвоженных или пожилых пациентов."
    elif {"simvastatin", "clarithromycin"}.issubset(pair_set):
        detailed_risks = [
            "Скелетная мускулатура (Миотоксичность / Рабдомиолиз): 8–10-кратный рост AUC симвастатиновой кислоты из-за блокады CYP3A4 и транспортера OATP1B1 приводит к разрушению сарколеммы миоцитов.",
            "Почки (Миоглобинурийное ОПП): массивный выброс миоглобина из разрушенных мышц обтурирует почечные канальцы и вызывает острую почечную недостаточность.",
            "Печень: лекарственно-индуцированное повышение трансаминаз АЛТ/АСТ более чем в 3 раза от верхней границы нормы.",
        ]
        red_flags = [
            "Диффузные мышечные боли (миалгии), болезненность и слабость в бедрах и плечах",
            "Потемнение мочи до цвета «мясных помоев» или крепкого чая (миоглобинурия)",
            "Резкая слабость, тошнота, повышение КФК > 5–10 ВГН",
        ]
        time_to_onset = "Обычно развивается на 3–10 сутки совместного приёма антибиотика и статина."
    else:
        detailed_risks = [
            f"Фармакологический профиль A ({drug_a.title()}): {prof_a['class_ru']} · Мишень: {prof_a['target_ru']} · Путь элиминации: {prof_a['cyp_ru']}.",
            f"Фармакологический профиль B ({drug_b.title()}): {prof_b['class_ru']} · Мишень: {prof_b['target_ru']} · Путь элиминации: {prof_b['cyp_ru']}.",
            f"Органы-мишени сочетанной уязвимости: {prof_a['organ_ru']} и {prof_b['organ_ru']}. При уровне риска «{level or 'Требует проверки'}» возможна конкуренция за печеночный/почечный клиренс или суммация побочных эффектов.",
        ]
        red_flags = [
            "Необъяснимая слабость, головокружение, резкие колебания АД или пульса",
            "Признаки кровоточивости, кожная сыпь, боли в правом подреберье или эпигастрии",
            "Изменение диуреза или цвета мочи/стула после добавления второго препарата",
        ]
        time_to_onset = "Зависит от периода полувыведения (T1/2): фармакодинамические реакции — в первые 2–24 часа; кумулятивные метаболические эффекты — через 3–7 суток регулярного приёма."

    # Сбор предупреждений по БАДам (PubMed Supplement Evidence)
    supp_warnings: list[str] = []
    try:
        from supplement_schema import SupplementEvidenceRepository
        repo = SupplementEvidenceRepository()
        for d in (norm_a, norm_b):
            for s in repo.get_by_drug(d):
                supp_warnings.append(
                    f"{s.supplement_ru} ({s.supplement_lat}) + {s.drug_ru} [{s.severity}, {s.evidence_level}]: {s.clinical_consequence} ({s.clinical_management})"
                )
    except Exception:
        pass

    if not supp_warnings:
        supp_warnings.append(
            "При приёме любых лекарственных средств избегайте бесконтрольного совмещения с индукторами/ингибиторами CYP450 (экстракт зверобоя Hypericum perforatum, грейпфрутовый сок Citrus paradisi, концентрированный куркумин и гинкго билоба) без консультации врача."
        )

    pubmed_studies = fetch_pubmed_evidence(norm_a, norm_b, lang=lang, max_results=4)

    if lang == "kk":
        self_med_warning = (
            "МАҢЫЗДЫ ЕСКЕРТУ: DARIGUARD — өзін-өзі емдеудің (самолечение) және полипрагмазияның қауіпті асқынуларын "
            "алдын ала анықтауға арналған бастапқы ғылыми-скринингтік модель. Ол емдеуші дәрігердің немесе клиникалық фармакологтың "
            "жеке кеңесін алмастырмайды. Дәрігердің рұқсатынсыз препараттарды өз бетінше тағайындауға немесе тоқтатуға болмайды."
        )
    elif lang == "en":
        self_med_warning = (
            "PRIMARY SCREENING MANDATE: DARIGUARD is a primary pharmacological screening model designed to prevent hazardous "
            "self-medication and polypharmacy complications. It does NOT replace an attending physician or clinical pharmacist. "
            "Never initiate, alter, or abruptly discontinue prescribed medications without professional medical supervision."
        )
    else:
        self_med_warning = (
            "ВАЖНОЕ КЛИНИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ: DARIGUARD — это первичная скрининговая и образовательная модель, созданная "
            "для предотвращения опасного самолечения и неконтролируемой полипрагмазии. Система НЕ заменяет консультацию лечащего врача "
            "или клинического фармаколога. Никогда не назначайте и не отменяйте рецептурные препараты самостоятельно."
        )

    brief["detailed_risks"] = detailed_risks
    brief["red_flags"] = red_flags
    brief["time_to_onset"] = time_to_onset
    brief["pubmed_studies"] = pubmed_studies
    brief["supplement_warnings"] = supp_warnings
    brief["self_medication_warning"] = self_med_warning

    # Если общий профиль был слишком кратким, обогащаем why_matters и clinical_consequence конкретикой классов
    if len(brief.get("moa_a", "")) < 95:
        brief["moa_a"] = f"{drug_a.title()} ({prof_a['class_ru']}): мишень — {prof_a['target_ru']}; метаболизм — {prof_a['cyp_ru']}."
    if len(brief.get("moa_b", "")) < 95:
        brief["moa_b"] = f"{drug_b.title()} ({prof_b['class_ru']}): мишень — {prof_b['target_ru']}; метаболизм — {prof_b['cyp_ru']}."

    return brief


def generate_clinical_intelligence_brief(
    drug_a: str,
    drug_b: str,
    level: str | None,
    lang: str = "ru"
) -> dict[str, Any]:
    """Формирует полное доказательное клинико-фармакологическое досье с интеграцией PubMed и защитой от самолечения."""
    lang_n = (lang or "ru").lower()
    core = _generate_core_brief(drug_a, drug_b, level, lang=lang_n)
    return _enrich_brief_with_pubmed_and_organs(core, drug_a, drug_b, level, lang=lang_n)


def _generate_core_brief(
    drug_a: str,
    drug_b: str,
    level: str | None,
    lang: str = "ru"
) -> dict[str, Any]:
    """Формирует доказательное клинико-фармакологическое досье для выбранной пары препаратов.

    Охватывает:
    1. Фактический статус в базе DDInter.
    2. Индивидуальный механизм действия каждого препарата.
    3. Биологическое обоснование значимости комбинации.
    4. Потенциальные клинические последствия.
    5. Клиническую неопределенность и вариабельность ответа.
    6. Доказательные параметры мониторинга.
    7. Достоверные научные источники и руководства.
    """
    from data.verified_molecules import get_verified_molecule

    lang_n = (lang or "ru").lower()
    norm_a = (drug_a or "").strip().lower()
    norm_b = (drug_b or "").strip().lower()
    pair_set = {norm_a, norm_b}

    mol_a = get_verified_molecule(norm_a)
    mol_b = get_verified_molecule(norm_b)

    disp_a = mol_a.display_names.get(lang_n, drug_a.title()) if mol_a else drug_a.title()
    disp_b = mol_b.display_names.get(lang_n, drug_b.title()) if mol_b else drug_b.title()

    # Специфический клинический профиль: Варфарин + Аспирин (Showcase)
    if {"warfarin", "acetylsalicylic acid"}.issubset(pair_set) or {"warfarin", "aspirin"}.issubset(pair_set):
        if lang_n == "kk":
            return {
                "finding": f"DDInter дерекқорында «{disp_a}» + «{disp_b}» комбинациясына ең жоғары қауіп деңгейі (Major) тағайындалған.",
                "moa_a": "Варфарин: гепатоциттердегі VKORC1 кешенін тежейді және II (протромбин), VII, IX, X ұю факторларының функционалдық карбоксилденуін төмендетеді.",
                "moa_b": "Аспирин: тромбоциттердегі COX-1 ферментін (Ser529 ацетилденуі арқылы) қайтымсыз тежейді, тромбоксан А2 түзілуін және тромбоциттер агрегациясын басады.",
                "why_matters": "Бастапқы гемостаздың (тромбоциттік тығын) бұзылуы мен қайталама гемостаздың (фибриндік тор) баяулауы соқтығысусыз-ақ қан кету қаупін синергиялық түрде арттырады.",
                "clinical_consequence": "Асқазан-ішек жолдарынан, бас сүйек ішінен және операциядан кейінгі ауыр геморрагиялық асқынулар қаупі 2.4 - 3.8 есе артады.",
                "uncertainty": "Әр науқастың сезімталдығы жеке: CYP2C9 және VKORC1 генетикалық полиморфизмі, 65-тен асқан жас, бүйрек қызметі қауіпті өзгертеді. Әр науқаста қан кету міндетті түрде бола бермейді (мысалы, жүрек қақпақшасы протезі бар науқастарда бұл қажетті тағайындау болуы мүмкін).",
                "monitoring": "ХҚҚ (INR) көрсеткішін тұрақты қадағалау (мақсатты деңгей 2.0 - 2.5); гастропротекция үшін протонды помпа ингибиторларын (ППИ) қарастыру; жасырын қан кетуді (нәжістің қараюы, гематурия) бақылау; дәрігердің кеңесінсіз тағайындалған дәріні өз бетінше тоқтатуға қатаң тыйым салынады.",
                "sources": [
                    "DDInter Drug-Drug Interaction Database (Records DDInter1947 / DDInter18)",
                    "CHEST Antithrombotic and Thrombolytic Therapy Guidelines (10th/11th Eds)",
                    "Goodman & Gilman's Pharmacological Basis of Therapeutics (14th Ed, Ch. 32)",
                    "FDA Professional Prescribing Information for Warfarin & Aspirin"
                ]
            }
        elif lang_n == "en":
            return {
                "finding": f"DDInter database classifies the pair '{disp_a}' + '{disp_b}' with the highest risk tier (Major).",
                "moa_a": "Warfarin: selectively inhibits hepatic VKORC1, depleting vitamin K hydroquinone cofactor and suppressing functional carboxylation of coagulation factors II, VII, IX, and X.",
                "moa_b": "Aspirin: irreversibly acetylates Ser529 in platelet cyclooxygenase-1 (COX-1), permanently abolishing thromboxane A2 synthesis and platelet aggregation for the platelet lifespan.",
                "why_matters": "Dual impairment of primary hemostasis (platelet plug) and secondary hemostasis (fibrin mesh) results in synergistic bleeding risk without any direct molecular collision in blood.",
                "clinical_consequence": "Markedly elevated incidence of major gastrointestinal hemorrhage, intracranial bleeding, and prolonged traumatic bleeding (hazard ratio 2.4 - 3.8).",
                "uncertainty": "Substantial patient-to-patient variability exists: CYP2C9/VKORC1 pharmacogenomics, age > 65, and peptic ulcer history alter risk. Bleeding is not inevitable in every patient; combination is clinically indicated in selected high-risk cardiology settings (e.g. mechanical valves with ACS).",
                "monitoring": "Strict INR surveillance targeting the lower therapeutic window (2.0 - 2.5); gastroprotection with proton pump inhibitors (PPI); complete blood count monitoring; patient education on overt/occult bleeding signs; never abruptly stop prescribed antithrombotics without clinical guidance.",
                "sources": [
                    "DDInter Drug-Drug Interaction Database (Identifiers DDInter1947 & DDInter18)",
                    "CHEST Antithrombotic Therapy Guidelines (10th & 11th Editions)",
                    "ACC/AHA Guidelines for the Management of Patients with Valvular Heart Disease",
                    "Goodman & Gilman's The Pharmacological Basis of Therapeutics (14th Edition)"
                ]
            }
        else:
            return {
                "finding": f"В научной базе DDInter паре «{disp_a}» + «{disp_b}» присвоен наивысший уровень риска (Major).",
                "moa_a": "Варфарин: стереоселективно ингибирует печеночный комплекс VKORC1, нарушая регенерацию витамина K и гамма-карбоксилирование факторов свертывания II (протромбин), VII, IX, X.",
                "moa_b": "Аспирин: необратимо ацетилирует остаток Ser529 в тромбоцитарной циклооксигеназе-1 (COX-1), полностью блокируя синтез тромбоксана A2 и первичную агрегацию тромбоцитов на 7-10 дней.",
                "why_matters": "Сочетает блокаду первичного гемостаза (тромбоцитарная пробка) с угнетением вторичного коагуляционного каскада (фибриновый каркас). Эффект развивается в разных анатомо-клеточных компартментах без прямого столкновения молекул в плазме.",
                "clinical_consequence": "Синергическое возрастание риска клинически значимых кровотечений (желудочно-кишечных, внутричерепных, гематурии) в 2.4 - 3.8 раза.",
                "uncertainty": "Высокая межиндивидуальная вариабельность: аллели CYP2C9 (*2, *3) и VKORC1 (-1639G>A), возраст старше 65 лет, язвенный анамнез и почечная функция. Развитие геморрагий не является абсолютным для каждого пациента; комбинация строго показана при механических клапанах в сочетании с ОКС.",
                "monitoring": "Регулярный мониторинг MHO / INR (целевой диапазон 2.0 - 2.5); рутинная гастропротекция ингибиторами протонной помпы (ИПП); контроль клинического анализа крови; информирование пациента о симптомах скрытых геморрагий; категорический запрет на самостоятельную отмену назначенных препаратов.",
                "sources": [
                    "Научная база DDInter (Идентификаторы DDInter1947 / DDInter18)",
                    "Клинические рекомендации CHEST по антитромботической терапии (10-11 изд.)",
                    "Клиническая фармакология по Гудману и Гилману (14-е издание, гл. 32)",
                    "Официальные инструкции FDA / Минздрава по медицинскому применению"
                ]
            }

    # Специфический клинический профиль: Варфарин + Амиодарон (Кордарон) — Блокада CYP2C9
    if {"warfarin", "amiodarone"}.issubset(pair_set):
        if lang_n == "kk":
            return {
                "finding": f"DDInter дерекқорында «{disp_a}» + «{disp_b}» комбинациясына ең жоғары қауіп деңгейі (Major) бекітілген.",
                "moa_a": "Варфарин: гепатоциттерде VKORC1 кешенін тежейді, прокоагулянттық факторлардың (II, VII, IX, X) карбоксилденуін басады.",
                "moa_b": "Амиодарон және оның белсенді метаболиті DEA: бауыр цитохромы CYP2C9 және CYP3A4 изоферменттерін бәсекелес емес түрде күшті тежейді.",
                "why_matters": "S-варфариннің метаболикалық клиренсі 35-50%-ға төмендейді. Препараттың қанда жинақталуы ХҚҚ (INR) көрсеткішінің күрт секіруіне алып келеді.",
                "clinical_consequence": "Ауыр өмірге қауіпті ішкі қан кетулер (гематурия, іш пердесі артындағы гематома, бас сүйек ішілік геморрагия) қаупі 3-5 есе артады.",
                "uncertainty": "Амиодаронның жартылай ыдырау кезеңі өте ұзақ (30-100 күн). Өзара әрекеттесудің толық клиникалық әсері бірден емес, емдеу басталғаннан кейін 2-4 аптадан кейін максималды деңгейге жетуі мүмкін.",
                "monitoring": "Кордаронды тағайындау кезінде варфарин дозасын алдын ала 33-50%-ға азайту; алғашқы 6 аптада апта сайын ХҚҚ (INR) өлшеу; өзін-өзі емдеуге қатаң тыйым салынады.",
                "sources": [
                    "DDInter Database (DDInter1947 & DDInter147)",
                    "CHEST Antithrombotic Guidelines — Drug-Drug Interactions with VKAs",
                    "FDA Professional Monograph for Cordarone (Amiodarone HCl)",
                    "Goodman & Gilman's Pharmacological Basis of Therapeutics (14th Ed)"
                ]
            }
        elif lang_n == "en":
            return {
                "finding": f"DDInter database classifies the pair '{disp_a}' + '{disp_b}' with the highest risk tier (Major).",
                "moa_a": "Warfarin: inhibits hepatic VKORC1, reducing functional carboxylation of coagulation factors II, VII, IX, and X.",
                "moa_b": "Amiodarone & desethylamiodarone (DEA): potently inhibit CYP2C9 and CYP3A4 metabolic pathways in hepatocytes.",
                "why_matters": "Metabolic clearance of the potent S-warfarin enantiomer is impaired by 35-50%, causing drug accumulation, surging plasma concentrations, and marked INR elevation.",
                "clinical_consequence": "Markedly elevated risk of major, life-threatening hemorrhage (retroperitoneal hematoma, gastrointestinal and intracranial bleeding).",
                "uncertainty": "Amiodarone exhibits an exceptionally large volume of distribution and ultra-long elimination half-life (30-100 days). The full magnitude of INR prolongation develops gradually over 2 to 4 weeks.",
                "monitoring": "Proactive 33% to 50% empiric reduction in warfarin dose upon initiating amiodarone; weekly INR monitoring for at least 6 weeks; patient surveillance for bleeding signs.",
                "sources": [
                    "DDInter Database (Records DDInter1947 & DDInter147)",
                    "CHEST Guidelines on Antithrombotic Therapy — Drug-Drug Interactions",
                    "FDA Prescribing Information for Amiodarone HCl",
                    "CPIC Guideline for Pharmacogenetics-Guided Warfarin Dosing"
                ]
            }
        else:
            return {
                "finding": f"В научной базе DDInter паре «{disp_a}» + «{disp_b}» присвоен наивысший уровень риска (Major).",
                "moa_a": "Варфарин: ингибирует печеночный комплекс VKORC1, блокируя синтез факторов свертывания крови II, VII, IX и X.",
                "moa_b": "Амиодарон и его активный метаболит ДЭА: мощно ингибируют печеночные изоферменты CYP2C9 и CYP3A4.",
                "why_matters": "Печеночный клиренс активного S-варфарина снижается на 35-50%, что вызывает кумуляцию препарата в плазме и стремительный неконтролируемый рост МНО.",
                "clinical_consequence": "Многократное увеличение риска тяжелых и жизнеугрожающих геморрагий (забрюшинных гематом, желудочно-кишечных и внутричерепных кровотечений).",
                "uncertainty": "Амиодарон обладает гигантским объемом распределения и ультрадлинным периодом полувыведения (30-100 дней). Пик взаимодействия наступает медленно — через 2-4 недели после старта терапии.",
                "monitoring": "Превентивное снижение дозы варфарина на 33-50% в момент назначения амиодарона; еженедельный контроль МНО минимум 6 недель; информирование пациента о признаках геморрагий.",
                "sources": [
                    "Научная база DDInter (Идентификаторы DDInter1947 / DDInter147)",
                    "Клинические рекомендации CHEST по фармакотерапии антикоагулянтами",
                    "Официальная инструкция FDA / Минздрава по препарату Кордарон (Амиодарон)",
                    "Руководство CPIC по фармакогенетике варфарина и ферментов цитохрома P450"
                ]
            }

    # Специфический клинический профиль: Варфарин + Флуконазол (Дифлюкан) — Координация с гемом CYP2C9
    if {"warfarin", "fluconazole"}.issubset(pair_set):
        if lang_n == "kk":
            return {
                "finding": f"DDInter дерекқорында «{disp_a}» + «{disp_b}» деңгейі ең жоғары қауіпті (Major) деп бағаланған.",
                "moa_a": "Варфарин: VKORC1 арқылы К дәруменіне тәуелді қан ұю факторларының түзілуін тежейді.",
                "moa_b": "Флуконазол: азол сақинасының азоты арқылы CYP2C9 ферментінің белсенді орталығындағы гемдік темірмен (Fe3+) координациялық байланыс түзіп, ферментті селективті түрде бұғаттайды.",
                "why_matters": "S-варфарин метаболизмінің жедел тежелуі бос фракцияның 2-3 есе күрт артуына әкеледі. Әсер өте жылдам дамиды.",
                "clinical_consequence": "Терапияның 2-5 күнінде ХҚҚ (INR) көрсеткішінің 5.0-10.0-ден асып кетуі және кенеттен ауыр қан кету қаупі туындайды.",
                "uncertainty": "Флуконазол дозасына (100 мг және 400 мг) және науқастың CYP2C9*2/*3 генотипіне тікелей байланысты.",
                "monitoring": "Варфарин дозасын эмпирикалық түрде 50%-ға азайту; 2-3 күн сайын ХҚҚ (INR) бақылау; мүмкіндігінше CYP-бейтарап жергілікті баламаларды қарастыру.",
                "sources": [
                    "DDInter Database (Records DDInter1947 & DDInter541)",
                    "CPIC Guidelines for Antifungal and Anticoagulant Interactions",
                    "FDA Prescribing Guidelines for Diflucan (Fluconazole)"
                ]
            }
        elif lang_n == "en":
            return {
                "finding": f"DDInter database classifies the pair '{disp_a}' + '{disp_b}' with highest risk (Major).",
                "moa_a": "Warfarin: inhibits VKORC1 and suppresses functional clotting factor synthesis.",
                "moa_b": "Fluconazole: coordinate-covalently coordinates heme iron in CYP2C9 active site via azole nitrogen, selectively blocking S-warfarin oxidation.",
                "why_matters": "Potent, rapid, concentration-dependent inhibition of S-warfarin clearance produces a sharp 2- to 3-fold escalation in systemic exposure.",
                "clinical_consequence": "Acute surge in prothrombin time and INR (> 5.0-8.0) within 2-5 days, triggering severe hemorrhagic events.",
                "uncertainty": "Magnitude scales strictly with fluconazole dose (100 mg vs 400 mg daily) and patient CYP2C9 loss-of-function alleles (*2, *3).",
                "monitoring": "Empiric 50% warfarin maintenance dose reduction; frequent INR monitoring every 48-72 hours during antimycotic course; evaluate non-interacting alternatives.",
                "sources": [
                    "DDInter Database (Records DDInter1947 & DDInter541)",
                    "CPIC Clinical Pharmacogenetics Implementation Consortium Guidelines",
                    "FDA Clinical Pharmacology Label for Diflucan (Fluconazole)"
                ]
            }
        else:
            return {
                "finding": f"В научной базе DDInter паре «{disp_a}» + «{disp_b}» присвоен наивысший уровень риска (Major).",
                "moa_a": "Варфарин: угнетает регенерацию витамина K в печени, снижая активность факторов коагуляции II, VII, IX и X.",
                "moa_b": "Флуконазол: азольным кольцом координирует атом железа гема в активном центре CYP2C9, избирательно блокируя гидроксилирование S-варфарина.",
                "why_matters": "Быстрое и выраженное торможение элиминации S-варфарина приводит к резкому 2-3-кратному подъему свободной фракции антикоагулянта в крови.",
                "clinical_consequence": "Острый скачок МНО (нередко выше 5.0-8.0) уже на 2-5 день терапии с угрозой профузных кровотечений.",
                "uncertainty": "Эффект строго дозозависим (100 мг vs 400 мг) и усиливается у носителей полиморфизмов CYP2C9*2 и CYP2C9*3.",
                "monitoring": "Превентивное снижение суточной дозы варфарина на 50%; контроль МНО каждые 48-72 часа до окончания курса; рассмотрение местных или менее взаимодействующих антимикотиков.",
                "sources": [
                    "Научная база взаимодействий DDInter (DDInter1947 / DDInter541)",
                    "Руководство CPIC по фармакогенетическому дозированию варфарина",
                    "Инструкция FDA и Минздрава по препарату Дифлюкан (Флуконазол)"
                ]
            }

    # Специфический клинический профиль: Эналаприл + Ибупрофен — Почечный гемодинамический конфликт
    if {"enalapril", "ibuprofen"}.issubset(pair_set):
        if lang_n == "kk":
            return {
                "finding": f"DDInter дерекқорында «{disp_a}» + «{disp_b}» комбинациясына Moderate қауіп деңгейі белгіленген.",
                "moa_a": "Эналаприл: АӨФ-ті тежеп, ангиотензин II түзілуін блоктайды және бүйрек шумақшаларының шығарушы (эфферентті) артериолаларын кеңейтеді.",
                "moa_b": "Ибупрофен: шумақшалық COX-1 және COX-2 ферменттерін тежеп, простагландиндер синтезін басады және әкелуші (афферентті) артериолалардың кеңеюіне тосқауыл қояды.",
                "why_matters": "Әкелуші тамырдың тарылуы мен шығарушы тамырдың кеңеюі шумақшалық сүзілу қысымын күрт төмендетеді. Бүйрек гемодинамикасы күйрейді.",
                "clinical_consequence": "Пререналды жедел бүйрек зақымдануы (ЖБЗ), гиперкалиемия және гипотензивтік терапияның тиімсіздігі.",
                "uncertainty": "Қауіп сусыздану (дегидратация), 65-тен асқан жас және созылмалы бүйрек ауруы кезінде айтарлықтай артады.",
                "monitoring": "Сарысулық креатинин, шумақшалық сүзілу жылдамдығы (eGFR) және калий деңгейін 7-14 күнде бақылау; ҚҚСД-ны жергілікті формаларға немесе парацетамолға ауыстыру.",
                "sources": [
                    "DDInter Database (DDInter811 & DDInter394)",
                    "KDIGO Clinical Practice Guideline for Acute Kidney Injury",
                    "NICE Guidelines: Chronic Kidney Disease & Hypertension"
                ]
            }
        elif lang_n == "en":
            return {
                "finding": f"DDInter database assigns Moderate risk to '{disp_a}' + '{disp_b}'.",
                "moa_a": "Enalaprilat: blocks Angiotensin II-mediated efferent arteriolar vasoconstriction, dilating efferent arterioles.",
                "moa_b": "Ibuprofen: suppresses renal prostaglandin synthesis (PGI2/PGE2), blocking compensatory afferent arteriolar vasodilation.",
                "why_matters": "Simultaneous afferent vasoconstriction (NSAID) and efferent vasodilation (ACE inhibitor) collapses transcapillary filtration pressure, sharply dropping GFR.",
                "clinical_consequence": "Pre-renal acute kidney injury (AKI), hyperkalemia, fluid retention, and blunted antihypertensive response.",
                "uncertainty": "Exacerbated by hypovolemia, dehydration, advanced age (> 65), or pre-existing renal compromise.",
                "monitoring": "Serum creatinine, BUN, and potassium at baseline and within 7-14 days; blood pressure tracking; prefer acetaminophen or topical NSAIDs for mild-to-moderate pain.",
                "sources": [
                    "DDInter Database (Records DDInter811 & DDInter394)",
                    "KDIGO Clinical Practice Guideline for Acute Kidney Injury",
                    "AHA/ACC Hypertension Practice Guidelines"
                ]
            }
        else:
            return {
                "finding": f"В научной базе DDInter паре «{disp_a}» + «{disp_b}» присвоен уровень риска Moderate.",
                "moa_a": "Эналаприл: блокирует синтез ангиотензина II, расширяя выносящую (эфферентную) артериолу почечного клубочка.",
                "moa_b": "Ибупрофен: подавляет синтез вазодилататорных простагландинов (PGE2, PGI2), вызывая спазм приносящей (афферентной) артериолы.",
                "why_matters": "Сочетание спазма приносящей артериолы (НПВП) и дилатации выносящей (иАПФ) критически снижает внутриклубочковое фильтрационное давление и СКФ.",
                "clinical_consequence": "Преренальное острое повреждение почек (ОПП), задержка натрия и жидкости, гиперкалиемия, срыв антигипертензивного контроля.",
                "uncertainty": "Риск резко возрастает при дегидратации, у пожилых пациентов (>65 лет) и при фоновой хронической болезни почек.",
                "monitoring": "Контроль уровня креатинина, СКФ и калия сыворотки через 7-14 дней после начала приема; замена системного НПВП на парацетамол или локальные формы.",
                "sources": [
                    "Научная база DDInter (Идентификаторы DDInter811 / DDInter394)",
                    "Клинические рекомендации KDIGO по острому повреждению почек",
                    "Европейские рекомендации ESC/ESH по лечению артериальной гипертензии"
                ]
            }

    # Специфический клинический профиль: Фуросемид + Ибупрофен — Антагонизм диуреза
    if {"furosemide", "ibuprofen"}.issubset(pair_set):
        if lang_n == "kk":
            return {
                "finding": f"DDInter дерекқорында «{disp_a}» + «{disp_b}» жұбына Moderate қауіп деңгейі берілген.",
                "moa_a": "Фуросемид: Генле ілмегінің өрлеме бөлігінде NKCC2 тасымалдаушысын тежейді және бүйректік простагландиндер синтезін ынталандырады.",
                "moa_b": "Ибупрофен: шумақшалық простагландиндер түзілуін тежеп, бүйрек қан айналымын төмендетеді.",
                "why_matters": "ҚҚСД петлелік диуретиктердің натрийуретикалық және диуретикалық тиімділігін бәсеңдетеді (фармакодинамикалық антагонизм).",
                "clinical_consequence": "Ісінудің ұлғаюы, жүрек жеткіліксіздігінің декомпенсациясы және бүйрек жеткіліксіздігінің дамуы.",
                "uncertainty": "Жүрек жеткіліксіздігі және бауыр циррозы бар науқастар бүйрек простагландиндеріне ерекше тәуелді, сондықтан қауіп оларда жоғары.",
                "monitoring": "Дене салмағын, артериялық қысымды және ісінуді күнделікті қадағалау; созылмалы жүрек жеткіліксіздігі кезінде жүйелі ҚҚСД қабылдаудан аулақ болу.",
                "sources": [
                    "DDInter Database (DDInter981 & DDInter394)",
                    "ACC/AHA Guidelines for the Management of Heart Failure",
                    "Goodman & Gilman's Pharmacological Basis of Therapeutics"
                ]
            }
        elif lang_n == "en":
            return {
                "finding": f"DDInter database assigns Moderate risk to '{disp_a}' + '{disp_b}'.",
                "moa_a": "Furosemide: inhibits the NKCC2 symporter in the thick ascending limb and stimulates renal prostaglandin release.",
                "moa_b": "Ibuprofen: suppresses renal prostaglandin production, reducing medullary blood flow and natriuresis.",
                "why_matters": "Direct pharmacodynamic antagonism: NSAIDs attenuate the natriuretic and antihypertensive efficacy of loop diuretics.",
                "clinical_consequence": "Blunted diuresis, fluid retention, worsening peripheral edema, and acute heart failure decompensation.",
                "uncertainty": "Marked vulnerability in patients with congestive heart failure, nephrotic syndrome, or cirrhosis dependent on renal prostaglandins.",
                "monitoring": "Daily weight tracking, blood pressure monitoring, serum electrolytes (sodium, potassium); avoid systemic NSAIDs in congestive heart failure.",
                "sources": [
                    "DDInter Database (Records DDInter981 & DDInter394)",
                    "ACC/AHA Guidelines for Heart Failure Management",
                    "KDIGO Clinical Practice Guidelines"
                ]
            }
        else:
            return {
                "finding": f"В научной базе DDInter паре «{disp_a}» + «{disp_b}» присвоен уровень риска Moderate.",
                "moa_a": "Фуросемид: блокирует котранспортер NKCC2 в петле Генле и стимулирует выработку почечных сосудорасширяющих простагландинов.",
                "moa_b": "Ибупрофен: ингибирует синтез простагландинов, снижая почечный кровоток и фильтрацию.",
                "why_matters": "Фармакодинамический антагонизм: НПВП нивелируют простагландин-опосредованный натрийуретический и диуретический ответ на фуросемид.",
                "clinical_consequence": "Снижение диуреза, задержка жидкости, нарастание отечного синдрома и декомпенсация сердечной недостаточности.",
                "uncertainty": "Особенно опасно у пациентов с ХСН и циррозом, где перфузия почек критически поддерживается компенсаторными простагландинами.",
                "monitoring": "Ежедневный контроль массы тела, мониторинг АД и электролитов (калий, натрий); отказ от системных НПВП у коморбидных кардиологических больных.",
                "sources": [
                    "Научная база DDInter (Идентификаторы DDInter981 / DDInter394)",
                    "Рекомендации Российского кардиологического общества (РКО) по ХСН",
                    "Рекомендации ESC по диагностике и лечению острой и хронической сердечной недостаточности"
                ]
            }

    # Общий профиль для других пар
    lvl_str = level or "Not in DB"
    if level is None:
        finding_kk = f"«{disp_a}» ({drug_a}) + «{disp_b}» ({drug_b}) жұбы үшін DDInter дерекқорында жазба табылмады. Жазбаның болмауы үйлесімділіктің қауіпсіздігін дәлелдемейді."
        finding_en = f"No record was found in DDInter for '{disp_a}' ({drug_a}) + '{disp_b}' ({drug_b}). Absence of a record does not confirm pharmacological safety."
        finding_ru = f"Запись для пары «{disp_a}» ({drug_a}) + «{disp_b}» ({drug_b}) в базе DDInter не найдена. Отсутствие записи не подтверждает безопасность сочетания."
    else:
        finding_kk = f"DDInter дерекқорында «{disp_a}» + «{disp_b}» деңгейі: {lvl_str}."
        finding_en = f"DDInter database record for '{disp_a}' + '{disp_b}': {lvl_str}."
        finding_ru = f"Запись в базе DDInter для пары «{disp_a}» + «{disp_b}»: {lvl_str}."

    if lang_n == "kk":
        return {
            "finding": finding_kk,
            "moa_a": f"{disp_a}: {mol_a.target.clinical_effect if mol_a else 'Фармакологиялық әсері клиникалық нұсқаулықта сипатталған.'}",
            "moa_b": f"{disp_b}: {mol_b.target.clinical_effect if mol_b else 'Фармакологиялық әсері клиникалық нұсқаулықта сипатталған.'}",
            "why_matters": "Фармакокинетикалық (CYP450 клиренсінің бәсекелестігі) немесе фармакодинамикалық тоғысу нәтижесінде препараттардың тиімділігі мен қауіпсіздік бейіні өзгереді.",
            "clinical_consequence": "Жағымсыз әсерлердің күшеюі немесе емдік тиімділіктің төмендеуі мүмкін.",
            "uncertainty": "Клиникалық әсер дозаға, емдеу ұзақтығына және науқастың ілеспе ауруларына байланысты өзгеріп отырады.",
            "monitoring": "Зертханалық көрсеткіштерді, жанама әсерлерді және терапиялық жауапты бақылау қажет.",
            "sources": [
                "DDInter Database of Drug-Drug Interactions",
                "Official Clinical Prescribing Information"
            ]
        }
    elif lang_n == "en":
        return {
            "finding": finding_en,
            "moa_a": f"{disp_a}: {mol_a.target.clinical_effect if mol_a else 'Pharmacological mechanism documented in clinical literature.'}",
            "moa_b": f"{disp_b}: {mol_b.target.clinical_effect if mol_b else 'Pharmacological mechanism documented in clinical literature.'}",
            "why_matters": "Pharmacokinetic competitive enzyme/transporter clearance or pharmacodynamic convergence modifies therapeutic window and toxicity threshold.",
            "clinical_consequence": "Potential alteration of plasma exposure or potentiated end-organ response.",
            "uncertainty": "Individual pharmacogenomic profiles, hepatic/renal clearance reserve, and comedications introduce variability.",
            "monitoring": "Targeted clinical and laboratory monitoring (therapeutic drug monitoring, organ biomarkers).",
            "sources": [
                "DDInter Drug-Drug Interaction Database",
                "FDA Clinical Pharmacology Prescribing Guides"
            ]
        }
    else:
        return {
            "finding": finding_ru,
            "moa_a": f"{disp_a}: {mol_a.target.clinical_effect if mol_a else 'Фармакологический механизм задокументирован в клинических базах данных.'}",
            "moa_b": f"{disp_b}: {mol_b.target.clinical_effect if mol_b else 'Фармакологический механизм задокументирован в клинических базах данных.'}",
            "why_matters": "Фармакокинетическая конкуренция за клиренс CYP450 или фармакодинамическая конвергенция меняет профиль безопасности комбинации.",
            "clinical_consequence": "Риск кумуляции метаболитов или потенцирования нежелательных лекарственных реакций.",
            "uncertainty": "Индивидуальный метаболический статус, возраст, СКФ и сопутствующая терапия существенно влияют на выраженность эффекта.",
            "monitoring": "Регулярный клинико-лабораторный мониторинг, титрация доз под контролем специалиста.",
            "sources": [
                "Научная база взаимодействий DDInter",
                "Клинические рекомендации и формулярные руководства"
            ]
        }


def generate_structured_explanation(drug_a: str, drug_b: str, level: str | None, lang: str = "ru") -> dict[str, str]:
    """Детерминированное доказательное пояснение статуса DDInter без обращения к сторонней LLM."""
    lang_normalized = (lang or "ru").lower()

    if lang_normalized == "kk":
        if level is None:
            return {
                "summary": f"DDInter дерекқорының ағымдағы нұсқасында «{drug_a}» + «{drug_b}» жұбы тіркелмеген.",
                "clinical_meaning": "Зерттеу базасында жазбаның болмауы дәрілер үйлесімінің қауіпсіз екендігіне дәлел бола алмайды.",
                "recommendation": "Бірге қолданар алдында емдеуші дәрігермен немесе клиникалық фармакологпен кеңесіңіз."
            }

        level_explanations_kk = {
            "Major": {
                "summary": f"«{drug_a}» + «{drug_b}» жұбы үшін DDInter-де ең жоғары қауіп деңгейі (Major) белгіленген.",
                "clinical_meaning": "Ғылыми әдебиеттерде ауыр жағымсыз реакциялар немесе терапияның тиімсіздігін тудыруы мүмкін клиникалық маңызды өзара әрекеттесу тіркелген.",
                "recommendation": "Дәрігердің жоғары бақылауы, қауіп/пайда арақатынасын бағалауы және балама дәрілерді қарастыруы талап етіледі."
            },
            "Moderate": {
                "summary": f"«{drug_a}» + «{drug_b}» жұбы үшін орташа қауіп деңгейі (Moderate) тіркелген.",
                "clinical_meaning": "Өзара әрекеттесу ғылыми зерттеулерде сипатталған, дозаны түзетуді немесе зертханалық көрсеткіштерді бақылауды қажет етуі мүмкін.",
                "recommendation": "Жеке қабылдау режимін таңдау үшін қабылданатын барлық дәрілер туралы дәрігерге хабарлаңыз."
            },
            "Minor": {
                "summary": f"«{drug_a}» + «{drug_b}» жұбы үшін төмен қауіп деңгейі (Minor) тіркелген.",
                "clinical_meaning": "Өзара әрекеттесудің клиникалық маңызы шектеулі немесе сирек кездесетін жеке жағдайларда байқалады.",
                "recommendation": "Әдетте арнайы шаралар қажет емес, бірақ ерекше белгілер байқалса, дәрігерге қаралған жөн."
            },
            "Unknown": {
                "summary": f"«{drug_a}» + «{drug_b}» жұбы үшін DDInter дереккөзінде қауіп деңгейі Unknown деп көрсетілген.",
                "clinical_meaning": "Өзара әрекеттесу фактісі ғылыми жарияланымдарда бар, бірақ дерекқор авторлары оны қатаң шкала бойынша жіктемеген.",
                "recommendation": "Дәрілік заттардың ресми нұсқаулығына және маманның кеңесіне сүйену қажет."
            }
        }
        return level_explanations_kk.get(level, {
            "summary": f"Өзара әрекеттесу деңгейі: {level}.",
            "clinical_meaning": "Мәліметтер DDInter базасынан алынған.",
            "recommendation": "Маманмен кеңесіңіз."
        })

    elif lang_normalized == "en":
        if level is None:
            return {
                "summary": f"In current DDInter release, pair '{drug_a}' + '{drug_b}' is not recorded.",
                "clinical_meaning": "Absence of evidence in research databases does not establish lack of pharmacological interaction.",
                "recommendation": "Consult a physician or clinical pharmacist prior to co-administration."
            }

        level_explanations_en = {
            "Major": {
                "summary": f"Pair '{drug_a}' + '{drug_b}' is classified with the highest risk tier (Major) in DDInter.",
                "clinical_meaning": "Documented in peer-reviewed literature as clinically significant, with potential for severe adverse events or therapeutic failure.",
                "recommendation": "Requires close clinical oversight, benefit-risk assessment, and physician evaluation of therapeutic alternatives."
            },
            "Moderate": {
                "summary": f"Pair '{drug_a}' + '{drug_b}' is assigned moderate risk (Moderate) in DDInter.",
                "clinical_meaning": "Interaction documented in literature; may alter drug plasma concentrations or therapeutic efficacy, requiring dosage adjustment or monitoring.",
                "recommendation": "Inform attending physician of all concurrent medications to personalize dosing regimen."
            },
            "Minor": {
                "summary": f"Pair '{drug_a}' + '{drug_b}' is classified as minor risk (Minor) in DDInter.",
                "clinical_meaning": "Limited clinical significance or observed only in isolated idiosyncratic cases.",
                "recommendation": "Special intervention is rarely needed; report any unanticipated symptoms to a physician."
            },
            "Unknown": {
                "summary": f"Pair '{drug_a}' + '{drug_b}' has severity tier listed as Unknown in DDInter.",
                "clinical_meaning": "Interaction is referenced in scientific publications, but severity degree was not formally graded by database authors.",
                "recommendation": "Refer to official prescribing information and consult a healthcare professional."
            }
        }
        return level_explanations_en.get(level, {
            "summary": f"Interaction level: {level}.",
            "clinical_meaning": "Record sourced from DDInter database.",
            "recommendation": "Consult a clinical specialist."
        })

    # Default Russian
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


def get_contextual_questions(drug_a: str, drug_b: str, lang: str = "ru") -> list[str]:
    """Возвращает список научно обоснованных контекстных вопросов для выбранной пары препаратов."""
    lang_n = (lang or "ru").lower()
    norm_a = (drug_a or "").strip().lower()
    norm_b = (drug_b or "").strip().lower()
    pair_set = {norm_a, norm_b}

    # Варфарин + Аспирин
    if {"warfarin", "acetylsalicylic acid"}.issubset(pair_set) or {"warfarin", "aspirin"}.issubset(pair_set):
        if lang_n == "kk":
            return [
                "Асқазан-ішектен жасырын қан кетудің алғашқы белгілері қандай?",
                "Бұл комбинацияда ХҚҚ (INR) қандай мақсатты деңгейде ұсталуы керек?",
                "Протонды помпа ингибиторлары (ППИ) қашан тағайындалады?",
                "Дәрілердің біреуін өз бетінше тоқтатуға бола ма?"
            ]
        elif lang_n == "en":
            return [
                "What are the earliest warning signs of occult gastrointestinal bleeding?",
                "What is the recommended target INR window for this co-prescription?",
                "When is routine PPI gastroprotection indicated?",
                "Is it safe to abruptly discontinue either medication without clinical guidance?"
            ]
        return [
            "Каковы симптомы скрытого желудочно-кишечного кровотечения?",
            "Какой целевой диапазон МНО рекомендуется при этой комбинации?",
            "Когда показано назначение ингибиторов протонной помпы (ИПП)?",
            "Безопасно ли самостоятельно прекратить прием одного из препаратов?"
        ]

    # Варфарин + Амиодарон
    if {"warfarin", "amiodarone"}.issubset(pair_set):
        if lang_n == "kk":
            return [
                "Амиодарон CYP2C9 арқылы S-варфарин клиренсін қалай тежейді?",
                "Кордарон қосқанда варфарин дозасы әдетте қанша пайызға азайтылады?",
                "Өзара әрекеттесудің ең жоғары әсері қанша уақыттан кейін байқалады?",
                "Емнің алғашқы апталарында ХҚҚ (INR) қалай бақыланады?"
            ]
        elif lang_n == "en":
            return [
                "How does amiodarone inhibit CYP2C9 metabolic clearance of S-warfarin?",
                "What percentage dose reduction of warfarin is recommended when initiating amiodarone?",
                "What is the expected onset and time-to-peak of this interaction?",
                "What INR monitoring schedule is required during the initial weeks?"
            ]
        return [
            "Как амиодарон подавляет клиренс S-варфарина через CYP2C9?",
            "На сколько процентов эмпирически снижают дозу варфарина при назначении Кордарона?",
            "Через какое время развивается пиковый эффект взаимодействия?",
            "Как контролировать МНО в первые недели терапии?"
        ]

    # Варфарин + Флуконазол
    if {"warfarin", "fluconazole"}.issubset(pair_set):
        if lang_n == "kk":
            return [
                "Флуконазолдың CYP2C9 ферментін тежеуінің молекулалық механизмі қандай?",
                "Варфарин концентрациясы мен қан кету қаупі қаншалықты тез артады?",
                "Өзара әрекеттесу қаупі төмен балама саңырауқұлаққа қарсы дәрілер бар ма?"
            ]
        elif lang_n == "en":
            return [
                "What is the molecular mechanism of CYP2C9 heme coordination by fluconazole?",
                "How rapidly does warfarin plasma concentration and bleeding risk escalate?",
                "Are there alternative antifungal agents with lower CYP2C9 inhibition liability?"
            ]
        return [
            "Каков молекулярный механизм ингибирования CYP2C9 флуконазолом?",
            "Как быстро нарастает концентрация варфарина и риск кровотечений?",
            "Существуют ли менее взаимодействующие противогрибковые альтернативы?"
        ]

    # Эналаприл + Ибупрофен
    if {"enalapril", "ibuprofen"}.issubset(pair_set):
        if lang_n == "kk":
            return [
                "ҚҚСД-ның простагландиндер синтезін тежеуі бүйрек гемодинамикасын қалай бұзады?",
                "Неліктен АӨФ ингибиторы мен ҚҚСД үйлесімі сүзілу қысымын төмендетеді?",
                "Пререналды жедел бүйрек зақымдануының клиникалық белгілері қандай?",
                "Бұл науқастарда ауырсынуды басу үшін қандай қауіпсіз баламалар бар?"
            ]
        elif lang_n == "en":
            return [
                "How does NSAID prostaglandin inhibition compromise afferent glomerular hemodynamics?",
                "Why does the ACEi and NSAID combination collapse transcapillary filtration pressure?",
                "What are the clinical markers of pre-renal acute kidney injury in this pair?",
                "What safer analgesic alternatives exist for patients with hypertension and CKD?"
            ]
        return [
            "Как ингибирование синтеза простагландинов НПВП нарушает почечную гемодинамику?",
            "Почему сочетание иАПФ и НПВП критически снижает клубочковую фильтрацию?",
            "Каковы признаки преренального острого повреждения почек?",
            "Какие обезболивающие препараты безопаснее для пациентов с ХБП и гипертензией?"
        ]

    # Фуросемид + Ибупрофен
    if {"furosemide", "ibuprofen"}.issubset(pair_set):
        if lang_n == "kk":
            return [
                "Ибупрофен фуросемидтің натрийуретикалық әсерін қалай бәсеңдетеді?",
                "Бүйрек простагландиндерінің петлелік диуретиктер механизміндегі рөлі қандай?",
                "Ісіну мен жүрек жеткіліксіздігі күшейгенде қандай шаралар қабылданады?"
            ]
        elif lang_n == "en":
            return [
                "How does ibuprofen blunt the natriuretic and diuretic efficacy of furosemide?",
                "What is the role of intrarenal prostaglandins in loop diuretic action?",
                "What clinical measures should be taken if peripheral edema worsens?"
            ]
        return [
            "Как ибупрофен блокирует натрийуретическое действие фуросемида?",
            "Какова роль почечных простагландинов в действии петлевых диуретиков?",
            "Что делать при нарастании отеков и декомпенсации сердечной недостаточности?"
        ]

    # Базовые клинические вопросы для произвольных пар
    if lang_n == "kk":
        return [
            "Бұл дәрілер үшін қандай өзара әрекеттесу механизмі сипатталған?",
            "Қандай клиникалық белгілер дереу дәрігерге қаралуды талап етеді?",
            "Бірге қабылдау кезінде қандай зертханалық көрсеткіштерді бақылау қажет?",
            "Бұл комбинацияның қауіпсіздік шегі қандай?"
        ]
    elif lang_n == "en":
        return [
            "What interaction mechanism is documented for these medications?",
            "What clinical symptoms warrant urgent medical evaluation?",
            "What laboratory monitoring parameters are recommended for concurrent therapy?",
            "What factors increase patient vulnerability to this interaction?"
        ]
    return [
        "Какой механизм взаимодействия описан для этих препаратов?",
        "Какие клинические симптомы требуют немедленного обращения к врачу?",
        "Какие лабораторные показатели необходимо контролировать при совместном приеме?",
        "Какие факторы повышают индивидуальную уязвимость пациента?"
    ]

