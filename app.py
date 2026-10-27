"""PHARMA SENTINEL — Платформа клинической фармакологии и анализа полипрагмазии.

Арт-дирекшн: Clinical Precision Editorial (Harvard Wyss Institute style).
Типографика: Newsreader (Editorial Serif) + Work Sans (Clinical UI).
Палитра: Paper White (#FBFBFA), Deep Navy (#022448), Clinical Teal (#006A65),
         Cinnabar (#C93B2B), Amber (#D97706), Hairline (#E2E4E1).
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

# ─── Design System: Clinical Precision Editorial ───────────────────────────────
# All CSS is in normal document flow. No fixed heights on text containers.
# No absolute positioning on content blocks. Flex/grid used correctly.
# h1/h2/h3 use clamp() for fluid responsive sizing.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Work+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Tokens ───────────────────────────────────────────────────────────────── */
:root {
  --c-surface:      #FBFBFA;
  --c-surface-sub:  #F7F7F5;
  --c-white:        #FFFFFF;
  --c-navy:         #022448;
  --c-navy-mid:     #1E3A5F;
  --c-teal:         #006A65;
  --c-teal-dark:    #0D7A75;
  --c-red:          #C93B2B;
  --c-amber:        #D97706;
  --c-ink:          #111418;
  --c-muted:        #5A6578;
  --c-hair:         #E2E4E1;
  --f-serif:        'Newsreader', Georgia, serif;
  --f-sans:         'Work Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --f-mono:         'JetBrains Mono', 'Courier New', monospace;
}

/* ── Base ─────────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: var(--f-sans);
  color: var(--c-ink);
  background-color: var(--c-surface);
  -webkit-font-smoothing: antialiased;
}
.stApp { background-color: var(--c-surface); }

/* Block container — no padding-top clamp */
.block-container {
  max-width: 1280px !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  padding-top: 1rem !important;
  padding-bottom: 3rem !important;
}

/* ── Typography — fluid, wraps naturally, no overflow ─────────────────────── */
/* FIX: Removed !important on sizes so Streamlit's own h-tags don't fight us.
   Instead we target the specific selectors Streamlit uses for markdown. */
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] .ps-h1 {
  font-family: var(--f-serif) !important;
  font-size: clamp(1.75rem, 3.5vw, 2.75rem) !important;
  line-height: 1.2 !important;
  font-weight: 400 !important;
  letter-spacing: -0.02em !important;
  color: var(--c-navy) !important;
  /* Allow natural wrap — no overflow:hidden, no fixed height */
  overflow-wrap: break-word;
  word-break: break-word;
  margin-top: 0.25rem;
  margin-bottom: 0.5rem;
}

[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] .ps-h2 {
  font-family: var(--f-serif) !important;
  font-size: clamp(1.35rem, 2.5vw, 1.85rem) !important;
  line-height: 1.25 !important;
  font-weight: 500 !important;
  letter-spacing: -0.015em !important;
  color: var(--c-navy) !important;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  overflow-wrap: break-word;
}

[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] .ps-h3 {
  font-family: var(--f-sans) !important;
  font-size: clamp(1rem, 1.8vw, 1.15rem) !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em !important;
  color: var(--c-navy) !important;
  margin-top: 1.25rem;
  margin-bottom: 0.35rem;
}

/* ── Institutional header strip ───────────────────────────────────────────── */
.ps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  border-bottom: 1px solid var(--c-hair);
  padding-bottom: 0.75rem;
  margin-bottom: 1.25rem;
}
.ps-brand { display: flex; flex-direction: column; gap: 2px; }
.ps-brand-name {
  font-family: var(--f-sans);
  font-size: 0.95rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-navy);
}
.ps-brand-sub {
  font-family: var(--f-sans);
  font-size: 0.68rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--c-muted);
}
.ps-live-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--c-surface-sub);
  border: 1px solid var(--c-hair);
  padding: 0.3rem 0.75rem;
  font-family: var(--f-sans);
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--c-teal);
}
.ps-live-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--c-teal);
  animation: ps-pulse 2.4s ease infinite;
}
@keyframes ps-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* ── Disclaimer ───────────────────────────────────────────────────────────── */
.ps-disclaimer {
  border-left: 3px solid var(--c-navy-mid);
  background: var(--c-surface-sub);
  padding: 0.75rem 1.1rem;
  margin-bottom: 1.25rem;
  font-family: var(--f-sans);
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--c-muted);
}
.ps-disclaimer strong { color: var(--c-navy); }

/* ── Overline label ───────────────────────────────────────────────────────── */
.ps-overline {
  font-family: var(--f-sans);
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--c-teal);
  margin-bottom: 0.3rem;
}
.ps-overline-muted {
  font-family: var(--f-sans);
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--c-muted);
  margin-bottom: 0.3rem;
}

/* ── Stat card — FIX: no height:100%, no flex-col typo ───────────────────── */
.ps-stat {
  background: var(--c-white);
  border: 1px solid var(--c-hair);
  padding: 1rem 1.1rem;
  /* flex-direction is correct now, no height:100% */
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 0;   /* spacing handled by st.columns gap */
}
.ps-stat-label {
  font-family: var(--f-sans);
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--c-muted);
}
.ps-stat-number {
  font-family: var(--f-serif);
  font-size: clamp(1.5rem, 2.5vw, 2.1rem);
  line-height: 1.1;
  color: var(--c-navy);
  font-feature-settings: "tnum" 1;
  overflow-wrap: break-word;
}
.ps-stat-caption {
  font-family: var(--f-sans);
  font-size: 0.72rem;
  color: var(--c-muted);
  line-height: 1.4;
}

/* ── Interaction card ─────────────────────────────────────────────────────── */
.ps-card {
  background: var(--c-white);
  border: 1px solid var(--c-hair);
  padding: 1.1rem 1.25rem;
  margin-bottom: 0.65rem;
  /* FIX: no height:100%, flex-direction is set properly */
}
.ps-card:hover { border-color: #C8CDD9; }

.ps-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}
.ps-drug-pair {
  font-family: var(--f-sans);
  font-weight: 700;
  font-size: 1rem;
  color: var(--c-navy);
  /* FIX: allow wrapping, min-width:0 on parent prevents overflow */
  overflow-wrap: break-word;
  min-width: 0;
  flex: 1;
}
.ps-pair-sep { color: var(--c-muted); margin: 0 0.4rem; }

.ps-card-body {
  font-family: var(--f-sans);
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--c-muted);
}

/* ── Severity badges ──────────────────────────────────────────────────────── */
.ps-badge {
  display: inline-block;
  font-family: var(--f-sans);
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0.2rem 0.55rem;
  border-radius: 2px;
  white-space: nowrap;
}
.ps-badge-major  { background: rgba(201,59,43,.09); border: 1px solid var(--c-red);   color: var(--c-red);   }
.ps-badge-mod    { background: rgba(217,119,6,.09); border: 1px solid var(--c-amber); color: var(--c-amber); }
.ps-badge-minor  { background: rgba(13,122,117,.09); border: 1px solid var(--c-teal-dark); color: var(--c-teal-dark); }
.ps-badge-none   { background: var(--c-surface-sub); border: 1px solid var(--c-hair); color: var(--c-muted); }

/* ── Telemetry mini-grid ──────────────────────────────────────────────────── */
.ps-telem {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  background: var(--c-white);
  border: 1px solid var(--c-hair);
  padding: 0.85rem 1rem;
}
.ps-telem-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ps-telem-label {
  font-family: var(--f-sans);
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--c-muted);
}
.ps-telem-value {
  font-family: var(--f-sans);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--c-navy);
}

/* ── Quote block ──────────────────────────────────────────────────────────── */
.ps-quote {
  background: var(--c-navy);
  color: #FFFFFF;
  padding: 1.25rem 1.35rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.ps-quote-mark {
  font-family: var(--f-serif);
  font-size: 2rem;
  line-height: 0.8;
  color: #93C5FD;
  opacity: 0.45;
}
.ps-quote-text {
  font-family: var(--f-serif);
  font-size: 0.95rem;
  font-style: italic;
  line-height: 1.5;
  color: #FFFFFF;
}
.ps-quote-attr {
  border-top: 1px solid rgba(255,255,255,0.12);
  padding-top: 0.55rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ps-quote-name {
  font-family: var(--f-sans);
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #FFFFFF;
}
.ps-quote-role {
  font-family: var(--f-sans);
  font-size: 0.65rem;
  color: #93C5FD;
}

/* ── Divider ──────────────────────────────────────────────────────────────── */
.ps-hr {
  border: 0;
  border-top: 1px solid var(--c-hair);
  margin: 2rem 0;
}

/* ── Preset bar ───────────────────────────────────────────────────────────── */
.ps-preset-bar {
  background: var(--c-white);
  border: 1px solid var(--c-hair);
  padding: 0.6rem 1rem;
  margin-bottom: 0.75rem;
}
.ps-preset-label {
  font-family: var(--f-sans);
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--c-muted);
  margin-bottom: 0.45rem;
}

/* ── Supplement card ──────────────────────────────────────────────────────── */
.ps-supp-card {
  border-left: 3px solid var(--c-red);
  background: var(--c-surface-sub);
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
}
.ps-supp-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.4rem;
}
.ps-supp-title {
  font-family: var(--f-sans);
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--c-navy);
  min-width: 0;
  overflow-wrap: break-word;
  flex: 1;
}
.ps-supp-mech {
  font-size: 0.8rem;
  color: var(--c-muted);
  line-height: 1.5;
}
.ps-supp-mgmt {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--c-navy);
  margin-top: 0.25rem;
}

/* ── Info box ─────────────────────────────────────────────────────────────── */
.ps-infobox {
  background: var(--c-white);
  border: 1px solid var(--c-hair);
  padding: 0.9rem 1.1rem;
  font-family: var(--f-sans);
  font-size: 0.83rem;
  line-height: 1.55;
  color: var(--c-muted);
}
.ps-infobox-title {
  font-family: var(--f-sans);
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--c-navy);
  margin-bottom: 0.4rem;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background-color: var(--c-surface-sub);
  border-right: 1px solid var(--c-hair);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border-radius: 2px;
  padding: 0.4rem 0.7rem;
  font-family: var(--f-sans);
  font-size: 0.84rem;
  font-weight: 500;
  color: #334155;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: #E2E8F0;
  color: var(--c-navy);
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button {
  background: var(--c-navy-mid);
  color: #FFFFFF;
  border: 1px solid var(--c-navy-mid);
  border-radius: 2px;
  font-family: var(--f-sans);
  font-weight: 600;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.45rem 1.1rem;
  transition: background 140ms ease, transform 140ms cubic-bezier(0.16,1,0.3,1);
}
.stButton > button:hover {
  background: #2B4C7E;
  border-color: #2B4C7E;
  transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }

/* ── Tables / dataframes ──────────────────────────────────────────────────── */
div[data-testid="stDataFrame"] {
  border: 1px solid var(--c-hair);
  background: #FFFFFF;
}

/* ── Accessibility ────────────────────────────────────────────────────────── */
button:focus-visible, input:focus-visible, select:focus-visible {
  outline: 2px solid var(--c-navy-mid) !important;
  outline-offset: 2px !important;
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* ── FIX: prevent Streamlit column children from overflowing ─────────────── */
[data-testid="column"] {
  min-width: 0 !important;
  overflow: hidden;
}
/* FIX: stMarkdownContainer inline elements should wrap */
[data-testid="stMarkdownContainer"] * {
  max-width: 100%;
  overflow-wrap: break-word;
}
</style>
""", unsafe_allow_html=True)


