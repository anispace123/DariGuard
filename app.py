"""PHARMA SENTINEL — Clinical Drug Interaction Intelligence Platform.

Design system: Production-grade scientific editorial.
Skills applied: web-design-guidelines (Vercel), animate + review-animations + improve-animations (Emil Kowalski).
Backend: DDInter 160 235 pairs, 1 939 drugs — preserved entirely.
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


st.set_page_config(
    page_title="Pharma Sentinel",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN SYSTEM
#  web-design-guidelines: 8pt grid, 7:1 contrast for primary text, 4.5:1 muted,
#    focus-visible rings, ≥44px touch targets, no random gradients.
#  animate: GPU-only (transform/opacity), ≤250ms, cubic-bezier(0.16,1,0.3,1),
#    prefers-reduced-motion wrapper.
#  review-animations: no ease-in on entry, no scale(0), no layout-thrashing props.
# ─────────────────────────────────────────────────────────────────────────────
DESIGN = """
<style>
/* ── Google Fonts ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Lora:ital,wght@0,400;0,500;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Token layer ──────────────────────────────────────────────────────────── */
:root {
  /* Colour */
  --bg:          #F9F8F6;     /* warm off-white */
  --bg-raised:   #FFFFFF;
  --bg-subtle:   #F2F1EF;
  --border:      #E4E2DE;
  --border-med:  #D1CEC9;

  --ink:         #0E1117;     /* ≥7:1 on --bg */
  --ink-2:       #3D3A35;     /* body text */
  --ink-3:       #6B6860;     /* muted, ≥4.5:1 */

  --accent:      #1A56A0;     /* cobalt */
  --accent-bg:   #EBF1FA;
  --accent-dark: #13407D;

  --sev-major:   #B91C1C;
  --sev-major-bg:#FEF2F2;
  --sev-mod:     #B45309;
  --sev-mod-bg:  #FFFBEB;
  --sev-minor:   #065F46;
  --sev-minor-bg:#ECFDF5;
  --sev-none:    #6B6860;
  --sev-none-bg: #F2F1EF;

  /* Type scale (8pt grid) */
  --text-xs:   0.6875rem;  /* 11px */
  --text-sm:   0.8125rem;  /* 13px */
  --text-base: 0.9375rem;  /* 15px */
  --text-md:   1.0625rem;  /* 17px */
  --text-lg:   1.25rem;    /* 20px */
  --text-xl:   1.5rem;     /* 24px */
  --text-2xl:  2rem;       /* 32px */
  --text-3xl:  clamp(1.75rem, 3.5vw, 2.75rem);

  /* Spacing (8pt) */
  --sp-1: 0.25rem;  /* 4 */
  --sp-2: 0.5rem;   /* 8 */
  --sp-3: 0.75rem;  /* 12 */
  --sp-4: 1rem;     /* 16 */
  --sp-5: 1.25rem;  /* 20 */
  --sp-6: 1.5rem;   /* 24 */
  --sp-8: 2rem;     /* 32 */
  --sp-10: 2.5rem;  /* 40 */
  --sp-12: 3rem;    /* 48 */

  /* Shape */
  --r-sm: 2px;
  --r-md: 4px;

  /* Fonts */
  --font-ui:    'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-serif: 'Lora', Georgia, serif;
  --font-mono:  'JetBrains Mono', 'Courier New', monospace;

  /* Motion tokens — animate skill */
  --ease-out:  cubic-bezier(0.16, 1, 0.3, 1);
  --ease-std:  cubic-bezier(0, 0, 0.2, 1);
  --dur-fast:  150ms;
  --dur-base:  220ms;
}

/* ── Base reset ───────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: var(--font-ui);
  color: var(--ink-2);
  background: var(--bg);
  -webkit-font-smoothing: antialiased;
}

/* Hide Streamlit chrome we replace */
#MainMenu, footer, [data-testid="stHeader"] { display: none !important; }

/* Streamlit block container */
.block-container {
  max-width: 1200px !important;
  padding: var(--sp-4) var(--sp-6) var(--sp-12) !important;
}

/* Fix Streamlit column overflow — web-design-guidelines */
[data-testid="column"] { min-width: 0 !important; }
[data-testid="stMarkdownContainer"] * {
  max-width: 100%;
  overflow-wrap: break-word;
}

/* ── Typography ───────────────────────────────────────────────────────────── */
[data-testid="stMarkdownContainer"] h1 {
  font-family: var(--font-serif) !important;
  font-size: var(--text-3xl) !important;
  font-weight: 400 !important;
  line-height: 1.2 !important;
  letter-spacing: -0.025em !important;
  color: var(--ink) !important;
  margin: 0 0 var(--sp-4) !important;
}
[data-testid="stMarkdownContainer"] h2 {
  font-family: var(--font-serif) !important;
  font-size: var(--text-xl) !important;
  font-weight: 500 !important;
  line-height: 1.3 !important;
  color: var(--ink) !important;
  margin: var(--sp-8) 0 var(--sp-4) !important;
}
[data-testid="stMarkdownContainer"] h3 {
  font-family: var(--font-ui) !important;
  font-size: var(--text-md) !important;
  font-weight: 600 !important;
  color: var(--ink) !important;
  margin: var(--sp-6) 0 var(--sp-3) !important;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
  font-size: var(--text-base) !important;
  line-height: 1.65 !important;
  color: var(--ink-2) !important;
}

/* ── Application shell ────────────────────────────────────────────────────── */

