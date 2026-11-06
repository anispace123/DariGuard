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
    message_code: str = field(default_factory=str)
    message_params: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.message_code:
            status = getattr(self, "status", "unknown")
            self.message_code = f"norm_{status}"

    @property
    def is_resolved(self) -> bool:
        """Успешно ли разрешено в один канонический идентификатор базы."""
        return self.status in ("canonical", "synonym") and self.canonical_name is not None

    @property
    def is_combination(self) -> bool:
        """Является ли препарат подтверждённой многокомпонентной комбинацией."""
        return self.status == "combination" and len(self.components) > 1

    def __getattr__(self, name: str) -> Any:
        if name == "message_code":
            status = getattr(self, "status", "unknown")
            return f"norm_{status}"
        if name == "message_params":
            return {}
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


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
                message=f"Найдено прямое совпадение в DDInter: {clean}.",
                message_code="norm_canonical",
                message_params={"canonical": clean}
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
                message_code="norm_combination",
                message_params={"name": ru_name, "components": comp_list, "desc": desc},
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
                    message_code="norm_synonym",
                    message_params={"alias": ru_name, "canonical": canonical},
                    details=entry
                )
            else:
                return NormalizationResult(
                    raw_query=query,
                    status="unsupported",
                    canonical_name=canonical,
                    display_name=ru_name,
                    message=f"Вещество «{canonical}» известно, но отсутствует в текущем срезе DDInter.",
                    message_code="norm_unsupported_inn",
                    message_params={"canonical": canonical},
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
                message_code="norm_unsupported",
                message_params={"name": ru_name, "reason": reason},
                details=unsup
            )

        # 5. Поиск похожих вариантов (Fuzzy matching) без автоматической подмены
        search_corpus = list(self.canonical_drugs.union(self.synonyms.keys()).union(self.combinations.keys()))
        suggestions = get_close_matches(clean, search_corpus, n=5, cutoff=0.6)

        return NormalizationResult(
            raw_query=query,
            status="not_found",
            message="Препарат не найден в базе DDInter и справочнике синонимов.",
            message_code="norm_not_found",
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

    def get_canonical_catalog_label(self, canonical_or_query: str) -> str | None:
        """Находит приоритетную отображаемую метку в каталоге для заданного препарата."""
        return get_canonical_catalog_label(self, canonical_or_query)

    def __getattr__(self, name: str) -> Any:
        if name == "get_canonical_catalog_label":
            return lambda query: get_canonical_catalog_label(self, query)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


def get_canonical_catalog_label(normalizer: Any, canonical_or_query: str) -> str | None:
    """Находит приоритетную отображаемую метку в каталоге для заданного препарата.

    Приоритет:
    1. Официальный перевод МНН (type == 'inn_translation'), например 'Эналаприл [enalapril]'
    2. Известный бренд (type == 'brand'), например 'Кордарон [amiodarone]'
    3. Каноническое английское имя из базы DDInter
    """
    if hasattr(normalizer, "normalize"):
        try:
            norm = normalizer.normalize(canonical_or_query)
            canon = norm.canonical_name if getattr(norm, "is_resolved", False) and norm.canonical_name else (canonical_or_query or "").strip().lower()
        except Exception:
            canon = (canonical_or_query or "").strip().lower()
    else:
        canon = (canonical_or_query or "").strip().lower()

    synonyms = getattr(normalizer, "synonyms", {})
    canonical_drugs = getattr(normalizer, "canonical_drugs", set())

    # 1. Поиск официального МНН в справочнике
    for alias, info in sorted(synonyms.items()):
        if info.get("canonical") == canon and info.get("type") == "inn_translation":
            ru = info.get("ru", alias.title())
            return f"{ru} [{canon}]"

    # 2. Поиск по брендам
    for alias, info in sorted(synonyms.items()):
        if info.get("canonical") == canon:
            ru = info.get("ru", alias.title())
            return f"{ru} [{canon}]"

    # 3. Английское МНН
    if canon in canonical_drugs:
        return canon

    return None


def safe_catalog_label(
    norm: Any,
    query: str,
    labels: list[str] | None = None,
    mapping: dict[str, str] | None = None
) -> str | None:
    """Безопасный поиск отображаемой метки препарата с тройным уровнем защиты от устаревших кэшей."""
    lbl = None
    fn = getattr(norm, "get_canonical_catalog_label", None)
    if fn is not None:
        try:
            lbl = fn(query)
        except Exception:
            lbl = None
    if not lbl:
        try:
            lbl = get_canonical_catalog_label(norm, query)
        except Exception:
            lbl = None

    if lbl and (labels is None or lbl in labels):
        return lbl

    clean_q = (query or "").strip().lower()
    if labels:
        if mapping:
            for l, val in mapping.items():
                if val == clean_q:
                    return l
        for l in labels:
            if clean_q in l.lower():
                return l
    return None