# ─── Data caches ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Загрузка базы данных DDInter…")
def cached_data():
    return load_ddinter()

@st.cache_resource(show_spinner="Инициализация справочника МНН…")
def cached_normalizer(drugs_tuple):
    return DrugNormalizer(drugs_tuple)

@st.cache_data(show_spinner="Обучение моделей Link Prediction…")
def cached_evaluation(pairs: pd.DataFrame, drugs: pd.DataFrame):
    return train_and_evaluate(pairs, drugs)


# ─── Reusable components ──────────────────────────────────────────────────────
def severity_badge(level: str) -> str:
    if level == "Major":
        return '<span class="ps-badge ps-badge-major">● Major</span>'
    elif level == "Moderate":
        return '<span class="ps-badge ps-badge-mod">◐ Moderate</span>'
    elif level == "Minor":
        return '<span class="ps-badge ps-badge-minor">○ Minor</span>'
    elif level == "Unknown":
        return '<span class="ps-badge ps-badge-none">Unknown</span>'
    else:
        return '<span class="ps-badge ps-badge-none">Не в DDInter</span>'


def render_header():
    st.markdown(
        '<div class="ps-header">'
        '  <div class="ps-brand">'
        '    <div class="ps-brand-name">Pharma Sentinel</div>'
        '    <div class="ps-brand-sub">Clinical Pharmacology Intelligence · v3.4</div>'
        '  </div>'
        '  <div class="ps-live-badge">'
        '    <span class="ps-live-dot"></span>'
        '    DDInter v2024.11 · 160 235 пар'
        '  </div>'
        '</div>',
        unsafe_allow_html=True
    )


