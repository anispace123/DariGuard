"""DARIGUARD — Unified State Management Architecture.

Provides single-source-of-truth state management across all platform views:
- Command Center (Workspace / Анализ назначений)
- Molecular Intelligence Lab (Молекулярная лаборатория)
- Phyto & Supplements (БАДы и Фитопрепараты)
- Interaction Intelligence (Граф сети взаимодействий)
- ML Research (ML-исследования и валидация)
- AI Pharmacology Copilot (ИИ-аналитик)
- Evidence & Reports (Доказательная база и отчеты)

Guarantees atomic synchronization between session variables and Streamlit
BaseWeb selectbox/multiselect widget keys, preventing revert loops, state fragmentation,
and stale DOM overrides.
"""
from __future__ import annotations

import streamlit as st
from typing import Any, Sequence


DEFAULT_PAIR = ("warfarin", "acetylsalicylic acid")
DEFAULT_COHORT = "preset_bleeding"

REFERENCE_COMBINATIONS = [
    {
        "id": "warfarin_aspirin",
        "a": "warfarin",
        "b": "acetylsalicylic acid",
        "label_ru": "Варфарин + Аспирин · Геморрагический конфликт [Major]",
        "label_kk": "Варфарин + Аспирин · Геморрагиялық қақтығыс [Major]",
        "label_en": "Warfarin + Aspirin · Hemorrhagic Convergence [Major]",
        "badge": "Major",
    },
    {
        "id": "warfarin_amiodarone",
        "a": "warfarin",
        "b": "amiodarone",
        "label_ru": "Варфарин + Амиодарон (Кордарон) · Ингибирование CYP2C9 [Major]",
        "label_kk": "Варфарин + Амиодарон (Кордарон) · CYP2C9 тежелуі [Major]",
        "label_en": "Warfarin + Amiodarone · CYP2C9 Inhibition [Major]",
        "badge": "Major",
    },
    {
        "id": "warfarin_fluconazole",
        "a": "warfarin",
        "b": "fluconazole",
        "label_ru": "Варфарин + Флуконазол (Дифлюкан) · Координация с гемом [Major]",
        "label_kk": "Варфарин + Флуконазол (Дифлюкан) · Геммен үйлесу [Major]",
        "label_en": "Warfarin + Fluconazole · CYP2C9 Heme Coordination [Major]",
        "badge": "Major",
    },
    {
        "id": "enalapril_ibuprofen",
        "a": "enalapril",
        "b": "ibuprofen",
        "label_ru": "Эналаприл + Ибупрофен · Почечная гемодинамика [Moderate]",
        "label_kk": "Эналаприл + Ибупрофен · Бүйрек гемодинамикасы [Moderate]",
        "label_en": "Enalapril + Ibuprofen · Renal Hemodynamic Conflict [Moderate]",
        "badge": "Moderate",
    },
    {
        "id": "furosemide_ibuprofen",
        "a": "furosemide",
        "b": "ibuprofen",
        "label_ru": "Фуросемид (Лазикс) + Ибупрофен · Антагонизм диуреза [Moderate]",
        "label_kk": "Фуросемид (Лазикс) + Ибупрофен · Диурез антагонизмі [Moderate]",
        "label_en": "Furosemide + Ibuprofen · Diuretic Antagonism [Moderate]",
        "badge": "Moderate",
    },
]


def init_session_state(default_lang: str = "kk") -> None:
    """Инициализирует базовые ключи состояния сессии, если они отсутствуют."""
    if "lang" not in st.session_state:
        st.session_state.lang = default_lang
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "workspace"
    if "sound_enabled" not in st.session_state:
        st.session_state.sound_enabled = False
    if "workspace_multiselect" not in st.session_state:
        st.session_state.workspace_multiselect = []
    if "active_pair" not in st.session_state:
        st.session_state.active_pair = DEFAULT_PAIR
    if "active_cohort" not in st.session_state:
        st.session_state.active_cohort = DEFAULT_COHORT
    if "ws_severity_filter" not in st.session_state:
        st.session_state.ws_severity_filter = "All"
    if "ws_severity_pills" not in st.session_state:
        st.session_state.ws_severity_pills = "All"
    if "mol_custom_a" not in st.session_state:
        st.session_state.mol_custom_a = DEFAULT_PAIR[0]
    if "mol_custom_b" not in st.session_state:
        st.session_state.mol_custom_b = DEFAULT_PAIR[1]
    if "mol_active_pair" not in st.session_state:
        st.session_state.mol_active_pair = "warfarin_aspirin"
    if "ai_a" not in st.session_state:
        st.session_state.ai_a = DEFAULT_PAIR[0]
    if "ai_b" not in st.session_state:
        st.session_state.ai_b = DEFAULT_PAIR[1]


