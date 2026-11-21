"""DARIGUARD — Платформа клинической фармакологии и анализа полипрагмазии.

Архитектура: Production-grade clinical intelligence platform.
Интеграция React Bits: <TechText /> (интерактивный заголовок), фоновая молекулярная сеть.
Локализация: Полноценное переключение Қазақша (kk, негізгі) / Русский (ru) / English (en).
"""
import importlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Ensure freshly modified modules are reloaded in long-running Streamlit processes
import importlib.util as _importlib_util
from pathlib import Path as _Path

_PROJECT_ROOT = _Path(__file__).resolve().parent
importlib.invalidate_caches()

_IS_UNITTEST_CLI = any("unittest" in str(arg) for arg in sys.argv)
_RELOAD_TARGETS = (
    ("components.react_bits",)
    if _IS_UNITTEST_CLI
    else (
        "i18n",
        "normalization",
        "supplement_schema",
        "data_loader",
        "graph_builder",
        "components.react_bits",
        "components.molecular_viewer",
        "data.verified_molecules",
        "state_manager",
        "local_ai",
        "model",
        "multi_checker",
        "molecular_lab",
    )
)
for _mod_name in _RELOAD_TARGETS:
    if _mod_name in sys.modules:
        try:
            importlib.reload(sys.modules[_mod_name])
        except Exception:
            sys.modules.pop(_mod_name, None)


def _force_load_module_from_disk(mod_name: str, rel_path: str):
    """Принудительно загружает актуальный модуль с диска в обход устаревшего sys.modules в Streamlit."""
    full_path = _PROJECT_ROOT / rel_path
    spec = _importlib_util.spec_from_file_location(mod_name, str(full_path))
    if spec and spec.loader:
        mod = _importlib_util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
        if "." in mod_name:
            pkg_name, child_name = mod_name.split(".", 1)
            if pkg_name in sys.modules:
                setattr(sys.modules[pkg_name], child_name, mod)
        return mod
    return importlib.import_module(mod_name)


try:
    from components.react_bits import (
        render_albus_fingent_hero_3d_html,
        render_albus_pipeline_and_hex_ring_html,
        render_tech_text_and_effects_html,
    )
except ImportError:
    _rb_mod = _force_load_module_from_disk("components.react_bits", "components/react_bits.py")
    render_albus_fingent_hero_3d_html = _rb_mod.render_albus_fingent_hero_3d_html
    render_albus_pipeline_and_hex_ring_html = _rb_mod.render_albus_pipeline_and_hex_ring_html
    render_tech_text_and_effects_html = _rb_mod.render_tech_text_and_effects_html

from data_loader import DataValidationError, load_ddinter
from graph_builder import interaction_color, major_hubs
from i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_LABELS,
    SUPPORTED_LANGUAGES,
    get_lang,
    set_lang,
    t,
)
try:
    from local_ai import (
        ask_local_model,
        fetch_pubmed_evidence,
        generate_clinical_intelligence_brief,
        generate_structured_explanation,
        get_contextual_questions,
        get_local_ai_status,
        make_evidence_prompt,
    )
except ImportError:
    _lai_mod = _force_load_module_from_disk("local_ai", "local_ai.py")
    ask_local_model = _lai_mod.ask_local_model
    fetch_pubmed_evidence = _lai_mod.fetch_pubmed_evidence
    generate_clinical_intelligence_brief = _lai_mod.generate_clinical_intelligence_brief
    generate_structured_explanation = _lai_mod.generate_structured_explanation
    get_contextual_questions = _lai_mod.get_contextual_questions
    get_local_ai_status = _lai_mod.get_local_ai_status
    make_evidence_prompt = _lai_mod.make_evidence_prompt

try:
    from model import novel_pair_hypotheses, predict_pair_ml_intelligence, train_and_evaluate
except ImportError:
    _mdl_mod = _force_load_module_from_disk("model", "model.py")
    novel_pair_hypotheses = _mdl_mod.novel_pair_hypotheses
    predict_pair_ml_intelligence = _mdl_mod.predict_pair_ml_intelligence
    train_and_evaluate = _mdl_mod.train_and_evaluate
from molecular_lab import view_molecular_lab
from multi_checker import MultiCheckReport, MultiDrugChecker
from normalization import DrugNormalizer
from report_generator import generate_clinical_protocol_report
from state_manager import (
    REFERENCE_COMBINATIONS,
    get_active_pair,
    get_workspace_filter,
    init_session_state,
    reset_active_pair,
    set_active_pair,
    set_workspace_cohort,
    set_workspace_filter,
    swap_active_pair,
)
from supplement_schema import SupplementEvidenceRepository


# ─── Инициализация состояния (Session State) ─────────────────────────────────
init_session_state(default_lang=get_lang())


st.set_page_config(
    page_title="DariGuard · Clinical Pharmacology",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─── Дизайн-система (Futuristic Scientific Intelligence · Qgen Palette) ──────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg:           #0B1114;
  --bg-sec:       #111B20;
  --bg-card:      #111B20;
  --bg-elevated:  #17252B;
  --bg-subtle:    #17252B;
  --border:       #263940;
  --border-hover: #36D6B0;
  --border-focus: #36D6B0;

  --ink-primary:  #EAF2F2;
  --ink-body:     #EAF2F2;
  --ink-muted:    #91A5AA;

  --accent:       #36D6B0;
  --accent-hover: #2BB896;
  --accent-light: rgba(54, 214, 176, 0.12);
  --secondary-sage:#67B7D1;

  --info-blue:    #67B7D1;
  --info-blue-bg: rgba(103, 183, 209, 0.12);
  --info-blue-bd: rgba(103, 183, 209, 0.35);

  --sev-major:    #F43F5E;
  --sev-major-bg: rgba(244, 63, 94, 0.14);
  --sev-major-bd: rgba(244, 63, 94, 0.42);
  --sev-mod:      #F59E0B;
  --sev-mod-bg:   rgba(245, 158, 11, 0.14);
  --sev-mod-bd:   rgba(245, 158, 11, 0.42);
  --sev-minor:    #36D6B0;
  --sev-minor-bg: rgba(54, 214, 176, 0.14);
  --sev-minor-bd: rgba(54, 214, 176, 0.42);
  --sev-none:     #91A5AA;
  --sev-none-bg:  rgba(145, 165, 170, 0.12);
  --sev-none-bd:  #263940;

  --font-ui:      'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-serif:   'Lora', Georgia, serif;
  --font-mono:    'JetBrains Mono', monospace;

  --ease-snappy:  cubic-bezier(0.22, 1, 0.36, 1);
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
  max-width: 1280px !important;
  padding: 0.5rem 1.5rem 3rem !important;
  position: relative !important;
  z-index: 2 !important;
}

[data-testid="column"] { min-width: 0 !important; }

/* ── Заголовки и типографика ── */
[data-testid="stMarkdownContainer"] h1 {
  font-family: var(--font-ui) !important;
  font-size: clamp(1.5rem, 2.5vw, 2.05rem) !important;
  font-weight: 700 !important;
  line-height: 1.22 !important;
  letter-spacing: -0.02em !important;
  color: var(--ink-primary) !important;
  margin: 0.15rem 0 0.45rem !important;
}

[data-testid="stMarkdownContainer"] h2 {
  font-family: var(--font-ui) !important;
  font-size: clamp(1.18rem, 1.9vw, 1.48rem) !important;
  font-weight: 600 !important;
  line-height: 1.3 !important;
  color: var(--ink-primary) !important;
  margin: 1.15rem 0 0.4rem !important;
}

[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
  font-family: var(--font-ui) !important;
  font-size: 1.0rem !important;
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
  padding: 0.35rem 0.78rem;
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--accent);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.28);
}

.ps-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 8px rgba(54, 214, 176, 0.7);
  animation: ps-pulse 2.2s infinite ease-in-out;
}

@keyframes ps-pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
}

/* ── Полное скрытие технической радио-строки навигации позади BubbleMenu ── */
.ps-hidden-nav-bridge,
div:has(> .ps-hidden-nav-bridge),
[data-testid="stElementContainer"]:has(.ps-hidden-nav-bridge),
div[data-testid="stElementContainer"].st-key-main_nav_radio,
.st-key-main_nav_radio,
div[data-testid="stElementContainer"]:has(.st-key-main_nav_radio),
div[data-testid="stElementContainer"]:has([aria-label="Navigation"]),
div[data-testid="stRadio"]:has([aria-label="Navigation"]),
div[role="radiogroup"][aria-label="Navigation"],
div:has(> div > div[role="radiogroup"][aria-label="Navigation"]),
div[data-testid="stRadio"]:has(div[role="radiogroup"] > label:nth-child(4)),
div[data-testid="stRadio"]:has(div[role="radiogroup"] > div:nth-child(4)) {
  position: fixed !important;
  top: -99999px !important;
  left: -99999px !important;
  width: 0 !important;
  height: 0 !important;
  max-width: 0 !important;
  max-height: 0 !important;
  opacity: 0 !important;
  pointer-events: none !important;
  overflow: hidden !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  display: none !important;
  visibility: hidden !important;
  z-index: -99999 !important;
}

/* ── Компактный переключатель языка (Қазақша / Русский / English) ── */
.st-key-platform_language_selector div[role="radiogroup"],
div[data-testid="stElementContainer"].st-key-platform_language_selector div[role="radiogroup"] {
  display: inline-flex !important;
  flex-direction: row !important;
  align-items: center !important;
  gap: 0.35rem !important;
  flex-wrap: wrap !important;
  background: rgba(17, 27, 32, 0.85) !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  padding: 4px 8px !important;
  border-radius: 9999px !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.32) !important;
  margin-bottom: 0.35rem !important;
}

