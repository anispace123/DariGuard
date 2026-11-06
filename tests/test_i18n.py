"""Tests for the internationalization (i18n) module."""
import os
import unittest
from unittest.mock import patch

from i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    check_catalog_parity,
    get_all_keys,
    get_lang,
    reload_catalogs,
    set_lang,
    t,
)


class TestI18n(unittest.TestCase):
    """Verifies i18n catalog integrity, default language, and missing key policies."""

    def setUp(self):
        reload_catalogs()
        if "PS_I18N_STRICT" in os.environ:
            del os.environ["PS_I18N_STRICT"]

    def test_default_language_is_kazakh(self):
        """Kazakh (kk) must strictly be the default platform language."""
        self.assertEqual(DEFAULT_LANGUAGE, "kk")
        # In a fresh environment without session_state or query_params
        self.assertEqual(get_lang(), "kk")

    def test_supported_languages(self):
        """Supported languages must include kk, ru, and en."""
        self.assertIn("kk", SUPPORTED_LANGUAGES)
        self.assertIn("ru", SUPPORTED_LANGUAGES)
        self.assertIn("en", SUPPORTED_LANGUAGES)

    def test_catalog_100_percent_parity(self):
        """All supported languages must have 100% key parity (no missing keys in any language)."""
        discrepancies = check_catalog_parity()
        self.assertEqual(
            discrepancies,
            {},
            f"Catalog key discrepancy detected between languages: {discrepancies}"
        )
        # Ensure we have substantial coverage (>= 140 keys)
        all_keys = get_all_keys()
        self.assertGreaterEqual(len(all_keys), 140)

    def test_no_silent_fallback_for_missing_key(self):
        """A missing key must not silently return another language's text."""
        missing_key = "non_existent_medical_key_12345"
        with patch("i18n.get_lang", return_value="kk"):
            rendered = t(missing_key)
            self.assertEqual(rendered, f"⟦kk:{missing_key}⟧")

    def test_strict_mode_raises_on_missing_key(self):
        """When PS_I18N_STRICT=1, a missing key must raise KeyError."""
        os.environ["PS_I18N_STRICT"] = "1"
        try:
            with patch("i18n.get_lang", return_value="kk"):
                with self.assertRaises(KeyError):
                    t("completely_unknown_key_xyz")
        finally:
            del os.environ["PS_I18N_STRICT"]

    def test_parameter_formatting_in_all_languages(self):
        """Interpolation variables like {train} and {test} must format cleanly in all languages."""
        sample_key = "ml_sample"
        for lang in SUPPORTED_LANGUAGES:
            with patch("i18n.get_lang", return_value=lang):
                res = t(sample_key, train=1000, test=500)
                self.assertIn("1000", res)
                self.assertIn("500", res)
                self.assertNotIn("{train}", res)
                self.assertNotIn("{test}", res)

    def test_kazakh_translations_not_empty(self):
        """Every Kazakh entry must be a non-empty string."""
        for key in get_all_keys("kk"):
            with patch("i18n.get_lang", return_value="kk"):
                val = t(key)
                self.assertTrue(bool(val.strip()), f"Key '{key}' is empty in Kazakh locale")


if __name__ == "__main__":
    unittest.main()
