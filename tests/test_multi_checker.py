"""Тесты модуля комплексной проверки списка лекарств (полипрагмазии)."""
import unittest
import pandas as pd
from normalization import DrugNormalizer
from multi_checker import MultiDrugChecker, LEVEL_RANK


class TestMultiChecker(unittest.TestCase):
    """Проверка логики мульти-чекера."""

    def setUp(self):
        self.canonical = {"acetylsalicylic acid", "warfarin", "ibuprofen", "metformin"}
        self.normalizer = DrugNormalizer(self.canonical)
        self.pairs_df = pd.DataFrame({
            "DDInterID_A": ["D1", "D1"],
            "Drug_A": ["acetylsalicylic acid", "acetylsalicylic acid"],
            "DDInterID_B": ["D2", "D3"],
            "Drug_B": ["ibuprofen", "warfarin"],
            "Level": ["Major", "Major"]
        })
        self.checker = MultiDrugChecker(self.pairs_df, self.normalizer)

    def test_pairwise_combinations_count(self):
        """Для 3 уникальных препаратов должно формироваться ровно 3 пары (N*(N-1)/2)."""
        report = self.checker.check_list(["аспирин", "варфарин", "метформин"])
        self.assertEqual(len(report.resolved_drugs), 3)
        self.assertEqual(len(report.pairs), 3)

    def test_duplicate_ingredient_detection(self):
        """Ввод 'Аспирин' и 'Аспирин Кардио' должен вызывать предупреждение о дублировании МНН."""
        report = self.checker.check_list(["Аспирин", "Аспирин Кардио", "Варфарин"])
        self.assertGreater(len(report.duplicates_detected), 0)
        self.assertIn("acetylsalicylic acid", report.duplicates_detected[0])
        # Уникальных МНН должно остаться 2: acetylsalicylic acid и warfarin
        self.assertEqual(len(report.resolved_drugs), 2)
        # Соответственно ровно 1 пара
        self.assertEqual(len(report.pairs), 1)

    def test_sorting_by_severity(self):
        """Пары должны сортироваться по тяжести (Major в начале таблицы)."""
        report = self.checker.check_list(["аспирин", "варфарин", "метформин"])
        # Первая пара должна быть Major (аспирин + варфарин)
        self.assertEqual(report.pairs[0].level, "Major")
        # Метформин не имеет связи с аспирином в нашей тестовой выборке -> Not in DB
        last_pair = report.pairs[-1]
        self.assertEqual(last_pair.level, "Not in DB")

    def test_disclaimer_presence(self):
        """Обязательно должен присутствовать дисклеймер об отсутствии замены врачу."""
        report = self.checker.check_list(["аспирин", "варфарин"])
        self.assertIn("не заменяет", report.safety_disclaimer.lower())
        self.assertIn("ddinter", report.safety_disclaimer.lower())


if __name__ == "__main__":
    unittest.main()