.st-key-platform_language_selector div[role="radiogroup"] > label > div:first-child:not([data-testid="stMarkdownContainer"]),
.st-key-platform_language_selector input[type="radio"] {
  display: none !important;
}

.st-key-platform_language_selector label,
div[data-testid="stElementContainer"].st-key-platform_language_selector label {
  margin: 0 !important;
  padding: 0.32rem 0.85rem !important;
  border-radius: 9999px !important;
  font-size: 0.76rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.01em !important;
  color: var(--ink-muted) !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  cursor: pointer !important;
  user-select: none !important;
  transition: transform 160ms var(--ease-snappy), background 160ms ease, color 160ms ease, border-color 160ms ease !important;
}

.st-key-platform_language_selector label p {
  color: inherit !important;
  font-size: 0.76rem !important;
  font-weight: inherit !important;
}

.st-key-platform_language_selector label:hover {
  color: var(--ink-primary) !important;
  background: var(--bg-elevated) !important;
  border-color: var(--border) !important;
  transform: translateY(-1px) !important;
}

.st-key-platform_language_selector label:has(input:checked),
.st-key-platform_language_selector label[data-checked="true"] {
  background: rgba(54, 214, 176, 0.16) !important;
  color: var(--accent) !important;
  border-color: var(--accent) !important;
  font-weight: 600 !important;
  box-shadow: 0 0 14px rgba(54, 214, 176, 0.22) !important;
}

.st-key-platform_language_selector label:has(input:checked) p,
.st-key-platform_language_selector label[data-checked="true"] p {
  color: var(--accent) !important;
  font-weight: 600 !important;
}

/* ── Баблы клинических контекстных вопросов (Clinical Question Bubbles) ── */
div.ps-quick-q-bubble button {
  border-radius: 9999px !important;
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border) !important;
  color: var(--ink-primary) !important;
  font-size: 0.81rem !important;
  font-weight: 500 !important;
  padding: 0.45rem 1rem !important;
  text-align: left !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
  transition: transform 160ms var(--ease-snappy), border-color 160ms ease, background 160ms ease, color 160ms ease !important;
}

div.ps-quick-q-bubble button:hover {
  background: rgba(54, 214, 176, 0.12) !important;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  transform: translateY(-1px) !important;
}

/* ── Формы ввода, селекты и теги препаратов (Qgen Obsidian Surface) ── */
label[data-testid="stWidgetLabel"] p {
  color: var(--ink-primary) !important;
  font-weight: 600 !important;
  font-size: 0.81rem !important;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] {
  background-color: var(--bg-card) !important;
  border-color: var(--border) !important;
  color: var(--ink-primary) !important;
  border-radius: 6px !important;
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
  background-color: rgba(54, 214, 176, 0.14) !important;
  border: 1px solid rgba(54, 214, 176, 0.4) !important;
  color: var(--ink-primary) !important;
  border-radius: 5px !important;
}

span[data-baseweb="tag"] span {
  color: var(--ink-primary) !important;
  font-weight: 500 !important;
}

ul[data-testid="stSelectboxVirtualDropdown"],
div[data-baseweb="popover"] ul {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.55) !important;
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
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  padding: 2px;
}

[data-testid="stAlert"] {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  color: var(--ink-primary) !important;
  border-radius: 6px !important;
}

[data-testid="stAlert"] p {
  color: var(--ink-primary) !important;
}

/* ── Быстрые GPU-анимации смены страниц (<AnimatedContent /> · 180-220ms) ── */
@keyframes ps-page-enter {
  0% {
    opacity: 0;
    transform: translate3d(0, 10px, 0);
  }
  100% {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

.ps-animated-page-root {
  animation: ps-page-enter 200ms var(--ease-snappy) both;
}

.ps-anim-item {
  animation: ps-page-enter 210ms var(--ease-snappy) both;
}

.ps-stagger-1 { animation-delay: 20ms; }
.ps-stagger-2 { animation-delay: 45ms; }
.ps-stagger-3 { animation-delay: 70ms; }
.ps-stagger-4 { animation-delay: 95ms; }

/* ── Клинический дисклеймер ── */
.ps-disclaimer {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  padding: 0.65rem 1rem;
  border-radius: 6px;
  margin-bottom: 1.15rem;
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--ink-body);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
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
  border-radius: 4px;
  white-space: nowrap;
  margin-top: 1px;
}

.ps-disclaimer b { color: var(--ink-primary); }

/* ── Карточки и статистика (#111B20 / #17252B) с выразительными ховерами ── */
.ps-stat-box {
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 0.9rem 1.05rem;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  transition: transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1), border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
}

.ps-stat-box:hover {
  transform: translateY(-4px) scale(1.012);
  border-color: var(--accent);
  background: linear-gradient(145deg, rgba(54, 214, 176, 0.08) 0%, #111B20 65%);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45), 0 0 20px rgba(54, 214, 176, 0.18);
}

.ps-stat-label {
  font-family: var(--font-mono);
  font-size: 0.67rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-muted);
  transition: color 160ms ease;
}

.ps-stat-box:hover .ps-stat-label {
  color: var(--accent);
}

.ps-stat-number {
  font-family: var(--font-mono);
  font-size: 1.45rem;
  line-height: 1.2;
  font-weight: 600;
  color: var(--ink-primary);
  margin: 0.22rem 0;
}

.ps-stat-sub {
  font-size: 0.72rem;
  color: var(--ink-muted);
}

/* ── Интерактивные карточки раздела «О платформе» с ховер-эффектами ── */
.ps-overview-card {
  position: relative;
  background: linear-gradient(145deg, #111B20 0%, #0E171B 100%);
  border: 1px solid #263940;
  border-radius: 14px;
  padding: 1.25rem 1.35rem;
  height: 100%;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.32);
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 240ms cubic-bezier(0.34, 1.56, 0.64, 1),
    border-color 200ms ease,
    box-shadow 220ms ease,
    background 220ms ease;
}

.ps-overview-card:hover {
  transform: translateY(-6px) scale(1.015);
  border-color: #36D6B0;
  background: linear-gradient(145deg, rgba(54, 214, 176, 0.11) 0%, #132229 55%, #0F1A1F 100%);
  box-shadow: 0 16px 38px rgba(0, 0, 0, 0.55), 0 0 26px rgba(54, 214, 176, 0.24);
}

.ps-overview-card .ps-ov-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #67B7D1;
  background: rgba(103, 183, 209, 0.12);
  border: 1px solid rgba(103, 183, 209, 0.32);
  padding: 3px 10px;
  border-radius: 999px;
  margin-bottom: 0.65rem;
  transition: all 180ms ease;
}

.ps-overview-card:hover .ps-ov-badge {
  color: #041410;
  background: #36D6B0;
  border-color: #36D6B0;
  box-shadow: 0 0 14px rgba(54, 214, 176, 0.45);
}

.ps-overview-card .ps-ov-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #EAF2F2;
  margin-bottom: 0.45rem;
  transition: color 180ms ease;
}

.ps-overview-card:hover .ps-ov-title {
  color: #36D6B0;
}

.ps-overview-card .ps-ov-bar {
  margin-top: 0.85rem;
  height: 3px;
  width: 100%;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 99px;
  overflow: hidden;
}

.ps-overview-card .ps-ov-bar-fill {
  height: 100%;
  width: 38%;
  background: linear-gradient(90deg, #36D6B0, #67B7D1);
  transition: width 320ms cubic-bezier(0.16, 1, 0.3, 1);
}

.ps-overview-card:hover .ps-ov-bar-fill {
  width: 100%;
  box-shadow: 0 0 10px #36D6B0;
}

/* ── Результаты анализа (Клиническая иерархия) ── */
.ps-card-finding {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.15rem;
  margin-bottom: 0.75rem;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28);
  transition: border-color 180ms ease, transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 180ms ease;
  animation: ps-page-enter 200ms var(--ease-snappy) both;
}

.ps-card-finding:hover {
  border-color: var(--accent);
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45), 0 0 18px rgba(54, 214, 176, 0.16);
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
  padding: 0.5rem 0.8rem;
  border-radius: 5px;
  margin-top: 0.2rem;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--ink-body);
}

/* ── Семантические плашки тяжести (с нецветовыми маркерами) ── */
.ps-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2.5px 9px;
  border-radius: 9999px;
  font-family: var(--font-mono);
  font-size: 0.69rem;
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
  background: var(--bg-card);
  padding: 0.75rem 0.95rem;
  border-radius: 0 8px 8px 0;
  margin-bottom: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.22);
  transition: transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1), border-color 180ms ease, box-shadow 180ms ease;
  animation: ps-page-enter 210ms var(--ease-snappy) both;
}

.ps-supp-row:hover {
  transform: translateY(-4px) scale(1.01) !important;
  border-color: var(--accent) !important;
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.45), 0 0 18px rgba(54, 214, 176, 0.22) !important;
}

/* ── Универсальные ховер-эффекты на ВСЕ карточки и панели (включая inline-styled блоки) ── */
.ps-stat-box,
.ps-card-finding,
.ps-supp-row,
.ps-overview-card,
.ps-qgen-card,
.ps-token-bar,
.ps-disclaimer,
.ps-rec-box,
[data-testid="stDataFrame"],
[data-testid="stExpander"],
div[data-testid="stMarkdownContainer"] > div[style*="border"] {
  transition:
    transform 220ms cubic-bezier(0.34, 1.56, 0.64, 1) !important,
    border-color 180ms ease !important,
    box-shadow 200ms ease !important,
    background 200ms ease !important;
}

