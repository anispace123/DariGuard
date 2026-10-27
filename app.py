"""PHARMA SENTINEL — Платформа клинической фармакологии и анализа полипрагмазии.

Архитектура: Production-grade clinical intelligence platform.
Интеграция React Bits: <Galaxy /> (WebGL2 фон), <TechText /> (интерактивный заголовок), <AnimatedContent /> (анимация переходов и контента).
Локализация: Полноценное переключение RU / EN с сохранением всех синонимов и брендов.
"""
from difflib import get_close_matches
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from components.molecule_3d import render_molecule_3d_html
from components.react_bits import render_tech_text_and_effects_html
from data_loader import DataValidationError, load_ddinter
from graph_builder import interaction_color, major_hubs
from local_ai import (
    ask_local_model,
    generate_structured_explanation,
    get_local_ai_status,
    make_evidence_prompt,
)
from model import novel_pair_hypotheses, train_and_evaluate
from multi_checker import MultiDrugChecker
from normalization import DrugNormalizer
from supplement_schema import SupplementEvidenceRepository


# ─── Инициализация состояния (Session State) ─────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "RU"

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "workspace"


st.set_page_config(
    page_title="Pharma Sentinel · Clinical Pharmacology",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─── Централизованный словарь локализации (I18N — без дешевых эмодзи) ─────────
I18N = {
    "RU": {
        "brand_sub": "Клиническая фармакология",
        "live_db": "DDInter v2024.11 · 160 235 пар",
        "disclaimer_lead": "Клинический регламент:",
        "disclaimer_text": "Pharma Sentinel — исследовательская система биоинформатики. Не заменяет клинического суждения врача. Отсутствие записи в DDInter не является подтверждением безопасности комбинации.",
        # Навигация (строгая типографика без эмодзи)
        "nav_workspace": "Анализ взаимодействий",
        "nav_supplements": "БАДы и нутрицевтики",
        "nav_network": "Граф связей",
        "nav_ml": "ML-валидация",
        "nav_ai": "ИИ-аналитик",
        "nav_overview": "О платформе",
        # Рабочее пространство (Workspace)
        "ws_eyebrow": "Рабочая станция · Анализ полипрагмазии",
        "ws_title": "Анализ лекарственных назначений",
        "ws_subtitle": "Полномасштабный перекрестный аудит всех N×(N−1)/2 пар препаратов, детекция дублирования МНН и сопутствующих фитопрепаратов.",
        "presets_label": "Клинические когортные сценарии (быстрый ввод):",
        "preset_cyp": "Триада CYP2C9 · Варфарин + Кордарон + Дифлюкан",
        "preset_whammy": "Triple Whammy · Эналаприл + Фуросемид + Ибупрофен",
        "preset_bleeding": "Геморрагический конфликт · Варфарин + Аспирин",
        "search_label": "Когорта препаратов (поиск по МНН, бренду или торговому названию):",
        "search_help": "Распознает русские торговые марки (Нурофен, Кардиомагнил, Цитрамон, Омез), латиницу и канонические МНН.",
        "audit_protocol": "Протокол аудита",
        "audit_desc": "PS-8924 · DDInter Core<br>Расчёт пар N×(N−1)/2<br>Контроль дублирования МНН",
        "prompt_empty": "Для запуска анализа выберите как минимум 2 препарата в списке выше.",
        "risk_overall": "Профиль риска",
        "risk_sub": "По наивысшей тяжести",
        "stat_major": "Major",
        "stat_major_sub": "Критический риск",
        "stat_mod": "Moderate",
        "stat_mod_sub": "Требуют коррекции",
        "stat_minor": "Minor",
        "stat_minor_sub": "Малый риск",
        "stat_not_in_db": "Нет в DDInter",
        "stat_not_in_db_sub": "Не доказано как безопасное",
        "registry_title": "Реестр обнаруженных взаимодействий",
        "finding_label": "Клиническая оценка:",
        "finding_mechanism": "Механизм взаимодействия",
        "finding_clinical": "Клиническое значение",
        "finding_management": "Рекомендованная тактика",
        "audit_inn_count": "Веществ МНН:",
        "audit_pairs_count": "Пар комбинаций:",
        "supp_box_title": "Доказанные взаимодействия с сопутствующими БАДами и пищей",
        "management_label": "Тактика:",
        "dup_warning": "Дублирование действующего вещества:",
        # БАДы
        "supp_eyebrow": "Доказательная фито-токсикология",
        "supp_title": "База взаимодействий с БАДами и нутрицевтиками",
        "supp_desc": "Фармакокинетические конфликты экстрактов трав, микронутриентов и пищи с лекарствами со строгой доказательной градацией (Level A/B/C).",
        "supp_search_label": "Поиск по БАДу (Зверобой, Грейпфрут, Гинкго) или препарату:",
        "supp_filter_label": "Уровень доказательности:",
        "supp_all_levels": "Все уровни",
        "supp_found": "Найдено верифицированных записей:",
        "supp_type": "Тип:",
        "supp_mech": "Механизм:",
        "supp_conseq": "Последствие:",
        "supp_sources": "Первичные источники:",
        # Граф
        "net_eyebrow": "Топологический анализ графа",
        "net_title": "Интерактивная сеть связей DDInter",
        "net_desc": "Топологические окрестности препаратов в базе DDInter с ранжированием по степени риска.",
        "net_center": "Центральный узел (препарат):",
        "net_levels": "Уровни риска:",
        "net_max_edges": "Максимум связей:",
        "net_empty": "Для выбранного препарата и фильтров связей не найдено.",
        "net_hubs": "Топ-10 фармакологических хабов (по числу связей Major)",
        # ML
        "ml_eyebrow": "Научная валидация моделей",
        "ml_title": "Верификация Link Prediction (Leakage-Free)",
        "ml_desc": "Оценка моделей восстановления скрытых связей на графе DDInter. Обучающие и тестовые связи физически удалены из графа признаков для исключения утечки.",
        "ml_sample": "Выборка: {train} обучающих · {test} тестовых (сбалансированные классы).",
        "ml_conf_matrix": "Матрица ошибок (Случайный лес, порог 0.5)",
        # AI
        "ai_eyebrow": "Локальный языковой ассистент",
        "ai_title": "Контекстный ИИ-аналитик (Ollama)",
        "ai_desc": "Формирование доказательных текстовых пояснений по конкретным фактам DDInter без передачи данных во внешние облака.",
        "ai_drug_a": "Препарат A:",
        "ai_drug_b": "Препарат B:",
        "ai_question": "Клинический вопрос:",
        "ai_question_ph": "Например: в чем биологический механизм этого взаимодействия?",
        "ai_offline_title": "Структурированное пояснение (детерминированное, offline):",
        "ai_summary": "Суть:",
        "ai_clinical": "Клинический контекст:",
        "ai_recommendation": "Рекомендация:",
        "ai_status_title": "Статус локального сервиса Ollama",
        "ai_btn_generate": "Сгенерировать пояснение…",
        "ai_model": "Локальная модель:",
        "ai_resp": "Ответ модели:",
        # О платформе (Overview)
        "ov_eyebrow": "Инициатива 2025 · Вычислительная фармакология",
        "ov_title": "Картографирование скрытых границ полипрагмазии.",
        "ov_desc": "Детерминированный биоинформатический комплекс для исследования многокомпонентных межлекарственных взаимодействий, конкуренции за изоферменты CYP450 и полиорганной токсичности.",
        "ov_stat_pairs": "Индексировано пар",
        "ov_stat_drugs": "Уникальных веществ",
        "ov_stat_major": "Связей Major (критических)",
        "ov_btn_start": "Перейти к анализу назначений →",
        "ov_provenance_title": "Происхождение данных и методология",
        "ov_provenance_text": "Каждая межлекарственная связь подтверждена рецензируемой базой DDInter (Nucleic Acids Research, 2022). Данные нормализованы: устранены петли A=A, дубликаты свёрнуты по наивысшей тяжести, обеспечено сопоставление синонимов и торговых названий.",
        # Футер
        "footer_text": "Pharma Sentinel · Академический исследовательский проект, 2025.<br>База данных: DDInter v2024.11 (Xiong G. et al., NAR). Не является медицинским изделием.",
    },
    "EN": {
        "brand_sub": "Clinical Pharmacology Intelligence",
        "live_db": "DDInter v2024.11 · 160,235 pairs",
        "disclaimer_lead": "Clinical Protocol Notice:",
        "disclaimer_text": "Pharma Sentinel is a bioinformatics research instrument. It does not replace clinical judgment. Absence of a record in DDInter does not confirm pharmacological safety.",
        # Navigation (clean typography, no emojis)
        "nav_workspace": "Interaction Analysis",
        "nav_supplements": "Dietary Supplements",
        "nav_network": "Network Topology",
        "nav_ml": "ML Validation",
        "nav_ai": "Local AI Analyst",
        "nav_overview": "Overview & Provenance",
        # Workspace
        "ws_eyebrow": "Analysis Workspace · Polypharmacy",
        "ws_title": "Multi-Drug Safety Assessment",
        "ws_subtitle": "Full pairwise evaluation of all N×(N−1)/2 drug combinations, active ingredient duplication detection, and herbal conflict screening.",
        "presets_label": "Clinical Cohort Presets (Quick Load):",
        "preset_cyp": "CYP2C9 Triad · Warfarin + Amiodarone + Fluconazole",
        "preset_whammy": "Triple Whammy · Enalapril + Furosemide + Ibuprofen",
        "preset_bleeding": "Hemorrhagic Conflict · Warfarin + Aspirin",
        "search_label": "Prescription Cohort (Search by INN, brand, or trade name):",
        "search_help": "Resolves trade brands (Nurofen, Cardiomagnyl, Citramon, Omez), Latin/Cyrillic synonyms, and canonical DDInter INNs.",
        "audit_protocol": "Audit Protocol",
        "audit_desc": "PS-8924 · DDInter Core<br>Pairwise N×(N-1)/2 matrix<br>Active INN duplication guard",
        "prompt_empty": "Select at least 2 medications in the input box above to calculate interaction matrix.",
        "risk_overall": "Risk Profile",
        "risk_sub": "By highest severity",
        "stat_major": "Major",
        "stat_major_sub": "Critical risk",
        "stat_mod": "Moderate",
        "stat_mod_sub": "Requires monitoring",
        "stat_minor": "Minor",
        "stat_minor_sub": "Limited risk",
        "stat_not_in_db": "Not in DDInter",
        "stat_not_in_db_sub": "Not proven safe",
        "registry_title": "Pairwise Interaction Findings",
        "finding_label": "Clinical finding:",
        "finding_mechanism": "Interaction Mechanism",
        "finding_clinical": "Clinical Significance",
        "finding_management": "Recommended Action",
        "audit_inn_count": "Active INNs:",
        "audit_pairs_count": "Pairwise checks:",
        "supp_box_title": "Verified Dietary and Herbal Interactions for Current Cohort",
        "management_label": "Management:",
        "dup_warning": "Therapeutic duplication detected:",
        # Supplements
        "supp_eyebrow": "Evidence-Based Phytopharmacology",
        "supp_title": "Supplement & Herb Interaction Registry",
        "supp_desc": "Pharmacokinetic conflicts between herbal extracts, nutrients, and conventional drugs graded by clinical evidence (Level A/B/C).",
        "supp_search_label": "Search by supplement (St. John's wort, Grapefruit, Ginkgo) or drug:",
        "supp_filter_label": "Evidence level:",
        "supp_all_levels": "All levels",
        "supp_found": "Verified records found:",
        "supp_type": "Type:",
        "supp_mech": "Mechanism:",
        "supp_conseq": "Consequence:",
        "supp_sources": "Primary sources:",
        # Network
        "net_eyebrow": "Graph Topology Analysis",
        "net_title": "DDInter Network Interaction Map",
        "net_desc": "Topological neighborhoods of drugs in DDInter with risk-ranked edge visualization.",
        "net_center": "Central drug node:",
        "net_levels": "Risk levels:",
        "net_max_edges": "Max edges:",
        "net_empty": "No connections found for selected drug and filters.",
        "net_hubs": "Top 10 Pharmacological Hubs (by Major degree)",
        # ML
        "ml_eyebrow": "Scientific Model Validation",
        "ml_title": "Link Prediction Benchmark (Leakage-Free)",
        "ml_desc": "Evaluation of graph topological models for predicting unrecorded drug interactions with train/test edges strictly isolated from feature calculation.",
        "ml_sample": "Sample: {train} training · {test} test examples (balanced classes).",
        "ml_conf_matrix": "Random Forest Confusion Matrix (threshold 0.5)",
        # AI
        "ai_eyebrow": "Contextual Language Assistant",
        "ai_title": "Local AI Clinical Pharmacology Analyst",
        "ai_desc": "Evidence-grounded explanations of DDInter records generated locally using Ollama without sending patient data to cloud APIs.",
        "ai_drug_a": "Drug A:",
        "ai_drug_b": "Drug B:",
        "ai_question": "Clinical question:",
        "ai_question_ph": "E.g., What is the biochemical mechanism of this interaction?",
        "ai_offline_title": "Structured explanation (deterministic, offline):",
        "ai_summary": "Summary:",
        "ai_clinical": "Clinical context:",
        "ai_recommendation": "Recommendation:",
        "ai_status_title": "Local Ollama service status",
        "ai_btn_generate": "Generate explanation…",
        "ai_model": "Local model:",
        "ai_resp": "Model response:",
        # Overview
        "ov_eyebrow": "Initiative 2025 · Computational Pharmacology",
        "ov_title": "Mapping the unseen boundaries of polypharmacy.",
        "ov_desc": "A deterministic framework for identifying multi-agent pharmacokinetic clashes across hepatic CYP450 clearance pathways and renal transport systems.",
        "ov_stat_pairs": "Pairs indexed",
        "ov_stat_drugs": "Substances",
        "ov_stat_major": "Major interactions",
        "ov_btn_start": "Launch Interaction Analysis →",
        "ov_provenance_title": "Data Provenance & Scientific Integrity",
        "ov_provenance_text": "Every drug interaction is anchored in DDInter (Nucleic Acids Research, 2022). Records are canonically normalized: self-loops eliminated, duplicates collapsed by severity, and synonyms linked to verified INNs.",
        # Footer
        "footer_text": "Pharma Sentinel · Academic Research Project, 2025.<br>Database: DDInter v2024.11 (Xiong G. et al., NAR). Not a certified medical device.",
    }
}


def t(key: str, **kwargs) -> str:
    """Возвращает перевод по ключу для текущего выбранного языка."""
    lang = st.session_state.get("lang", "RU")
    text = I18N.get(lang, I18N["RU"]).get(key, I18N["RU"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text


# ─── Дизайн-система (Clinical Sage Palette) + Анимации переходов ─────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:           #F3F6F2;
  --bg-sec:       #EAF0E9;
  --bg-card:      #FFFFFF;
  --bg-elevated:  #F7F9F6;
  --bg-subtle:    #EAF0E9;
  --border:       #DCE4DA;
  --border-hover: #BCCEC0;
  --border-focus: #315E50;

  --ink-primary:  #26332D;
  --ink-body:     #26332D;
  --ink-muted:    #65736A;

  --accent:       #315E50;
  --accent-hover: #264B40;
  --accent-light: #EEF5F1;
  --secondary-sage:#789483;

  --info-blue:    #2E6171;
  --info-blue-bg: #EBF3F5;
  --info-blue-bd: #C6DDE4;

  --sev-major:    #B83A38;
  --sev-major-bg: #FDF2F2;
  --sev-major-bd: #F7CACA;
  --sev-mod:      #B4681E;
  --sev-mod-bg:   #FDF6EE;
  --sev-mod-bd:   #F7DFC2;
  --sev-minor:    #315E50;
  --sev-minor-bg: #EDF4F0;
  --sev-minor-bd: #CFE2D7;
  --sev-none:     #65736A;
  --sev-none-bg:  #F2F5F2;
  --sev-none-bd:  #DCE4DA;

  --font-ui:      'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-serif:   'Lora', Georgia, serif;
  --font-mono:    'JetBrains Mono', monospace;

  --ease-snappy:  cubic-bezier(0.16, 1, 0.3, 1);
  --ease-power3:  cubic-bezier(0.215, 0.61, 0.355, 1);
}

html, body, [class*="css"] {
  font-family: var(--font-ui);
  color: var(--ink-body);
  background-color: var(--bg);
  -webkit-font-smoothing: antialiased;
}

/* Прозрачность оболочки Streamlit для видимости фоновой молекулярной сети */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
  background: transparent !important;
  color: var(--ink-body) !important;
}

#MainMenu, footer, [data-testid="stHeader"] { display: none !important; }

.block-container, [data-testid="stMainBlockContainer"] {
  max-width: 1240px !important;
  padding: 0.5rem 1.5rem 3rem !important;
  position: relative !important;
  z-index: 2 !important;
}

[data-testid="column"] { min-width: 0 !important; }

/* ── Заголовки и типографика ── */
[data-testid="stMarkdownContainer"] h1 {
  font-family: var(--font-serif) !important;
  font-size: clamp(1.55rem, 2.8vw, 2.15rem) !important;
  font-weight: 500 !important;
  line-height: 1.25 !important;
  letter-spacing: -0.015em !important;
  color: var(--ink-primary) !important;
  margin: 0.15rem 0 0.45rem !important;
}

[data-testid="stMarkdownContainer"] h2 {
  font-family: var(--font-serif) !important;
  font-size: clamp(1.2rem, 2.0vw, 1.55rem) !important;
  font-weight: 500 !important;
  line-height: 1.3 !important;
  color: var(--ink-primary) !important;
  margin: 1.15rem 0 0.4rem !important;
}

[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
  font-family: var(--font-ui) !important;
  font-size: 1.02rem !important;
  font-weight: 600 !important;
  color: var(--ink-primary) !important;
  margin: 0.95rem 0 0.35rem !important;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] {
  color: var(--ink-muted);
}

hr {
  border-color: var(--border) !important;
}

/* ── Плашка статуса базы данных ── */
.ps-live-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 0.35rem 0.75rem;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--accent);
}