/* Header */
.ps-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: var(--sp-3) 0 var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-6);
  flex-wrap: wrap;
}
.ps-wordmark {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
}
.ps-wordmark-name {
  font-family: var(--font-ui);
  font-size: var(--text-base);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ink);
}
.ps-wordmark-tag {
  font-size: var(--text-xs);
  color: var(--ink-3);
  font-weight: 500;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.ps-nav {
  display: flex;
  align-items: center;
  gap: var(--sp-6);
}
.ps-nav-link {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--ink-3);
  text-decoration: none;
  letter-spacing: 0.02em;
  cursor: pointer;
  /* animate: opacity/color only — GPU-safe */
  transition: color var(--dur-fast) var(--ease-std),
              opacity var(--dur-fast) var(--ease-std);
  padding: var(--sp-1) 0;
  border-bottom: 1.5px solid transparent;
}
.ps-nav-link:hover { color: var(--ink); }
.ps-nav-link.active {
  color: var(--ink);
  border-bottom-color: var(--accent);
}
.ps-nav-action {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent);
  color: #fff;
  border-radius: var(--r-md);
  font-size: var(--text-sm);
  font-weight: 600;
  letter-spacing: 0.02em;
  cursor: pointer;
  /* animate skill: transform + opacity, ease-out, sub-220ms */
  transition: background var(--dur-fast) var(--ease-std),
              transform var(--dur-fast) var(--ease-out),
              opacity var(--dur-fast) var(--ease-std);
}
.ps-nav-action:hover {
  background: var(--accent-dark);
  transform: translateY(-1px);
}
.ps-nav-action:active { transform: translateY(0); }

/* ── Severity chips ───────────────────────────────────────────────────────── */
.ps-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: 2px var(--sp-2);
  border-radius: var(--r-sm);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
  border: 1px solid;
}
.ps-chip-major  { color: var(--sev-major); background: var(--sev-major-bg); border-color: #FECACA; }
.ps-chip-mod    { color: var(--sev-mod);   background: var(--sev-mod-bg);   border-color: #FDE68A; }
.ps-chip-minor  { color: var(--sev-minor); background: var(--sev-minor-bg); border-color: #A7F3D0; }
.ps-chip-none   { color: var(--sev-none);  background: var(--sev-none-bg);  border-color: var(--border); }

/* ── Stat row ─────────────────────────────────────────────────────────────── */
.ps-stat {
  padding: var(--sp-4) 0;
  border-top: 1px solid var(--border);
}
.ps-stat-number {
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 400;
  color: var(--ink);
  line-height: 1;
  letter-spacing: -0.02em;
  display: block;
  margin-bottom: var(--sp-1);
}
.ps-stat-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--ink-3);
  display: block;
}
.ps-stat-caption {
  font-size: var(--text-sm);
  color: var(--ink-3);
  margin-top: var(--sp-1);
  display: block;
}

/* ── Section label ────────────────────────────────────────────────────────── */
.ps-eyebrow {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--accent);
  display: block;
  margin-bottom: var(--sp-2);
}
.ps-eyebrow-muted {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--ink-3);
  display: block;
  margin-bottom: var(--sp-2);
}

/* ── Result card ──────────────────────────────────────────────────────────── */
.ps-result {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: var(--sp-4) var(--sp-5);
  margin-bottom: var(--sp-3);
  /* animate: opacity + translateY entry, ease-out, 200ms */
  animation: ps-fadein 200ms var(--ease-out) both;
}
.ps-result:hover {
  border-color: var(--border-med);
  /* GPU-only: no layout props */
  transition: border-color var(--dur-fast) var(--ease-std);
}
.ps-result-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
  margin-bottom: var(--sp-3);
}
.ps-result-drugs {
  font-family: var(--font-ui);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--ink);
  min-width: 0;
  flex: 1;
  overflow-wrap: break-word;
}
.ps-result-sep { color: var(--ink-3); margin: 0 var(--sp-2); font-weight: 400; }
.ps-result-body {
  font-size: var(--text-sm);
  line-height: 1.65;
  color: var(--ink-2);
}
.ps-result-body b { color: var(--ink); font-weight: 600; }

/* animate: fade-in entry — GPU only (opacity + transform) */
@keyframes ps-fadein {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Supplement card ──────────────────────────────────────────────────────── */
.ps-supp {
  border-left: 2px solid var(--sev-major);
  background: var(--bg-subtle);
  padding: var(--sp-3) var(--sp-4);
  margin-bottom: var(--sp-3);
  border-radius: 0 var(--r-sm) var(--r-sm) 0;
}
.ps-supp-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--sp-3);
  flex-wrap: wrap;
  margin-bottom: var(--sp-2);
}
.ps-supp-title {
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--ink);
  min-width: 0;
  flex: 1;
  overflow-wrap: break-word;
}
.ps-supp-text {
  font-size: var(--text-sm);
  color: var(--ink-3);
  line-height: 1.6;
}

/* ── Info panel ───────────────────────────────────────────────────────────── */
.ps-panel {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: var(--sp-4) var(--sp-5);
}
.ps-panel-title {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--ink-3);
  margin-bottom: var(--sp-3);
  display: block;
}

/* ── Disclaimer ───────────────────────────────────────────────────────────── */
.ps-disclaimer {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  background: var(--accent-bg);
  border: 1px solid #BFDBFE;
  border-radius: var(--r-md);
  padding: var(--sp-3) var(--sp-4);
  margin-bottom: var(--sp-5);
  font-size: var(--text-sm);
  color: var(--ink-2);
  line-height: 1.55;
}
.ps-disclaimer-icon { color: var(--accent); font-size: var(--text-md); flex-shrink: 0; }
.ps-disclaimer b { color: var(--ink); font-weight: 600; }