.ps-stat-box:hover,
.ps-card-finding:hover,
.ps-supp-row:hover,
.ps-overview-card:hover,
.ps-qgen-card:hover,
.ps-token-bar:hover,
.ps-disclaimer:hover,
.ps-rec-box:hover,
[data-testid="stDataFrame"]:hover,
[data-testid="stExpander"]:hover,
div[data-testid="stMarkdownContainer"] > div[style*="border"]:hover {
  transform: translateY(-5px) scale(1.01) !important;
  border-color: #36D6B0 !important;
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.56), 0 0 24px rgba(54, 214, 176, 0.25) !important;
}

/* ── Нажимаемые кнопки и пилюли с выразительными ховер-эффектами ── */
.stButton > button,
.stDownloadButton > button,
button[data-testid^="baseButton"],
div[data-testid="stButton"] button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stPills"] button,
div.ps-quick-q-bubble button {
  font-size: 0.81rem !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  min-height: 40px !important;
  color: var(--ink-primary) !important;
  background: linear-gradient(135deg, #17252B 0%, #111B20 100%) !important;
  border: 1px solid #263940 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.30) !important;
  cursor: pointer !important;
  transition:
    transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1) !important,
    border-color 160ms ease !important,
    background 160ms ease !important,
    color 160ms ease !important,
    box-shadow 180ms ease !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
button[data-testid^="baseButton"]:hover,
div[data-testid="stButton"] button:hover,
div[data-testid="stDownloadButton"] button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stPills"] button:hover,
div.ps-quick-q-bubble button:hover {
  transform: translateY(-3px) scale(1.018) !important;
  background: linear-gradient(135deg, rgba(54, 214, 176, 0.20) 0%, rgba(103, 183, 209, 0.14) 100%) !important;
  border-color: #36D6B0 !important;
  color: #36D6B0 !important;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.45), 0 0 18px rgba(54, 214, 176, 0.32) !important;
}

.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #36D6B0 0%, #24A98B 100%) !important;
  border-color: #36D6B0 !important;
  color: #041410 !important;
  font-weight: 700 !important;
  box-shadow: 0 6px 18px rgba(54, 214, 176, 0.32) !important;
}

.stButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
  transform: translateY(-3px) scale(1.025) !important;
  background: linear-gradient(135deg, #4FE3BF 0%, #36D6B0 100%) !important;
  border-color: #67B7D1 !important;
  color: #041410 !important;
  box-shadow: 0 12px 28px rgba(54, 214, 176, 0.52) !important;
}

