"""Модуль нормализации названий лекарств, МНН и торговых наименований.

Обеспечивает научную строгость:
1. Однозначное сопоставление синонимов и торговых марок с каноническими МНН из DDInter.
2. Обнаружение многокомпонентных препаратов (комбинаций) без скрытого усечения состава.
3. Распознавание известных препаратов, отсутствующих в DDInter, с честным информированием.
4. Запрет на неявную автозамену при неоднозначности (ambiguity check).
"""
from dataclasses import dataclass, field
from difflib import get_close_matches
import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data"
SYNONYMS_PATH = DATA_DIR / "drug_synonyms.json"


@dataclass
class NormalizationResult:
    """Результат попытки нормализации названия препарата."""
    raw_query: str
    status: str  # 'canonical', 'synonym', 'combination', 'unsupported', 'not_found', 'ambiguous'
    canonical_name: str | None = None
    display_name: str = ""
    components: list[str] = field(default_factory=list)
    clarification_needed: bool = False
    message: str = ""
    suggestions: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_resolved(self) -> bool:
        """Успешно ли разрешено в один канонический идентификатор базы."""
        return self.status in ("canonical", "synonym") and self.canonical_name is not None

    @property
    def is_combination(self) -> bool:
        """Является ли препарат подтверждённой многокомпонентной комбинацией."""
        return self.status == "combination" and len(self.components) > 1


class DrugNormalizer:
    """Нормализатор названий препаратов на основе справочника синонимов и канонической базы."""

    def __init__(self, canonical_drugs: Any = None, synonyms_path: Path | str = SYNONYMS_PATH):
        self.canonical_drugs: set[str] = set(canonical_drugs) if canonical_drugs is not None else set()
        self.synonyms: dict[str, dict[str, Any]] = {}
        self.combinations: dict[str, dict[str, Any]] = {}
        self.unsupported: dict[str, dict[str, Any]] = {}
        self._load_synonyms(Path(synonyms_path))

    def _load_synonyms(self, path: Path) -> None:
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.synonyms = {k.strip().lower(): v for k, v in data.get("synonyms", {}).items()}
                self.combinations = {k.strip().lower(): v for k, v in data.get("combinations", {}).items()}
                self.unsupported = {k.strip().lower(): v for k, v in data.get("recognized_unsupported", {}).items()}
            except Exception:
                # В случае проблем со справочником работаем строго по каноническим МНН
                self.synonyms = {}
                self.combinations = {}
                self.unsupported = {}

    def set_canonical_drugs(self, drugs: set[str]) -> None:
        """Обновляет множество известных канонических МНН (например, из загрузчика DDInter)."""
        self.canonical_drugs = {d.strip().lower() for d in drugs}

    def normalize(self, query: str) -> NormalizationResult:
        """Нормализует строку запроса к каноническому виду с проверкой однозначности."""
        clean = (query or "").strip().lower()
        if not clean:
            return NormalizationResult(
                raw_query=query,
                status="not_found",
                message="Пустой запрос."
            )

        # 1. Точное совпадение с каноническим МНН в DDInter
        if clean in self.canonical_drugs:
            return NormalizationResult(
                raw_query=query,
                status="canonical",
                canonical_name=clean,
                display_name=clean,
                message=f"Найдено прямое совпадение в DDInter: {clean}."
            )

        # 2. Проверка комбинаций (многокомпонентных составов)
        if clean in self.combinations:
            comb = self.combinations[clean]
            comp_list = comb.get("components", [])
            ru_name = comb.get("ru", clean.title())
            desc = comb.get("description", "")
            return NormalizationResult(
                raw_query=query,
                status="combination",
                display_name=ru_name,
                components=comp_list,
                clarification_needed=True,
                message=f"«{ru_name}» — многокомпонентный препарат. {desc}",
                details=comb
            )

        # 3. Проверка однозначных синонимов и торговых наименований
        if clean in self.synonyms:
            entry = self.synonyms[clean]
            canonical = entry.get("canonical", "").strip().lower()
            ru_name = entry.get("ru", clean.title())
            en_inn = entry.get("en_inn", canonical.title())
            # Проверяем, существует ли каноническое вещество в активном наборе DDInter
            if not self.canonical_drugs or canonical in self.canonical_drugs:
                return NormalizationResult(
                    raw_query=query,
                    status="synonym",
                    canonical_name=canonical,
                    display_name=f"{ru_name} ({en_inn})",
                    message=f"Синоним «{ru_name}» сопоставлен с каноническим МНН «{canonical}».",
                    details=entry
                )
            else:
                return NormalizationResult(
                    raw_query=query,
                    status="unsupported",
                    canonical_name=canonical,
                    display_name=ru_name,
                    message=f"Вещество «{canonical}» известно, но отсутствует в текущем срезе DDInter.",
                    details=entry
                )

        # 4. Проверка известных препаратов, отсутствующих в DDInter
        if clean in self.unsupported:
            unsup = self.unsupported[clean]
            ru_name = unsup.get("ru", clean.title())
            reason = unsup.get("reason", "Препарат отсутствует в датасете DDInter.")
            return NormalizationResult(
                raw_query=query,
                status="unsupported",
                display_name=ru_name,
                message=f"«{ru_name}» распознан, но не поддерживается: {reason}",
                details=unsup
            )

        # 5. Поиск похожих вариантов (Fuzzy matching) без автоматической подмены
        search_corpus = list(self.canonical_drugs.union(self.synonyms.keys()).union(self.combinations.keys()))
        suggestions = get_close_matches(clean, search_corpus, n=5, cutoff=0.6)

        return NormalizationResult(
            raw_query=query,
            status="not_found",
            message="Препарат не найден в базе DDInter и справочнике синонимов.",
            suggestions=suggestions
        )

    def get_search_catalog(self) -> list[tuple[str, str]]:
        """Возвращает список пар (отображаемая_метка, каноническое_имя_или_ключ) для автокомплита в UI."""
        items: list[tuple[str, str]] = []
        # Добавляем русские синонимы с понятным указанием МНН
        for alias, info in sorted(self.synonyms.items(), key=lambda x: x[1].get("ru", x[0])):
            ru_label = info.get("ru", alias.title())
            canonical = info.get("canonical", alias)
            items.append((f"{ru_label} [{canonical}]", canonical))

        # Добавляем комбинации
        for comb_key, comb_info in sorted(self.combinations.items(), key=lambda x: x[1].get("ru", x[0])):
            ru_label = comb_info.get("ru", comb_key.title())
            items.append((f"{ru_label} [комбинация: {', '.join(comb_info.get('components', []))}]", comb_key))

        # Добавляем канонические английские МНН из DDInter
        for drug in sorted(self.canonical_drugs):
            items.append((drug, drug))

        # Убираем дубликаты по меткам с сохранением порядка
        seen = set()
        unique_items = []
        for label, val in items:
            if label.lower() not in seen:
                seen.add(label.lower())
                unique_items.append((label, val))
        return unique_items