def get_active_pair() -> tuple[str, str]:
    """Возвращает текущую активную пару препаратов (канонические МНН в нижнем регистре)."""
    pair = st.session_state.get("active_pair")
    if isinstance(pair, (tuple, list)) and len(pair) == 2:
        return (str(pair[0]).strip().lower(), str(pair[1]).strip().lower())

    a = st.session_state.get("mol_custom_a") or st.session_state.get("ai_a") or DEFAULT_PAIR[0]
    b = st.session_state.get("mol_custom_b") or st.session_state.get("ai_b") or DEFAULT_PAIR[1]
    return (str(a).strip().lower(), str(b).strip().lower())


def find_catalog_label(
    query: str,
    normalizer: Any | None = None,
    catalog_labels: list[str] | None = None,
    catalog_map: dict[str, str] | None = None
) -> str | None:
    """Находит отображаемую метку препарата в каталоге с многоуровневым сопоставлением."""
    clean_q = (query or "").strip().lower()
    if not clean_q:
        return None

    # 1. Метод normalizer.get_canonical_catalog_label
    if normalizer is not None and hasattr(normalizer, "get_canonical_catalog_label"):
        try:
            lbl = normalizer.get_canonical_catalog_label(clean_q)
            if lbl and (catalog_labels is None or lbl in catalog_labels):
                return lbl
        except Exception:
            pass

    # 2. Нормализация к каноническому имени через normalizer.normalize
    canon = clean_q
    if normalizer is not None and hasattr(normalizer, "normalize"):
        try:
            res = normalizer.normalize(clean_q)
            if getattr(res, "is_resolved", False) and res.canonical_name:
                canon = res.canonical_name.strip().lower()
        except Exception:
            pass

    # 3. Прямое сопоставление по словарю catalog_map (label -> canon)
    if catalog_map:
        for lbl, val in catalog_map.items():
            if val.strip().lower() == canon:
                return lbl

    # 4. Поиск подстроки [canon] в метках
    if catalog_labels:
        for lbl in catalog_labels:
            lbl_low = lbl.lower()
            if f"[{canon}]" in lbl_low or canon == lbl_low or canon in lbl_low:
                return lbl

    return None


def _match_showcase_id(clean_a: str, clean_b: str) -> str:
    """Определяет идентификатор эталонной пары, если комбинация входит в REFERENCE_COMBINATIONS."""
    pair_set = {clean_a, clean_b}
    for ref in REFERENCE_COMBINATIONS:
        if {ref["a"], ref["b"]} == pair_set:
            return ref["id"]
    return "custom"


