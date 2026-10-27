"""Интеграционные регрессионные тесты приложения."""
import unittest
from data_loader import load_ddinter
from normalization import DrugNormalizer
from supplement_schema import SupplementEvidenceRepository
from multi_checker import MultiDrugChecker
from local_ai import get_local_ai_status, generate_structured_explanation


class TestAppIntegration(unittest.TestCase):
    """Сквозная проверка связей между компонентами приложения."""

    @classmethod
    def setUpClass(cls):
        cls.pairs, cls.drugs = load_ddinter()
        cls.names = cls.drugs["drug"].tolist()
        cls.normalizer = DrugNormalizer(cls.names)
        cls.supp_repo = SupplementEvidenceRepository()
        cls.checker = MultiDrugChecker(cls.pairs, cls.normalizer)

    def test_full_pipeline_pair_check(self):
        """Проверка цепочки: нормализация -> поиск в DDInter -> объяснение."""
        norm_a = self.normalizer.normalize("аспирин")
        norm_b = self.normalizer.normalize("варфарин")
        self.assertTrue(norm_a.is_resolved)
        self.assertTrue(norm_b.is_resolved)

        match = self.pairs[
            (self.pairs.Drug_A == min(norm_a.canonical_name, norm_b.canonical_name)) &
            (self.pairs.Drug_B == max(norm_a.canonical_name, norm_b.canonical_name))
        ]
        self.assertFalse(match.empty)
        level = match.iloc[0]["Level"]
        self.assertEqual(level, "Major")

        explanation = generate_structured_explanation(norm_a.canonical_name, norm_b.canonical_name, level)
        self.assertIn("Major", explanation["summary"])

    def test_full_pipeline_multi_check(self):
        """Проверка мульти-чекера со списком из 4 препаратов (включая русские бренды)."""
        report = self.checker.check_list(["Нурофен", "Ксарелто", "Парацетамол", "Аспирин Кардио"])
        self.assertIsInstance(report.resolved_drugs, list)
        self.assertGreaterEqual(len(report.pairs), 6)  # 4 вещества -> 6 пар
        df = report.to_dataframe()
        self.assertEqual(len(df), len(report.pairs))
        self.assertIn("Уровень риска", df.columns)

    def test_supplement_linkage_with_pipeline(self):
        """Проверка связи препаратов списка с базой БАДов."""
        supps = self.supp_repo.get_by_drug("warfarin")
        self.assertGreater(len(supps), 0)
        self.assertEqual(supps[0].drug_canonical, "warfarin")


if __name__ == "__main__":
    unittest.main()