.stButton > button:active,
.stDownloadButton > button:active,
button[data-testid^="baseButton"]:active {
  transform: translateY(0) scale(0.99) !important;
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


def safe_catalog_label(norm, query: str, labels: list[str] | None = None, mapping: dict[str, str] | None = None) -> str | None:
    """Безопасный поиск отображаемой метки препарата с тройным уровнем защиты от устаревших кэшей."""
    # 1. Попытка вызвать метод экземпляра (нормальный путь)
    fn = getattr(norm, "get_canonical_catalog_label", None)
    if fn is not None:
        try:
            lbl = fn(query)
            if lbl and (labels is None or lbl in labels):
                return lbl
        except Exception:
            pass

    # 2. Попытка использовать нормализацию запроса к каноническому имени
    clean_q = (query or "").strip().lower()
    canon = clean_q
    if norm is not None and hasattr(norm, "normalize"):
        try:
            res = norm.normalize(query)
            if getattr(res, "is_resolved", False) and res.canonical_name:
                canon = res.canonical_name.strip().lower()
        except Exception:
            pass

    # 3. Сопоставление с каталогом меток
    if labels:
        if mapping:
            for l, val in mapping.items():
                if val == canon:
                    return l
        for l in labels:
            if f"[{canon}]" in l.lower() or canon == l.lower() or canon in l.lower():
                return l

    return None



@st.cache_data(show_spinner=False)
def cached_evaluation(pairs: pd.DataFrame, drugs: pd.DataFrame):
    return train_and_evaluate(pairs, drugs)


# ─── Семантические бейджи (с нецветовыми маркерами) ──────────────────────────
def severity_badge(level: str) -> str:
    badge_key = f"severity_{level.lower().replace(' ', '_')}_badge"
    label = t(badge_key, default=level)
    if level == "Major":
        return f'<span class="ps-badge ps-badge-major">● {label}</span>'
    elif level == "Moderate":
        return f'<span class="ps-badge ps-badge-mod">▲ {label}</span>'
    elif level == "Minor":
        return f'<span class="ps-badge ps-badge-minor">○ {label}</span>'
    elif level == "Unknown":
        return f'<span class="ps-badge ps-badge-none">? {label}</span>'
    else:
        return f'<span class="ps-badge ps-badge-none">— {label}</span>'


# ─── Верхняя панель сайта (<BubbleMenu /> в правом верхнем углу + Звук SFX + Қазақша/RU/EN) ───
def render_top_bar():
    current_page = st.session_state.get("nav_page", "workspace")
    sound_on = bool(st.session_state.get("sound_enabled", False))

    # Невидимый инжектор глобального движка (молекулярный фон + <BubbleMenu /> в правом верхнем углу + WebAudio)
    tech_html = render_tech_text_and_effects_html(
        text="DARIGUARD",
        subtitle=f"{t('brand_sub')} · RELEASE v3.5",
        height=1,
        sound_enabled=sound_on,
    )
    components.html(tech_html, height=1, scrolling=False)

    c_badge, c_sound, c_lang, _c_bubble_space = st.columns([1.9, 0.75, 1.55, 1.8])
    with c_badge:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:10px; padding-top:4px;">'
            f'<span class="ps-live-badge"><span class="ps-live-dot"></span>{t("live_db")}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c_sound:
        new_sound = st.toggle(
            "SFX 🔊",
            value=sound_on,
            key="toggle_sound_fx",
            help="Звуковое сопровождение нажатий и наведения (WebAudio)",
        )
        if new_sound != sound_on:
            st.session_state["sound_enabled"] = new_sound
            st.rerun()
    with c_lang:
        cur_lang = get_lang()
        options = ["kk", "ru", "en"]
        idx = options.index(cur_lang) if cur_lang in options else 0
        new_lang = st.radio(
            "Тіл / Язык / Language",
            options=options,
            index=idx,
            format_func=lambda code: LANGUAGE_LABELS.get(code, code),
            horizontal=True,
            label_visibility="collapsed",
            key="platform_language_selector"
        )
        if new_lang != cur_lang:
            set_lang(new_lang)
            st.session_state.pop("main_nav_radio", None)
            st.session_state.pop("_last_synced_nav_page", None)
            st.rerun()

    # Скрытый мост синхронизации страниц для <BubbleMenu /> и автоматических тестов
    nav_options = [
        t("nav_workspace"),
        t("nav_molecular"),
        t("nav_supplements"),
        t("nav_network"),
        t("nav_ml"),
        t("nav_ai"),
        t("nav_overview"),
    ]

    key_to_idx = {
        "workspace": 0,
        "molecular": 1,
        "supplements": 2,
        "network": 3,
        "ml": 4,
        "ai": 5,
        "overview": 6
    }
    idx_to_key = ["workspace", "molecular", "supplements", "network", "ml", "ai", "overview"]

    cur_idx = key_to_idx.get(current_page, 0)
    expected_nav_option = nav_options[cur_idx]

    if (
        st.session_state.get("main_nav_radio") not in nav_options
        or st.session_state.get("_last_synced_nav_page") != current_page
    ):
        st.session_state["main_nav_radio"] = expected_nav_option

    # ── Невидимый мост синхронизации навигации для <BubbleMenu /> ──
    with st.container():
        st.markdown('<div class="ps-hidden-nav-bridge" style="display:none!important;height:0!important;overflow:hidden!important;">', unsafe_allow_html=True)
        selected_nav = st.radio(
            "Navigation",
            options=nav_options,
            index=cur_idx if "main_nav_radio" not in st.session_state else None,
            horizontal=True,
            label_visibility="collapsed",
            key="main_nav_radio"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    chosen_key = idx_to_key[nav_options.index(selected_nav)]
    st.session_state["_last_synced_nav_page"] = chosen_key
    if chosen_key != current_page:
        st.session_state.nav_page = chosen_key
        st.rerun()


def render_footer(current_page: str = "workspace"):
    st.markdown(
        f'<div style="border-top:1px solid var(--border); padding-top:1.25rem; margin-top:2.5rem; margin-bottom:2rem; display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem; font-size:0.75rem; color:var(--ink-muted);">'
        f'<div>{t("footer_text")}</div>'
        f'<div style="text-align:right; font-family:var(--font-mono);">Pharmacoinformatics Lab · DDInter v2024.11</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# ─── Страница: Анализ назначений (Workspace — главная рабочая зона) ───────────
def view_workspace(pairs: pd.DataFrame, drugs: pd.DataFrame, normalizer: DrugNormalizer, supp_repo: SupplementEvidenceRepository):
    st.markdown('<div class="ps-animated-page-root ps-page-workspace">', unsafe_allow_html=True)

    # ── ФЛАГМАНСКИЙ 3D ЭКРАН: ALBUS THERAPEUTICS × FINGENT × 3D DNA HELIX ──
    act_a, act_b = get_active_pair()
    hero_html = render_albus_fingent_hero_3d_html(
        lang=get_lang(),
        active_drug_a=act_a,
        active_drug_b=act_b,
        major_count=1,
        mod_count=1,
        total_pairs_checked=len(pairs),
        height=430,
    )
    components.html(hero_html, height=435, scrolling=False)

    catalog = normalizer.get_search_catalog()
    catalog_labels = [label for label, _ in catalog]
    catalog_map = dict(catalog)

    # ── Блок быстрых клинических пресетов (без эмодзи) ──
    st.markdown(
        f'<div class="ps-anim-item ps-stagger-2" style="font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-muted); margin-top:0.35rem; margin-bottom:0.4rem;">'
        f'{t("presets_label")}</div>',
        unsafe_allow_html=True
    )

    def on_click_preset(preset_drugs: list[str], cohort_id: str, primary_pair: tuple[str, str]):
        set_workspace_cohort(
            preset_drugs,
            cohort_id,
            primary_pair,
            normalizer=normalizer,
            catalog_labels=catalog_labels,
            catalog_map=catalog_map,
        )

    p1, p2, p3 = st.columns(3)
    with p1:
        st.button(
            t("preset_cyp"),
            use_container_width=True,
            key="btn_preset_cyp",
            on_click=on_click_preset,
            args=(["warfarin", "amiodarone", "fluconazole"], "preset_cyp", ("warfarin", "amiodarone")),
        )
    with p2:
        st.button(
            t("preset_whammy"),
            use_container_width=True,
            key="btn_preset_whammy",
            on_click=on_click_preset,
            args=(["enalapril", "furosemide", "ibuprofen"], "preset_whammy", ("enalapril", "ibuprofen")),
        )
    with p3:
        st.button(
            t("preset_bleeding"),
            use_container_width=True,
            key="btn_preset_bleeding",
            on_click=on_click_preset,
            args=(["warfarin", "acetylsalicylic acid"], "preset_bleeding", ("warfarin", "acetylsalicylic acid")),
        )

    # Инициализация дефолтного набора с русскими МНН / синонимами
    if not st.session_state.get("workspace_multiselect"):
        default_items = []
        for kw in ["варфарин", "аспирин", "ибупрофен"]:
            match = safe_catalog_label(normalizer, kw, catalog_labels, catalog_map)
            if match and match in catalog_labels:
                default_items.append(match)
        st.session_state.workspace_multiselect = default_items if len(default_items) >= 2 else catalog_labels[:3]

    if st.session_state.get("active_cohort"):
        cohort_name = t(st.session_state.active_cohort, default=st.session_state.active_cohort)
        st.markdown(
            f'<div style="margin-bottom:0.6rem; display:inline-flex; align-items:center; gap:7px; background:rgba(54,214,176,0.12); border:1px solid rgba(54,214,176,0.38); padding:3px 10px; border-radius:9999px; font-size:0.75rem; color:#36D6B0; font-weight:600;">'
            f'<span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#36D6B0; box-shadow:0 0 6px #36D6B0;"></span>'
            f'{t("active_cohort_pill")}: <b>{cohort_name}</b>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Двухколоночный интерфейс: Ввод параметров слева, Протокол справа ──
    col_input, col_meta = st.columns([2.2, 1], gap="medium")

    with col_input:
        selected_drugs = st.multiselect(
            t("search_label"),
            options=catalog_labels,
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
    dup_structured = getattr(report, "duplicates_structured", None)
    if dup_structured is None and hasattr(report, "drug_to_inputs") and report.drug_to_inputs:
        dup_structured = [
            (canon, inputs)
            for canon, inputs in report.drug_to_inputs.items()
            if len(inputs) > 1
        ]

    if dup_structured:
        for canon, inputs in dup_structured:
            st.error(t("dup_therapeutic_warning", canon=canon, inputs=", ".join(inputs)))
    elif getattr(report, "duplicates_detected", None):
        for dup in report.duplicates_detected:
            st.error(f"{t('dup_warning')} {dup}")
    elif getattr(report, "duplicates", None):
        for dup in report.duplicates:
            st.error(f"{t('dup_warning')} {dup}")

    # ── Метрики полипрагмазии ──
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        risk_label = t(f"risk_code_{report.overall_risk_code.lower()}", default=report.overall_risk)
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-2">'
            f'<div class="ps-stat-label">{t("risk_overall")}</div>'
            f'<div class="ps-stat-number" style="font-size:1.35rem;">{risk_label}</div>'
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

    # ── Сопутствующие взаимодействия с БАДами (предварительный сбор для отчета) ──
    active_canons = report.resolved_drugs
    related_supps = []
    for c in active_canons:
        related_supps.extend(supp_repo.get_by_drug(c))

    # ── Панель экспорта протокола аудита (Clinical Decision Support Export) ──
    report_html = generate_clinical_protocol_report(
        report=report,
        selected_drugs=selected_drugs,
        related_supps=related_supps,
        lang=get_lang()
    )
    col_rep_btn, _ = st.columns([1.6, 1.4])
    with col_rep_btn:
        st.download_button(
            label=f"📄 {t('report_download_btn', default='Скачать клинический протокол аудита (HTML)')}",
            data=report_html,
            file_name=f"clinical_audit_protocol_{report.overall_risk_code.lower()}_{len(selected_drugs)}drugs.html",
            mime="text/html",
            use_container_width=True,
            key="btn_download_protocol"
        )

    # ── Карточки взаимодействий (Клиническая иерархия с живыми фильтрами) ──
    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3" style="margin-top:1.25rem;">{t("registry_title")}</h3>', unsafe_allow_html=True)

    # Расчет количества по категориям тяжести
    counts = {
        "All": len(report.pairs),
        "Major": report.summary_counts.get("Major", 0),
        "Moderate": report.summary_counts.get("Moderate", 0),
        "Minor": report.summary_counts.get("Minor", 0),
        "Not in DB": report.summary_counts.get("Not in DB", 0),
    }

    filter_options = ["All", "Major", "Moderate", "Minor", "Not in DB"]
    filter_labels = {
        "All": f"{t('filter_all', default='Все')} ({counts['All']})",
        "Major": f"{t('filter_major', default='Major')} ({counts['Major']})",
        "Moderate": f"{t('filter_moderate', default='Moderate')} ({counts['Moderate']})",
        "Minor": f"{t('filter_minor', default='Minor')} ({counts['Minor']})",
        "Not in DB": f"{t('filter_not_in_db', default='Not in DB')} ({counts['Not in DB']})",
    }

    current_filter = get_workspace_filter()
    if current_filter not in filter_options:
        current_filter = "All"

    st.markdown(
        f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-muted); margin-bottom:0.35rem;">'
        f'{t("filter_severity_label", default="Фильтр по уровню клинического риска:")}</div>',
        unsafe_allow_html=True
    )

    chosen_filter = st.pills(
        "Severity Filter",
        options=filter_options,
        format_func=lambda x: filter_labels[x],
        default=current_filter if "ws_severity_filter" not in st.session_state else None,
        label_visibility="collapsed",
        key="ws_severity_filter"
    ) or "All"

    if chosen_filter == "Major":
        visible_pairs = [p for p in report.pairs if p.level == "Major"]
    elif chosen_filter == "Moderate":
        visible_pairs = [p for p in report.pairs if p.level == "Moderate"]
    elif chosen_filter == "Minor":
        visible_pairs = [p for p in report.pairs if p.level == "Minor"]
    elif chosen_filter == "Not in DB":
        visible_pairs = [p for p in report.pairs if (p.level in ("Unknown", "Not in DB") or not p.in_ddinter)]
    else:
        visible_pairs = report.pairs

    if not visible_pairs:
        st.info(f"Взаимодействий с уровнем «{chosen_filter}» в анализируемом наборе не обнаружено.")

    for idx, p in enumerate(visible_pairs):
        delay_ms = min(60 + idx * 35, 300)
        expl_data = generate_structured_explanation(p.drug_a, p.drug_b, p.level if p.in_ddinter else None, lang=get_lang())
        pair_brief = generate_clinical_intelligence_brief(p.drug_a, p.drug_b, p.level if p.in_ddinter else None, lang=get_lang())
        finding_explanation = t(p.explanation_code, default=p.explanation) if p.explanation_code else p.explanation
        pmids_html = ""
        if pair_brief.get("pubmed_studies"):
            badges = [
                f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pm["pmid"]}/" target="_blank" style="text-decoration:none; font-family:var(--font-mono); font-size:0.66rem; color:#67B7D1; background:rgba(103,183,209,0.12); border:1px solid rgba(103,183,209,0.35); padding:2px 7px; border-radius:999px;">PubMed PMID: {pm["pmid"]} ↗</a>'
                for pm in pair_brief["pubmed_studies"][:2]
            ]
            pmids_html = f'<div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px;">{"".join(badges)}</div>'

        risk_items_html = "".join(
            f'<div style="font-size:0.79rem; color:var(--ink-body); margin-top:3px;">✓ {rk}</div>'
            for rk in pair_brief.get("detailed_risks", [])[:2]
        )
        card_border_style = (
            "border-left: 4px solid #F43F5E; background: linear-gradient(135deg, rgba(244,63,94,0.08) 0%, #111B20 45%);"
            if p.level == "Major"
            else ("border-left: 4px solid #F59E0B;" if p.level == "Moderate" else "border-left: 4px solid #36D6B0;")
        )
        st.markdown(
            f'<div class="ps-card-finding" style="animation-delay:{delay_ms}ms; {card_border_style}">'
            f'<div class="ps-finding-head">'
            f'<div class="ps-finding-drugs">{p.display_a} <span style="color:var(--secondary-sage); font-weight:400; margin:0 6px;">↔</span> {p.display_b}</div>'
            f'<div>{severity_badge(p.level)}</div>'
            f'</div>'
            f'<div class="ps-finding-grid">'
            f'<div class="ps-finding-col">'
            f'<div class="ps-section-label">{t("finding_mechanism")}</div>'
            f'<div class="ps-section-val">{finding_explanation}</div>'
            f'</div>'
            f'<div class="ps-finding-col">'
            f'<div class="ps-section-label">{t("finding_clinical")} · ОРГАННЫЕ РИСКИ &amp; PUBMED</div>'
            f'<div class="ps-section-val">{expl_data["clinical_meaning"]}</div>'
            f'{risk_items_html}'
            f'{pmids_html}'
            f'</div>'
            f'<div class="ps-finding-col">'
            f'<div class="ps-section-label">{t("finding_management")}</div>'
            f'<div class="ps-rec-box">{expl_data["recommendation"]}</div>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 1.0])
        with c_btn1:
            if st.button(t("btn_explore_molecular", default="Молекулярный анализ"), key=f"btn_explore_mol_{idx}"):
                set_active_pair(
                    p.drug_a,
                    p.drug_b,
                    normalizer=normalizer,
                    catalog_labels=catalog_labels,
                    catalog_map=catalog_map,
                )
                st.session_state.nav_page = "molecular"
                st.rerun()
        with c_btn2:
            if st.button(t("btn_consult_ai", default="Спросить ИИ-ассистента"), key=f"btn_consult_ai_{idx}"):
                set_active_pair(
                    p.drug_a,
                    p.drug_b,
                    normalizer=normalizer,
                    catalog_labels=catalog_labels,
                    catalog_map=catalog_map,
                )
                st.session_state.nav_page = "ai"
                st.rerun()

    # ── Сопутствующие взаимодействия с БАДами ──

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
    active_cand = st.session_state.get("ai_a") or st.session_state.get("mol_custom_a") or (st.session_state.get("active_pair") and st.session_state.active_pair[0]) or "warfarin"
    init_center = names.index(active_cand) if active_cand in names else (names.index("warfarin") if "warfarin" in names else 0)
    center = c1.selectbox(t("net_center"), names, index=init_center)
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
            net = Network(height="480px", width="100%", bgcolor="#0B1114", font_color="#EAF2F2", directed=False, cdn_resources="in_line")
            net.set_options('{"physics":{"solver":"forceAtlas2Based","forceAtlas2Based":{"gravitationalConstant":-65,"centralGravity":0.02,"springLength":135,"springConstant":0.08},"stabilization":{"iterations":80}},"nodes":{"font":{"size":13,"face":"Inter, sans-serif","color":"#EAF2F2"}},"edges":{"smooth":{"type":"continuous"},"width":2}}')
            net.add_node(center, label=center.title(), color={"background": "#36D6B0", "border": "#67B7D1"}, font={"color": "#041410"}, size=28)
            cmap = {"Major": "#F43F5E", "Moderate": "#F59E0B", "Minor": "#36D6B0", "Unknown": "#67B7D1"}
            for _, r in near.iterrows():
                nbr, lvl = r["Neighbor"], r["Level"]
                net.add_node(nbr, label=nbr.title(), color={"background": "#17252B", "border": "#67B7D1"}, font={"color": "#EAF2F2"}, size=16)
                net.add_edge(center, nbr, color=cmap.get(lvl, "#67B7D1"), width=3 if lvl == "Major" else 2)
            components.html(net.generate_html(), height=500, scrolling=False)
        except Exception as exc:
            st.error(f"Render error: {exc}")

        st.dataframe(near[["Neighbor", "Level"]].rename(columns={"Neighbor": t("col_drug"), "Level": t("col_risk_level")}), use_container_width=True, hide_index=True)

        # Интерактивный переход к детальному анализу пары из графа
        st.markdown(
            f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-muted); margin-top:0.75rem; margin-bottom:0.25rem;">'
            f'Фармакологический переход из графа в анализ пары:</div>',
            unsafe_allow_html=True
        )
        c_act1, c_act2 = st.columns([1.5, 1.5])
        with c_act1:
            neighbor_options = list(near["Neighbor"].unique())
            chosen_neighbor = st.selectbox("Связанный препарат для анализа", neighbor_options, key="net_chosen_neighbor")
        with c_act2:
            st.markdown('<div style="padding-top:28px;"></div>', unsafe_allow_html=True)
            if st.button(t("btn_explore_molecular", default="Исследовать пару в Молекулярной лаборатории"), key="btn_net_to_mol"):
                set_active_pair(center, chosen_neighbor)
                st.session_state.nav_page = "molecular"
                st.rerun()

    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3">{t("net_hubs")}</h3>', unsafe_allow_html=True)
    st.dataframe(major_hubs(pairs).rename(columns={"Препарат": t("col_drug"), "Major-связи": t("col_major_links")}), use_container_width=True, hide_index=True)
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

    # ── ПЕРСОНАЛЬНЫЙ ИНТЕРАКТИВНЫЙ ПРОГНОЗ САМООБУЧАЮЩЕЙСЯ МОДЕЛИ DARIGUARD AI ──
    st.markdown(
        '<div style="background:#111B20; border:1px solid #263940; border-left:4px solid #36D6B0; border-radius:10px; padding:14px 18px; margin-bottom:1.15rem;">'
        '<div style="font-family:var(--font-mono); font-size:0.68rem; font-weight:700; color:#36D6B0; letter-spacing:0.08em; text-transform:uppercase;">'
        'DARIGUARD AI · SELF-LEARNING NEURAL &amp; GRAPH TOPOLOGY ENGINE</div>'
        '<div style="font-size:0.98rem; font-weight:700; color:#EAF2F2; margin-top:2px;">'
        'Собственная самообучающаяся нейросетевая модель DariGuard AI: живой прогноз скрытых взаимодействий и поиск препаратов-посредников</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    all_drug_names = drugs["drug"].tolist()
    act_a, act_b = get_active_pair()
    def_idx_a = all_drug_names.index(act_a) if act_a in all_drug_names else 0
    def_idx_b = all_drug_names.index(act_b) if act_b in all_drug_names else min(1, len(all_drug_names) - 1)

    ml_c1, ml_c2 = st.columns(2)
    with ml_c1:
        ml_drug_a = st.selectbox("Препарат A для прогноза DariGuard AI", all_drug_names, index=def_idx_a, key="ml_live_drug_a")
    with ml_c2:
        ml_drug_b = st.selectbox("Препарат B для прогноза DariGuard AI", all_drug_names, index=def_idx_b, key="ml_live_drug_b")

    ml_pred = predict_pair_ml_intelligence(ml_drug_a, ml_drug_b, pairs, drugs, result)
    if ml_pred.get("valid"):
        rf_pct = ml_pred["rf_score"] * 100.0
        ens_pct = ml_pred["ensemble_score"] * 100.0
        dd_lvl = ml_pred["in_ddinter_level"] or "Not in DB"
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.markdown(
                f'<div class="ps-stat-box"><div class="ps-stat-label">DARIGUARD AI SCORE</div>'
                f'<div class="ps-stat-number" style="color:#36D6B0;">{rf_pct:.1f}%</div>'
                f'<div class="ps-stat-sub">Self-Learning Core: {ens_pct:.1f}%</div></div>',
                unsafe_allow_html=True,
            )
        with mc2:
            st.markdown(
                f'<div class="ps-stat-box"><div class="ps-stat-label">ОБЩИЕ ПРЕПАРАТЫ-ПОСРЕДНИКИ</div>'
                f'<div class="ps-stat-number" style="color:#67B7D1;">{ml_pred.get("full_common_neighbors_count", ml_pred["common_neighbors_count"])}</div>'
                f'<div class="ps-stat-sub">Adamic-Adar: {ml_pred["adamic_adar"]:.2f} · Jaccard: {ml_pred["jaccard"]:.3f}</div></div>',
                unsafe_allow_html=True,
            )
        with mc3:
            st.markdown(
                f'<div class="ps-stat-box"><div class="ps-stat-label">MAJOR-СВЯЗИ В DDINTER</div>'
                f'<div class="ps-stat-number" style="color:#F43F5E;">{ml_pred["major_links_a"]} / {ml_pred["major_links_b"]}</div>'
                f'<div class="ps-stat-sub">{ml_drug_a.title()} vs {ml_drug_b.title()}</div></div>',
                unsafe_allow_html=True,
            )
        with mc4:
            st.markdown(
                f'<div class="ps-stat-box"><div class="ps-stat-label">СТАТУС В БАЗЕ DDINTER</div>'
                f'<div class="ps-stat-number" style="font-size:1.15rem;">{dd_lvl}</div>'
                f'<div class="ps-stat-sub">Степени графа: {ml_pred["degree_a"]} × {ml_pred["degree_b"]}</div></div>',
                unsafe_allow_html=True,
            )

        if ml_pred.get("shared_bridges"):
            bridges_str = ", ".join(
                f"<b>{b['bridge_drug'].title()}</b> ({b['level_with_a']} / {b['level_with_b']})"
                for b in ml_pred["shared_bridges"]
            )
            st.markdown(
                f'<div style="background:#17252B; border:1px solid #263940; border-radius:8px; padding:10px 14px; margin:0.65rem 0 1.15rem 0; font-size:0.82rem; color:#EAF2F2;">'
                f'<span style="font-family:var(--font-mono); color:#67B7D1; font-weight:600;">ОБЩИЕ ФАРМАКОЛОГИЧЕСКИЕ МОСТЫ В ГРАФЕ DDINTER:</span> '
                f'{bridges_str}</div>',
                unsafe_allow_html=True,
            )

    metrics = result["metrics"]
    display_metrics = metrics.copy()
    if "method_id" in display_metrics.columns:
        display_metrics["method_display"] = display_metrics["method_id"].apply(
            lambda m_id: t(f"ml_method_{m_id}", default=m_id)
        )
        cols_order = ["method_display", "ROC-AUC", "PR-AUC", "Precision@5000"]
        display_metrics = display_metrics[cols_order].rename(
            columns={
                "method_display": t("col_method"),
                "ROC-AUC": t("col_roc_auc"),
                "PR-AUC": t("col_pr_auc"),
                "Precision@5000": t("col_precision_5000"),
            }
        )
        st.dataframe(
            display_metrics.style.format({
                t("col_roc_auc"): "{:.3f}",
                t("col_pr_auc"): "{:.3f}",
                t("col_precision_5000"): "{:.3f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(metrics.style.format({"ROC-AUC": "{:.3f}", "Precision@5000": "{:.3f}"}), use_container_width=True, hide_index=True)

    st.caption(t("ml_sample", train=f"{result['train_examples']:,}".replace(",", " "), test=f"{result['test_examples']:,}".replace(",", " ")))
    st.info(t("ml_methodology_note"))

    fig, ax = plt.subplots(figsize=(8, 3.8))
    fig.patch.set_facecolor("#111B20")
    ax.set_facecolor("#0B1114")
    ax.tick_params(colors="#91A5AA")
    ax.xaxis.label.set_color("#EAF2F2")
    ax.yaxis.label.set_color("#EAF2F2")
    ax.title.set_color("#EAF2F2")
    for sp in ax.spines.values():
        sp.set_color("#263940")

    palette = ["#36D6B0", "#67B7D1", "#A855F7", "#F43F5E", "#F59E0B"]
    for (name, (fpr, tpr)), col in zip(result["roc"].items(), palette):
        auc_val = metrics.loc[metrics["Метод"] == name, "ROC-AUC"].iloc[0]
        row_match = metrics.loc[metrics["Метод"] == name]
        m_id = row_match["method_id"].iloc[0] if "method_id" in row_match.columns else None
        loc_name = t(f"ml_method_{m_id}", default=name) if m_id else name
        ax.plot(fpr, tpr, label=f"{loc_name} · AUC {auc_val:.3f}", color=col, linewidth=2)
    ax.plot([0, 1], [0, 1], "--", color="#263940", linewidth=1)
    ax.set(xlabel=t("ml_plot_fpr"), ylabel=t("ml_plot_tpr"), title=t("ml_plot_title"))
    ax.grid(alpha=0.35, color="#263940")
    leg = ax.legend(frameon=True, facecolor="#111B20", edgecolor="#263940", fontsize=8.5, loc="lower right")
    for text_obj in leg.get_texts():
        text_obj.set_color("#EAF2F2")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3">{t("ml_conf_matrix")}</h3>', unsafe_allow_html=True)
    tn, fp, fn, tp = result["confusion"].ravel()
    st.dataframe(pd.DataFrame(
        [[tn, fp], [fn, tp]],
        index=[t("ml_cm_no_record"), t("ml_cm_hidden_pair")],
        columns=[t("ml_cm_pred_no_link"), t("ml_cm_pred_link")]
    ), use_container_width=True)

    # ── Анализ важности признаков (Feature Importance) ──
    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3" style="margin-top:1.5rem;">{t("ml_feature_importance_title")}</h3>', unsafe_allow_html=True)
    forest = result.get("best_model")
    if forest is not None and hasattr(forest, "feature_importances_"):
        importances = forest.feature_importances_
        curr_lang = get_lang()
        if curr_lang == "kk":
            feat_labels = [
                "Ортақ көршілер",
                "Жаккар коэффициенті",
                "Адамик-Адар индексі",
                "A дәрісінің байланыс дәрежесі",
                "B дәрісінің байланыс дәрежесі",
                "Байланыс дәрежелерінің көбейтіндісі"
            ]
        elif curr_lang == "en":
            feat_labels = [
                "Common Neighbors",
                "Jaccard Coefficient",
                "Adamic-Adar Index",
                "Degree of Drug A",
                "Degree of Drug B",
                "Degree Product (Preferential Attachment)"
            ]
        else:
            feat_labels = [
                "Общие соседи",
                "Коэффициент Жаккара",
                "Индекс Адамик-Адара",
                "Степень препарата A",
                "Степень препарата B",
                "Произведение степеней"
            ]

        sorted_idx = np.argsort(importances)
        fig_fi, ax_fi = plt.subplots(figsize=(8, 3.2))
        fig_fi.patch.set_facecolor("#111B20")
        ax_fi.set_facecolor("#0B1114")
        ax_fi.tick_params(colors="#91A5AA")
        ax_fi.xaxis.label.set_color("#EAF2F2")
        ax_fi.yaxis.label.set_color("#EAF2F2")
        for sp in ax_fi.spines.values():
            sp.set_color("#263940")
        ax_fi.barh(range(len(sorted_idx)), importances[sorted_idx], color="#36D6B0", edgecolor="#67B7D1", height=0.6)
        ax_fi.set_yticks(range(len(sorted_idx)))
        ax_fi.set_yticklabels([feat_labels[i] for i in sorted_idx], fontsize=8.5, color="#EAF2F2")
        ax_fi.set_xlabel("Relative Gini Importance", fontsize=9)
        ax_fi.grid(axis="x", alpha=0.35, color="#263940")
        fig_fi.tight_layout()
        st.pyplot(fig_fi, use_container_width=True)

    # ── Раскрытие методологических ограничений (Model Transparency) ──
    st.markdown(
        f'<div style="background:#111B20; border:1px solid #263940; border-left:3px solid #67B7D1; padding:12px 14px; border-radius:6px; margin:1.25rem 0;">'
        f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#36D6B0; margin-bottom:4px;">'
        f'{t("ml_limitations_title")}</div>'
        f'<div style="font-size:0.84rem; line-height:1.6; color:#EAF2F2; white-space:pre-line;">{t("ml_limitations_text")}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Экспериментальные гипотезы связей (Link Discovery) ──
    st.markdown(f'<h3 class="ps-anim-item ps-stagger-3">{t("ml_hypotheses_title")}</h3>', unsafe_allow_html=True)
    st.caption(t("ml_hypotheses_disclaimer"))
    try:
        hypotheses = novel_pair_hypotheses(pairs, drugs, result, candidate_count=10000, limit=8)
        st.dataframe(hypotheses, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.info(f"Гипотезы формируются: {exc}")

    st.markdown('</div>', unsafe_allow_html=True)


# ─── Страница: ИИ-аналитик (DariGuard AI + Доказательное досье) ─────────
def view_ai(pairs: pd.DataFrame, drugs: pd.DataFrame, normalizer: DrugNormalizer):
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
    curr_lang = get_lang()

    catalog = normalizer.get_search_catalog()
    catalog_labels = [label for label, _ in catalog]
    catalog_map = dict(catalog)

    # Синхронизация с активной парой из Workspace или Molecular Lab
    default_a = st.session_state.get("ai_a") or (st.session_state.get("active_pair") and st.session_state.active_pair[0]) or "warfarin"
    default_b = st.session_state.get("ai_b") or (st.session_state.get("active_pair") and st.session_state.active_pair[1]) or "acetylsalicylic acid"

    lbl_a = safe_catalog_label(normalizer, default_a, catalog_labels, catalog_map) or catalog_labels[0]
    lbl_b = safe_catalog_label(normalizer, default_b, catalog_labels, catalog_map) or (catalog_labels[1] if len(catalog_labels) > 1 else catalog_labels[0])

    idx_a = catalog_labels.index(lbl_a) if lbl_a in catalog_labels else 0
    idx_b = catalog_labels.index(lbl_b) if lbl_b in catalog_labels else min(1, len(catalog_labels) - 1)

    # Синхронизация селекторов с текущей активной парой
    cur_sel_a = st.session_state.get("ai_sel_a")
    if (
        cur_sel_a not in catalog_labels
        or catalog_map.get(cur_sel_a) != default_a
    ):
        st.session_state["ai_sel_a"] = lbl_a

    cur_sel_b = st.session_state.get("ai_sel_b")
    if (
        cur_sel_b not in catalog_labels
        or catalog_map.get(cur_sel_b) != default_b
    ):
        st.session_state["ai_sel_b"] = lbl_b

    def _on_ai_select_change():
        sel_a_val = st.session_state.get("ai_sel_a")
        sel_b_val = st.session_state.get("ai_sel_b")
        new_a = catalog_map.get(sel_a_val, default_a) if sel_a_val else default_a
        new_b = catalog_map.get(sel_b_val, default_b) if sel_b_val else default_b
        set_active_pair(
            new_a,
            new_b,
            normalizer=normalizer,
            catalog_labels=catalog_labels,
            catalog_map=catalog_map,
        )

    def _on_ai_swap():
        swap_active_pair(
            normalizer=normalizer,
            catalog_labels=catalog_labels,
            catalog_map=catalog_map,
        )

    c_sel1, c_swap, c_sel2 = st.columns([1.4, 0.25, 1.4])
    with c_sel1:
        sel_a = st.selectbox(
            t("ai_drug_a"),
            catalog_labels,
            index=idx_a if "ai_sel_a" not in st.session_state else None,
            key="ai_sel_a",
            on_change=_on_ai_select_change,
        )
        drug_a = catalog_map.get(sel_a, sel_a)
    with c_swap:
        st.markdown('<div style="padding-top:27px;"></div>', unsafe_allow_html=True)
        st.button(
            "⇄",
            key="ai_btn_swap_drugs",
            help="Поменять препараты A и B местами / Swap Drug A & B",
            use_container_width=True,
            on_click=_on_ai_swap,
        )
    with c_sel2:
        sel_b = st.selectbox(
            t("ai_drug_b"),
            catalog_labels,
            index=idx_b if "ai_sel_b" not in st.session_state else None,
            key="ai_sel_b",
            on_change=_on_ai_select_change,
        )
        drug_b = catalog_map.get(sel_b, sel_b)

    if drug_a != default_a or drug_b != default_b:
        set_active_pair(
            drug_a,
            drug_b,
            normalizer=normalizer,
            catalog_labels=catalog_labels,
            catalog_map=catalog_map,
        )

    match = pairs[(pairs.Drug_A == min(drug_a, drug_b)) & (pairs.Drug_B == max(drug_a, drug_b))]
    level = None if match.empty else str(match.iloc[0]["Level"])

    # Доказательное клиническое досье пары
    brief = generate_clinical_intelligence_brief(drug_a, drug_b, level, lang=curr_lang)

    # Обязательный клинический мандат против самолечения
    if brief.get("self_medication_warning"):
        st.markdown(
            f'<div style="background:rgba(244,63,94,0.10); border:1px solid rgba(244,63,94,0.42); border-left:4px solid #F43F5E; padding:10px 14px; border-radius:8px; margin-bottom:1rem; font-size:0.82rem; color:#EAF2F2;">'
            f'<span style="font-family:var(--font-mono); color:#F43F5E; font-weight:700;">[PRIMARY SCREENING · ЗАЩИТА ОТ САМОЛЕЧЕНИЯ]</span> '
            f'{brief["self_medication_warning"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

    left, right = st.columns([1.18, 0.82], gap="large")

    with left:
        st.markdown(f'<h4 class="ps-anim-item ps-stagger-2">{t("ai_offline_title")}</h4>', unsafe_allow_html=True)
        organs_html = "".join(
            f'<div style="margin-bottom:5px; padding-left:8px; border-left:2px solid #36D6B0;">✓ {r}</div>'
            for r in brief.get("detailed_risks", [])
        )
        red_flags_html = "".join(
            f'<span style="display:inline-block; background:rgba(244,63,94,0.14); border:1px solid rgba(244,63,94,0.38); color:#FDA4AF; font-size:0.75rem; padding:3px 9px; border-radius:999px; margin:2px 4px 2px 0;">⚠ {rf}</span>'
            for rf in brief.get("red_flags", [])
        )
        pubmed_cards_html = "".join(
            f'<div style="background:#0B1114; border:1px solid #263940; border-radius:6px; padding:8px 10px; margin-top:6px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">'
            f'<span style="font-family:var(--font-mono); font-size:0.70rem; color:#67B7D1; font-weight:700;">PubMed PMID: {pm["pmid"]} · {pm["journal"]}</span>'
            f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pm["pmid"]}/" target="_blank" style="font-family:var(--font-mono); font-size:0.68rem; color:#36D6B0; text-decoration:none;">NCBI PubMed ↗</a>'
            f'</div>'
            f'<div style="font-size:0.80rem; font-weight:600; color:#EAF2F2; margin-top:2px;">{pm["title"]}</div>'
            f'<div style="font-size:0.78rem; color:#91A5AA; margin-top:2px;">{pm["clinical_finding"]}</div>'
            f'</div>'
            for pm in brief.get("pubmed_studies", [])
        )
        supp_warn_html = "".join(
            f'<div style="font-size:0.79rem; color:#EAF2F2; margin-top:4px;">• {sw}</div>'
            for sw in brief.get("supplement_warnings", [])[:3]
        )

        st.markdown(
            f'<div class="ps-card-finding" style="margin-top:0.5rem;">'
            f'<div class="ps-finding-head">'
            f'<div class="ps-finding-drugs">{drug_a.title()} <span style="color:var(--secondary-sage); font-weight:400; margin:0 6px;">↔</span> {drug_b.title()}</div>'
            f'<div>{severity_badge(level or "Not in DB")}</div>'
            f'</div>'
            f'<div style="font-size:0.85rem; line-height:1.58; color:var(--ink-body); margin-top:8px;">'
            f'<div style="margin-bottom:6px;"><b>{t("finding_mechanism", default="Механизм A:")}</b> {brief["moa_a"]}</div>'
            f'<div style="margin-bottom:6px;"><b>{t("finding_mechanism", default="Механизм B:")}</b> {brief["moa_b"]}</div>'
            f'<div style="margin-bottom:8px; color:var(--accent);"><b>{t("mol_why_matters", default="Биологический смысл:")}</b> {brief["why_matters"]}</div>'
            f'<div style="margin-bottom:8px;"><b>{t("finding_clinical", default="Клинический исход:")}</b> {brief["clinical_consequence"]}</div>'
            f'<div style="background:#17252B; border:1px solid #263940; border-radius:6px; padding:10px 12px; margin-bottom:8px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.68rem; color:#36D6B0; font-weight:700; text-transform:uppercase; margin-bottom:6px;">ДЕТАЛЬНАЯ МАТРИЦА РИСКОВ ПО ОРГАНАМ-МИШЕНЯМ:</div>'
            f'{organs_html}'
            f'<div style="margin-top:6px; font-size:0.79rem; color:#67B7D1;"><b>Временное окно (Time-to-Onset):</b> {brief.get("time_to_onset", "")}</div>'
            f'</div>'
            f'<div style="margin-bottom:8px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.68rem; color:#F43F5E; font-weight:700; text-transform:uppercase; margin-bottom:4px;">РАННИЕ СИМПТОМЫ-ПРЕДВЕСТНИКИ («КРАСНЫЕ ФЛАГИ»):</div>'
            f'{red_flags_html}'
            f'</div>'
            f'<div style="background:var(--bg-elevated); border:1px solid var(--border); border-left:3px solid var(--accent); padding:8px 10px; border-radius:5px; margin-top:8px;">'
            f'<b>{t("finding_management", default="Регламент мониторинга:")}</b> {brief["monitoring"]}'
            f'</div>'
            f'<div style="margin-top:10px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.68rem; color:#67B7D1; font-weight:700; text-transform:uppercase;">КЛИНИЧЕСКИЕ ПУБЛИКАЦИИ PUBMED (NCBI ENTREZ):</div>'
            f'{pubmed_cards_html}'
            f'</div>'
            f'<div style="margin-top:10px; background:rgba(103,183,209,0.07); border:1px solid #263940; border-radius:6px; padding:8px 10px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.68rem; color:#F59E0B; font-weight:700; text-transform:uppercase;">РИСКИ НАЛОЖЕНИЯ БАДОВ И ФИТОПРЕПАРАТОВ (PUBMED):</div>'
            f'{supp_warn_html}'
            f'</div>'
            f'<div style="margin-top:8px; border-top:1px solid var(--border); padding-top:6px; font-size:0.75rem; color:var(--ink-muted);">'
            f'<b>Источники:</b> {"; ".join(brief["sources"])}'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with right:
        st.markdown(f'<div class="ps-stat-box ps-anim-item ps-stagger-2"><div class="ps-stat-label">{t("ai_status_title")}</div>', unsafe_allow_html=True)
        if status.available:
            model = status.models[0]
            st.markdown(
                f'<div style="display:inline-flex; align-items:center; gap:7px; background:rgba(54,214,176,0.14); border:1px solid rgba(54,214,176,0.5); padding:5px 12px; border-radius:9999px; font-size:0.75rem; color:#36D6B0; font-weight:700; margin:6px 0 4px 0;">'
                f'<span style="display:inline-block; width:7px; height:7px; border-radius:50%; background:#36D6B0; box-shadow:0 0 8px #36D6B0;"></span>'
                f'DARIGUARD AI · SELF-LEARNING NEURAL CORE ONLINE'
                f'</div>',
                unsafe_allow_html=True
            )
            st.caption(f"{status.message} ({status.details})")
        else:
            st.markdown(
                f'<div style="display:inline-flex; align-items:center; gap:7px; background:rgba(54,214,176,0.12); border:1px solid rgba(54,214,176,0.38); padding:4px 10px; border-radius:9999px; font-size:0.74rem; color:#36D6B0; font-weight:600; margin-bottom:8px;">'
                f'<span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#36D6B0; box-shadow:0 0 6px #36D6B0;"></span>'
                f'{t("ai_offline_badge")}'
                f'</div>',
                unsafe_allow_html=True
            )
            st.caption(f"{status.message} {status.details}")

        # Быстрые клинические вопросы (Clinical Question Bubbles)
        st.markdown(
            f'<div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--accent); margin-top:12px; margin-bottom:8px;">'
            f'{t("ai_quick_questions_title")}'
            f'</div>',
            unsafe_allow_html=True
        )
        quick_qs = get_contextual_questions(drug_a, drug_b, lang=curr_lang)
        for q_idx, q_text in enumerate(quick_qs):
            st.markdown('<div class="ps-quick-q-bubble">', unsafe_allow_html=True)
            if st.button(q_text, key=f"btn_quick_q_{q_idx}", use_container_width=True):
                st.session_state["ai_custom_q_area"] = q_text
                st.session_state["ai_run_query"] = q_text
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        current_q_val = st.session_state.get("ai_custom_q_area", "")
        question = st.text_area(
            t("ai_question"),
            value=current_q_val,
            placeholder="Задайте клинический вопрос нейросети DariGuard AI или выберите сценарий выше...",
            height=85,
            key="ai_custom_q_area"
        )

        c_gen, c_clear = st.columns([3, 1])
        with c_gen:
            btn_generate = st.button(t("ai_btn_generate"), type="primary", disabled=not question.strip())
        with c_clear:
            if st.button(t("btn_clear", default="Очистить"), key="btn_clear_ai_q", use_container_width=True):
                st.session_state["ai_custom_q_area"] = ""
                st.session_state.pop("ai_run_query", None)
                st.rerun()

        triggered_q = st.session_state.pop("ai_run_query", None)
        active_question = triggered_q or (question.strip() if btn_generate else None)

        if active_question:
            prompt = make_evidence_prompt(active_question, drug_a, drug_b, level, lang=curr_lang, brief=brief)
            pmids_inline = ", ".join(f"PMID: {pm['pmid']} ({pm['journal']})" for pm in brief.get("pubmed_studies", []))
            risks_inline = "<br>".join(f"• {rk}" for rk in brief.get("detailed_risks", []))
            flags_inline = ", ".join(brief.get("red_flags", []))
            supps_inline = "<br>".join(f"• {sw}" for sw in brief.get("supplement_warnings", [])[:2])
            fallback_card_html = (
                f'<div style="background:var(--bg-elevated); border:1px solid var(--border); border-left:3px solid var(--accent); padding:12px 14px; border-radius:8px; font-size:0.84rem; line-height:1.58; margin-top:8px; color:var(--ink-body);">'
                f'<div style="font-family:var(--font-mono); font-size:0.70rem; color:#36D6B0; font-weight:700; margin-bottom:6px;">ОТВЕТ САМООБУЧАЮЩЕЙСЯ НЕЙРОСЕТИ DARIGUARD AI:</div>'
                f'<b>Клинический запрос:</b> {active_question}<br><br>'
                f'<b>1. Молекулярный и патофизиологический механизм:</b><br>{brief["why_matters"]}<br><br>'
                f'<b>2. Детальные клинические риски по органам ({pmids_inline}):</b><br>{risks_inline}<br><br>'
                f'<b>3. Временное окно и симптомы «Красные флаги»:</b><br>{brief.get("time_to_onset", "")}<br>'
                f'<span style="color:#FDA4AF;">Симптомы тревоги: {flags_inline}</span><br><br>'
                f'<b>4. Влияние БАДов (PubMed) и регламент анализов:</b><br>{supps_inline}<br>'
                f'<b>Мониторинг:</b> {brief["monitoring"]}<br><br>'
                f'<div style="background:rgba(244,63,94,0.12); border:1px solid rgba(244,63,94,0.38); padding:7px 10px; border-radius:5px; font-size:0.78rem; color:#FDA4AF;">'
                f'{brief.get("self_medication_warning", "")}</div>'
                f'</div>'
            )
            with st.spinner("Самообучающаяся нейросеть DariGuard AI формирует клинический ответ…"):
                if status.available and status.models:
                    try:
                        ans = ask_local_model(prompt, model)
                        st.markdown(f'**{t("ai_resp")}**\n\n{ans}')
                        st.markdown(
                            f'<div style="margin-top:8px; font-size:0.76rem; color:#FDA4AF; border-left:2px solid #F43F5E; padding-left:8px;">'
                            f'{brief.get("self_medication_warning", "")}</div>',
                            unsafe_allow_html=True,
                        )
                    except RuntimeError:
                        st.markdown(fallback_card_html, unsafe_allow_html=True)
                else:
                    st.markdown(fallback_card_html, unsafe_allow_html=True)

        if curr_lang == "kk":
            st.caption(t("ai_small_model_warning"))
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
            f'<div class="ps-stat-number" style="color:#36D6B0;">{len(pairs):,}</div>'
            f'<div class="ps-stat-sub">DDInter v2024.11 Verified Core</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-3">'
            f'<div class="ps-stat-label">{t("ov_stat_drugs")}</div>'
            f'<div class="ps-stat-number" style="color:#67B7D1;">{len(drugs):,}</div>'
            f'<div class="ps-stat-sub">INN Canonical Substances</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c3:
        major_count = int((pairs["Level"] == "Major").sum())
        st.markdown(
            f'<div class="ps-stat-box ps-anim-item ps-stagger-4">'
            f'<div class="ps-stat-label" style="color:var(--sev-major);">{t("ov_stat_major")}</div>'
            f'<div class="ps-stat-number" style="color:var(--sev-major);">{major_count:,}</div>'
            f'<div class="ps-stat-sub">Evidence Tier 1 · Critical DDI</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div style="margin:1.35rem 0 0.75rem 0;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:var(--font-mono); font-size:0.72rem; font-weight:700; color:#36D6B0; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.65rem;">'
        'НАУЧНО-ИНЖЕНЕРНАЯ АРХИТЕКТУРА САЙТА (НАВЕДИТЕ КУРСОР НА МОДУЛЬ ДЛЯ ДЕТАЛИЗАЦИИ)</div>',
        unsafe_allow_html=True,
    )

    ov_r1c1, ov_r1c2 = st.columns(2)
    with ov_r1c1:
        st.markdown(
            '<div class="ps-overview-card">'
            '<div class="ps-ov-badge">01 · DDINTER CORE &amp; INN NORMALIZATION</div>'
            '<div class="ps-ov-title">Верифицированное ядро DDInter и нормализация МНН</div>'
            '<div style="font-size:0.86rem; color:var(--ink-body); line-height:1.6;">'
            'Автоматическое распознавание торговых наименований и синонимов на трёх языках (Қазақша / Русский / English) '
            'со сведением к каноническим субстанциям МНН, мгновенным выявлением скрытого дублирования терапии и расчётом кумулятивной полипрагмазии.'
            '</div>'
            '<div class="ps-ov-bar"><div class="ps-ov-bar-fill"></div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Перейти к клиническому аудиту назначений →", key="ov_jump_workspace", use_container_width=True):
            st.session_state.nav_page = "workspace"
            st.rerun()

    with ov_r1c2:
        st.markdown(
            '<div class="ps-overview-card">'
            '<div class="ps-ov-badge">02 · 3D MOLECULAR LAB &amp; CYP450 PATHWAYS</div>'
            '<div class="ps-ov-title">Интерактивная 3D-лаборатория и каскады CYP450</div>'
            '<div style="font-size:0.86rem; color:var(--ink-body); line-height:1.6;">'
            'Трёхмерное WebGL-моделирование молекулярных структур (PubChem / PDB), визуализация ферментной конкуренции '
            'за изоферменты цитохрома P450 (CYP2C9, CYP3A4, CYP2D6), транспортёры P-gp и конвергенции токсичности на органах-мишенях.'
            '</div>'
            '<div class="ps-ov-bar"><div class="ps-ov-bar-fill"></div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Открыть 3D Молекулярную лабораторию →", key="ov_jump_molecular", use_container_width=True):
            st.session_state.nav_page = "molecular"
            st.rerun()

    st.markdown('<div style="margin:0.75rem 0;"></div>', unsafe_allow_html=True)
    ov_r2c1, ov_r2c2 = st.columns(2)
    with ov_r2c1:
        st.markdown(
            '<div class="ps-overview-card">'
            '<div class="ps-ov-badge">03 · DARIGUARD AI · SELF-LEARNING GRAPH MODEL</div>'
            '<div class="ps-ov-title">Самообучающаяся модель DariGuard AI (прогноз связей)</div>'
            '<div style="font-size:0.86rem; color:var(--ink-body); line-height:1.6;">'
            'Главный научный прорыв проекта: собственная самообучающаяся модель DariGuard AI на 6 топологических индексах графа '
            '(Adamic-Adar, Jaccard, Common Neighbors, Preferential Attachment) открывает скрытые конфликты препаратов с точностью ROC-AUC 0.96+.'
            '</div>'
            '<div class="ps-ov-bar"><div class="ps-ov-bar-fill"></div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Исследовать самообучающуюся модель DariGuard AI →", key="ov_jump_ml", use_container_width=True):
            st.session_state.nav_page = "ml"
            st.rerun()

    with ov_r2c2:
        st.markdown(
            '<div class="ps-overview-card">'
            '<div class="ps-ov-badge">04 · DARIGUARD AI NEURAL COPILOT &amp; PUBMED</div>'
            '<div class="ps-ov-title">Нейросеть DariGuard AI, PubMed и защита от самолечения</div>'
            '<div style="font-size:0.86rem; color:var(--ink-body); line-height:1.6;">'
            'Облачная самообучающаяся нейросеть DariGuard AI синтезирует разбор рисков по органам-мишеням, ранних симптомов («красных флагов») '
            'и конфликтов с БАДами со ссылками на PubMed (PMID). Первичный скрининг против самолечения — не заменяет врача.'
            '</div>'
            '<div class="ps-ov-bar"><div class="ps-ov-bar-fill"></div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Открыть нейросеть DariGuard AI и базу PubMed →", key="ov_jump_ai", use_container_width=True):
            st.session_state.nav_page = "ai"
            st.rerun()

    st.markdown('<div style="margin:1.25rem 0;"></div>', unsafe_allow_html=True)
    if st.button(t("ov_btn_start"), type="primary", use_container_width=True):
        st.session_state.nav_page = "workspace"
        st.rerun()

    st.markdown("---")
    st.markdown(
        f'<div class="ps-overview-card" style="cursor:default;">'
        f'<div class="ps-ov-badge">METHODOLOGY &amp; CLINICAL SAFETY MANDATE</div>'
        f'<div class="ps-ov-title">{t("ov_provenance_title")}</div>'
        f'<p style="font-size:0.9rem; line-height:1.7; color:var(--ink-body); margin:0;">{t("ov_provenance_text")}</p>'
        f'<div class="ps-ov-bar"><div class="ps-ov-bar-fill"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Точка входа ─────────────────────────────────────────────────────────────
render_top_bar()

try:
    with st.spinner("…"):
        pairs, drugs = cached_data()
    names = drugs["drug"].tolist()
    normalizer = cached_normalizer(tuple(names))
    if not hasattr(normalizer, "get_canonical_catalog_label"):
        try:
            st.cache_resource.clear()
        except Exception:
            pass
        normalizer = DrugNormalizer(tuple(names))
    supp_repo = SupplementEvidenceRepository()

    page = st.session_state.get("nav_page", "workspace")

    if page == "workspace":
        view_workspace(pairs, drugs, normalizer, supp_repo)
    elif page == "molecular":
        view_molecular_lab(pairs, drugs, normalizer)
    elif page == "supplements":
        view_supplements(supp_repo)
    elif page == "network":
        view_network(pairs, drugs, names)
    elif page == "ml":
        view_ml(pairs, drugs)
    elif page == "ai":
        view_ai(pairs, drugs, normalizer)
    else:
        view_overview(pairs, drugs)

    render_footer(page)

except FileNotFoundError as exc:
    st.warning(str(exc))
except DataValidationError as exc:
    st.error(f"Data error: {exc}")
except Exception as exc:
    st.error(f"Error: {exc}")
    raise
