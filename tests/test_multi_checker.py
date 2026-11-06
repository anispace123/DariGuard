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

    def test_multicheckreport_direct_construction_with_duplicates(self):
        """Прямое конструирование MultiCheckReport при наличии дубликатов."""
        from multi_checker import MultiCheckReport
        # Конструирование в устаревшем стиле (9 позиционных аргументов)
        report = MultiCheckReport(
            raw_inputs=["Аспирин", "Аспирин Кардио"],
            resolved_drugs=["acetylsalicylic acid"],
            drug_to_inputs={"acetylsalicylic acid": ["Аспирин", "Аспирин Кардио"]},
            duplicates_detected=["Терапевтическое дублирование: acetylsalicylic acid"],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 0, "Moderate": 0, "Minor": 0, "Unknown": 0, "Not in DB": 0},
            overall_risk="ВЫСОКИЙ РИСК",
            safety_disclaimer="Дисклеймер"
        )
        # Проверяем автоматическое заполнение duplicates_structured
        self.assertTrue(hasattr(report, "duplicates_structured"))
        self.assertEqual(len(report.duplicates_structured), 1)
        canon, inputs = report.duplicates_structured[0]
        self.assertEqual(canon, "acetylsalicylic acid")
        self.assertEqual(len(inputs), 2)
        # Проверяем легаси-псевдоним duplicates
        self.assertTrue(hasattr(report, "duplicates"))
        self.assertEqual(report.duplicates, report.duplicates_detected)

    def test_multicheckreport_direct_construction_without_duplicates(self):
        """Прямое конструирование MultiCheckReport без дубликатов."""
        from multi_checker import MultiCheckReport
        report = MultiCheckReport(
            raw_inputs=["Варфарин", "Аспирин"],
            resolved_drugs=["warfarin", "acetylsalicylic acid"],
            drug_to_inputs={"warfarin": ["Варфарин"], "acetylsalicylic acid": ["Аспирин"]},
            duplicates_detected=[],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 1, "Moderate": 0, "Minor": 0, "Unknown": 0, "Not in DB": 0},
            overall_risk="ВЫСОКИЙ РИСК",
            safety_disclaimer="Дисклеймер"
        )
        self.assertEqual(len(report.duplicates_structured), 0)
        self.assertEqual(len(report.duplicates_detected), 0)
        self.assertEqual(len(report.duplicates), 0)

    def test_multicheckreport_legacy_attribute_fallback(self):
        """Проверка динамического fallback-доступа если атрибут удален из __dict__."""
        from multi_checker import MultiCheckReport
        report = MultiCheckReport(
            raw_inputs=["Аспирин", "Аспирин Кардио"],
            resolved_drugs=["acetylsalicylic acid"],
            drug_to_inputs={"acetylsalicylic acid": ["Аспирин", "Аспирин Кардио"]},
            duplicates_detected=["Предупреждение"],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={},
            overall_risk="ВЫСОКИЙ РИСК",
            safety_disclaimer="Дисклеймер"
        )
        # Удаляем атрибут из словаря экземпляра для симуляции старого объекта из кэша
        if "duplicates_structured" in report.__dict__:
            del report.__dict__["duplicates_structured"]
        if "duplicates" in report.__dict__:
            del report.__dict__["duplicates"]

        # Доступ не должен падать с AttributeError
        self.assertEqual(len(report.duplicates_structured), 1)
        self.assertEqual(report.duplicates_structured[0][0], "acetylsalicylic acid")
        self.assertEqual(report.duplicates, ["Предупреждение"])

    def test_overall_risk_code_calculation_tiers(self):
        """Проверка расчета overall_risk_code для всех степеней риска."""
        from multi_checker import MultiCheckReport

        # 1. HIGH через Major
        rep_high_major = MultiCheckReport(
            raw_inputs=["A", "B"],
            resolved_drugs=["A", "B"],
            drug_to_inputs={"A": ["A"], "B": ["B"]},
            duplicates_detected=[],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 1, "Moderate": 0, "Minor": 0, "Unknown": 0, "Not in DB": 0},
            overall_risk="ВЫСОКИЙ РИСК",
            safety_disclaimer=""
        )
        self.assertEqual(rep_high_major.overall_risk_code, "HIGH")

        # 2. HIGH через дубликат действующего вещества
        rep_high_dup = MultiCheckReport(
            raw_inputs=["A1", "A2"],
            resolved_drugs=["A"],
            drug_to_inputs={"A": ["A1", "A2"]},
            duplicates_detected=["dup"],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 0, "Moderate": 0, "Minor": 0, "Unknown": 0, "Not in DB": 0},
            overall_risk="ВЫСОКИЙ РИСК",
            safety_disclaimer=""
        )
        self.assertEqual(rep_high_dup.overall_risk_code, "HIGH")

        # 3. MODERATE
        rep_mod = MultiCheckReport(
            raw_inputs=["A", "B"],
            resolved_drugs=["A", "B"],
            drug_to_inputs={"A": ["A"], "B": ["B"]},
            duplicates_detected=[],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 0, "Moderate": 2, "Minor": 0, "Unknown": 0, "Not in DB": 0},
            overall_risk="УМЕРЕННЫЙ РИСК",
            safety_disclaimer=""
        )
        self.assertEqual(rep_mod.overall_risk_code, "MODERATE")

        # 4. LOW
        rep_low = MultiCheckReport(
            raw_inputs=["A", "B"],
            resolved_drugs=["A", "B"],
            drug_to_inputs={"A": ["A"], "B": ["B"]},
            duplicates_detected=[],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 0, "Moderate": 0, "Minor": 1, "Unknown": 0, "Not in DB": 0},
            overall_risk="НИЗКИЙ РИСК",
            safety_disclaimer=""
        )
        self.assertEqual(rep_low.overall_risk_code, "LOW")

        # 5. UNDETERMINED
        rep_unk = MultiCheckReport(
            raw_inputs=["A", "B"],
            resolved_drugs=["A", "B"],
            drug_to_inputs={"A": ["A"], "B": ["B"]},
            duplicates_detected=[],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 0, "Moderate": 0, "Minor": 0, "Unknown": 1, "Not in DB": 0},
            overall_risk="НЕОПРЕДЕЛЁННЫЙ РИСК",
            safety_disclaimer=""
        )
        self.assertEqual(rep_unk.overall_risk_code, "UNDETERMINED")

        # 6. NO_DATA
        rep_nodata = MultiCheckReport(
            raw_inputs=["A", "B"],
            resolved_drugs=["A", "B"],
            drug_to_inputs={"A": ["A"], "B": ["B"]},
            duplicates_detected=[],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 0, "Moderate": 0, "Minor": 0, "Unknown": 0, "Not in DB": 2},
            overall_risk="ДАННЫЕ В DDINTER ОТСУТСТВУЮТ",
            safety_disclaimer=""
        )
        self.assertEqual(rep_nodata.overall_risk_code, "NO_DATA")

    def test_multicheckreport_overall_risk_code_fallback(self):
        """Проверка динамического fallback для overall_risk_code при отсутствии в __dict__."""
        from multi_checker import MultiCheckReport
        report = MultiCheckReport(
            raw_inputs=["A", "B"],
            resolved_drugs=["A", "B"],
            drug_to_inputs={"A": ["A"], "B": ["B"]},
            duplicates_detected=[],
            unresolved_inputs=[],
            pairs=[],
            summary_counts={"Major": 2, "Moderate": 0, "Minor": 0, "Unknown": 0, "Not in DB": 0},
            overall_risk="ВЫСОКИЙ РИСК",
            safety_disclaimer="Дисклеймер"
        )
        if "overall_risk_code" in report.__dict__:
            del report.__dict__["overall_risk_code"]

        # Не должно вызывать AttributeError
        self.assertEqual(report.overall_risk_code, "HIGH")

    def test_pairwise_interaction_explanation_code_fallback(self):
        """Проверка динамического fallback для PairwiseInteraction.explanation_code."""
        from multi_checker import PairwiseInteraction
        pair = PairwiseInteraction(
            drug_a="a",
            drug_b="b",
            display_a="A",
            display_b="B",
            level="Major",
            in_ddinter=True
        )
        if "explanation_code" in pair.__dict__:
            del pair.__dict__["explanation_code"]
        self.assertEqual(pair.explanation_code, "exp_major")

    def test_normalization_result_message_code_fallback(self):
        """Проверка динамического fallback для NormalizationResult.message_code."""
        from normalization import NormalizationResult
        norm_res = NormalizationResult(
            raw_query="аспирин",
            status="canonical"
        )
        if "message_code" in norm_res.__dict__:
            del norm_res.__dict__["message_code"]
        self.assertEqual(norm_res.message_code, "norm_canonical")
        if "message_params" in norm_res.__dict__:
            del norm_res.__dict__["message_params"]
        self.assertEqual(norm_res.message_params, {})


if __name__ == "__main__":
    unittest.main()