def set_active_pair(
    drug_a: str,
    drug_b: str,
    cohort_id: str | None = None,
    showcase_id: str | None = None,
    normalizer: Any | None = None,
    catalog_labels: list[str] | None = None,
    catalog_map: dict[str, str] | None = None,
) -> None:
    """Атомарно обновляет активную пару препаратов во всех модулях платформы."""
    clean_a = str(drug_a).strip().lower()
    clean_b = str(drug_b).strip().lower()
    pair = (clean_a, clean_b)

    resolved_showcase = showcase_id or _match_showcase_id(clean_a, clean_b)

    st.session_state["active_pair"] = pair
    st.session_state["_last_synced_active_pair"] = pair
    if cohort_id is not None:
        st.session_state["active_cohort"] = cohort_id
    elif showcase_id is not None:
        st.session_state["active_cohort"] = showcase_id
    else:
        st.session_state["active_cohort"] = resolved_showcase

    # Синхронизация Молекулярной лаборатории
    st.session_state["mol_custom_a"] = clean_a
    st.session_state["mol_custom_b"] = clean_b
    st.session_state["_last_mol_custom_a"] = clean_a
    st.session_state["_last_mol_custom_b"] = clean_b
    st.session_state["mol_active_pair"] = resolved_showcase

    # Синхронизация ИИ-аналитика
    st.session_state["ai_a"] = clean_a
    st.session_state["ai_b"] = clean_b
    st.session_state["_last_ai_a"] = clean_a
    st.session_state["_last_ai_b"] = clean_b

    # Разрешение отображаемых меток для виджетов селекторов на всех страницах
    lbl_a = find_catalog_label(clean_a, normalizer, catalog_labels, catalog_map)
    lbl_b = find_catalog_label(clean_b, normalizer, catalog_labels, catalog_map)

    for prefix in ("mol", "ai", "cmd", "net"):
        if lbl_a:
            st.session_state[f"{prefix}_sel_a"] = lbl_a
        if lbl_b:
            st.session_state[f"{prefix}_sel_b"] = lbl_b

    # Регистрация перехода в журнале наблюдаемости состояния
    if "transition_log" not in st.session_state or not isinstance(st.session_state.transition_log, list):
        st.session_state["transition_log"] = []

    st.session_state["transition_log"].append({
        "event": f"pair_update:{resolved_showcase}",
        "requested_pair": (drug_a, drug_b),
        "canonical_pair": pair,
        "widget_pair": (lbl_a or clean_a, lbl_b or clean_b),
        "analysis_pair": pair,
        "rendered_pair": (clean_a, clean_b)
    })
    st.session_state["transition_log"] = st.session_state["transition_log"][-10:]


def swap_active_pair(
    normalizer: Any | None = None,
    catalog_labels: list[str] | None = None,
    catalog_map: dict[str, str] | None = None,
) -> None:
    """Атомарно меняет местами Препарат A и Препарат B во всех модулях."""
    cur_a, cur_b = get_active_pair()
    set_active_pair(
        cur_b,
        cur_a,
        normalizer=normalizer,
        catalog_labels=catalog_labels,
        catalog_map=catalog_map,
    )


def reset_active_pair(
    normalizer: Any | None = None,
    catalog_labels: list[str] | None = None,
    catalog_map: dict[str, str] | None = None,
) -> None:
    """Сбрасывает активную пару к эталонной комбинации по умолчанию."""
    set_active_pair(
        DEFAULT_PAIR[0],
        DEFAULT_PAIR[1],
        cohort_id=DEFAULT_COHORT,
        showcase_id="warfarin_aspirin",
        normalizer=normalizer,
        catalog_labels=catalog_labels,
        catalog_map=catalog_map,
    )


def set_workspace_cohort(
    preset_drugs: Sequence[str],
    cohort_id: str,
    primary_pair: tuple[str, str],
    normalizer: Any | None = None,
    catalog_labels: list[str] | None = None,
    catalog_map: dict[str, str] | None = None,
) -> None:
    """Атомарно применяет клинический пресет в Workspace и синхронизирует всю платформу."""
    new_items: list[str] = []
    for d in preset_drugs:
        lbl = find_catalog_label(d, normalizer, catalog_labels, catalog_map)
        if lbl:
            new_items.append(lbl)
        elif catalog_labels and catalog_map:
            clean_d = d.strip().lower()
            match = next((l for l in catalog_labels if catalog_map.get(l, "").lower() == clean_d or clean_d in l.lower()), None)
            if match:
                new_items.append(match)

    if new_items:
        st.session_state["workspace_multiselect"] = new_items
        st.session_state["ws_selection"] = new_items

    matched_sc = _match_showcase_id(primary_pair[0], primary_pair[1])
    set_active_pair(
        primary_pair[0],
        primary_pair[1],
        cohort_id=cohort_id,
        showcase_id=matched_sc if matched_sc != "custom" else cohort_id,
        normalizer=normalizer,
        catalog_labels=catalog_labels,
        catalog_map=catalog_map,
    )


def get_workspace_filter() -> str:
    """Возвращает текущий фильтр степени тяжести для Workspace."""
    return st.session_state.get("ws_severity_filter", "All")


def set_workspace_filter(filter_level: str) -> None:
    """Устанавливает фильтр степени тяжести для Workspace."""
    st.session_state["ws_severity_filter"] = filter_level
    st.session_state["ws_severity_pills"] = filter_level
