"""Тесты модуля локального ИИ и структурированных объяснений."""
import unittest
from local_ai import (
    get_local_ai_status,
    make_evidence_prompt,
    generate_structured_explanation,
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


if __name__ == "__main__":
    unittest.main()