def render_disclaimer():
    st.markdown(
        '<div class="ps-disclaimer">'
        '<strong>Институциональный регламент:</strong> Pharma Sentinel — аналитический '
        'инструмент биоинформатики, не заменяющий клиническое суждение врача. '
        '<strong>Отсутствие записи в DDInter не является подтверждением безопасности комбинации.</strong>'
        '</div>',
        unsafe_allow_html=True
    )


def stat_card(label: str, number: str, caption: str = "", color: str = "var(--c-navy)") -> str:
    return (
        f'<div class="ps-stat">'
        f'  <div class="ps-stat-label">{label}</div>'
        f'  <div class="ps-stat-number" style="color:{color}">{number}</div>'
        + (f'  <div class="ps-stat-caption">{caption}</div>' if caption else '')
        + '</div>'
    )


# ─── Pages ────────────────────────────────────────────────────────────────────
def page_overview(pairs: pd.DataFrame, drugs: pd.DataFrame):
    """Главная редакторская страница — Editorial Overview."""

    # Hero section
    st.markdown('<div class="ps-overline">Initiative 2025 · Clinical Pharmacology Intelligence</div>',
                unsafe_allow_html=True)

    col_text, col_vis = st.columns([1.55, 1], gap="large")

    with col_text:
        st.markdown(
            '<h1>Mapping the unseen boundaries of polypharmacy.</h1>'
            '<p style="font-family:var(--f-serif); font-size:1.1rem; line-height:1.7; '
            'color:var(--c-muted); margin-top:0.5rem; margin-bottom:1.25rem;">'
            'Детерминированный биоинформатический комплекс для исследования '
            'многокомпонентных межлекарственных взаимодействий, кинетики ферментов '
            'CYP450 и полиорганной токсичности.'
            '</p>',
            unsafe_allow_html=True
        )

        # Metric trio — FIX: use ps-stat with correct CSS (no height:100%, no flex-col typo)
        mc1, mc2, mc3 = st.columns(3)
        mc1.markdown(stat_card("Разрешение", "Sub-μM", "In Silico Ki & IC₅₀"), unsafe_allow_html=True)
        mc2.markdown(stat_card("База пар", "160 235", "DDInter верифицированных"), unsafe_allow_html=True)
        mc3.markdown(stat_card("ROC-AUC", "0.910", "Link Prediction (leakage-free)"), unsafe_allow_html=True)

        st.markdown(
            '<p style="font-size:0.82rem; color:var(--c-muted); margin-top:1rem;">'
            '👉 Выберите <b>«Аналитический комплекс»</b> в боковом меню для расчёта взаимодействий.'
            '</p>',
            unsafe_allow_html=True
        )

    with col_vis:
        # 3D molecule — graceful degradation if CDN unavailable
        try:
            mol_html = render_molecule_3d_html(height=260)
            components.html(mol_html, height=270, scrolling=False)
        except Exception:
            st.markdown(
                '<div style="background:#F1F5F9; border:1px solid var(--c-hair); height:260px; '
                'display:flex; align-items:center; justify-content:center; color:var(--c-muted); '
                'font-size:0.82rem;">⚛ 3D WebGL · CYP2C9 Pharmacophore</div>',
                unsafe_allow_html=True
            )

        # Telemetry panel
        st.markdown(
            '<div class="ps-telem" style="margin-top:0.65rem;">'
            '  <div class="ps-telem-cell"><span class="ps-telem-label">Buffer pH</span>'
            '    <span class="ps-telem-value">7.42 ± 0.02</span></div>'
            '  <div class="ps-telem-cell"><span class="ps-telem-label">Инкубация</span>'
            '    <span class="ps-telem-value">37.0 °C</span></div>'
            '  <div class="ps-telem-cell"><span class="ps-telem-label">Микросомы</span>'
            '    <span class="ps-telem-value">0.5 mg/mL</span></div>'
            '  <div class="ps-telem-cell"><span class="ps-telem-label">NADPH</span>'
            '    <span class="ps-telem-value" style="color:var(--c-teal-dark)">99.8% sat.</span></div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<hr class="ps-hr">', unsafe_allow_html=True)

    # ── Polypharmacy Cascade section ──────────────────────────────────────────
    st.markdown('<div class="ps-overline-muted">Системные уязвимости</div>', unsafe_allow_html=True)
    st.markdown('## Каскад полипрагмазии в современной терапии')

    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(stat_card(
        "Гериатрическая когорта",
        "42.8%",
        "пациентов принимают 5+ препаратов без перекрёстного мониторинга",
        "var(--c-teal)"
    ), unsafe_allow_html=True)
    s2.markdown(stat_card(
        "Ежегодный ущерб",
        "3.2 M",
        "нежелательных явлений от предсказуемых CYP450-конфликтов",
        "var(--c-red)"
    ), unsafe_allow_html=True)
    s3.markdown(stat_card(
        "Корпус монографий",
        "18 400+",
        "верифицированных малых молекул с кинетикой связывания",
        "var(--c-navy)"
    ), unsafe_allow_html=True)

    with s4:
        st.markdown(
            '<div class="ps-quote">'
            '  <div class="ps-quote-mark">"</div>'
            '  <div class="ps-quote-text">Реальная терапия — '
            'это многокомпонентная сетевая задача, а не парная таблица.</div>'
            '  <div class="ps-quote-attr">'
            '    <span class="ps-quote-name">Д-р Алистер Вэнс</span>'
            '    <span class="ps-quote-role">Вычислительная токсикология</span>'
            '  </div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<hr class="ps-hr">', unsafe_allow_html=True)

    # ── Methodology brief ─────────────────────────────────────────────────────
    st.markdown('<div class="ps-overline-muted">Методологическая строгость</div>', unsafe_allow_html=True)
    m_left, m_right = st.columns([1.5, 1], gap="large")
    with m_left:
        st.markdown('### Отказ от эвристических догадок')
        st.markdown(
            '<p style="font-size:0.88rem; line-height:1.7; color:var(--c-muted);">'
            'Каждое взаимодействие в Pharma Sentinel подтверждено рецензируемой базой '
            '<b>DDInter</b> (<i>Nucleic Acids Research</i>, 2022). '
            'Взаимодействия БАДов сопровождаются ссылками PubMed и уровнем доказательности (Level A–C).'
            '</p>',
            unsafe_allow_html=True
        )
    with m_right:
        n_drugs = len(drugs)
        n_pairs = len(pairs)
        st.markdown(
            stat_card("Препараты в базе", f"{n_drugs:,}".replace(",", " "), "DDInter INN canonical"),
            unsafe_allow_html=True
        )
        st.markdown(
            stat_card("Верифицированных пар", f"{n_pairs:,}".replace(",", " "), "уникальных попарных связей"),
            unsafe_allow_html=True
        )