.ps-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 2px rgba(49, 94, 80, 0.2);
  animation: ps-pulse 2.2s infinite ease-in-out;
}

@keyframes ps-pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
}

/* ── Навигационная полоса вкладок ── */
div[data-testid="stRadio"] > div[role="radiogroup"] {
  display: flex;
  flex-direction: row;
  gap: 0.35rem;
  flex-wrap: wrap;
  background: var(--bg-sec);
  padding: 4px;
  border-radius: 4px;
  border: 1px solid var(--border);
  margin-bottom: 1.15rem;
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label {
  margin: 0 !important;
  padding: 0.42rem 0.95rem !important;
  border-radius: 3px;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.01em !important;
  color: var(--ink-muted) !important;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: transform 140ms var(--ease-snappy), background 140ms ease, color 140ms ease, border-color 140ms ease;
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label p {
  color: inherit !important;
  font-size: 0.82rem !important;
  font-weight: inherit !important;
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
  color: var(--ink-primary) !important;
  background: rgba(255, 255, 255, 0.7);
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"],
div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
  background: #FFFFFF !important;
  color: var(--accent) !important;
  border-color: var(--border) !important;
  font-weight: 600 !important;
  box-shadow: 0 1px 3px rgba(38, 51, 45, 0.07);
}

/* ── Формы ввода, селекты и теги препаратов на светлых поверхностях #FFFFFF / #F7F9F6 ── */
label[data-testid="stWidgetLabel"] p {
  color: var(--ink-primary) !important;
  font-weight: 600 !important;
  font-size: 0.83rem !important;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] {
  background-color: #FFFFFF !important;
  border-color: var(--border) !important;
  color: var(--ink-primary) !important;
  border-radius: 3px !important;
}

div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"]:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent) !important;
}

div[data-baseweb="select"] input,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
  color: var(--ink-primary) !important;
}