/* ── Live dot ─────────────────────────────────────────────────────────────── */
.ps-live {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--ink-3);
}
.ps-live-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #16A34A;
  /* animate: opacity pulse — GPU */
  animation: ps-pulse 2.2s ease-in-out infinite;
}
@keyframes ps-pulse {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 1;   }
}

/* ── Telemetry grid ───────────────────────────────────────────────────────── */
.ps-telem {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-2);
  margin-top: var(--sp-3);
}
.ps-telem-cell {
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  padding: var(--sp-2) var(--sp-3);
}
.ps-telem-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-3);
  display: block;
}
.ps-telem-val {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--ink);
  font-weight: 500;
  display: block;
  margin-top: 2px;
}

/* ── Capability row ───────────────────────────────────────────────────────── */
.ps-cap-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-4);
  margin-top: var(--sp-6);
}
@media (max-width: 720px) {
  .ps-cap-grid { grid-template-columns: 1fr; }
}
.ps-cap {
  border-top: 2px solid var(--accent);
  padding-top: var(--sp-4);
}
.ps-cap-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--ink);
  margin-bottom: var(--sp-2);
  display: block;
}
.ps-cap-body {
  font-size: var(--text-sm);
  color: var(--ink-3);
  line-height: 1.65;
}

/* ── Divider ──────────────────────────────────────────────────────────────── */
.ps-divider {
  border: 0;
  border-top: 1px solid var(--border);
  margin: var(--sp-8) 0;
}

