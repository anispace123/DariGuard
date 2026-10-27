"""Схема и модуль работы с доказательной базой взаимодействий лекарств и БАДов.

Научные принципы:
1. Каждая запись содержит уровень доказательности (Level A, B, C).
2. Обязательны проверяемые библиографические источники (PMID / DOI / регуляторные акты).
3. Данные БАДов изолированы от базовой матрицы связей DDInter и не искажают ML-эксперименты.
"""
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data"
SUPPLEMENTS_FILE = DATA_DIR / "supplements_evidence.json"


@dataclass
class SupplementInteraction:
    """Модель доказанного взаимодействия БАД / нутриента с лекарственным препаратом."""
    id: str
    supplement_ru: str
    supplement_lat: str
    supplement_key: str
    drug_canonical: str
    drug_ru: str
    severity: str  # 'Major', 'Moderate', 'Minor'
    interaction_type: str
    mechanism: str
    clinical_consequence: str
    clinical_management: str
    evidence_level: str  # 'Level A', 'Level B', 'Level C'
    citations: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SupplementInteraction":
        return cls(
            id=data.get("id", ""),
            supplement_ru=data.get("supplement_ru", ""),
            supplement_lat=data.get("supplement_lat", ""),
            supplement_key=data.get("supplement_key", ""),
            drug_canonical=data.get("drug_canonical", "").lower(),
            drug_ru=data.get("drug_ru", ""),
            severity=data.get("severity", "Moderate"),
            interaction_type=data.get("interaction_type", ""),
            mechanism=data.get("mechanism", ""),
            clinical_consequence=data.get("clinical_consequence", ""),
            clinical_management=data.get("clinical_management", ""),
            evidence_level=data.get("evidence_level", "Level C"),
            citations=data.get("citations", [])
        )


class SupplementEvidenceRepository:
    """Репозиторий доказательных данных по БАДам и пищевым факторам."""

    def __init__(self, data_path: Path | str = SUPPLEMENTS_FILE):
        self.data_path = Path(data_path)
        self.interactions: list[SupplementInteraction] = []
        self.evidence_standards: dict[str, str] = {}
        self.reload()

    def reload(self) -> None:
        """Перечитывает файл доказательной базы."""
        self.interactions.clear()
        if not self.data_path.is_file():
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.evidence_standards = payload.get("evidence_standards", {})
            for raw_item in payload.get("interactions", []):
                self.interactions.append(SupplementInteraction.from_dict(raw_item))
        except Exception:
            self.interactions = []

    def get_by_drug(self, drug_canonical: str) -> list[SupplementInteraction]:
        """Возвращает все доказанные взаимодействия БАДов для конкретного канонического препарата."""
        clean = (drug_canonical or "").strip().lower()
        return [i for i in self.interactions if i.drug_canonical == clean]

    def get_all(self) -> list[SupplementInteraction]:
        """Возвращает полный список записей доказательной базы."""
        return list(self.interactions)

    def search(self, query: str) -> list[SupplementInteraction]:
        """Поиск по названию БАДа или лекарства."""
        q = (query or "").strip().lower()
        if not q:
            return self.get_all()
        return [
            i for i in self.interactions
            if q in i.supplement_ru.lower() or q in i.supplement_lat.lower()
            or q in i.drug_canonical.lower() or q in i.drug_ru.lower()
        ]
