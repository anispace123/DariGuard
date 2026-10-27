"""Тесты загрузчика данных DDInter."""
import unittest
import pandas as pd
from data_loader import load_ddinter, REQUIRED_COLUMNS, LEVEL_WEIGHT, DataValidationError


class TestDataLoader(unittest.TestCase):
    """Проверка загрузки и очистки набора DDInter."""

    @classmethod
    def setUpClass(cls):
        cls.pairs, cls.drugs = load_ddinter()

    def test_loaded_structure(self):
        """Проверяем, что результат содержит правильные структуры и колонки."""
        self.assertIsInstance(self.pairs, pd.DataFrame)
        self.assertIsInstance(self.drugs, pd.DataFrame)
        for col in REQUIRED_COLUMNS:
            self.assertIn(col, self.pairs.columns)
        self.assertIn("drug", self.drugs.columns)
        self.assertIn("node_id", self.drugs.columns)

    def test_canonical_pair_ordering(self):
        """Проверяем, что в каждой паре Drug_A строго меньше Drug_B (канонический порядок)."""
        self.assertTrue((self.pairs["Drug_A"] < self.pairs["Drug_B"]).all())

    def test_no_self_loops(self):
        """Проверяем, что петли (Drug_A == Drug_B) полностью удалены."""
        self.assertEqual((self.pairs["Drug_A"] == self.pairs["Drug_B"]).sum(), 0)

    def test_no_duplicate_pairs(self):
        """Проверяем, что нет дублирующихся пар после сворачивания по уровню."""
        dups = self.pairs.duplicated(subset=["Drug_A", "Drug_B"])
        self.assertEqual(dups.sum(), 0)

    def test_level_values_are_valid(self):
        """Проверяем, что уровни соответствуют только допустимым значениям."""
        allowed_levels = set(LEVEL_WEIGHT.keys())
        actual_levels = set(self.pairs["Level"].unique())
        self.assertTrue(actual_levels.issubset(allowed_levels))

    def test_drugs_count_and_pairs_count(self):
        """Проверяем контрольные значения: не менее 1900 препаратов и 150000 пар."""
        self.assertGreaterEqual(len(self.drugs), 1900)
        self.assertGreaterEqual(len(self.pairs), 150000)


if __name__ == "__main__":
    unittest.main()