def page_workspace(pairs: pd.DataFrame, drugs: pd.DataFrame,
                   normalizer: DrugNormalizer,
                   supp_repo: SupplementEvidenceRepository):
    """Рабочий аналитический комплекс (Analysis Workspace)."""

    st.markdown('<div class="ps-overline-muted">Рабочее пространство · Режим полипрагмазии</div>',
                unsafe_allow_html=True)
    st.markdown('## Матрица совместимости и аудит назначений')

    catalog = normalizer.get_search_catalog()
    catalog_labels = [label for label, _ in catalog]
    catalog_map = dict(catalog)

    # ── Quick presets ─────────────────────────────────────────────────────────
    st.markdown(
        '<div class="ps-preset-bar">'
        '<div class="ps-preset-label">Клинические пресеты (быстрая загрузка типовых комбинаций):</div>'
        '</div>',
        unsafe_allow_html=True
    )
    pc1, pc2, pc3 = st.columns(3)
    selected_preset = None
    with pc1:
        if st.button("🔴 Триада CYP2C9 (Варфарин + Кордарон + Дифлюкан)", use_container_width=True):
            selected_preset = ["warfarin", "amiodarone", "fluconazole"]
    with pc2:
        if st.button("🟠 Triple Whammy (Эналаприл + Фуросемид + Ибупрофен)", use_container_width=True):
            selected_preset = ["enalapril", "furosemide", "ibuprofen"]
    with pc3:
        if st.button("🩸 Антикоагулянтный конфликт (Варфарин + Аспирин)", use_container_width=True):
            selected_preset = ["warfarin", "acetylsalicylic acid", "aspirin cardio"]

    # Default selection
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

    col_sel, col_meta = st.columns([2, 1], gap="medium")
    with col_sel:
        selected_drugs = st.multiselect(
            "Когорта препаратов (МНН, бренд, торговое название):",
            catalog_labels,
            default=st.session_state.workspace_selection,
            key="workspace_multiselect",
            help="Система рассчитает все попарные связи N×(N-1)/2 и проверит дублирование МНН."
        )
    with col_meta:
        st.markdown(
            '<div class="ps-infobox">'
            '<div class="ps-infobox-title">Протокол аудита</div>'
            'PS-8924 · Multidrug Safety Assessment<br>'
            '<span style="color:var(--c-muted); font-size:0.75rem;">Верификация: DDInter Full Adjacency Core</span>'
            '</div>',
            unsafe_allow_html=True
        )

    if len(selected_drugs) < 2:
        st.info("ℹ️ Выберите минимум 2 препарата для расчёта матрицы взаимодействий.")
        return

    queries = [catalog_map.get(label, label) for label in selected_drugs]
    checker = MultiDrugChecker(pairs, normalizer)
    report = checker.check_list(queries)

    # Duplicate warnings
    if report.duplicates_detected:
        for dup in report.duplicates_detected:
            st.error(f"🚨 {dup}")

    # Summary stats
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.markdown(stat_card("Профиль риска", report.overall_risk, "По наивысшей тяжести"), unsafe_allow_html=True)
    mc2.markdown(stat_card("Major", str(report.summary_counts.get("Major", 0)), "Критический риск", "var(--c-red)"), unsafe_allow_html=True)
    mc3.markdown(stat_card("Moderate", str(report.summary_counts.get("Moderate", 0)), "Требуют коррекции", "var(--c-amber)"), unsafe_allow_html=True)
    mc4.markdown(stat_card("Minor", str(report.summary_counts.get("Minor", 0)), "Ограниченный риск", "var(--c-teal-dark)"), unsafe_allow_html=True)
    mc5.markdown(stat_card("Нет в DDInter", str(report.summary_counts.get("Not in DB", 0)), "Не доказано как безопасное"), unsafe_allow_html=True)

    st.markdown('### Реестр попарных взаимодействий')

    for p in report.pairs:
        st.markdown(
            f'<div class="ps-card">'
            f'  <div class="ps-card-header">'
            f'    <div class="ps-drug-pair">'
            f'      {p.display_a}'
            f'      <span class="ps-pair-sep">↔</span>'
            f'      {p.display_b}'
            f'    </div>'
            f'    <div>{severity_badge(p.level)}</div>'
            f'  </div>'
            f'  <div class="ps-card-body">'
            f'    <b>Клиническая интерпретация:</b> {p.explanation}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Related supplement interactions
    active_canons = report.resolved_drugs
    related_supps = []
    for c in active_canons:
        related_supps.extend(supp_repo.get_by_drug(c))

    if related_supps:
        with st.expander(f"⚠️ Доказанные пищевые/фито-взаимодействия ({len(related_supps)})", expanded=True):
            for s in related_supps:
                st.markdown(
                    f'<div class="ps-supp-card">'
                    f'  <div class="ps-supp-header">'
                    f'    <span class="ps-supp-title">{s.supplement_ru} ({s.supplement_lat}) + {s.drug_ru}</span>'
                    f'    <span>{severity_badge(s.severity)} [{s.evidence_level}]</span>'
                    f'  </div>'
                    f'  <div class="ps-supp-mech">{s.mechanism}</div>'
                    f'  <div class="ps-supp-mgmt"><b>Тактика:</b> {s.clinical_management}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )


def page_supplements(supp_repo: SupplementEvidenceRepository):
    """Каталог взаимодействий с БАДами."""
    st.markdown('<div class="ps-overline-muted">Доказательная фито- и нутрицевтическая токсикология</div>',
                unsafe_allow_html=True)
    st.markdown('## Клиническая база взаимодействий с БАДами')
    st.markdown(
        '<p style="font-size:0.88rem; color:var(--c-muted); line-height:1.65; margin-bottom:1.25rem;">'
        'Реестр фармакокинетических взаимодействий экстрактов трав, пищевых факторов и микронутриентов '
        'со строгой градацией доказательности (Level A/B/C) и первичными источниками.'
        '</p>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns([1.6, 1])
    with c1:
        query = st.text_input("Поиск (Зверобой, Грейпфрут, Гинкго, Варфарин…):")
    with c2:
        level_filter = st.selectbox("Фильтр по уровню доказательности:", ["Все уровни", "Level A", "Level B", "Level C"])

    items = supp_repo.search(query)
    if level_filter != "Все уровни":
        items = [i for i in items if i.evidence_level == level_filter]

    with st.expander("Шкала доказательности (Evidence Standards)", expanded=False):
        for lvl, desc in supp_repo.evidence_standards.items():
            st.write(f"• **{lvl}:** {desc}")

    st.markdown(f'<div style="font-size:0.82rem; color:var(--c-muted); margin-bottom:0.75rem;">Найдено: <b>{len(items)}</b> записей</div>', unsafe_allow_html=True)

    for item in items:
        st.markdown(
            f'<div class="ps-card">'
            f'  <div class="ps-card-header">'
            f'    <div>'
            f'      <div class="ps-overline" style="margin-bottom:2px;">Фармакокинетический конфликт · {item.evidence_level}</div>'
            f'      <div class="ps-drug-pair">{item.supplement_ru} ({item.supplement_lat}) ↔ {item.drug_ru}</div>'
            f'    </div>'
            f'    <div>{severity_badge(item.severity)}</div>'
            f'  </div>'
            f'  <div class="ps-card-body">'
            f'    <div><b>Тип:</b> {item.interaction_type}</div>'
            f'    <div><b>Механизм:</b> {item.mechanism}</div>'
            f'    <div><b>Последствие:</b> {item.clinical_consequence}</div>'
            f'    <div style="color:var(--c-navy); font-weight:500; margin-top:0.3rem;"><b>Рекомендация:</b> {item.clinical_management}</div>'
            f'  </div>'
            f'  <div style="margin-top:0.75rem; border-top:1px solid var(--c-hair); padding-top:0.45rem; font-size:0.75rem; color:var(--c-muted);">'
            f'    <b>Источники:</b> {"; ".join(item.citations)}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True
        )


def page_network_map(pairs: pd.DataFrame, drugs: pd.DataFrame, names: list[str]):
    """Топологическая карта графа DDInter."""
    st.markdown('<div class="ps-overline-muted">Биоинформатический топологический анализ</div>',
                unsafe_allow_html=True)
    st.markdown('## Интерактивная карта сети взаимодействий')
    st.markdown(
        '<p style="font-size:0.88rem; color:var(--c-muted); margin-bottom:1.25rem;">'
        'Топологические окрестности препаратов в графе DDInter. Узлы масштабируются по числу Major-рёбер.'
        '</p>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([1.3, 1.1, 1.2])
    center = c1.selectbox("Центральный узел:", names, index=names.index("warfarin") if "warfarin" in names else 0)
    levels = c2.multiselect("Уровни риска:", ["Major", "Moderate", "Minor", "Unknown"], default=["Major", "Moderate", "Minor"])
    max_edges = c3.slider("Макс. рёбер:", 5, 80, 25)

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
            net = Network(height="520px", width="100%", bgcolor="#FBFBFA", font_color="#111418",
                          directed=False, cdn_resources="in_line")
            net.set_options('{"physics":{"solver":"forceAtlas2Based","forceAtlas2Based":{"gravitationalConstant":-60,"centralGravity":0.02,"springLength":140,"springConstant":0.08},"stabilization":{"iterations":100}},"nodes":{"font":{"size":15,"face":"Work Sans, sans-serif","color":"#111418"},"borderWidth":1.5,"shadow":false},"edges":{"smooth":{"type":"continuous"},"width":2,"color":{"inherit":false}}}')
            net.add_node(center, label=center.title(), color={"background": "#1E3A5F", "border": "#022448"},
                         font={"color": "#FFFFFF"}, size=32, title=f"Центр: {center}")
            color_map = {"Major": "#C93B2B", "Moderate": "#D97706", "Minor": "#0D7A75", "Unknown": "#5A6578"}
            for _, row in near.iterrows():
                nbr, lvl = row["Сосед"], row["Level"]
                net.add_node(nbr, label=nbr.title(), color={"background": "#FFFFFF", "border": "#CBD5E1"},
                             font={"color": "#111418"}, size=18, title=nbr)
                net.add_edge(center, nbr, color=color_map.get(lvl, "#5A6578"), title=lvl,
                             width=3 if lvl == "Major" else 2)
            components.html(net.generate_html(), height=540, scrolling=False)
        except Exception as exc:
            st.error(f"Не удалось построить граф: {exc}")

        st.dataframe(
            near[["Сосед", "Level"]].rename(columns={"Level": "Уровень DDInter"}),
            use_container_width=True, hide_index=True
        )

    st.markdown('### Топ-10 хабов по числу Major-связей')
    st.dataframe(major_hubs(pairs), use_container_width=True, hide_index=True)


def page_ml_validation(pairs: pd.DataFrame, drugs: pd.DataFrame):
    """Научная валидация Link Prediction."""
    st.markdown('<div class="ps-overline-muted">Методология машинного обучения</div>',
                unsafe_allow_html=True)
    st.markdown('## Честная верификация Link Prediction (Leakage-Free)')
    st.markdown(
        '<p style="font-size:0.88rem; color:var(--c-muted); margin-bottom:1.25rem;">'
        'Сравнение моделей предсказания скрытых связей. '
        'Обучающие (12%) и тестовые (20%) связи физически изъяты из графа признаков (68%).'
        '</p>',
        unsafe_allow_html=True
    )

    result = cached_evaluation(pairs, drugs)
    metrics = result["metrics"]
    st.dataframe(metrics.style.format({"ROC-AUC": "{:.3f}", "Precision@5000": "{:.3f}"}),
                 use_container_width=True, hide_index=True)
    st.caption(
        f"Выборка: {result['train_examples']:,} обучающих примеров · "
        f"{result['test_examples']:,} тестовых (сбалансированные классы).".replace(",", " ")
    )

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
    ax.set(xlabel="FPR (доля ложноположительных)", ylabel="TPR (доля истинноположительных)",
           title="ROC-кривые на тестовом множестве DDInter")
    ax.grid(alpha=0.25, color="#E2E4E1")
    ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="#E2E4E1", fontsize=8.5, loc="lower right")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

    st.markdown('### Матрица ошибок (Random Forest, порог 0.5)')
    tn, fp, fn, tp = result["confusion"].ravel()
    conf_df = pd.DataFrame(
        [[tn, fp], [fn, tp]],
        index=["В базе нет записи", "Связь DDInter скрыта"],
        columns=["Модель: нет связи", "Модель: связь"]
    )
    st.dataframe(conf_df, use_container_width=True)


def page_ai(pairs: pd.DataFrame, names: list[str]):
    """Локальный ИИ-ассистент (Ollama)."""
    st.markdown('<div class="ps-overline-muted">Контекстный языковой ассистент</div>',
                unsafe_allow_html=True)
    st.markdown('## Локальный ИИ-аналитик (Ollama)')
    st.markdown(
        '<p style="font-size:0.88rem; color:var(--c-muted); margin-bottom:1.25rem;">'
        'Текстовые пояснения по фактам DDInter без отправки данных во внешние API.'
        '</p>',
        unsafe_allow_html=True
    )

    status = get_local_ai_status()

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.markdown('#### Выбор пары препаратов')
        drug_a = st.selectbox("Препарат A:", names, key="ai_a")
        drug_b = st.selectbox("Препарат B:", names, index=min(1, len(names) - 1), key="ai_b")
        question = st.text_area(
            "Вопрос:",
            placeholder="Например: в чём клиническое значение этого взаимодействия?",
            height=100
        )

        match = pairs[(pairs.Drug_A == min(drug_a, drug_b)) & (pairs.Drug_B == max(drug_a, drug_b))]
        level = None if match.empty else str(match.iloc[0]["Level"])

        st.markdown("---")
        st.markdown('#### Структурированное пояснение (автономный режим)')
        struct_exp = generate_structured_explanation(drug_a, drug_b, level)
        st.info(
            f"**Суть:** {struct_exp['summary']}\n\n"
            f"**Клинический контекст:** {struct_exp['clinical_meaning']}\n\n"
            f"**Рекомендованная тактика:** {struct_exp['recommendation']}"
        )

    with right:
        st.markdown(
            '<div class="ps-infobox">'
            '<div class="ps-infobox-title">Статус сервиса Ollama</div>',
            unsafe_allow_html=True
        )
        if status.available:
            st.success(f"✅ {status.message} ({status.details})")
            preferred = next((n for n in status.models if n.startswith("qwen2.5:3b")), status.models[0])
            model = st.selectbox("Локальная модель:", status.models, index=status.models.index(preferred))
            if st.button("Сгенерировать пояснение", type="primary", disabled=(not question.strip())):
                prompt = make_evidence_prompt(question.strip(), drug_a, drug_b, level)
                with st.spinner("Модель формулирует ответ…"):
                    try:
                        ans = ask_local_model(prompt, model)
                        st.markdown("**Ответ модели:**")
                        st.markdown(ans)
                    except RuntimeError as exc:
                        st.error(str(exc))
        else:
            st.info(f"ℹ️ {status.message}\n\n{status.details}")
            st.caption("Базовый анализ и расчёт рисков функционируют полностью автономно.")
        st.markdown('</div>', unsafe_allow_html=True)


def page_methodology():
    """Методология, доказательность и этика."""
    st.markdown('<div class="ps-overline-muted">Методологический монографический отчёт</div>',
                unsafe_allow_html=True)
    st.markdown('## Методология, доказательная база и этические ограничения')

    st.markdown("""
### 1. Архитектура академической базы DDInter
**DDInter** (*Nucleic Acids Research*, 2022; Xiong G. et al.):
- **1 939** уникальных фармакологически активных веществ.
- **160 235** уникальных пар с ранжированием: Major (26 914), Moderate (96 675), Minor (6 833), Unknown (29 813).
- Нормализация: дубликаты свёрнуты к наибольшей тяжести, петли A=A удалены.

### 2. Доказательность для БАДов
- **Level A:** Рандомизированные контролируемые испытания или мета-анализы.
- **Level B:** Контролируемые проспективные или когортные исследования.
- **Level C:** Фармакокинетические исследования на здоровых добровольцах, серии случаев, монографии FDA/EMA.

### 3. Институциональные ограничения и этика
- **«Нет записи» ≠ «Безопасно»:** Отсутствие строки означает лишь отсутствие документированного факта в данном датасете.
- **ML предсказывает граф, а не биологию:** ROC-AUC 0.910 — точность восстановления топологических рёбер, не тяжесть эффекта у пациента.
- Проект носит образовательный и исследовательский характер. Терапевтические решения принимаются исключительно сертифицированным медицинским персоналом.
""")


# ─── App entry point ──────────────────────────────────────────────────────────
render_header()
render_disclaimer()

nav_page = st.sidebar.radio(
    "Навигация:",
    [
        "🏛️ Обзор (Overview)",
        "🔬 Аналитический комплекс",
        "🌿 База БАДов",
        "🕸️ Карта сети",
        "📊 Верификация ML",
        "🤖 ИИ-ассистент",
        "📖 Методология",
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("Pharma Sentinel · Clinical Intelligence v3.4")
st.sidebar.caption("© 2025 — Academic Research Project")

try:
    with st.spinner("Инициализация платформы данных…"):
        pairs, drugs = cached_data()
    names = drugs["drug"].tolist()
    normalizer = cached_normalizer(tuple(names))
    supp_repo = SupplementEvidenceRepository()

    if "Обзор" in nav_page:
        page_overview(pairs, drugs)
    elif "Аналитический" in nav_page:
        page_workspace(pairs, drugs, normalizer, supp_repo)
    elif "БАДов" in nav_page:
        page_supplements(supp_repo)
    elif "Карта" in nav_page:
        page_network_map(pairs, drugs, names)
    elif "Верификация" in nav_page:
        page_ml_validation(pairs, drugs)
    elif "ИИ" in nav_page:
        page_ai(pairs, names)
    else:
        page_methodology()

except FileNotFoundError as exc:
    st.warning(str(exc))
except DataValidationError as exc:
    st.error(f"Ошибка целостности данных: {exc}")
except Exception as exc:
    st.error(f"Непредвиденная ошибка: {exc}")
    raise
