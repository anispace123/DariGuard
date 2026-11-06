"""Тесты для трех клинических сценариев быстрого поиска (пресетов).

Проверяет:
1. Триада CYP2C9: Варфарин + Кордарон (Амиодарон) + Дифлюкан (Флуконазол) -> HIGH
2. Triple Whammy: Эналаприл + Фуросемид (Лазикс) + Ибупрофен -> MODERATE
3. Геморрагический конфликт: Варфарин + Аспирин (Ацетилсалициловая кислота) -> HIGH
"""
import unittest
from data_loader import load_ddinter
from normalization import DrugNormalizer
from multi_checker import MultiDrugChecker


class TestQuickSearchPresets(unittest.TestCase):
    """Сквозное тестирование работы трех быстрых сценариев полипрагмазии."""

    @classmethod
    def setUpClass(cls):
        cls.pairs, cls.drugs = load_ddinter()
        cls.names = cls.drugs["drug"].tolist()
        cls.normalizer = DrugNormalizer(cls.names)
        cls.checker = MultiDrugChecker(cls.pairs, cls.normalizer)
        cls.catalog = cls.normalizer.get_search_catalog()
        cls.catalog_labels = [label for label, _ in cls.catalog]
        cls.catalog_map = dict(cls.catalog)

    def test_preset_1_cyp_triad(self):
        """Пресет 1: Триада CYP2C9 (Варфарин + Кордарон + Дифлюкан)."""
        # Проверка разрешения русских названий и синонимов
        norm_w = self.normalizer.normalize("варфарин")
        norm_a = self.normalizer.normalize("кордарон")
        norm_f = self.normalizer.normalize("дифлюкан")

        self.assertTrue(norm_w.is_resolved)
        self.assertEqual(norm_w.canonical_name, "warfarin")

        self.assertTrue(norm_a.is_resolved)
        self.assertEqual(norm_a.canonical_name, "amiodarone")

        self.assertTrue(norm_f.is_resolved)
        self.assertEqual(norm_f.canonical_name, "fluconazole")

        # Проверка поиска канонических меток каталога
        lbl_w = self.normalizer.get_canonical_catalog_label("warfarin")
        lbl_a = self.normalizer.get_canonical_catalog_label("amiodarone")
        lbl_f = self.normalizer.get_canonical_catalog_label("fluconazole")

        self.assertIn(lbl_w, self.catalog_labels)
        self.assertIn(lbl_a, self.catalog_labels)
        self.assertIn(lbl_f, self.catalog_labels)

        # Проверка полного чека по пресету
        report = self.checker.check_list(["warfarin", "amiodarone", "fluconazole"])
        self.assertEqual(len(report.resolved_drugs), 3)
        self.assertEqual(len(report.pairs), 3)
        self.assertEqual(report.overall_risk_code, "HIGH")
        self.assertEqual(report.summary_counts.get("Major", 0), 3)

    def test_preset_2_triple_whammy(self):
        """Пресет 2: Triple Whammy (Эналаприл + Фуросемид + Ибупрофен)."""
        # Проверка разрешения русских названий и синонимов
        norm_e = self.normalizer.normalize("эналаприл")
        norm_f = self.normalizer.normalize("фуросемид")
        norm_l = self.normalizer.normalize("лазикс")
        norm_i = self.normalizer.normalize("ибупрофен")

        self.assertTrue(norm_e.is_resolved)
        self.assertEqual(norm_e.canonical_name, "enalapril")

        self.assertTrue(norm_f.is_resolved)
        self.assertEqual(norm_f.canonical_name, "furosemide")

        self.assertTrue(norm_l.is_resolved)
        self.assertEqual(norm_l.canonical_name, "furosemide")

        self.assertTrue(norm_i.is_resolved)
        self.assertEqual(norm_i.canonical_name, "ibuprofen")

        # Проверка меток каталога
        lbl_e = self.normalizer.get_canonical_catalog_label("enalapril")
        lbl_f = self.normalizer.get_canonical_catalog_label("furosemide")
        lbl_i = self.normalizer.get_canonical_catalog_label("ibuprofen")

        self.assertIn(lbl_e, self.catalog_labels)
        self.assertIn(lbl_f, self.catalog_labels)
        self.assertIn(lbl_i, self.catalog_labels)

        # Проверка полного чека по пресету
        report = self.checker.check_list(["enalapril", "furosemide", "ibuprofen"])
        self.assertEqual(len(report.resolved_drugs), 3)
        self.assertEqual(len(report.pairs), 3)
        self.assertEqual(report.overall_risk_code, "MODERATE")
        self.assertEqual(report.summary_counts.get("Moderate", 0), 2)

    def test_preset_3_bleeding_conflict(self):
        """Пресет 3: Геморрагический конфликт (Варфарин + Аспирин)."""
        # Проверка разрешения
        norm_w = self.normalizer.normalize("варфарин")
        norm_a = self.normalizer.normalize("аспирин")

        self.assertTrue(norm_w.is_resolved)
        self.assertEqual(norm_w.canonical_name, "warfarin")

        self.assertTrue(norm_a.is_resolved)
        self.assertEqual(norm_a.canonical_name, "acetylsalicylic acid")

        # Проверка меток каталога
        lbl_w = self.normalizer.get_canonical_catalog_label("warfarin")
        lbl_a = self.normalizer.get_canonical_catalog_label("acetylsalicylic acid")

        self.assertIn(lbl_w, self.catalog_labels)
        self.assertIn(lbl_a, self.catalog_labels)

        # Проверка полного чека по пресету
        report = self.checker.check_list(["warfarin", "acetylsalicylic acid"])
        self.assertEqual(len(report.resolved_drugs), 2)
        self.assertEqual(len(report.pairs), 1)
        self.assertEqual(report.overall_risk_code, "HIGH")
        self.assertEqual(report.pairs[0].level, "Major")
        self.assertEqual(report.pairs[0].explanation_code, "exp_major")

    def test_backward_compatible_catalog_label_lookup(self):
        """Проверка обратной совместимости при поиске меток (защита от устаревших кэшей и версий)."""
        from normalization import get_canonical_catalog_label, safe_catalog_label

        # 1. Вызов как функции модуля
        lbl_func = get_canonical_catalog_label(self.normalizer, "варфарин")
        self.assertIsNotNone(lbl_func)
        self.assertIn("варфарин", lbl_func.lower())

        # 2. Вызов безопасного хелпера safe_catalog_label
        lbl_safe = safe_catalog_label(self.normalizer, "варфарин", self.catalog_labels, self.catalog_map)
        self.assertEqual(lbl_safe, lbl_func)

        # 3. Имитация устаревшего объекта без метода get_canonical_catalog_label
        class StaleNormalizerMock:
            def __init__(self, drugs):
                self.canonical_drugs = set(drugs)
                self.synonyms = {"варфарин": {"canonical": "warfarin", "ru": "Варфарин", "type": "inn_translation"}}

            def normalize(self, q):
                from normalization import NormalizationResult
                return NormalizationResult(raw_query=q, status="synonym", canonical_name="warfarin")

        stale_mock = StaleNormalizerMock(self.names)
        # У mock нет get_canonical_catalog_label
        self.assertFalse(hasattr(stale_mock, "get_canonical_catalog_label"))
        # safe_catalog_label всё равно должен корректно вернуть метку каталога
        res = safe_catalog_label(stale_mock, "варфарин", self.catalog_labels, self.catalog_map)
        self.assertIsNotNone(res)
        self.assertIn("warfarin", res.lower())

    def test_all_presets_clinical_briefs_and_questions_trilingual(self):
        """Проверка генерации 7-компонентных досье и контекстных вопросов для всех 3 когорт на 3 языках."""
        from local_ai import (
            generate_clinical_intelligence_brief,
            get_contextual_questions,
            make_evidence_prompt,
        )

        test_cohorts = [
            # Пресет 1: Триада CYP2C9
            ("cyp_triad", [("warfarin", "amiodarone", "Major"), ("warfarin", "fluconazole", "Major")]),
            # Пресет 2: Triple Whammy
            ("triple_whammy", [("enalapril", "ibuprofen", "Moderate"), ("furosemide", "ibuprofen", "Moderate")]),
            # Пресет 3: Bleeding
            ("bleeding", [("warfarin", "acetylsalicylic acid", "Major")]),
        ]

        required_brief_keys = [
            "finding", "moa_a", "moa_b", "why_matters",
            "clinical_consequence", "uncertainty", "monitoring", "sources"
        ]

        for cohort_name, pairs in test_cohorts:
            for drug_a, drug_b, level in pairs:
                for lang in ["kk", "ru", "en"]:
                    with self.subTest(cohort=cohort_name, pair=f"{drug_a}+{drug_b}", lang=lang):
                        brief = generate_clinical_intelligence_brief(drug_a, drug_b, level, lang=lang)
                        self.assertIsInstance(brief, dict)
                        for key in required_brief_keys:
                            self.assertIn(key, brief)
                            self.assertTrue(len(brief[key]) > 0, f"Key {key} is empty in {lang}")

                        # Проверка контекстных вопросов
                        questions = get_contextual_questions(drug_a, drug_b, lang=lang)
                        self.assertIsInstance(questions, list)
                        self.assertGreaterEqual(len(questions), 3)
                        for q in questions:
                            self.assertTrue(isinstance(q, str) and len(q) > 5)

                        # Проверка формирования подсказки для LLM
                        prompt = make_evidence_prompt(
                            question=questions[0],
                            drug_a=drug_a,
                            drug_b=drug_b,
                            level=level,
                            lang=lang,
                            brief=brief,
                        )
                        self.assertIsInstance(prompt, str)
                        self.assertIn(drug_a, prompt)
                        self.assertIn(drug_b, prompt)
                        self.assertIn(questions[0], prompt)




if __name__ == "__main__":
    unittest.main()
