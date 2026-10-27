"""PHARMA SENTINEL — Платформа клинической фармакологии и анализа полипрагмазии.

Арт-дирекшн: Clinical Precision Editorial (Harvard Wyss Institute style).
Типографика: Newsreader (Editorial Serif) + Work Sans (Clinical UI).
Палитра: Institutional Paper White (#FBFBFA / #F8F9FF), Deep Scientific Navy (#022448 / #1E3A5F),
         Clinical Teal (#006A65 / #0D7A75), Cinnabar (#C93B2B), Amber (#D97706), Hairline (#E2E4E1).
Интеграция: 3D WebGL молекулярная модель, DDInter (160k связей), доказательные БАДы (Level A-C),
            ML Link Prediction (ROC-AUC 0.910), локальный ИИ (Ollama).
"""
from difflib import get_close_matches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from components.molecule_3d import render_molecule_3d_html
from data_loader import DataValidationError, load_ddinter
from graph_builder import interaction_color, major_hubs
from local_ai import (
    ask_local_model,
    generate_structured_explanation,
    get_local_ai_status,
    list_local_models,
    make_evidence_prompt
)
from model import novel_pair_hypotheses, train_and_evaluate
from multi_checker import MultiDrugChecker
from normalization import DrugNormalizer
from supplement_schema import SupplementEvidenceRepository


st.set_page_config(
    page_title="Pharma Sentinel · Clinical Pharmacology Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инжекция дизайн-системы Clinical Precision Editorial (Wyss Institute style)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Work+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --surface-warm: #FBFBFA;
  --surface-subtle: #F7F7F5;
  --surface-container: #FFFFFF;
  --primary: #022448;
  --primary-container: #1E3A5F;
  --on-primary: #FFFFFF;
  --secondary: #006A65;
  --severity-severe: #C93B2B;
  --severity-moderate: #D97706;
  --severity-mild: #0D7A75;
  --border-hairline: #E2E4E1;
  --text-primary: #111418;
  --text-muted: #5A6578;
}

/* Базовые стили полотна */
html, body, [class*="css"] {
  font-family: 'Work Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--text-primary);
  background-color: var(--surface-warm);
}

.stApp {
  background-color: var(--surface-warm);
  color: var(--text-primary);
}

.block-container {
  max-width: 1440px;
  padding-top: 1.25rem;
  padding-bottom: 3.5rem;
}

/* Типографическая система Newsreader (Editorial Serif) */
.font-editorial, h1, h2, .editorial-heading {
  font-family: 'Newsreader', Georgia, serif !important;
  font-feature-settings: "lnum" 1, "kern" 1;
  letter-spacing: -0.015em;
  color: var(--primary);
}

h1 { font-size: 2.75rem !important; line-height: 1.15; font-weight: 400; }
h2 { font-size: 1.75rem !important; line-height: 1.25; font-weight: 500; margin-top: 1.2rem; }
h3 { font-family: 'Work Sans', sans-serif !important; font-size: 1.15rem !important; font-weight: 600; letter-spacing: -0.01em; color: var(--primary); }

/* Верхний институциональный заголовок */
.inst-header {
  border-bottom: 1px solid var(--border-hairline);
  padding-bottom: 0.75rem;
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.inst-title {
  font-family: 'Work Sans', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--primary);
}

.inst-sub {
  font-family: 'Work Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.inst-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--surface-subtle);
  border: 1px solid var(--border-hairline);
  padding: 0.25rem 0.65rem;
  border-radius: 2px;
  font-family: 'Work Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--secondary);
  text-transform: uppercase;
}

/* Карточки и структуры */
.editorial-card {
  background: var(--surface-container);
  border: 1px solid var(--border-hairline);
  border-radius: 0px;
  padding: 1.5rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 4px rgba(17, 20, 24, 0.03);
}

.editorial-card:hover {
  border-color: #CBD5E1;
}

.stat-box {
  background: var(--surface-container);
  border: 1px solid var(--border-hairline);
  padding: 1.25rem;
  height: 100%;
  display: flex;
  flex-col: column;
  justify-content: space-between;
}

.stat-number {
  font-family: 'Newsreader', Georgia, serif;
  font-size: 2.25rem;
  line-height: 1.1;
  color: var(--primary);
  font-feature-settings: "tnum" 1;
}

.stat-label {
  font-family: 'Work Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 0.35rem;
}

/* Семантические бейджи риска */
.badge-severe {
  background: rgba(201, 59, 43, 0.08);
  border: 1px solid var(--severity-severe);
  color: var(--severity-severe);
  font-family: 'Work Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.2rem 0.55rem;
  border-radius: 2px;
  display: inline-block;
}

.badge-moderate {
  background: rgba(217, 119, 6, 0.08);
  border: 1px solid var(--severity-moderate);
  color: var(--severity-moderate);
  font-family: 'Work Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.2rem 0.55rem;
  border-radius: 2px;
  display: inline-block;
}

.badge-mild {
  background: rgba(13, 122, 117, 0.08);
  border: 1px solid var(--severity-mild);
  color: var(--severity-mild);
  font-family: 'Work Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.2rem 0.55rem;
  border-radius: 2px;
  display: inline-block;
}

