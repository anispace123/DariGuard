"""Тесты модуля локального ИИ и структурированных объяснений."""
import unittest
from local_ai import (
    get_local_ai_status,
    make_evidence_prompt,
    generate_structured_explanation,
    generate_clinical_intelligence_brief,
    get_contextual_questions,
    ask_local_model,
    LocalAIStatus
)


class TestLocalAI(unittest.TestCase):
    """Проверка безопасной деградации ИИ-модуля и формирования контекста."""

    def test_status_when_offline_does_not_crash(self):
        """Проверка статуса при недоступном Ollama не должна бросать исключений."""
        # Указываем заведомо неактивный порт
        status = get_local_ai_status(base_url="http://localhost:59999", timeout=0.2)
        self.assertIsInstance(status, LocalAIStatus)
        self.assertFalse(status.available)
        self.assertEqual(status.status_code, "unreachable")
        self.assertIn("не подключён", status.message)

    def test_evidence_prompt_construction(self):
        """Промпт должен строго включать факты и предостережения."""
        prompt = make_evidence_prompt("В чем риск?", "warfarin", "aspirin", "Major")
        self.assertIn("warfarin", prompt)
        self.assertIn("aspirin", prompt)
        self.assertIn("Major", prompt)
        self.assertIn("врач", prompt.lower())

    def test_evidence_prompt_for_missing_entry(self):
        """Промпт при отсутствии записи должен предупреждать об отсутствии гарантий безопасности."""
        prompt = make_evidence_prompt("Опасно ли?", "drug_x", "drug_y", None)
        self.assertIn("не найдена", prompt)
        self.assertIn("не подтверждает безопасность", prompt)

    def test_structured_explanation_deterministic(self):
        """Детерминированное объяснение должно выдавать клинический контекст для всех уровней."""
        for level in ["Major", "Moderate", "Minor", "Unknown", None]:
            exp = generate_structured_explanation("drug_a", "drug_b", level)
            self.assertIn("summary", exp)
            self.assertIn("clinical_meaning", exp)
            self.assertIn("recommendation", exp)

    def test_clinical_intelligence_brief_for_all_cohorts(self):
        """Проверка генерации 7-компонентного досье для всех когортных пар на kk, ru, en."""
        test_pairs = [
            ("warfarin", "acetylsalicylic acid", "Major"),
            ("warfarin", "amiodarone", "Major"),
            ("warfarin", "fluconazole", "Major"),
            ("enalapril", "ibuprofen", "Moderate"),
            ("furosemide", "ibuprofen", "Moderate"),
        ]
        required_keys = [
            "finding", "moa_a", "moa_b", "why_matters",
            "clinical_consequence", "uncertainty", "monitoring", "sources"
        ]
        for drug_a, drug_b, lvl in test_pairs:
            for lang in ["kk", "ru", "en"]:
                brief = generate_clinical_intelligence_brief(drug_a, drug_b, lvl, lang=lang)
                for k in required_keys:
                    self.assertIn(k, brief, f"Key '{k}' missing for {drug_a}+{drug_b} in {lang}")
                    self.assertTrue(len(brief[k]) > 0, f"Empty value for key '{k}' in {lang}")

    def test_contextual_questions_coverage(self):
        """Проверка возврата релевантных клинических вопросов для когортных пар."""
        for lang in ["kk", "ru", "en"]:
            qs_bleeding = get_contextual_questions("warfarin", "acetylsalicylic acid", lang=lang)
            self.assertGreaterEqual(len(qs_bleeding), 3)

            qs_cyp = get_contextual_questions("warfarin", "amiodarone", lang=lang)
            self.assertGreaterEqual(len(qs_cyp), 3)

            qs_whammy = get_contextual_questions("enalapril", "ibuprofen", lang=lang)
            self.assertGreaterEqual(len(qs_whammy), 3)

    def test_structured_evidence_prompt_includes_pharmacology(self):
        """Промпт для Ollama обязан содержать структурированные фармакологические данные."""
        prompt_ru = make_evidence_prompt(
            "В чем опасность сочетания?",
            "warfarin",
            "amiodarone",
            "Major",
            lang="ru"
        )
        self.assertIn("CYP2C9", prompt_ru)
        self.assertIn("VKORC1", prompt_ru)
        self.assertIn("клиренс", prompt_ru.lower())
        self.assertIn("мониторинг", prompt_ru.lower())

    def test_ask_local_model_unavailable_raises_runtime_error(self):
        """При недоступном сервисе Ollama функция должна безопасно выбрасывать RuntimeError, а не крашить процесс."""
        with self.assertRaises(RuntimeError) as ctx:
            ask_local_model("test prompt", "qwen2.5:3b", base_url="http://localhost:59999", timeout=0.2)
        self.assertIn("Не удалось получить ответ", str(ctx.exception))



if __name__ == "__main__":
    unittest.main()
