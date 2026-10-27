"""Тесты репозитория и схемы доказательной базы БАДов."""
import unittest
from supplement_schema import SupplementEvidenceRepository, SupplementInteraction


class TestSupplementSchema(unittest.TestCase):
    """Проверка загрузки и валидации данных БАДов."""

    @classmethod
    def setUpClass(cls):
        cls.repo = SupplementEvidenceRepository()

    def test_repository_loads_entries(self):
        """Репозиторий должен успешно загружать проверенные записи."""
        items = self.repo.get_all()
        self.assertGreater(len(items), 0)

    def test_each_item_has_required_evidence_fields(self):
        """Каждая запись обязана содержать доказательства и источники."""
        for item in self.repo.get_all():
            self.assertIsInstance(item, SupplementInteraction)
            self.assertTrue(item.id.startswith("SUPP-"))
            self.assertIn(item.severity, ["Major", "Moderate", "Minor"])
            self.assertIn(item.evidence_level, ["Level A", "Level B", "Level C"])
            self.assertGreater(len(item.mechanism), 10)
            self.assertGreater(len(item.clinical_consequence), 10)
            self.assertGreater(len(item.citations), 0, f"Запись {item.id} не содержит цитирований!")

    def test_query_by_drug(self):
        """Поиск взаимодействий по каноническому препарату (Варфарин)."""
        warfarin_supps = self.repo.get_by_drug("warfarin")
        self.assertGreaterEqual(len(warfarin_supps), 1)
        supp_names = [s.supplement_ru.lower() for s in warfarin_supps]
        # Зверобой или витамин K должны присутствовать
        self.assertTrue(any("зверобой" in n or "витамин k" in n for n in supp_names))


if __name__ == "__main__":
    unittest.main()