span[data-baseweb="tag"] {
  background-color: var(--accent-light) !important;
  border: 1px solid #D2E4DA !important;
  color: var(--ink-primary) !important;
  border-radius: 3px !important;
}

span[data-baseweb="tag"] span {
  color: var(--ink-primary) !important;
  font-weight: 500 !important;
}

ul[data-testid="stSelectboxVirtualDropdown"],
div[data-baseweb="popover"] ul {
  background-color: #FFFFFF !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 4px 12px rgba(38, 51, 45, 0.08) !important;
}

div[data-baseweb="popover"] li {
  color: var(--ink-primary) !important;
}

div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"] {
  background-color: var(--bg-elevated) !important;
  color: var(--accent) !important;
}

/* ── Таблицы и алерты ── */
[data-testid="stDataFrame"] {
  background: #FFFFFF !important;
  border: 1px solid var(--border) !important;
  border-radius: 3px !important;
  padding: 2px;
}

[data-testid="stAlert"] {
  background-color: #FFFFFF !important;
  border: 1px solid var(--border) !important;
  color: var(--ink-primary) !important;
  border-radius: 3px !important;
}

[data-testid="stAlert"] p {
  color: var(--ink-primary) !important;
}

/* ── Анимация смены страниц и появления контента (<AnimatedContent />) ── */
@keyframes ps-page-enter {
  0% {
    opacity: 0;
    transform: translate3d(0, 18px, 0);
  }
  100% {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

.ps-animated-page-root {
  animation: ps-page-enter 420ms var(--ease-snappy) both;
}

.ps-anim-item {
  animation: ps-page-enter 440ms var(--ease-snappy) both;
}

.ps-stagger-1 { animation-delay: 35ms; }
.ps-stagger-2 { animation-delay: 75ms; }
.ps-stagger-3 { animation-delay: 115ms; }
.ps-stagger-4 { animation-delay: 155ms; }

/* ── Клинический дисклеймер (Сдержанный клинический синий / зеленый) ── */
.ps-disclaimer {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: #FFFFFF;
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  padding: 0.65rem 1rem;
  border-radius: 3px;
  margin-bottom: 1.25rem;
  font-size: 0.81rem;
  line-height: 1.5;
  color: var(--ink-body);
  box-shadow: 0 1px 2px rgba(38, 51, 45, 0.03);
}

.ps-disclaimer-tag {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--info-blue);
  background: var(--info-blue-bg);
  border: 1px solid var(--info-blue-bd);
  padding: 2px 6px;
  border-radius: 2px;
  white-space: nowrap;
  margin-top: 1px;
}

.ps-disclaimer b { color: var(--ink-primary); }

/* ── Карточки и статистика (#FFFFFF / #F7F9F6) ── */
.ps-stat-box {
  background: #FFFFFF;
  border: 1px solid var(--border);
  padding: 0.85rem 1rem;
  border-radius: 3px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 1px 2px rgba(38, 51, 45, 0.03);
  transition: transform 160ms var(--ease-snappy), border-color 160ms ease;
}

.ps-stat-box:hover {
  transform: translateY(-1px);
  border-color: var(--border-hover);
}

.ps-stat-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-muted);
}