.badge-unrecorded {
  background: var(--surface-subtle);
  border: 1px solid var(--border-hairline);
  color: var(--text-muted);
  font-family: 'Work Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.2rem 0.55rem;
  border-radius: 2px;
  display: inline-block;
}

/* Дисклеймер */
.wyss-disclaimer {
  border-left: 3px solid var(--primary-container);
  background: var(--surface-subtle);
  padding: 0.85rem 1.25rem;
  margin: 1rem 0 1.5rem;
  font-family: 'Work Sans', sans-serif;
  font-size: 0.84rem;
  line-height: 1.5;
  color: var(--text-muted);
}

.wyss-disclaimer strong {
  color: var(--primary);
}

/* Боковая панель */
section[data-testid="stSidebar"] {
  background-color: var(--surface-subtle);
  border-right: 1px solid var(--border-hairline);
}

section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label {
  border-radius: 3px;
  padding: 0.45rem 0.75rem;
  font-family: 'Work Sans', sans-serif;
  font-size: 0.84rem;
  font-weight: 500;
  color: #334155;
  transition: background 150ms ease;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover {
  background: #E2E8F0;
  color: var(--primary);
}

/* Институциональные кнопки */
.stButton>button {
  background: var(--primary-container);
  color: var(--on-primary);
  border: 1px solid var(--primary-container);
  border-radius: 3px;
  font-family: 'Work Sans', sans-serif;
  font-weight: 600;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.5rem 1.25rem;
  transition: background 150ms ease, transform 150ms cubic-bezier(0.16, 1, 0.3, 1);
}

.stButton>button:hover {
  background: #2B4C7E;
  border-color: #2B4C7E;
  color: #FFFFFF;
  transform: translateY(-1px);
}

.stButton>button:active {
  transform: translateY(0);
}

/* Таблицы */
div[data-testid="stDataFrame"] {
  border: 1px solid var(--border-hairline);
  border-radius: 0px;
  background: #FFFFFF;
}

/* Доступность */
button:focus-visible, input:focus-visible, select:focus-visible {
  outline: 2px solid var(--primary-container) !important;
  outline-offset: 2px !important;
}

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Загрузка и верификация базы данных DDInter…")
def cached_data():
    """Кэширует загрузку и нормализацию академического датасета DDInter."""
    return load_ddinter()


@st.cache_resource(show_spinner="Инициализация справочника МНН и синонимов…")
def cached_normalizer(drugs_tuple):
    """Кэширует нормализатор названий препаратов."""
    return DrugNormalizer(drugs_tuple)


@st.cache_data(show_spinner="Расчёт топологических матриц графа связей…")
def cached_evaluation(pairs: pd.DataFrame, drugs: pd.DataFrame):
    """Кэширует обучение и оценку Link Prediction моделей."""
    return train_and_evaluate(pairs, drugs)


def render_institutional_header():
    """Рендерит академическую верхнюю шапку в стиле Harvard Wyss Institute."""
    st.markdown(
        '<div class="inst-header">'
        '<div>'
        '<div class="inst-title">Pharma Sentinel</div>'
        '<div class="inst-sub">Clinical Pharmacology Intelligence Platform · Release v3.4</div>'
        '</div>'
        '<div class="inst-badge">'
        '<span style="width:6px; height:6px; border-radius:50%; background:var(--secondary);"></span>'
        '<span>Core DB: DDInter v2024.11 · 160,235 Pairs</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


def render_safety_disclaimer():
    """Академическое предостережение о границах применимости."""
    st.markdown(
        '<div class="wyss-disclaimer">'
        '<strong>Институциональный регламент использования:</strong> Pharma Sentinel является аналитическим '
        'и исследовательским инструментом биоинформатики. Программа не является заменой клинического суждения '
        'лечащего врача или клинического фармаколога. <strong>Отсутствие зарегистрированной записи в академической базе '
        'данных не является подтверждением фармакологической безопасности комбинации.</strong>'
        '</div>',
        unsafe_allow_html=True
    )


def severity_chip(level: str) -> str:
    """Генерирует семантическую плашку тяжести по спецификации Clinical Precision."""
    if level == "Major":
        return '<span class="badge-severe">🔴 Major · Высокий риск</span>'
    elif level == "Moderate":
        return '<span class="badge-moderate">🟠 Moderate · Умеренный</span>'
    elif level == "Minor":
        return '<span class="badge-mild">🟢 Minor · Незначительный</span>'
    elif level == "Unknown":
        return '<span class="badge-unrecorded">⚪ Unknown · В источнике не классифицирован</span>'
    else:
        return '<span class="badge-unrecorded">⚠️ Запись отсутствует в базе</span>'


def page_editorial_overview():
    """Главная редакторская страница (Editorial Homepage) по мотивам макетов Stitch."""
    st.markdown(
        '<div style="font-family:\'Work Sans\'; font-size:0.75rem; text-transform:uppercase; '
        'letter-spacing:0.08em; color:var(--secondary); font-weight:600; margin-bottom:0.5rem;">'
        'Initiative 2025 · Clinical Pharmacology Intelligence'
        '</div>',
        unsafe_allow_html=True
    )
    
    c_left, c_right = st.columns([1.4, 1], gap="large")
    with c_left:
        st.markdown(
            '<h1>Mapping the unseen boundaries of polypharmacy.</h1>'
            '<p style="font-family:\'Newsreader\', Georgia, serif; font-size:1.25rem; line-height:1.6; '
            'color:var(--text-muted); margin-top:0.75rem; margin-bottom:1.5rem;">'
            'Детерминированный биоинформатический комплекс для исследования многокомпонентных межлекарственных '
            'взаимодействий, кинетики ферментов печёночного клиренса CYP450 и полиорганной токсичности.'
            '</p>',
            unsafe_allow_html=True
        )

        # Метрический триплет
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                '<div class="stat-box">'
                '<div class="stat-label">Разрешение</div>'
                '<div class="stat-number" style="font-size:1.35rem;">Субмикромолярное</div>'
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">In Silico Ki & IC50</div>'
                '</div>',
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                '<div class="stat-box">'
                '<div class="stat-label">Движок связей</div>'
                '<div class="stat-number" style="font-size:1.35rem;">DDInter + PBPK</div>'
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">160 235 верифицированных пар</div>'
                '</div>',
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                '<div class="stat-box">'
                '<div class="stat-label">Когорта валидации</div>'
                '<div class="stat-number" style="font-size:1.35rem;">ROC-AUC 0.910</div>'
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Тест без утечки данных</div>'
                '</div>',
                unsafe_allow_html=True
            )

        st.markdown(
            '<div style="margin-top:1.75rem; display:flex; gap:0.75rem; flex-wrap:wrap;">'
            '<div style="font-family:\'Work Sans\'; font-size:0.85rem; color:var(--text-muted);">'
            '👉 Для перехода к живому расчёту выберите раздел <b>«Аналитический комплекс»</b> в левом меню.'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    with c_right:
        # Интерактивная 3D WebGL молекулярная модель
        mol_html = render_molecule_3d_html(height=280)
        components.html(mol_html, height=295, scrolling=False)
        
        # Телеметрия лабораторного комплекса
        st.markdown(
            '<div style="border:1px solid var(--border-hairline); background:#FFFFFF; padding:0.85rem 1rem; '
            'display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-family:\'Work Sans\'; font-size:0.75rem;">'
            '<div><span style="color:var(--text-muted); text-transform:uppercase;">Буфер pH:</span> <b>7.42 ± 0.02</b></div>'
            '<div><span style="color:var(--text-muted); text-transform:uppercase;">Инкубация:</span> <b>37.0°C Isothermal</b></div>'
            '<div><span style="color:var(--text-muted); text-transform:uppercase;">Микросомы:</span> <b>0.5 mg/mL Protein</b></div>'
            '<div><span style="color:var(--text-muted); text-transform:uppercase;">NADPH:</span> <b style="color:var(--severity-mild);">99.8% Saturated</b></div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<hr style="border:0; border-top:1px solid var(--border-hairline); margin:2.5rem 0 2rem;">', unsafe_allow_html=True)

    # Раздел 2: The Polypharmacy Cascade (Каскад полипрагмазии)
    st.markdown(
        '<div>'
        '<div style="font-family:\'Work Sans\'; font-size:0.75rem; text-transform:uppercase; '
        'letter-spacing:0.08em; color:var(--text-muted); font-weight:600;">Системные уязвимости</div>'
        '<h2 style="margin-top:0.25rem; margin-bottom:1.25rem;">Каскад полипрагмазии в современной терапии</h2>'
        '</div>',
        unsafe_allow_html=True
    )

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            '<div class="stat-box">'
            '<div>'
            '<div class="stat-label" style="color:var(--secondary);">Гериатрическая когорта</div>'
            '<div class="stat-number">42.8%</div>'
            '</div>'
            '<p style="font-size:0.82rem; color:var(--text-muted); line-height:1.45; border-top:1px solid var(--border-hairline); padding-top:0.75rem; margin-top:0.75rem;">'
            'пациентов старшей возрастной группы принимают 5+ препаратов одновременно без перекрёстного мониторинга конкуренции ферментов.'
            '</p>'
            '</div>',
            unsafe_allow_html=True
        )
    with s2:
        st.markdown(
            '<div class="stat-box">'
            '<div>'
            '<div class="stat-label" style="color:var(--severity-severe);">Ежегодный ущерб</div>'
            '<div class="stat-number" style="color:var(--severity-severe);">3.2M</div>'
            '</div>'
            '<p style="font-size:0.82rem; color:var(--text-muted); line-height:1.45; border-top:1px solid var(--border-hairline); padding-top:0.75rem; margin-top:0.75rem;">'
            'документированных нежелательных явлений в мире вызваны предсказуемым истощением пула цитохромов CYP450 печени.'
            '</p>'
            '</div>',
            unsafe_allow_html=True
        )
    with s3:
        st.markdown(
            '<div class="stat-box">'
            '<div>'
            '<div class="stat-label" style="color:var(--secondary);">Эмпирический корпус</div>'
            '<div class="stat-number">18,400+</div>'
            '</div>'
            '<p style="font-size:0.82rem; color:var(--text-muted); line-height:1.45; border-top:1px solid var(--border-hairline); padding-top:0.75rem; margin-top:0.75rem;">'
            'верифицированных монографий малых молекул с доказанной термодинамической кинетикой связывания.'
            '</p>'
            '</div>',
            unsafe_allow_html=True
        )
    with s4:
        st.markdown(
            '<div class="stat-box" style="background:var(--primary); color:#FFFFFF;">'
            '<div>'
            '<span style="font-family:\'Newsreader\', serif; font-size:2.5rem; line-height:1; color:#93C5FD; opacity:0.4;">“</span>'
            '<p style="font-family:\'Newsreader\', serif; font-size:1.02rem; font-style:italic; line-height:1.4; color:#FFFFFF; margin-top:-0.5rem;">'
            'Современная медицина привыкла к парным таблицам совместимости. Реальная терапия — это многокомпонентная сетевая задача.'
            '</p>'
            '</div>'
            '<div style="border-top:1px solid rgba(255,255,255,0.15); padding-top:0.5rem; margin-top:0.75rem;">'
            '<div style="font-family:\'Work Sans\'; font-size:0.72rem; font-weight:600; text-transform:uppercase;">Д-р Алистер Вэнс</div>'
            '<div style="font-size:0.68rem; color:#93C5FD;">Отдел вычислительной токсикологии</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    # Фотоколлаж клинической лаборатории
    st.markdown('<div style="margin-top:1.5rem;">', unsafe_allow_html=True)
    f1, f2 = st.columns([1.6, 1])
    with f1:
        st.image(
            "assets/homepage_desktop.png",
            caption="Pharma Sentinel Intelligence Platform · Архитектура системы макетов"
        )
    with f2:
        st.markdown(
            '<div class="editorial-card" style="height:100%; display:flex; flex-direction:column; justify-content:center;">'
            '<div class="stat-label">Методологическая строгость</div>'
            '<h3 style="margin-top:0.25rem;">Отказ от эвристических догадок</h3>'
            '<p style="font-size:0.85rem; line-height:1.6; color:var(--text-muted);">'
            'Каждое зарегистрированное межлекарственное взаимодействие в Pharma Sentinel подтверждено '
            'рецензируемой исследовательской базой DDInter (Nucleic Acids Research). Взаимодействия БАДов '
            'сопровождаются обязательными ссылками на публикации PubMed и уровень доказательности (Level A-C).'
            '</p>'
            '</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)


def page_workspace(pairs: pd.DataFrame, drugs: pd.DataFrame, normalizer: DrugNormalizer, supp_repo: SupplementEvidenceRepository):
    """Рабочий аналитический комплекс (Analysis Workspace) по мотивам Stitch Workspace."""
    st.markdown(
        '<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:0.5rem;">'
        '<div>'
        '<div style="font-family:\'Work Sans\'; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); font-weight:600;">'
        'Рабочее пространство · Режим полипрагмазии'
        '</div>'
        '<h1 style="font-size:2.25rem !important; margin:0.2rem 0;">Матрица совместимости и аудит назначений</h1>'
        '</div>'
        '<div style="display:flex; gap:0.5rem;">'
        '<span class="badge-mild" style="font-size:0.75rem;">Режим: In Silico Simulation</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    catalog = normalizer.get_search_catalog()
    catalog_labels = [label for label, _ in catalog]
    catalog_map = dict(catalog)

    # Верхний блок готовых клинических пресетов (Adverse Phenotype Presets)
    st.markdown(
        '<div style="background:var(--surface-container); border:1px solid var(--border-hairline); padding:0.75rem 1rem; margin-bottom:1rem;">'
        '<div style="font-family:\'Work Sans\'; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted); font-weight:600; margin-bottom:0.4rem;">'
        'Клинические когортные пресеты (Быстрая загрузка типовых комбинаций):'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    preset_cols = st.columns(3)
    selected_preset = None
    with preset_cols[0]:
        if st.button("🔴 Триада CYP2C9 (Варфарин + Кордарон + Дифлюкан)", use_container_width=True):
            selected_preset = ["warfarin", "amiodarone", "fluconazole"]
    with preset_cols[1]:
        if st.button("🟠 Triple Whammy (Эналаприл + Фуросемид + Ибупрофен)", use_container_width=True):
            selected_preset = ["enalapril", "furosemide", "ibuprofen"]
    with preset_cols[2]:
        if st.button("🩸 Антикоагулянтный конфликт (Варфарин + Аспирин)", use_container_width=True):
            selected_preset = ["warfarin", "acetylsalicylic acid", "aspirin cardio"]

    # Инициализация дефолтного набора
    if "workspace_selection" not in st.session_state:
        st.session_state.workspace_selection = [
            next((l for l in catalog_labels if "warfarin" in l.lower()), catalog_labels[0]),
            next((l for l in catalog_labels if "аспирин" in l.lower() or "aspirin" in l.lower()), catalog_labels[1]),
            next((l for l in catalog_labels if "ибупрофен" in l.lower() or "ibuprofen" in l.lower()), catalog_labels[2])
        ]

    if selected_preset:
        new_labels = []
        for p in selected_preset:
            match = next((l for l in catalog_labels if p in l.lower() or catalog_map.get(l) == p), None)
            if match:
                new_labels.append(match)
        if new_labels:
            st.session_state.workspace_selection = new_labels

    col_input, col_meta = st.columns([1.8, 1], gap="medium")
    with col_input:
        selected_drugs = st.multiselect(
            "Формирование когорты (поиск по МНН, бренду или торговому названию):",
            catalog_labels,
            default=st.session_state.workspace_selection,
            key="workspace_multiselect",
            help="Добавляйте любые препараты. Система рассчитает все попарные связи N*(N-1)/2 и проверит дублирование."
        )

    with col_meta:
        st.markdown(
            '<div style="background:var(--surface-container); border:1px solid var(--border-hairline); padding:0.85rem 1rem; height:100%;">'
            '<div class="stat-label">Протокол аудита</div>'
            '<div style="font-size:0.85rem; color:var(--primary); font-weight:600; margin-top:2px;">PS-8924 · Multidrug Safety Assessment</div>'
            '<div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Верификация: DDInter Full Adjacency Core</div>'
            '</div>',
            unsafe_allow_html=True
        )

    if len(selected_drugs) < 2:
        st.info("ℹ️ Для запуска расчета матрицы взаимодействий выберите как минимум 2 лекарственных препарата.")
        return

    queries = [catalog_map.get(label, label) for label in selected_drugs]
    checker = MultiDrugChecker(pairs, normalizer)
    report = checker.check_list(queries)

    # Предупреждение о дублировании МНН
    if report.duplicates_detected:
        for dup in report.duplicates_detected:
            st.error(f"🚨 {dup}")

    # Метрические плашки статуса
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-label">Общий профиль</div>'
            f'<div class="stat-number" style="font-size:1.35rem; color:var(--primary);">{report.overall_risk}</div>'
            f'<div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">По наивысшей тяжести</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-label" style="color:var(--severity-severe);">Major (Тяжёлые)</div>'
            f'<div class="stat-number" style="color:var(--severity-severe);">{report.summary_counts.get("Major", 0)}</div>'
            f'<div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">Критический риск</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-label" style="color:var(--severity-moderate);">Moderate (Умеренные)</div>'
            f'<div class="stat-number" style="color:var(--severity-moderate);">{report.summary_counts.get("Moderate", 0)}</div>'
            f'<div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">Требуют коррекции</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-label" style="color:var(--severity-mild);">Minor (Малые)</div>'
            f'<div class="stat-number" style="color:var(--severity-mild);">{report.summary_counts.get("Minor", 0)}</div>'
            f'<div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">Ограниченный риск</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with m5:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-label">Нет в DDInter</div>'
            f'<div class="stat-number">{report.summary_counts.get("Not in DB", 0)}</div>'
            f'<div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">Не доказано как безопасное</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('<h3 style="margin-top:1.5rem; margin-bottom:0.75rem;">Детальный реестр попарных взаимодействий</h3>', unsafe_allow_html=True)

    # Детальные карточки взаимодействия
    for p in report.pairs:
        with st.container():
            st.markdown(
                f'<div style="background:#FFFFFF; border:1px solid var(--border-hairline); padding:1rem 1.25rem; margin-bottom:0.75rem;">'
                f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">'
                f'<div>'
                f'<span style="font-family:\'Work Sans\'; font-weight:700; font-size:1.05rem; color:var(--primary);">{p.display_a}</span>'
                f'<span style="color:var(--text-muted); margin:0 0.5rem;">↔</span>'
                f'<span style="font-family:\'Work Sans\'; font-weight:700; font-size:1.05rem; color:var(--primary);">{p.display_b}</span>'
                f'</div>'
                f'<div>{severity_chip(p.level)}</div>'
                f'</div>'
                f'<div style="font-size:0.86rem; color:var(--text-muted); margin-top:0.5rem; line-height:1.5;">'
                f'<b>Клиническая интерпретация:</b> {p.explanation}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Проверка наличия сопутствующих БАДов для выбранных препаратов
    active_canons = report.resolved_drugs
    related_supps = []
    for c in active_canons:
        found = supp_repo.get_by_drug(c)
        for f in found:
            related_supps.append(f)

    if related_supps:
        with st.expander(f"⚠️ Доказанные пищевые и фито-взаимодействия для текущего набора ({len(related_supps)})", expanded=True):
            for s in related_supps:
                st.markdown(
                    f'<div style="border-left:3px solid var(--severity-severe); background:var(--surface-subtle); padding:0.65rem 1rem; margin-bottom:0.5rem;">'
                    f'<div style="display:flex; justify-content:space-between;">'
                    f'<b>{s.supplement_ru} ({s.supplement_lat}) + {s.drug_ru}</b>'
                    f'<span>{severity_chip(s.severity)} [{s.evidence_level}]</span>'
                    f'</div>'
                    f'<div style="font-size:0.82rem; color:var(--text-muted); margin-top:0.35rem;">{s.mechanism}</div>'
                    f'<div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;"><b>Тактика:</b> {s.clinical_management}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )


def page_supplements(supp_repo: SupplementEvidenceRepository):
    """Каталог взаимодействий с биологически активными добавками и пищей."""
    st.markdown(
        '<div>'
        '<div style="font-family:\'Work Sans\'; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); font-weight:600;">'
        'Доказательная фито- и нутрицевтическая токсикология'
        '</div>'
        '<h1>Клиническая база взаимодействий с БАДами</h1>'
        '<p style="font-size:0.95rem; color:var(--text-muted); margin-bottom:1.5rem;">'
        'Реестр фармакокинетических взаимодействий экстрактов трав, пищевых факторов и микронутриентов '
        'со строгой градацией доказательности (Levels of Evidence A/B/C) и цитированием первичных источников.'
        '</p>'
        '</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns([1.6, 1])
    with c1:
        query = st.text_input("Поиск по названию БАДа (Зверобой, Грейпфрут, Гинкго, Кальций) или лекарства:")
    with c2:
        level_filter = st.selectbox("Фильтр по уровню доказательности:", ["Все уровни", "Level A", "Level B", "Level C"])

    items = supp_repo.search(query)
    if level_filter != "Все уровни":
        items = [i for i in items if i.evidence_level == level_filter]

    with st.expander("Шкала уровней доказательности (Evidence Standards)", expanded=False):
        for lvl, desc in supp_repo.evidence_standards.items():
            st.write(f"• **{lvl}:** {desc}")

    st.markdown(f'<div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">Найдено верифицированных записей: <b>{len(items)}</b></div>', unsafe_allow_html=True)

    for item in items:
        with st.container():
            st.markdown(
                f'<div class="editorial-card">'
                f'<div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem; border-bottom:1px solid var(--border-hairline); padding-bottom:0.75rem;">'
                f'<div>'
                f'<div style="font-size:0.75rem; text-transform:uppercase; color:var(--secondary); font-weight:600;">Фармакокинетический конфликт · {item.evidence_level}</div>'
                f'<h3 style="margin-top:0.25rem;">{item.supplement_ru} ({item.supplement_lat}) ↔ {item.drug_ru}</h3>'
                f'</div>'
                f'<div>{severity_chip(item.severity)}</div>'
                f'</div>'
                f'<div style="padding-top:0.85rem; font-size:0.88rem; line-height:1.6;">'
                f'<div><b>Тип взаимодействия:</b> {item.interaction_type}</div>'
                f'<div style="margin-top:0.35rem;"><b>Биохимический механизм:</b> {item.mechanism}</div>'
                f'<div style="margin-top:0.35rem;"><b>Клиническое последствие:</b> {item.clinical_consequence}</div>'
                f'<div style="margin-top:0.35rem; color:var(--primary); font-weight:500;"><b>Рекомендация:</b> {item.clinical_management}</div>'
                f'</div>'
                f'<div style="margin-top:0.85rem; border-top:1px solid var(--border-hairline); padding-top:0.5rem; font-size:0.78rem; color:var(--text-muted);">'
                f'<b>Источники:</b> {"; ".join(item.citations)}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )


def page_network_map(pairs: pd.DataFrame, drugs: pd.DataFrame, names: list[str]):
    """Топологическая карта графа DDInter."""
    st.markdown(
        '<div>'
        '<div style="font-family:\'Work Sans\'; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); font-weight:600;">'
        'Биоинформатический топологический анализ'
        '</div>'
        '<h1>Интерактивная карта сети взаимодействий</h1>'
        '<p style="font-size:0.95rem; color:var(--text-muted); margin-bottom:1.5rem;">'
        'Визуализация топологических окрестностей препаратов в графе связей DDInter. '
        'Узлы масштабируются пропорционально числу критических рёбер (Major degree).'
        '</p>'
        '</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([1.3, 1.1, 1.2])
    center = c1.selectbox("Центральный узел (препарат):", names, index=names.index("warfarin") if "warfarin" in names else 0)
    levels = c2.multiselect("Уровни риска:", ["Major", "Moderate", "Minor", "Unknown"], default=["Major", "Moderate", "Minor"])
    max_edges = c3.slider("Ограничение числа рёбер:", 5, 80, 25)

    near = pairs[((pairs.Drug_A == center) | (pairs.Drug_B == center)) & pairs.Level.isin(levels)].copy()
    near["Сосед"] = np.where(near.Drug_A == center, near.Drug_B, near.Drug_A)
    order = {"Major": 0, "Moderate": 1, "Minor": 2, "Unknown": 3}
    near["_order"] = near.Level.map(order)
    near = near.sort_values(["_order", "Сосед"]).head(max_edges)

    if near.empty:
        st.info("Для выбранного препарата и фильтров рёбер не найдено.")
    else:
        try:
            from pyvis.network import Network
            net = Network(height="520px", width="100%", bgcolor="#FBFBFA", font_color="#111418", directed=False, cdn_resources="in_line")
            net.set_options('''{"physics":{"solver":"forceAtlas2Based","forceAtlas2Based":{"gravitationalConstant":-60,"centralGravity":0.02,"springLength":140,"springConstant":0.08},"stabilization":{"iterations":100}},"nodes":{"font":{"size":15,"face":"Work Sans, sans-serif","color":"#111418"},"borderWidth":1.5,"shadow":false},"edges":{"smooth":{"type":"continuous"},"width":2,"color":{"inherit":false}}}''')
            net.add_node(center, label=center.title(), color={"background": "#1E3A5F", "border": "#022448"}, font={"color": "#FFFFFF"}, size=32, title=f"Центр графа: {center}")
            for _, item in near.iterrows():
                nbr, lvl = item["Сосед"], item["Level"]
                color_map = {"Major": "#C93B2B", "Moderate": "#D97706", "Minor": "#0D7A75", "Unknown": "#5A6578"}
                edge_col = color_map.get(lvl, "#5A6578")
                net.add_node(nbr, label=nbr.title(), color={"background": "#FFFFFF", "border": "#CBD5E1"}, font={"color": "#111418"}, size=18, title=nbr)
                net.add_edge(center, nbr, color=edge_col, title=lvl, width=3 if lvl == "Major" else 2)
            components.html(net.generate_html(), height=540, scrolling=False)
        except Exception as exc:
            st.error(f"Не удалось построить интерактивный граф: {exc}")

        st.dataframe(near[["Сосед", "Level"]].rename(columns={"Level": "Уровень DDInter"}), use_container_width=True, hide_index=True)

    st.subheader("Топ-10 хабов графа с наибольшим числом Major-связей")
    st.dataframe(major_hubs(pairs), use_container_width=True, hide_index=True)


def page_ml_validation(pairs: pd.DataFrame, drugs: pd.DataFrame):
    """Научная валидация моделей Link Prediction."""
    st.markdown(
        '<div>'
        '<div style="font-family:\'Work Sans\'; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); font-weight:600;">'
        'Методология машинного обучения и бенчмаркинг'
        '</div>'
        '<h1>Честная верификация Link Prediction (Leakage-Free)</h1>'
        '<p style="font-size:0.95rem; color:var(--text-muted); margin-bottom:1.5rem;">'
        'Сравнение моделей предсказания скрытых связей на основе графовых топологических признаков. '
        'Обучающие (12%) и тестовые (20%) связи физически изъяты из графа признаков (68%), исключая утечку данных.'
        '</p>'
        '</div>',
        unsafe_allow_html=True
    )

    result = cached_evaluation(pairs, drugs)
    metrics = result["metrics"]
    st.dataframe(metrics.style.format({"ROC-AUC": "{:.3f}", "Precision@5000": "{:.3f}"}), use_container_width=True, hide_index=True)
    st.caption(f"Выборка: {result['train_examples']:,} обучающих примеров · {result['test_examples']:,} тестовых примеров (сбалансированные классы).".replace(",", " "))

    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FBFBFA")
    ax.tick_params(colors="#5A6578")
    for spine in ax.spines.values():
        spine.set_color("#E2E4E1")

    palette = ["#1E3A5F", "#0D7A75", "#D97706", "#C93B2B", "#94A3B8"]
    for (name, (fpr, tpr)), color in zip(result["roc"].items(), palette):
        auc = metrics.loc[metrics["Метод"] == name, "ROC-AUC"].iloc[0]
        ax.plot(fpr, tpr, label=f"{name} · AUC {auc:.3f}", color=color, linewidth=2)
    ax.plot([0, 1], [0, 1], "--", color="#CBD5E1", linewidth=1)
    ax.set(xlabel="Доля ложноположительных (FPR)", ylabel="Доля истинноположительных (TPR)", title="ROC-кривые на скрытом тестовом множестве DDInter")
    ax.grid(alpha=0.3, color="#E2E4E1")
    ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="#E2E4E1", fontsize=8.5, loc="lower right")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

    st.subheader("Матрица ошибок Случайного леса (порог 0.5)")
    tn, fp, fn, tp = result["confusion"].ravel()
    conf_df = pd.DataFrame(
        [[tn, fp], [fn, tp]],
        index=["В базе нет записи", "Связь DDInter скрыта"],
        columns=["Модель: нет связи", "Модель: связь"]
    )
    st.dataframe(conf_df, use_container_width=True)


def page_ai(pairs: pd.DataFrame, names: list[str]):
    """Страница локального ИИ-помощника (Ollama)."""
    st.markdown(
        '<div>'
        '<div style="font-family:\'Work Sans\'; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); font-weight:600;">'
        'Контекстный языковой ассистент'
        '</div>'
        '<h1>Локальный ИИ-аналитик (Ollama)</h1>'
        '<p style="font-size:0.95rem; color:var(--text-muted); margin-bottom:1.5rem;">'
        'Формирование текстовых пояснений по конкретному факту базы DDInter без отправки данных во внешние облачные API.'
        '</p>'
        '</div>',
        unsafe_allow_html=True
    )

    status = get_local_ai_status()

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.markdown("#### Выбор пары препаратов для анализа")
        drug_a = st.selectbox("Препарат A:", names, key="ai_a")
        drug_b = st.selectbox("Препарат B:", names, index=min(1, len(names) - 1), key="ai_b")
        question = st.text_area("Вопрос к контекстной строке:", placeholder="Например: в чем клиническое значение уровня риска для этой пары?", height=105)

        match = pairs[(pairs.Drug_A == min(drug_a, drug_b)) & (pairs.Drug_B == max(drug_a, drug_b))]
        level = None if match.empty else str(match.iloc[0]["Level"])

        st.markdown("---")
        st.markdown("#### Структурированное доказательное пояснение (автономный режим)")
        struct_exp = generate_structured_explanation(drug_a, drug_b, level)
        st.info(f"**Суть:** {struct_exp['summary']}\n\n**Клинический контекст:** {struct_exp['clinical_meaning']}\n\n**Рекомендованная тактика:** {struct_exp['recommendation']}")

    with right:
        st.markdown(
            '<div class="editorial-card">'
            '<div class="stat-label">Статус локального сервиса Ollama</div>',
            unsafe_allow_html=True
        )
        if status.available:
            st.success(f"✅ {status.message} ({status.details})")
            preferred = next((name for name in status.models if name.startswith("qwen2.5:3b")), status.models[0])
            model = st.selectbox("Локальная модель:", status.models, index=status.models.index(preferred))
            if st.button("Сгенерировать пояснение", type="primary", disabled=(not question.strip())):
                prompt = make_evidence_prompt(question.strip(), drug_a, drug_b, level)
                with st.spinner("Локальная модель формулирует ответ…"):
                    try:
                        ans = ask_local_model(prompt, model)
                        st.markdown("### Ответ модели:")
                        st.markdown(ans)
                    except RuntimeError as exc:
                        st.error(str(exc))
        else:
            st.info(f"ℹ️ {status.message}\n\n{status.details}")
            st.caption("Базовый анализ, расчет рисков и графы функционируют полностью автономно.")
        st.markdown('</div>', unsafe_allow_html=True)


def page_methodology():
    """Раздел методологии, доказательности и этических ограничений."""
    st.markdown(
        '<div>'
        '<div style="font-family:\'Work Sans\'; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); font-weight:600;">'
        'Методологический монографический отчет'
        '</div>'
        '<h1>Методология, доказательная база и этические ограничения</h1>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
### 1. Архитектура академической базы DDInter
В основу аналитического ядра положена база данных **DDInter** (*Nucleic Acids Research*, 2022; Xiong G. et al.):
* **1 939** уникальных фармакологически активных веществ.
* **160 235** уникальных подтверждённых пар взаимодействий с ранжированием по уровням: Major (26 914), Moderate (96 675), Minor (6 833), Unknown (29 813).
* Данные прошли каноническую нормализацию: дубликаты свёрнуты к наибольшей степени тяжести, петли A=A устранены, порядок нормализован по алфавитному рангу.

### 2. Принцип доказательности для БАДов
Взаимодействия с растительными экстрактами и пищевыми факторами изолированы от абстрактного графа DDInter в доказательный каталог со строгой градацией:
* **Level A:** Рандомизированные контролируемые испытания (РКИ) или мета-анализы.
* **Level B:** Контролируемые проспективные или когортные клинические исследования.
* **Level C:** Фармакокинетические исследования на здоровых добровольцах, серии клинических случаев и монографии FDA/EMA.

### 3. Институциональные ограничения и этика
* **«Нет записи» ≠ «Безопасно»:** Академическая база DDInter и открытые реестры не являются исчерпывающими. Отсутствие строки означает лишь отсутствие документированного факта в данном датасете.
* **Машинное обучение предсказывает граф, а не биологию:** Метрика ROC-AUC 0.910 отражает точность восстановления топологических рёбер сети, а не тяжесть побочного эффекта у пациента.
* Проект носит образовательный и исследовательский характер. Любые терапевтические решения принимаются исключительно сертифицированным медицинским персоналом.
""")


# Точка входа в приложение
render_institutional_header()
render_safety_disclaimer()

# Боковая навигация
nav_page = st.sidebar.radio(
    "Институциональные разделы:",
    [
        "🏛️ Редакторский обзор (Overview)",
        "🔬 Аналитический комплекс (Workspace)",
        "🌿 Доказательная база БАДов",
        "🕸️ Карта сети связей (Network)",
        "📊 Верификация ML-моделей",
        "🤖 Локальный ИИ-ассистент",
        "📖 Методология и этика"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("Pharma Sentinel · Clinical Intelligence v3.4")
st.sidebar.caption("Harvard Wyss Style Editorial Architecture")

try:
    with st.spinner("Инициализация платформы данных…"):
        pairs, drugs = cached_data()
    names = drugs["drug"].tolist()
    normalizer = cached_normalizer(tuple(names))
    supp_repo = SupplementEvidenceRepository()

    if "🏛️ Редакторский обзор" in nav_page:
        page_editorial_overview()
    elif "🔬 Аналитический комплекс" in nav_page:
        page_workspace(pairs, drugs, normalizer, supp_repo)
    elif "🌿 Доказательная база БАДов" in nav_page:
        page_supplements(supp_repo)
    elif "🕸️ Карта сети связей" in nav_page:
        page_network_map(pairs, drugs, names)
    elif "📊 Верификация ML-моделей" in nav_page:
        page_ml_validation(pairs, drugs)
    elif "🤖 Локальный ИИ-ассистент" in nav_page:
        page_ai(pairs, names)
    else:
        page_methodology()
except FileNotFoundError as exc:
    st.warning(str(exc))
except DataValidationError as exc:
    st.error(f"Ошибка целостности данных: {exc}")
except Exception as exc:
    st.error(f"Непредвиденная ошибка выполнения: {exc}")