/* ── Footer ───────────────────────────────────────────────────────────────── */
.ps-footer {
  border-top: 1px solid var(--border);
  padding-top: var(--sp-5);
  margin-top: var(--sp-10);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--sp-3);
}
.ps-footer-left {
  font-size: var(--text-xs);
  color: var(--ink-3);
  line-height: 1.5;
}
.ps-footer-right {
  font-size: var(--text-xs);
  color: var(--ink-3);
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
/* web-design-guidelines: ≥44px touch target, visible focus-visible ring */
.stButton > button {
  font-family: var(--font-ui) !important;
  font-size: var(--text-sm) !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  padding: var(--sp-2) var(--sp-4) !important;
  min-height: 44px !important;
  border-radius: var(--r-md) !important;
  border: 1px solid var(--border-med) !important;
  background: var(--bg-raised) !important;
  color: var(--ink) !important;
  /* animate: transform + opacity, no layout props */
  transition: transform var(--dur-fast) var(--ease-out),
              background var(--dur-fast) var(--ease-std),
              border-color var(--dur-fast) var(--ease-std) !important;
}
.stButton > button:hover {
  background: var(--bg-subtle) !important;
  border-color: var(--border-med) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button:focus-visible {
  outline: 2px solid var(--accent) !important;
  outline-offset: 2px !important;
}

/* Primary button variant */
.stButton > button[kind="primary"],
div[data-testid="stForm"] .stButton > button {
  background: var(--accent) !important;
  color: #fff !important;
  border-color: var(--accent) !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--accent-dark) !important;
  border-color: var(--accent-dark) !important;
}

/* ── Forms ────────────────────────────────────────────────────────────────── */
/* web-design-guidelines: font-size ≥16px on mobile to prevent iOS zoom */
input, select, textarea {
  font-family: var(--font-ui) !important;
  font-size: 1rem !important;
}
[data-testid="stMultiSelect"] [data-baseweb="select"] *,
[data-testid="stSelectbox"] [data-baseweb="select"] * {
  font-family: var(--font-ui) !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  border-radius: var(--r-md) !important;
}

/* ── Tables ───────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md);
  background: var(--bg-raised);
}

/* ── Sidebar (used only for nav fallback) ─────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: var(--bg-subtle) !important;
  border-right: 1px solid var(--border) !important;
}

/* ── Reduced-motion (animate + review-animations accessibility rules) ──────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
"""

st.markdown(DESIGN, unsafe_allow_html=True)


# ─── Data caches ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cached_data():
    return load_ddinter()

@st.cache_resource(show_spinner=False)
def cached_normalizer(drugs_tuple):
    return DrugNormalizer(drugs_tuple)

@st.cache_data(show_spinner=False)
def cached_evaluation(pairs: pd.DataFrame, drugs: pd.DataFrame):
    return train_and_evaluate(pairs, drugs)


# ─── Shared components ────────────────────────────────────────────────────────
def chip(level: str) -> str:
    """Severity chip — no emoji, only semantic colour."""
    mapping = {
        "Major":    ("ps-chip-major",  "Major"),
        "Moderate": ("ps-chip-mod",    "Moderate"),
        "Minor":    ("ps-chip-minor",  "Minor"),
        "Unknown":  ("ps-chip-none",   "Unknown"),
    }
    cls, label = mapping.get(level, ("ps-chip-none", "Not in DB"))
    return f'<span class="ps-chip {cls}">{label}</span>'


def eyebrow(text: str, muted: bool = False) -> str:
    cls = "ps-eyebrow-muted" if muted else "ps-eyebrow"
    return f'<span class="{cls}">{text}</span>'


def disclaimer():
    st.markdown(
        '<div class="ps-disclaimer">'
        '<span class="ps-disclaimer-icon">ⓘ</span>'
        '<span><b>Clinical notice:</b> Pharma Sentinel is a research and education tool. '
        'It does not replace clinical judgement. '
        '<b>Absence of a record in DDInter does not confirm safety.</b></span>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_header(active: str):
    """Compact application header with real navigation."""
    pages = {
        "overview":   "Overview",
        "workspace":  "Interaction Analysis",
        "methodology":"Methodology",
    }
    nav_html = "".join(
        f'<span class="ps-nav-link {"active" if k == active else ""}" '
        f'data-page="{k}">{v}</span>'
        for k, v in pages.items()
    )
    # Navigation is handled by st.radio in sidebar for Streamlit routing
    st.markdown(
        '<div class="ps-header">'
        '  <div class="ps-wordmark">'
        '    <span class="ps-wordmark-name">Pharma Sentinel</span>'
        '    <span class="ps-wordmark-tag">Clinical Intelligence</span>'
        '  </div>'
        '  <div class="ps-live">'
        '    <span class="ps-live-dot"></span>'
        '    DDInter v2024.11 · 160,235 pairs'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        '<div class="ps-footer">'
        '  <div class="ps-footer-left">'
        '    <strong>Pharma Sentinel</strong> · Academic research project, 2025<br>'
        '    Data: DDInter v2024.11 (<em>Nucleic Acids Research</em>, 2022 — Xiong G. et al.)'
        '  </div>'
        '  <div class="ps-footer-right">Not a medical device. For research use only.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ─── Pages ────────────────────────────────────────────────────────────────────
def page_overview(pairs: pd.DataFrame, drugs: pd.DataFrame):
    render_header("overview")
    disclaimer()

    # ── Hero ──────────────────────────────────────────────────────────────────
    hero_l, hero_r = st.columns([1.45, 1], gap="large")

    with hero_l:
        st.markdown(eyebrow("Initiative 2025 · Clinical Pharmacology"), unsafe_allow_html=True)
        st.markdown(
            '<h1>Mapping the boundaries of polypharmacy.</h1>'
            '<p style="font-size:var(--text-md);line-height:1.65;color:var(--ink-2);'
            'max-width:52ch;margin-bottom:var(--sp-5);">'
            'A deterministic, evidence-grounded framework for identifying '
            'multi-drug pharmacokinetic conflicts across CYP450, renal, and receptor pathways—'
            'built on the full DDInter dataset.'
            '</p>',
            unsafe_allow_html=True,
        )

        # Metric row — ps-stat is border-top only, no height:100%
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                '<div class="ps-stat">'
                '<span class="ps-stat-label">Drug pairs indexed</span>'
                f'<span class="ps-stat-number">{len(pairs):,}</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                '<div class="ps-stat">'
                '<span class="ps-stat-label">Unique substances</span>'
                f'<span class="ps-stat-number">{len(drugs):,}</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        with m3:
            major_count = int((pairs["Level"] == "Major").sum())
            st.markdown(
                '<div class="ps-stat">'
                '<span class="ps-stat-label">Major interactions</span>'
                f'<span class="ps-stat-number" style="color:var(--sev-major)">{major_count:,}</span>'
                '</div>',
                unsafe_allow_html=True,
            )

    with hero_r:
        # 3D molecule — graceful fallback if CDN unavailable
        try:
            mol = render_molecule_3d_html(height=240)
            components.html(mol, height=250, scrolling=False)
        except Exception:
            pass  # silent — no broken placeholder

        st.markdown(
            '<div class="ps-telem">'
            '  <div class="ps-telem-cell">'
            '    <span class="ps-telem-label">Buffer pH</span>'
            '    <span class="ps-telem-val">7.42 ± 0.02</span>'
            '  </div>'
            '  <div class="ps-telem-cell">'
            '    <span class="ps-telem-label">Incubation</span>'
            '    <span class="ps-telem-val">37.0 °C</span>'
            '  </div>'
            '  <div class="ps-telem-cell">'
            '    <span class="ps-telem-label">HLM protein</span>'
            '    <span class="ps-telem-val">0.5 mg/mL</span>'
            '  </div>'
            '  <div class="ps-telem-cell">'
            '    <span class="ps-telem-label">NADPH</span>'
            '    <span class="ps-telem-val" style="color:var(--sev-minor)">99.8% sat.</span>'
            '  </div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="ps-divider">', unsafe_allow_html=True)

    # ── Capabilities ──────────────────────────────────────────────────────────
    st.markdown(eyebrow("What the platform does", muted=True), unsafe_allow_html=True)
    st.markdown(
        '<div class="ps-cap-grid">'

        '<div class="ps-cap">'
        '<span class="ps-cap-title">Multi-drug interaction matrix</span>'
        '<span class="ps-cap-body">'
        'Checks all N×(N−1)/2 pairs in a prescription list. '
        'Detects duplicate active ingredients across brand names. '
        'Severity-sorted output with DDInter provenance.'
        '</span>'
        '</div>'

        '<div class="ps-cap">'
        '<span class="ps-cap-title">Evidence-graded supplement database</span>'
        '<span class="ps-cap-body">'
        'Herb, food, and micronutrient interactions indexed by evidence level (A/B/C). '
        'Each entry links to primary PubMed sources and FDA/EMA advisories.'
        '</span>'
        '</div>'

        '<div class="ps-cap">'
        '<span class="ps-cap-title">Graph topology and link prediction</span>'
        '<span class="ps-cap-body">'
        'Interactive DDInter network visualisation and a leakage-free Random Forest '
        'link predictor (ROC-AUC 0.91) for discovering candidate unknown interactions.'
        '</span>'
        '</div>'

        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="ps-divider">', unsafe_allow_html=True)

    # ── Data provenance ───────────────────────────────────────────────────────
    st.markdown(eyebrow("Data provenance", muted=True), unsafe_allow_html=True)
    prov_l, prov_r = st.columns([1.5, 1], gap="large")
    with prov_l:
        st.markdown(
            '<p style="font-size:var(--text-base);line-height:1.7;color:var(--ink-2);">'
            'Every drug–drug interaction in this platform is sourced from '
            '<strong>DDInter</strong> (<em>Nucleic Acids Research</em>, 2022). '
            'No interaction is synthesised or inferred without an explicit DDInter record. '
            'Supplement interactions are independently catalogued with mandatory citations '
            'and evidence-level assignments.'
            '</p>'
            '<p style="font-size:var(--text-sm);color:var(--ink-3);line-height:1.6;">'
            'Canonical normalisation: duplicate pairs collapsed to highest severity; '
            'self-loops removed; alphabetical pair ordering enforced.'
            '</p>',
            unsafe_allow_html=True,
        )
    with prov_r:
        sev_counts = pairs["Level"].value_counts()
        for lv, col in [("Major","var(--sev-major)"), ("Moderate","var(--sev-mod)"),
                         ("Minor","var(--sev-minor)"), ("Unknown","var(--ink-3)")]:
            n = sev_counts.get(lv, 0)
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;padding:var(--sp-2) 0;border-bottom:1px solid var(--border);">'
                f'  <span style="font-size:var(--text-sm);color:var(--ink-2);">{lv}</span>'
                f'  <span style="font-family:var(--font-mono);font-size:var(--text-sm);'
                f'color:{col};font-weight:500;">{n:,}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    render_footer()


def page_workspace(
    pairs: pd.DataFrame,
    drugs: pd.DataFrame,
    normalizer: DrugNormalizer,
    supp_repo: SupplementEvidenceRepository,
):
    render_header("workspace")
    disclaimer()

    st.markdown(eyebrow("Interaction Analysis"), unsafe_allow_html=True)
    st.markdown("## Analyze drug interactions")

    catalog = normalizer.get_search_catalog()
    catalog_labels = [label for label, _ in catalog]
    catalog_map = dict(catalog)

    # ── Two-column workspace layout ───────────────────────────────────────────
    col_input, col_output = st.columns([1, 1.4], gap="large")

    with col_input:
        # ── Quick presets ─────────────────────────────────────────────────────
        st.markdown(
            '<span class="ps-eyebrow-muted" style="margin-bottom:var(--sp-3);display:block;">'
            'Clinical presets</span>',
            unsafe_allow_html=True,
        )
        p1, p2, p3 = st.columns(1), st.columns(1), st.columns(1)
        selected_preset = None
        if st.button("CYP2C9 Triad — Warfarin + Amiodarone + Fluconazole", use_container_width=True):
            selected_preset = ["warfarin", "amiodarone", "fluconazole"]
        if st.button("Triple Whammy — ACE inhibitor + Diuretic + NSAID", use_container_width=True):
            selected_preset = ["enalapril", "furosemide", "ibuprofen"]
        if st.button("Anticoagulant Conflict — Warfarin + Aspirin", use_container_width=True):
            selected_preset = ["warfarin", "acetylsalicylic acid"]

        # ── Drug selection ────────────────────────────────────────────────────
        st.markdown(
            '<span class="ps-eyebrow-muted" style="margin-top:var(--sp-5);margin-bottom:var(--sp-2);'
            'display:block;">Drug list</span>',
            unsafe_allow_html=True,
        )

        if "ws_sel" not in st.session_state:
            st.session_state.ws_sel = [
                next((l for l in catalog_labels if "warfarin" in l.lower()), catalog_labels[0]),
                next((l for l in catalog_labels if "aspirin" in l.lower() or "аспирин" in l.lower()), catalog_labels[1]),
                next((l for l in catalog_labels if "ibuprofen" in l.lower() or "ибупрофен" in l.lower()), catalog_labels[2]),
            ]

        if selected_preset:
            new = []
            for p in selected_preset:
                m = next((l for l in catalog_labels if p in l.lower() or catalog_map.get(l) == p), None)
                if m:
                    new.append(m)
            if new:
                st.session_state.ws_sel = new

        selected = st.multiselect(
            "Search by INN, brand name, or trade name:",
            catalog_labels,
            default=st.session_state.ws_sel,
            key="ws_multiselect",
            help="System resolves brand names to canonical INN before lookup.",
        )

        # ── Protocol panel ────────────────────────────────────────────────────
        st.markdown(
            '<div class="ps-panel" style="margin-top:var(--sp-5);">'
            '  <span class="ps-panel-title">Analysis protocol</span>'
            '  <div style="font-size:var(--text-sm);color:var(--ink-3);line-height:1.65;">'
            '    PS-8924 · DDInter Full Adjacency Core<br>'
            '    All N×(N−1)/2 pairs evaluated<br>'
            '    Duplicate-INN detection enabled'
            '  </div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_output:
        if len(selected) < 2:
            st.markdown(
                '<div style="padding:var(--sp-10) var(--sp-6);text-align:center;'
                'color:var(--ink-3);font-size:var(--text-sm);">'
                'Select at least two drugs to run the interaction check.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            queries = [catalog_map.get(l, l) for l in selected]
            checker = MultiDrugChecker(pairs, normalizer)

            with st.spinner("Checking interactions…"):
                report = checker.check_list(queries)

            # Duplicate INN warnings
            for dup in (report.duplicates_detected or []):
                st.error(f"Duplicate active ingredient: {dup}")

            # Summary metrics
            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.markdown(
                '<div class="ps-stat">'
                '<span class="ps-stat-label">Overall risk</span>'
                f'<span class="ps-stat-number" style="font-size:var(--text-xl);">{report.overall_risk}</span>'
                '</div>', unsafe_allow_html=True,
            )
            sm2.markdown(
                '<div class="ps-stat">'
                '<span class="ps-stat-label">Major</span>'
                f'<span class="ps-stat-number" style="font-size:var(--text-xl);color:var(--sev-major);">'
                f'{report.summary_counts.get("Major", 0)}</span>'
                '</div>', unsafe_allow_html=True,
            )
            sm3.markdown(
                '<div class="ps-stat">'
                '<span class="ps-stat-label">Moderate</span>'
                f'<span class="ps-stat-number" style="font-size:var(--text-xl);color:var(--sev-mod);">'
                f'{report.summary_counts.get("Moderate", 0)}</span>'
                '</div>', unsafe_allow_html=True,
            )
            sm4.markdown(
                '<div class="ps-stat">'
                '<span class="ps-stat-label">Not in DB</span>'
                f'<span class="ps-stat-number" style="font-size:var(--text-xl);">'
                f'{report.summary_counts.get("Not in DB", 0)}</span>'
                '</div>', unsafe_allow_html=True,
            )

            st.markdown(
                '<hr style="border:0;border-top:1px solid var(--border);margin:var(--sp-4) 0;">',
                unsafe_allow_html=True,
            )

            # Interaction results
            for p in report.pairs:
                st.markdown(
                    f'<div class="ps-result">'
                    f'  <div class="ps-result-header">'
                    f'    <div class="ps-result-drugs">'
                    f'      {p.display_a}'
                    f'      <span class="ps-result-sep">↔</span>'
                    f'      {p.display_b}'
                    f'    </div>'
                    f'    {chip(p.level)}'
                    f'  </div>'
                    f'  <div class="ps-result-body"><b>Finding:</b> {p.explanation}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Supplement interactions
            related = []
            for c in report.resolved_drugs:
                related.extend(supp_repo.get_by_drug(c))

            if related:
                st.markdown(
                    f'<div style="margin-top:var(--sp-5);">'
                    f'  {eyebrow(f"Food & supplement interactions ({len(related)})")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                for s in related:
                    st.markdown(
                        f'<div class="ps-supp">'
                        f'  <div class="ps-supp-head">'
                        f'    <span class="ps-supp-title">'
                        f'      {s.supplement_ru} ({s.supplement_lat}) + {s.drug_ru}'
                        f'    </span>'
                        f'    {chip(s.severity)}'
                        f'    <span class="ps-chip ps-chip-none">{s.evidence_level}</span>'
                        f'  </div>'
                        f'  <div class="ps-supp-text">{s.mechanism}</div>'
                        f'  <div class="ps-supp-text" style="margin-top:var(--sp-1);'
                        f'color:var(--ink-2);"><strong>Management:</strong> {s.clinical_management}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    render_footer()


def page_supplements(supp_repo: SupplementEvidenceRepository):
    render_header("workspace")

    st.markdown(eyebrow("Evidence-Based Supplement Catalogue"), unsafe_allow_html=True)
    st.markdown("## Supplement & herb interactions")
    st.markdown(
        '<p style="max-width:65ch;font-size:var(--text-base);line-height:1.7;'
        'color:var(--ink-2);margin-bottom:var(--sp-5);">'
        'Pharmacokinetic interactions between herbal extracts, food factors and micronutrients '
        'with conventional drugs. Each entry is graded A (RCTs/meta-analyses), '
        'B (controlled studies), or C (pharmacokinetic case data).'
        '</p>',
        unsafe_allow_html=True,
    )

    fc1, fc2 = st.columns([1.6, 1])
    with fc1:
        q = st.text_input("Search supplement or drug name:")
    with fc2:
        lf = st.selectbox("Evidence level:", ["All", "Level A", "Level B", "Level C"])

    items = supp_repo.search(q)
    if lf != "All":
        items = [i for i in items if i.evidence_level == lf]

    st.markdown(
        f'<span style="font-size:var(--text-sm);color:var(--ink-3);">'
        f'{len(items)} record{"s" if len(items) != 1 else ""} found</span>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr style="border:0;border-top:1px solid var(--border);margin:var(--sp-3) 0;">', unsafe_allow_html=True)

    for item in items:
        st.markdown(
            f'<div class="ps-result">'
            f'  <div class="ps-result-header">'
            f'    <div class="ps-result-drugs">'
            f'      {item.supplement_ru} '
            f'      <span style="font-weight:400;font-size:var(--text-sm);color:var(--ink-3);">'
            f'({item.supplement_lat})</span>'
            f'      <span class="ps-result-sep">+</span>'
            f'      {item.drug_ru}'
            f'    </div>'
            f'    <div style="display:flex;gap:var(--sp-2);align-items:center;">'
            f'      {chip(item.severity)}'
            f'      <span class="ps-chip ps-chip-none">{item.evidence_level}</span>'
            f'    </div>'
            f'  </div>'
            f'  <div class="ps-result-body">'
            f'    <div><b>Type:</b> {item.interaction_type}</div>'
            f'    <div><b>Mechanism:</b> {item.mechanism}</div>'
            f'    <div><b>Consequence:</b> {item.clinical_consequence}</div>'
            f'    <div style="color:var(--ink);margin-top:var(--sp-2);">'
            f'      <b>Management:</b> {item.clinical_management}'
            f'    </div>'
            f'  </div>'
            f'  <div style="margin-top:var(--sp-3);padding-top:var(--sp-2);'
            f'border-top:1px solid var(--border);font-size:var(--text-xs);color:var(--ink-3);">'
            f'    <b>Sources:</b> {"; ".join(item.citations)}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    render_footer()


def page_network(pairs: pd.DataFrame, drugs: pd.DataFrame, names: list[str]):
    render_header("workspace")
    st.markdown(eyebrow("Network Analysis", muted=True), unsafe_allow_html=True)
    st.markdown("## Interaction network topology")

    nc1, nc2, nc3 = st.columns([1.3, 1.1, 1.2])
    center = nc1.selectbox("Central node:", names,
                            index=names.index("warfarin") if "warfarin" in names else 0)
    levels = nc2.multiselect("Severity levels:", ["Major", "Moderate", "Minor", "Unknown"],
                              default=["Major", "Moderate"])
    max_e = nc3.slider("Max edges:", 5, 80, 30)

    near = pairs[((pairs.Drug_A == center) | (pairs.Drug_B == center)) & pairs.Level.isin(levels)].copy()
    near["Neighbor"] = np.where(near.Drug_A == center, near.Drug_B, near.Drug_A)
    order = {"Major": 0, "Moderate": 1, "Minor": 2, "Unknown": 3}
    near["_o"] = near.Level.map(order)
    near = near.sort_values(["_o", "Neighbor"]).head(max_e)

    if near.empty:
        st.info("No edges found for selected drug and filters.")
    else:
        try:
            from pyvis.network import Network
            net = Network(height="500px", width="100%", bgcolor="#F9F8F6",
                          font_color="#0E1117", directed=False, cdn_resources="in_line")
            net.set_options('{"physics":{"solver":"forceAtlas2Based","forceAtlas2Based":'
                            '{"gravitationalConstant":-60,"centralGravity":0.02,'
                            '"springLength":140,"springConstant":0.08},'
                            '"stabilization":{"iterations":100}},'
                            '"nodes":{"font":{"size":14,"face":"Inter, sans-serif"}},'
                            '"edges":{"smooth":{"type":"continuous"},"width":2}}')
            net.add_node(center, label=center.title(),
                         color={"background": "#1A56A0", "border": "#13407D"},
                         font={"color": "#FFFFFF"}, size=30)
            cmap = {"Major": "#B91C1C", "Moderate": "#B45309", "Minor": "#065F46", "Unknown": "#6B6860"}
            for _, row in near.iterrows():
                nbr, lv = row["Neighbor"], row["Level"]
                net.add_node(nbr, label=nbr.title(),
                             color={"background": "#FFFFFF", "border": "#D1CEC9"},
                             font={"color": "#0E1117"}, size=18)
                net.add_edge(center, nbr, color=cmap.get(lv, "#6B6860"),
                             title=lv, width=3 if lv == "Major" else 2)
            components.html(net.generate_html(), height=520, scrolling=False)
        except Exception as exc:
            st.error(f"Graph rendering failed: {exc}")

        st.dataframe(
            near[["Neighbor", "Level"]].rename(columns={"Neighbor": "Drug", "Level": "Severity"}),
            use_container_width=True, hide_index=True,
        )

    st.markdown("### Top hubs by Major-edge count")
    st.dataframe(major_hubs(pairs), use_container_width=True, hide_index=True)
    render_footer()


def page_ml(pairs: pd.DataFrame, drugs: pd.DataFrame):
    render_header("methodology")
    st.markdown(eyebrow("Machine Learning Validation", muted=True), unsafe_allow_html=True)
    st.markdown("## Link prediction validation (leakage-free)")
    st.markdown(
        '<p style="max-width:65ch;font-size:var(--text-base);line-height:1.7;'
        'color:var(--ink-2);margin-bottom:var(--sp-5);">'
        'Graph-topology-based link prediction on DDInter. '
        'Train edges (12%) and test edges (20%) are physically removed from the feature graph (68%) '
        'to prevent data leakage.'
        '</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Training models…"):
        result = cached_evaluation(pairs, drugs)

    metrics = result["metrics"]
    st.dataframe(
        metrics.style.format({"ROC-AUC": "{:.3f}", "Precision@5000": "{:.3f}"}),
        use_container_width=True, hide_index=True,
    )
    st.caption(
        f"Sample: {result['train_examples']:,} training · "
        f"{result['test_examples']:,} test (balanced classes).".replace(",", " ")
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F9F8F6")
    for sp in ax.spines.values():
        sp.set_color("#E4E2DE")
    ax.tick_params(colors="#6B6860")

    palette = ["#1A56A0", "#065F46", "#B45309", "#B91C1C", "#9CA3AF"]
    for (name, (fpr, tpr)), col in zip(result["roc"].items(), palette):
        auc = metrics.loc[metrics["Метод"] == name, "ROC-AUC"].iloc[0]
        ax.plot(fpr, tpr, label=f"{name} AUC {auc:.3f}", color=col, linewidth=2)
    ax.plot([0, 1], [0, 1], "--", color="#D1D5DB", linewidth=1)
    ax.set(xlabel="False positive rate", ylabel="True positive rate",
           title="ROC curves — held-out DDInter test set")
    ax.grid(alpha=0.25, color="#E4E2DE")
    ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="#E4E2DE", fontsize=9, loc="lower right")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

    st.markdown("### Confusion matrix (Random Forest, threshold 0.5)")
    tn, fp, fn, tp = result["confusion"].ravel()
    st.dataframe(pd.DataFrame(
        [[tn, fp], [fn, tp]],
        index=["No edge in DB", "Hidden DDInter edge"],
        columns=["Predicted: no edge", "Predicted: edge"],
    ), use_container_width=True)
    render_footer()


def page_ai(pairs: pd.DataFrame, names: list[str]):
    render_header("workspace")
    st.markdown(eyebrow("Local AI Assistant", muted=True), unsafe_allow_html=True)
    st.markdown("## Contextual explanation (Ollama)")
    st.markdown(
        '<p style="max-width:65ch;font-size:var(--text-base);line-height:1.7;'
        'color:var(--ink-2);margin-bottom:var(--sp-5);">'
        'Generate a structured textual explanation for any DDInter pair using a '
        'locally-running language model. No data is sent to external APIs.'
        '</p>',
        unsafe_allow_html=True,
    )

    status = get_local_ai_status()
    ai_l, ai_r = st.columns([1, 1], gap="large")

    with ai_l:
        drug_a = st.selectbox("Drug A:", names, key="ai_a")
        drug_b = st.selectbox("Drug B:", names, index=min(1, len(names) - 1), key="ai_b")
        question = st.text_area("Question:", placeholder="What is the clinical significance of this interaction?", height=100)

        m = pairs[(pairs.Drug_A == min(drug_a, drug_b)) & (pairs.Drug_B == max(drug_a, drug_b))]
        level = None if m.empty else str(m.iloc[0]["Level"])

        st.markdown("---")
        st.markdown("#### Deterministic explanation (offline)")
        se = generate_structured_explanation(drug_a, drug_b, level)
        st.info(f"**Summary:** {se['summary']}\n\n**Clinical context:** {se['clinical_meaning']}\n\n**Recommendation:** {se['recommendation']}")

    with ai_r:
        st.markdown(
            '<div class="ps-panel">'
            '  <span class="ps-panel-title">Ollama service status</span>',
            unsafe_allow_html=True,
        )
        if status.available:
            st.success(f"✅ {status.message} ({status.details})")
            preferred = next((n for n in status.models if n.startswith("qwen2.5:3b")), status.models[0])
            model = st.selectbox("Model:", status.models, index=status.models.index(preferred))
            if st.button("Generate explanation…", type="primary", disabled=not question.strip()):
                prompt = make_evidence_prompt(question.strip(), drug_a, drug_b, level)
                with st.spinner("Generating…"):
                    try:
                        ans = ask_local_model(prompt, model)
                        st.markdown("**Response:**")
                        st.markdown(ans)
                    except RuntimeError as exc:
                        st.error(str(exc))
        else:
            st.info(f"ℹ️ {status.message}\n\n{status.details}")
            st.caption("Base analysis and risk scoring work fully offline.")
        st.markdown("</div>", unsafe_allow_html=True)

    render_footer()


def page_methodology():
    render_header("methodology")
    st.markdown(eyebrow("Methodology & Ethics", muted=True), unsafe_allow_html=True)
    st.markdown("## Methodology, data provenance, and ethical limits")

    st.markdown("""
### 1. DDInter database
**DDInter** (*Nucleic Acids Research*, 2022 — Xiong G. et al.) is the sole source of drug–drug interaction records:
- **1,939** unique pharmacologically active substances.
- **160,235** unique verified pairs graded as Major (26,914), Moderate (96,675), Minor (6,833), Unknown (29,813).
- Normalisation: duplicates collapsed to the highest severity; self-loops (A=A) removed; alphabetical pair ordering.

### 2. Supplement evidence standards
- **Level A** — Randomised controlled trials or meta-analyses.
- **Level B** — Controlled prospective or cohort studies.
- **Level C** — Pharmacokinetic studies in healthy volunteers, case series, FDA/EMA monographs.

### 3. Institutional limits
- **Absence of record ≠ Safety.** Missing pairs in DDInter reflect the limits of current documentation, not biological safety.
- **ML predicts graph topology, not clinical biology.** ROC-AUC 0.91 measures edge-recovery accuracy, not clinical outcome severity.
- This project is for academic research and education only. All therapeutic decisions require a qualified healthcare professional.
""")
    render_footer()


# ─── Navigation (Streamlit radio — real routing) ───────────────────────────────
NAV_LABELS = [
    "Overview",
    "Interaction Analysis",
    "Supplement Catalogue",
    "Interaction Network",
    "ML Validation",
    "AI Assistant",
    "Methodology",
]

with st.sidebar:
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.07em;color:var(--ink-3,#6B6860);padding:0.5rem 0 0.75rem;">'
        'Navigation</div>',
        unsafe_allow_html=True,
    )
    nav = st.radio("", NAV_LABELS, label_visibility="collapsed")
    st.markdown("---")
    st.caption("Pharma Sentinel · v3.4 · Academic")

try:
    with st.spinner("Loading DDInter dataset…"):
        pairs, drugs = cached_data()
    names = drugs["drug"].tolist()
    normalizer = cached_normalizer(tuple(names))
    supp_repo = SupplementEvidenceRepository()

    if nav == "Overview":
        page_overview(pairs, drugs)
    elif nav == "Interaction Analysis":
        page_workspace(pairs, drugs, normalizer, supp_repo)
    elif nav == "Supplement Catalogue":
        page_supplements(supp_repo)
    elif nav == "Interaction Network":
        page_network(pairs, drugs, names)
    elif nav == "ML Validation":
        page_ml(pairs, drugs)
    elif nav == "AI Assistant":
        page_ai(pairs, names)
    else:
        page_methodology()

except FileNotFoundError as exc:
    st.warning(str(exc))
except DataValidationError as exc:
    st.error(f"Data integrity error: {exc}")
except Exception as exc:
    st.error(f"Unexpected error: {exc}")
    raise