.ps-stat-number {
  font-family: var(--font-serif);
  font-size: 1.5rem;
  line-height: 1.2;
  font-weight: 500;
  color: var(--ink-primary);
  margin: 0.2rem 0;
}

.ps-stat-sub {
  font-size: 0.72rem;
  color: var(--ink-muted);
}

/* ── Результаты анализа (Клиническая иерархия) ── */
.ps-card-finding {
  background: #FFFFFF;
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 1rem 1.15rem;
  margin-bottom: 0.75rem;
  box-shadow: 0 1px 2px rgba(38, 51, 45, 0.03);
  transition: border-color 150ms ease, transform 160ms var(--ease-snappy);
  animation: ps-page-enter 420ms var(--ease-snappy) both;
}

.ps-card-finding:hover {
  border-color: var(--border-hover);
  transform: translateY(-1px);
}

.ps-finding-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.65rem;
}

.ps-finding-drugs {
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--ink-primary);
  flex: 1;
  min-width: 0;
  overflow-wrap: break-word;
}

.ps-finding-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.55rem;
}

.ps-finding-col {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.ps-section-label {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--secondary-sage);
}

.ps-section-val {
  font-size: 0.84rem;
  line-height: 1.55;
  color: var(--ink-body);
}

.ps-rec-box {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  padding: 0.45rem 0.75rem;
  border-radius: 2px;
  margin-top: 0.2rem;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--ink-body);
}

/* ── Семантические плашки тяжести (не только цвет, но и нецветовые маркеры) ── */
.ps-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2.5px 8px;
  border-radius: 2px;
  font-size: 0.71rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border: 1px solid;
  white-space: nowrap;
}

.ps-badge-major { color: var(--sev-major); background: var(--sev-major-bg); border-color: var(--sev-major-bd); }
.ps-badge-mod   { color: var(--sev-mod);   background: var(--sev-mod-bg);   border-color: var(--sev-mod-bd); }
.ps-badge-minor { color: var(--sev-minor); background: var(--sev-minor-bg); border-color: var(--sev-minor-bd); }
.ps-badge-none  { color: var(--sev-none);  background: var(--sev-none-bg);  border-color: var(--sev-none-bd); }

/* ── БАД-карточка ── */
.ps-supp-row {
  border: 1px solid var(--border);
  border-left: 3px solid var(--sev-major);
  background: #FFFFFF;
  padding: 0.75rem 0.95rem;
  border-radius: 0 3px 3px 0;
  margin-bottom: 0.5rem;
  box-shadow: 0 1px 2px rgba(38, 51, 45, 0.02);
  animation: ps-page-enter 440ms var(--ease-snappy) both;
}

/* ── Пресеты и кнопки ── */
.stButton > button {
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  border-radius: 3px !important;
  min-height: 38px !important;
  color: var(--ink-primary) !important;
  background: #FFFFFF !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 1px 2px rgba(38, 51, 45, 0.03) !important;
  transition: transform 140ms var(--ease-snappy), border-color 140ms ease, background 140ms ease !important;
}

.stButton > button:hover {
  transform: translateY(-1px) !important;
  background: var(--bg-elevated) !important;
  border-color: var(--secondary-sage) !important;
  color: var(--ink-primary) !important;
}

.stButton > button[kind="primary"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #FFFFFF !important;
  box-shadow: 0 1px 3px rgba(49, 94, 80, 0.2) !important;
}

.stButton > button[kind="primary"]:hover {
  background: var(--accent-hover) !important;
  border-color: var(--accent-hover) !important;
  color: #FFFFFF !important;
}

.stButton > button:active {
  transform: translateY(0) !important;
}

