"""Тесты модуля нормализации названий препаратов и синонимов."""
import unittest
from normalization import DrugNormalizer


class TestDrugNormalization(unittest.TestCase):
    """Проверка нормализации МНН, торговых марок и комбинаций."""

    @classmethod
    def setUpClass(cls):
        # Базовый набор канонических МНН для изоляции тестов
        cls.canonical = {
            "acetaminophen", "acetylsalicylic acid", "ibuprofen",
            "diclofenac", "warfarin", "metformin", "omeprazole",
            "caffeine", "amoxicillin"
        }
        cls.normalizer = DrugNormalizer(cls.canonical)

    def test_canonical_direct_match(self):
        """Прямой ввод канонического МНН из базы."""
        res = self.normalizer.normalize("ibuprofen")
        self.assertTrue(res.is_resolved)
        self.assertEqual(res.status, "canonical")
        self.assertEqual(res.canonical_name, "ibuprofen")

    def test_russian_synonym_resolution(self):
        """Русскоязычный синоним однозначно сопоставляется с каноническим МНН."""
        res = self.normalizer.normalize("парацетамол")
        self.assertTrue(res.is_resolved)
        self.assertEqual(res.status, "synonym")
        self.assertEqual(res.canonical_name, "acetaminophen")

    def test_brand_name_resolution(self):
        """Торговая марка сопоставляется с МНН."""
        res = self.normalizer.normalize("Нурофен")
        self.assertTrue(res.is_resolved)
        self.assertEqual(res.canonical_name, "ibuprofen")

    def test_combination_detection_requires_clarification(self):
        """Многокомпонентный препарат (Цитрамон) распознается и раскладывается на компоненты."""
        res = self.normalizer.normalize("Цитрамон")
        self.assertTrue(res.is_combination)
        self.assertEqual(res.status, "combination")
        self.assertTrue(res.clarification_needed)
        self.assertIn("acetylsalicylic acid", res.components)
        self.assertIn("acetaminophen", res.components)
        self.assertIn("caffeine", res.components)

    def test_unsupported_drug_warning(self):
        """Препарат, отсутствующий в DDInter (Но-шпа / Дротаверин), честно распознается без ложной безопасности."""
        res = self.normalizer.normalize("Но-шпа")
        self.assertEqual(res.status, "unsupported")
        self.assertFalse(res.is_resolved)
        self.assertIn("отсутствует в датасете", res.message)

    def test_fuzzy_suggestions_for_typos(self):
        """При опечатке возвращаются похожие варианты, но не происходит скрытой автозамены."""
        res = self.normalizer.normalize("парацетамал")
        self.assertEqual(res.status, "not_found")
        self.assertFalse(res.is_resolved)
        self.assertGreater(len(res.suggestions), 0)
        self.assertIn("парацетамол", res.suggestions)

    def test_empty_query(self):
        """Пустой запрос возвращает not_found."""
        res = self.normalizer.normalize("   ")
        self.assertEqual(res.status, "not_found")
        self.assertFalse(res.is_resolved)


if __name__ == "__main__":
    unittest.main()
