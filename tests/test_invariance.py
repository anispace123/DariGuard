"""Test for language invariance of clinical pharmacology analysis.

Clinical Invariant:
For an identical medication input, the clinical evaluation (resolved INNs,
pairwise combinations, severity levels, and risk codes) must be strictly identical
regardless of whether the active interface language is 'kk' (Kazakh), 'ru' (Russian),
or 'en' (English).
"""
import unittest
from unittest.mock import patch
import pandas as pd

from data_loader import load_ddinter
from normalization import DrugNormalizer
from multi_checker import MultiDrugChecker
from i18n import SUPPORTED_LANGUAGES, t


class TestLanguageInvariance(unittest.TestCase):
    """Verifies that medical findings are invariant under language transitions."""

    @classmethod
    def setUpClass(cls):
        cls.pairs, cls.drugs = load_ddinter()
        cls.canonical = set(cls.drugs["drug"].str.lower())
        cls.normalizer = DrugNormalizer(cls.canonical)
        cls.checker = MultiDrugChecker(cls.pairs, cls.normalizer)

    def test_pairwise_analysis_invariance_across_languages(self):
        """Clinical findings must be 100% invariant across kk, ru, and en."""
        test_regimen = ["варфарин", "аспирин", "ибупрофен"]

        results_by_lang = {}
        for lang in SUPPORTED_LANGUAGES:
            with patch("i18n.get_lang", return_value=lang):
                report = self.checker.check_list(test_regimen)
                pairs_fingerprint = [
                    (p.drug_a, p.drug_b, p.level, p.in_ddinter, p.explanation_code)
                    for p in report.pairs
                ]
                results_by_lang[lang] = {
                    "resolved": report.resolved_drugs,
                    "pairs": pairs_fingerprint,
                    "overall_risk_code": report.overall_risk_code,
                    "counts": report.summary_counts,
                }

        # Compare kk vs ru and kk vs en
        base_kk = results_by_lang["kk"]
        for other_lang in ("ru", "en"):
            other = results_by_lang[other_lang]
            self.assertEqual(
                base_kk["resolved"],
                other["resolved"],
                f"Resolved drugs differed between kk and {other_lang}"
            )
            self.assertEqual(
                base_kk["pairs"],
                other["pairs"],
                f"Pair findings differed between kk and {other_lang}"
            )
            self.assertEqual(
                base_kk["overall_risk_code"],
                other["overall_risk_code"],
                f"Overall risk code differed between kk and {other_lang}"
            )
            self.assertEqual(
                base_kk["counts"],
                other["counts"],
                f"Summary counts differed between kk and {other_lang}"
            )

    def test_duplicate_detection_invariance(self):
        """Therapeutic duplicate detection must identify the same canonical INN in all languages."""
        duplicate_regimen = ["Аспирин", "Аспирин Кардио", "Варфарин"]
        for lang in SUPPORTED_LANGUAGES:
            with patch("i18n.get_lang", return_value=lang):
                report = self.checker.check_list(duplicate_regimen)
                self.assertEqual(len(report.duplicates_structured), 1)
                canonical, inputs = report.duplicates_structured[0]
                self.assertEqual(canonical, "acetylsalicylic acid")
                self.assertEqual(len(inputs), 2)
                self.assertEqual(report.overall_risk_code, "HIGH")


if __name__ == "__main__":
    unittest.main()