/* ── Доступность ── */
button:focus-visible, input:focus-visible, select:focus-visible {
  outline: 2px solid var(--border-focus) !important;
  outline-offset: 1px !important;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
""", unsafe_allow_html=True)


# ─── Кэшируемые данные ───────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cached_data():
    return load_ddinter()


@st.cache_resource(show_spinner=False)
def cached_normalizer(drugs_tuple):
    return DrugNormalizer(drugs_tuple)


@st.cache_data(show_spinner=False)
def cached_evaluation(pairs: pd.DataFrame, drugs: pd.DataFrame):
    return train_and_evaluate(pairs, drugs)


# ─── Семантические бейджи (с нецветовыми маркерами) ──────────────────────────
def severity_badge(level: str) -> str:
    lang = st.session_state.get("lang", "RU")
    if level == "Major":
        label = "Major · Высокий риск" if lang == "RU" else "Major Risk"
        return f'<span class="ps-badge ps-badge-major">● {label}</span>'
    elif level == "Moderate":
        label = "Moderate · Умеренный" if lang == "RU" else "Moderate Risk"
        return f'<span class="ps-badge ps-badge-mod">▲ {label}</span>'
    elif level == "Minor":
        label = "Minor · Низкий риск" if lang == "RU" else "Minor Risk"
        return f'<span class="ps-badge ps-badge-minor">○ {label}</span>'
    elif level == "Unknown":
        label = "Не классифицирован" if lang == "RU" else "Unknown"
        return f'<span class="ps-badge ps-badge-none">? {label}</span>'
    else:
        label = "Нет в DDInter" if lang == "RU" else "Not in DDInter"
        return f'<span class="ps-badge ps-badge-none">— {label}</span>'


# ─── Верхняя панель (<TechText /> + <MolecularNetwork /> + RU/EN) ──────────
def render_top_bar():
    c_brand, c_meta, c_lang = st.columns([3.2, 2.0, 1.0])

    current_page = st.session_state.get("nav_page", "workspace")

    with c_brand:
        # Интерактивный заголовок <TechText /> + постоянная фоновая молекулярная сеть в window.parent
        # Важно: не передаём page_key, чтобы HTML-строка оставалась неизменной и Streamlit не пересоздавал iframe при смене вкладок!
        tech_html = render_tech_text_and_effects_html(
            text="PHARMA SENTINEL",
            subtitle=f"{t('brand_sub')} · RELEASE v3.5",
            height=72,
        )
        components.html(tech_html, height=74, scrolling=False)

    with c_meta:
        st.markdown(
            f'<div style="text-align:right; padding-top:16px;">'
            f'<span class="ps-live-badge"><span class="ps-live-dot"></span>{t("live_db")}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    with c_lang:
        st.markdown('<div style="padding-top:12px;"></div>', unsafe_allow_html=True)
        cur_lang = st.session_state.get("lang", "RU")
        new_lang = st.radio(
            "Lang",
            options=["RU", "EN"],
            index=0 if cur_lang == "RU" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="lang_toggle"
        )
        if new_lang != cur_lang:
            st.session_state.lang = new_lang
            st.rerun()

    # Горизонтальная навигационная панель без эмодзи
    nav_options = [
        t("nav_workspace"),
        t("nav_supplements"),
        t("nav_network"),
        t("nav_ml"),
        t("nav_ai"),
        t("nav_overview"),
    ]

    key_to_idx = {
        "workspace": 0,
        "supplements": 1,
        "network": 2,
        "ml": 3,
        "ai": 4,
        "overview": 5
    }
    idx_to_key = ["workspace", "supplements", "network", "ml", "ai", "overview"]

    cur_idx = key_to_idx.get(current_page, 0)

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=cur_idx,
        horizontal=True,
        label_visibility="collapsed",
        key="main_nav_radio"
    )

    chosen_key = idx_to_key[nav_options.index(selected_nav)]
    if chosen_key != current_page:
        st.session_state.nav_page = chosen_key
        st.rerun()

    # Клинический дисклеймер
    st.markdown(
        f'<div class="ps-disclaimer">'
        f'<span class="ps-disclaimer-tag">PROTOCOL</span>'
        f'<div><b>{t("disclaimer_lead")}</b> {t("disclaimer_text")}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_footer():
    st.markdown(
        f'<div style="border-top:1px solid var(--border); padding-top:1.25rem; margin-top:2.5rem; display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem; font-size:0.75rem; color:var(--ink-muted);">'
        f'<div>{t("footer_text")}</div>'
        f'<div style="text-align:right; font-family:var(--font-mono);">Pharmacoinformatics Lab · 2025</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# ─── Страница: Анализ назначений (Workspace — главная рабочая зона) ───────────
def view_workspace(pairs: pd.DataFrame, drugs: pd.DataFrame, normalizer: DrugNormalizer, supp_repo: SupplementEvidenceRepository):
    st.markdown(
        f'<div class="ps-animated-page-root ps-page-workspace">'
        f'<div class="ps-anim-item ps-stagger-1">'
        f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.07em; color:var(--accent);">'
        f'{t("ws_eyebrow")}</div>'
        f'<h1>{t("ws_title")}</h1>'
        f'<p style="font-size:0.92rem; color:var(--ink-muted); line-height:1.5; margin-bottom:1rem;">'
        f'{t("ws_subtitle")}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    catalog = normalizer.get_search_catalog()
    catalog_labels = [label for label, _ in catalog]
    catalog_map = dict(catalog)

    # ── Блок быстрых клинических пресетов (без эмодзи) ──
    st.markdown(
        f'<div class="ps-anim-item ps-stagger-2" style="font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-muted); margin-bottom:0.4rem;">'
        f'{t("presets_label")}</div>',
        unsafe_allow_html=True
    )

    p1, p2, p3 = st.columns(3)
    selected_preset = None
    with p1:
        if st.button(t("preset_cyp"), use_container_width=True):
            selected_preset = ["warfarin", "amiodarone", "fluconazole"]
    with p2:
        if st.button(t("preset_whammy"), use_container_width=True):
            selected_preset = ["enalapril", "furosemide", "ibuprofen"]
    with p3:
        if st.button(t("preset_bleeding"), use_container_width=True):
            selected_preset = ["warfarin", "acetylsalicylic acid"]

    # Инициализация дефолтного набора с русскими МНН / синонимами
    if "ws_selection" not in st.session_state:
        default_items = []
        for kw in ["варфарин", "аспирин", "ибупрофен"]:
            match = next((l for l in catalog_labels if kw in l.lower()), None)
            if match:
                default_items.append(match)
        st.session_state.ws_selection = default_items if len(default_items) >= 2 else catalog_labels[:3]

    if selected_preset:
        new_items = []
        for p in selected_preset:
            match = next((l for l in catalog_labels if p in l.lower() or catalog_map.get(l) == p), None)
            if match:
                new_items.append(match)
        if new_items:
            st.session_state.ws_selection = new_items

    # ── Двухколоночный интерфейс: Ввод параметров слева, Протокол справа ──
    col_input, col_meta = st.columns([2.2, 1], gap="medium")

    with col_input:
        selected_drugs = st.multiselect(
            t("search_label"),
            options=catalog_labels,
            default=st.session_state.ws_selection,
            key="workspace_multiselect",
            help=t("search_help")
        )

    with col_meta:
        inn_count = len(selected_drugs)
        pairs_count = len(selected_drugs) * (len(selected_drugs) - 1) // 2 if len(selected_drugs) >= 2 else 0
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-2" style="height:100%;">'
            f'<div>'
            f'<div class="ps-stat-label">{t("audit_protocol")}</div>'
            f'<div style="font-size:0.82rem; color:var(--ink-body); line-height:1.5; margin-top:0.35rem;">{t("audit_desc")}</div>'
            f'</div>'
            f'<div style="margin-top:0.75rem; padding-top:0.6rem; border-top:1px solid var(--border); font-size:0.75rem; color:var(--ink-muted); font-family:var(--font-mono);">'
            f'<div>{t("audit_inn_count")} <b>{inn_count}</b></div>'
            f'<div style="margin-top:2px;">{t("audit_pairs_count")} <b>{pairs_count}</b></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    if len(selected_drugs) < 2:
        st.info(t("prompt_empty"))
        st.markdown('</div>', unsafe_allow_html=True)
        return

    queries = [catalog_map.get(label, label) for label in selected_drugs]
    checker = MultiDrugChecker(pairs, normalizer)
    report = checker.check_list(queries)

    # Предупреждения о дублировании МНН
    if report.duplicates_detected:
        for dup in report.duplicates_detected:
            st.error(f"{t('dup_warning')} {dup}")

    # ── Метрики полипрагмазии ──
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-2">'
            f'<div class="ps-stat-label">{t("risk_overall")}</div>'
            f'<div class="ps-stat-number" style="font-size:1.35rem;">{report.overall_risk}</div>'
            f'<div class="ps-stat-sub">{t("risk_sub")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-2">'
            f'<div class="ps-stat-label" style="color:var(--sev-major);">{t("stat_major")}</div>'
            f'<div class="ps-stat-number" style="color:var(--sev-major);">{report.summary_counts.get("Major", 0)}</div>'
            f'<div class="ps-stat-sub">{t("stat_major_sub")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-3">'
            f'<div class="ps-stat-label" style="color:var(--sev-mod);">{t("stat_mod")}</div>'
            f'<div class="ps-stat-number" style="color:var(--sev-mod);">{report.summary_counts.get("Moderate", 0)}</div>'
            f'<div class="ps-stat-sub">{t("stat_mod_sub")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-3">'
            f'<div class="ps-stat-label" style="color:var(--sev-minor);">{t("stat_minor")}</div>'
            f'<div class="ps-stat-number" style="color:var(--sev-minor);">{report.summary_counts.get("Minor", 0)}</div>'
            f'<div class="ps-stat-sub">{t("stat_minor_sub")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with m5:
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-4">'
            f'<div class="ps-stat-label">{t("stat_not_in_db")}</div>'
            f'<div class="ps-stat-number">{report.summary_counts.get("Not in DB", 0)}</div>'
            f'<div class="ps-stat-sub">{t("stat_not_in_db_sub")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Карточки взаимодействий (Клиническая иерархия) ──
    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3" style="margin-top:1.5rem;">{t("registry_title")}</h3>', unsafe_allow_html=True)

    for idx, p in enumerate(report.pairs):
        delay_ms = min(100 + idx * 45, 500)
        expl_data = generate_structured_explanation(p.drug_a, p.drug_b, p.level if p.in_ddinter else None)
        st.markdown(
            f'<div class="ps-card-finding" style="animation-delay:{delay_ms}ms;">'
            f'<div class="ps-finding-head">'
            f'<div class="ps-finding-drugs">{p.display_a} <span style="color:var(--secondary-sage); font-weight:400; margin:0 6px;">↔</span> {p.display_b}</div>'
            f'<div>{severity_badge(p.level)}</div>'
            f'</div>'
            f'<div class="ps-finding-grid">'
            f'<div class="ps-finding-col">'
            f'<div class="ps-section-label">{t("finding_mechanism")}</div>'
            f'<div class="ps-section-val">{p.explanation}</div>'
            f'</div>'
            f'<div class="ps-finding-col">'
            f'<div class="ps-section-label">{t("finding_clinical")}</div>'
            f'<div class="ps-section-val">{expl_data["clinical_meaning"]}</div>'
            f'</div>'
            f'<div class="ps-finding-col">'
            f'<div class="ps-section-label">{t("finding_management")}</div>'
            f'<div class="ps-rec-box">{expl_data["recommendation"]}</div>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Сопутствующие взаимодействия с БАДами ──
    active_canons = report.resolved_drugs
    related_supps = []
    for c in active_canons:
        related_supps.extend(supp_repo.get_by_drug(c))

    if related_supps:
        st.markdown(f'<h3 class="ps-anim-item ps-stagger-4" style="margin-top:1.25rem;">{t("supp_box_title")} ({len(related_supps)})</h3>', unsafe_allow_html=True)
        for s in related_supps:
            st.markdown(
                f'<div class="ps-supp-row">'
                f'<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem; flex-wrap:wrap;">'
                f'<div><b>{s.supplement_ru} ({s.supplement_lat}) + {s.drug_ru}</b></div>'
                f'<div>{severity_badge(s.severity)} <span class="ps-badge ps-badge-none">{s.evidence_level}</span></div>'
                f'</div>'
                f'<div style="font-size:0.83rem; color:var(--ink-body); margin-top:0.35rem;">{s.mechanism}</div>'
                f'<div style="font-size:0.8rem; color:var(--ink-primary); margin-top:0.25rem;"><b>{t("management_label")}</b> {s.clinical_management}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)


# ─── Страница: Доказательная база БАДов ──────────────────────────────────────
def view_supplements(supp_repo: SupplementEvidenceRepository):
    st.markdown(
        f'<div class="ps-animated-page-root ps-page-supplements">'
        f'<div class="ps-anim-item ps-stagger-1">'
        f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.07em; color:var(--accent);">'
        f'{t("supp_eyebrow")}</div>'
        f'<h1>{t("supp_title")}</h1>'
        f'<p style="font-size:0.92rem; color:var(--ink-muted); line-height:1.5; margin-bottom:1.25rem;">'
        f'{t("supp_desc")}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns([1.6, 1])
    with c1:
        query = st.text_input(t("supp_search_label"))
    with c2:
        level_filter = st.selectbox(t("supp_filter_label"), [t("supp_all_levels"), "Level A", "Level B", "Level C"])

    items = supp_repo.search(query)
    if level_filter != t("supp_all_levels"):
        items = [i for i in items if i.evidence_level == level_filter]

    st.markdown(
        f'<div class="ps-anim-item ps-stagger-2" style="font-size:0.82rem; color:var(--ink-muted); margin-bottom:0.75rem;">'
        f'{t("supp_found")} <b>{len(items)}</b></div>',
        unsafe_allow_html=True
    )

    for idx, item in enumerate(items):
        delay_ms = min(80 + idx * 50, 500)
        st.markdown(
            f'<div class="ps-card-finding" style="animation-delay:{delay_ms}ms;">'
            f'<div class="ps-finding-head">'
            f'<div>'
            f'<div style="font-size:0.7rem; font-weight:600; text-transform:uppercase; color:var(--accent);">'
            f'{item.evidence_level} · {item.interaction_type}</div>'
            f'<div class="ps-finding-drugs">{item.supplement_ru} ({item.supplement_lat}) ↔ {item.drug_ru}</div>'
            f'</div>'
            f'<div>{severity_badge(item.severity)}</div>'
            f'</div>'
            f'<div class="ps-finding-body">'
            f'<div><b>{t("supp_mech")}</b> {item.mechanism}</div>'
            f'<div style="margin-top:0.25rem;"><b>{t("supp_conseq")}</b> {item.clinical_consequence}</div>'
            f'<div style="margin-top:0.25rem; color:var(--accent); font-weight:600;"><b>{t("management_label")}</b> {item.clinical_management}</div>'
            f'</div>'
            f'<div style="margin-top:0.6rem; border-top:1px solid var(--border); padding-top:0.4rem; font-size:0.75rem; color:var(--ink-muted);">'
            f'<b>{t("supp_sources")}</b> {"; ".join(item.citations)}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)


# ─── Страница: Граф сети взаимодействий ──────────────────────────────────────
def view_network(pairs: pd.DataFrame, drugs: pd.DataFrame, names: list[str]):
    st.markdown(
        f'<div class="ps-animated-page-root ps-page-network">'
        f'<div class="ps-anim-item ps-stagger-1">'
        f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.07em; color:var(--accent);">'
        f'{t("net_eyebrow")}</div>'
        f'<h1>{t("net_title")}</h1>'
        f'<p style="font-size:0.92rem; color:var(--ink-muted); line-height:1.5; margin-bottom:1.25rem;">'
        f'{t("net_desc")}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([1.3, 1.1, 1.2])
    center = c1.selectbox(t("net_center"), names, index=names.index("warfarin") if "warfarin" in names else 0)
    levels = c2.multiselect(t("net_levels"), ["Major", "Moderate", "Minor", "Unknown"], default=["Major", "Moderate"])
    max_edges = c3.slider(t("net_max_edges"), 5, 80, 25)

    near = pairs[((pairs.Drug_A == center) | (pairs.Drug_B == center)) & pairs.Level.isin(levels)].copy()
    near["Neighbor"] = np.where(near.Drug_A == center, near.Drug_B, near.Drug_A)
    order = {"Major": 0, "Moderate": 1, "Minor": 2, "Unknown": 3}
    near["_order"] = near.Level.map(order)
    near = near.sort_values(["_order", "Neighbor"]).head(max_edges)

    if near.empty:
        st.info(t("net_empty"))
    else:
        try:
            from pyvis.network import Network
            net = Network(height="480px", width="100%", bgcolor="#F7F9F6", font_color="#26332D", directed=False, cdn_resources="in_line")
            net.set_options('{"physics":{"solver":"forceAtlas2Based","forceAtlas2Based":{"gravitationalConstant":-60,"centralGravity":0.02,"springLength":130,"springConstant":0.08},"stabilization":{"iterations":80}},"nodes":{"font":{"size":14,"face":"Inter, sans-serif","color":"#26332D"}},"edges":{"smooth":{"type":"continuous"},"width":2}}')
            net.add_node(center, label=center.title(), color={"background": "#315E50", "border": "#26332D"}, font={"color": "#FFFFFF"}, size=28)
            cmap = {"Major": "#B83A38", "Moderate": "#B4681E", "Minor": "#315E50", "Unknown": "#65736A"}
            for _, r in near.iterrows():
                nbr, lvl = r["Neighbor"], r["Level"]
                net.add_node(nbr, label=nbr.title(), color={"background": "#FFFFFF", "border": "#789483"}, font={"color": "#26332D"}, size=16)
                net.add_edge(center, nbr, color=cmap.get(lvl, "#65736A"), width=3 if lvl == "Major" else 2)
            components.html(net.generate_html(), height=500, scrolling=False)
        except Exception as exc:
            st.error(f"Render error: {exc}")

        st.dataframe(near[["Neighbor", "Level"]].rename(columns={"Neighbor": "Препарат", "Level": "Уровень риска"}), use_container_width=True, hide_index=True)

    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3">{t("net_hubs")}</h3>', unsafe_allow_html=True)
    st.dataframe(major_hubs(pairs), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Страница: Валидация ML моделей ──────────────────────────────────────────
def view_ml(pairs: pd.DataFrame, drugs: pd.DataFrame):
    st.markdown(
        f'<div class="ps-animated-page-root ps-page-ml">'
        f'<div class="ps-anim-item ps-stagger-1">'
        f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.07em; color:var(--accent);">'
        f'{t("ml_eyebrow")}</div>'
        f'<h1>{t("ml_title")}</h1>'
        f'<p style="font-size:0.92rem; color:var(--ink-muted); line-height:1.5; margin-bottom:1.25rem;">'
        f'{t("ml_desc")}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    result = cached_evaluation(pairs, drugs)
    metrics = result["metrics"]
    st.dataframe(metrics.style.format({"ROC-AUC": "{:.3f}", "Precision@5000": "{:.3f}"}), use_container_width=True, hide_index=True)
    st.caption(t("ml_sample", train=f"{result['train_examples']:,}".replace(",", " "), test=f"{result['test_examples']:,}".replace(",", " ")))

    fig, ax = plt.subplots(figsize=(8, 3.8))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F7F9F6")
    ax.tick_params(colors="#65736A")
    ax.xaxis.label.set_color("#26332D")
    ax.yaxis.label.set_color("#26332D")
    ax.title.set_color("#26332D")
    for sp in ax.spines.values():
        sp.set_color("#DCE4DA")

    palette = ["#315E50", "#789483", "#2E6171", "#B83A38", "#B4681E"]
    for (name, (fpr, tpr)), col in zip(result["roc"].items(), palette):
        auc = metrics.loc[metrics["Метод"] == name, "ROC-AUC"].iloc[0]
        ax.plot(fpr, tpr, label=f"{name} · AUC {auc:.3f}", color=col, linewidth=2)
    ax.plot([0, 1], [0, 1], "--", color="#BCCEC0", linewidth=1)
    ax.set(xlabel="False Positive Rate (FPR)", ylabel="True Positive Rate (TPR)", title="ROC Curves — Held-out DDInter Test Set")
    ax.grid(alpha=0.4, color="#DCE4DA")
    leg = ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="#DCE4DA", fontsize=8.5, loc="lower right")
    for text_obj in leg.get_texts():
        text_obj.set_color("#26332D")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3">{t("ml_conf_matrix")}</h3>', unsafe_allow_html=True)
    tn, fp, fn, tp = result["confusion"].ravel()
    st.dataframe(pd.DataFrame(
        [[tn, fp], [fn, tp]],
        index=["В базе нет записи" if st.session_state.lang == "RU" else "No record in DB", "Связь DDInter скрыта" if st.session_state.lang == "RU" else "Hidden DDInter pair"],
        columns=["Предсказано: нет связи" if st.session_state.lang == "RU" else "Predicted: no link", "Предсказано: связь" if st.session_state.lang == "RU" else "Predicted: link"]
    ), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Страница: ИИ-ассистент (Ollama) ─────────────────────────────────────────
def view_ai(pairs: pd.DataFrame, names: list[str]):
    st.markdown(
        f'<div class="ps-animated-page-root ps-page-ai">'
        f'<div class="ps-anim-item ps-stagger-1">'
        f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.07em; color:var(--accent);">'
        f'{t("ai_eyebrow")}</div>'
        f'<h1>{t("ai_title")}</h1>'
        f'<p style="font-size:0.92rem; color:var(--ink-muted); line-height:1.5; margin-bottom:1.25rem;">'
        f'{t("ai_desc")}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    status = get_local_ai_status()
    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        drug_a = st.selectbox(t("ai_drug_a"), names, key="ai_a")
        drug_b = st.selectbox(t("ai_drug_b"), names, index=min(1, len(names) - 1), key="ai_b")
        question = st.text_area(t("ai_question"), placeholder=t("ai_question_ph"), height=95)

        match = pairs[(pairs.Drug_A == min(drug_a, drug_b)) & (pairs.Drug_B == max(drug_a, drug_b))]
        level = None if match.empty else str(match.iloc[0]["Level"])

        st.markdown(f'<h4 class="ps-anim-item ps-stagger-2">{t("ai_offline_title")}</h4>', unsafe_allow_html=True)
        se = generate_structured_explanation(drug_a, drug_b, level)
        st.info(f"**{t('ai_summary')}** {se['summary']}\n\n**{t('ai_clinical')}** {se['clinical_meaning']}\n\n**{t('ai_recommendation')}** {se['recommendation']}")

    with right:
        st.markdown(f'<div class="ps-stat-box ps-anim-item ps-stagger-2"><div class="ps-stat-label">{t("ai_status_title")}</div>', unsafe_allow_html=True)
        if status.available:
            st.success(f"{status.message} ({status.details})")
            preferred = next((n for n in status.models if n.startswith("qwen2.5:3b")), status.models[0])
            model = st.selectbox(t("ai_model"), status.models, index=status.models.index(preferred))
            if st.button(t("ai_btn_generate"), type="primary", disabled=not question.strip()):
                prompt = make_evidence_prompt(question.strip(), drug_a, drug_b, level)
                with st.spinner("…"):
                    try:
                        ans = ask_local_model(prompt, model)
                        st.markdown(f'**{t("ai_resp")}**\n\n{ans}')
                    except RuntimeError as exc:
                        st.error(str(exc))
        else:
            st.info(f"{status.message}\n\n{status.details}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─── Страница: О платформе и методология ────────────────────────────────────
def view_overview(pairs: pd.DataFrame, drugs: pd.DataFrame):
    st.markdown(
        f'<div class="ps-animated-page-root ps-page-overview">'
        f'<div class="ps-anim-item ps-stagger-1">'
        f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.07em; color:var(--accent);">'
        f'{t("ov_eyebrow")}</div>'
        f'<h1>{t("ov_title")}</h1>'
        f'<p style="font-size:1.05rem; font-family:var(--font-serif); color:var(--ink-body); line-height:1.65; max-width:68ch; margin-bottom:1.5rem;">'
        f'{t("ov_desc")}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-2">'
            f'<div class="ps-stat-label">{t("ov_stat_pairs")}</div>'
            f'<div class="ps-stat-number">{len(pairs):,}</div>'
            f'<div class="ps-stat-sub">DDInter Full Core</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-3">'
            f'<div class="ps-stat-label">{t("ov_stat_drugs")}</div>'
            f'<div class="ps-stat-number">{len(drugs):,}</div>'
            f'<div class="ps-stat-sub">INN Substances</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c3:
        major_count = int((pairs["Level"] == "Major").sum())
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-4">'
            f'<div class="ps-stat-label" style="color:var(--sev-major);">{t("ov_stat_major")}</div>'
            f'<div class="ps-stat-number" style="color:var(--sev-major);">{major_count:,}</div>'
            f'<div class="ps-stat-sub">Evidence Tier 1</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div style="margin:1.25rem 0;"></div>', unsafe_allow_html=True)
    if st.button(t("ov_btn_start"), type="primary"):
        st.session_state.nav_page = "workspace"
        st.rerun()

    st.markdown("---")
    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3">{t("ov_provenance_title")}</h3>', unsafe_allow_html=True)
    st.markdown(f'<p class="ps-anim-item ps-stagger-4" style="font-size:0.9rem; line-height:1.7; color:var(--ink-body);">{t("ov_provenance_text")}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Точка входа ─────────────────────────────────────────────────────────────
render_top_bar()

try:
    with st.spinner("…"):
        pairs, drugs = cached_data()
    names = drugs["drug"].tolist()
    normalizer = cached_normalizer(tuple(names))
    supp_repo = SupplementEvidenceRepository()

    page = st.session_state.get("nav_page", "workspace")

    if page == "workspace":
        view_workspace(pairs, drugs, normalizer, supp_repo)
    elif page == "supplements":
        view_supplements(supp_repo)
    elif page == "network":
        view_network(pairs, drugs, names)
    elif page == "ml":
        view_ml(pairs, drugs)
    elif page == "ai":
        view_ai(pairs, names)
    else:
        view_overview(pairs, drugs)

    render_footer()

except FileNotFoundError as exc:
    st.warning(str(exc))
except DataValidationError as exc:
    st.error(f"Data error: {exc}")
except Exception as exc:
    st.error(f"Error: {exc}")
    raise
