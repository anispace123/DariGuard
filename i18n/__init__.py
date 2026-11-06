"""PHARMA SENTINEL — Internationalization (i18n) Engine.

Supports:
- Kazakh (kk) — Default and primary platform language
- Russian (ru)
- English (en)

Policy:
- Strict missing-key behavior: in strict mode (PS_I18N_STRICT=1) raises KeyError;
  in default mode logs warning and returns ⟦lang:key⟧.
  NEVER silently fall back to another language for missing keys.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any
import streamlit as st

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
REVIEW_CATALOG_PATH = Path(__file__).resolve().parent / "review.json"

SUPPORTED_LANGUAGES = ("kk", "ru", "en")
DEFAULT_LANGUAGE = "kk"

LANGUAGE_LABELS = {
    "kk": "Қазақша",
    "ru": "Русский",
    "en": "English",
}

_CATALOGS: dict[str, dict[str, str]] = {}
_CATALOG_MTIMES: dict[str, float] = {}


def _load_catalogs() -> dict[str, dict[str, str]]:
    """Loads all JSON translation files from locales directory with mtime checking."""
    global _CATALOGS, _CATALOG_MTIMES
    for lang in SUPPORTED_LANGUAGES:
        file_path = LOCALES_DIR / f"{lang}.json"
        if file_path.exists():
            try:
                mtime = os.path.getmtime(file_path)
                if lang not in _CATALOGS or _CATALOG_MTIMES.get(lang) != mtime:
                    with open(file_path, "r", encoding="utf-8") as f:
                        _CATALOGS[lang] = json.load(f)
                    _CATALOG_MTIMES[lang] = mtime
            except Exception as exc:
                logging.error(f"Error loading translation catalog for {lang}: {exc}")
                if lang not in _CATALOGS:
                    _CATALOGS[lang] = {}
        else:
            _CATALOGS[lang] = {}
    return _CATALOGS


def reload_catalogs() -> None:
    """Forces reloading catalogs from disk (useful for tests and updates)."""
    global _CATALOGS, _CATALOG_MTIMES
    _CATALOGS = {}
    _CATALOG_MTIMES = {}
    _load_catalogs()


def get_lang() -> str:
    """Retrieves current platform language from query params or session state.
    Defaults strictly to 'kk' (Kazakh).
    """
    try:
        # Check query params first if inside Streamlit context
        qp = st.query_params
        if "lang" in qp:
            q_lang = str(qp["lang"]).lower()
            if q_lang in SUPPORTED_LANGUAGES:
                if "lang" in st.session_state and st.session_state["lang"] != q_lang:
                    st.session_state["lang"] = q_lang
                return q_lang
    except Exception:
        pass

    try:
        if "lang" in st.session_state:
            s_lang = str(st.session_state["lang"]).lower()
            if s_lang in SUPPORTED_LANGUAGES:
                return s_lang
    except Exception:
        pass

    return DEFAULT_LANGUAGE


def set_lang(lang: str) -> None:
    """Sets current language in session state and query parameters."""
    normalized = str(lang).lower()
    if normalized not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language '{lang}'. Choose from: {SUPPORTED_LANGUAGES}")

    try:
        st.session_state["lang"] = normalized
        st.query_params["lang"] = normalized
    except Exception:
        pass


def t(key: str, default: str | None = None, **kwargs: Any) -> str:
    """Translates key for the active language.
    
    If key is missing:
    - If PS_I18N_STRICT=1: raises KeyError.
    - Otherwise: logs warning and returns ⟦lang:key⟧ (or default if provided).
    No silent fallback across languages.
    """
    catalogs = _load_catalogs()
    lang = get_lang()
    catalog = catalogs.get(lang, {})

    if key not in catalog:
        reload_catalogs()
        catalog = _CATALOGS.get(lang, {})

    if key in catalog:
        val = catalog[key]
        if kwargs:
            try:
                return val.format(**kwargs)
            except Exception as e:
                logging.error(f"Formatting error for key '{key}' in lang '{lang}': {e}")
                return val
        return val

    # Key is missing in active language catalog
    strict = os.environ.get("PS_I18N_STRICT", "").strip().lower() in ("1", "true", "yes")
    err_msg = f"Missing i18n key '{key}' in locale '{lang}'"
    logging.warning(err_msg)

    if strict:
        raise KeyError(err_msg)

    if default is not None:
        if kwargs:
            try:
                return default.format(**kwargs)
            except Exception:
                return default
        return default

    return f"⟦{lang}:{key}⟧"


def get_all_keys(lang: str | None = None) -> set[str]:
    """Returns set of all keys in a given language catalog or the union across all."""
    catalogs = _load_catalogs()
    if lang:
        return set(catalogs.get(lang, {}).keys())
    all_keys = set()
    for cat in catalogs.values():
        all_keys.update(cat.keys())
    return all_keys


def check_catalog_parity() -> dict[str, list[str]]:
    """Checks whether all supported locales share the exact same keys.
    Returns dict mapping lang -> list of missing keys.
    """
    catalogs = _load_catalogs()
    all_keys = get_all_keys()
    discrepancies: dict[str, list[str]] = {}
    for lang in SUPPORTED_LANGUAGES:
        lang_keys = set(catalogs.get(lang, {}).keys())
        missing = sorted(list(all_keys - lang_keys))
        if missing:
            discrepancies[lang] = missing
    return discrepancies
