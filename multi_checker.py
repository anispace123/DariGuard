"""Анализатор списка лекарств (полипрагмазии) на взаимные взаимодействия.

Обеспечивает:
1. Защиту от повторов и обнаружение опасного терапевтического дублирования (одно МНН под разными марками).
2. Полный попарный анализ N*(N-1)/2 уникальных комбинаций.
3. Научную сортировку по тяжести (Major -> Moderate -> Minor -> Unknown -> Нет в базе).
4. Обязательный дисклеймер: отсутствие записи != безопасность.
"""
from dataclasses import dataclass, field
import itertools
from typing import Any
import pandas as pd

from normalization import DrugNormalizer, NormalizationResult


LEVEL_RANK = {
    "Major": 4,
    "Moderate": 3,
    "Minor": 2,
    "Unknown": 1,
    "Not in DB": 0
}

SEVERITY_BADGES = {
    "Major": "Major (Высокий риск)",
    "Moderate": "Moderate (Умеренный)",
    "Minor": "Minor (Незначительный)",
    "Unknown": "Unknown (Не классифицирован)",
    "Not in DB": "В базе нет записи"
}


@dataclass
class PairwiseInteraction:
    """Результат анализа одной конкретной пары препаратов."""
    drug_a: str
    drug_b: str
    display_a: str
    display_b: str
    level: str  # 'Major', 'Moderate', 'Minor', 'Unknown', 'Not in DB'
    in_ddinter: bool
    explanation: str = ""
    explanation_code: str = field(default_factory=str)
    severity_rank: int = 0

    def __post_init__(self) -> None:
        if not self.explanation_code:
            lvl = getattr(self, "level", "Not in DB")
            code_map = {
                "Major": "exp_major",
                "Moderate": "exp_moderate",
                "Minor": "exp_minor",
                "Unknown": "exp_unknown",
                "Not in DB": "exp_not_in_db",
            }
            self.explanation_code = code_map.get(lvl, "exp_not_in_db")

    def __getattr__(self, name: str) -> Any:
        if name == "explanation_code":
            lvl = getattr(self, "level", "Not in DB")
            code_map = {
                "Major": "exp_major",
                "Moderate": "exp_moderate",
                "Minor": "exp_minor",
                "Unknown": "exp_unknown",
                "Not in DB": "exp_not_in_db",
            }
            return code_map.get(lvl, "exp_not_in_db")
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


@dataclass
class MultiCheckReport:
    """Полный отчёт проверки списка препаратов."""
    raw_inputs: list[str]
    resolved_drugs: list[str]
    drug_to_inputs: dict[str, list[str]]
    duplicates_detected: list[str]
    unresolved_inputs: list[NormalizationResult]
    pairs: list[PairwiseInteraction]
    summary_counts: dict[str, int]
    overall_risk: str
    safety_disclaimer: str
    overall_risk_code: str = field(default_factory=str)
    safety_disclaimer_code: str = field(default_factory=lambda: "disclaimer_text")
    duplicates_structured: list[tuple[str, list[str]]] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Обеспечивает синхронизацию и обратную совместимость дубликатов и кодов риска."""
        if not self.duplicates and self.duplicates_detected:
            self.duplicates = list(self.duplicates_detected)
        elif not self.duplicates_detected and self.duplicates:
            self.duplicates_detected = list(self.duplicates)

        if not self.duplicates_structured and self.drug_to_inputs:
            self.duplicates_structured = [
                (canon, list(inputs))
                for canon, inputs in self.drug_to_inputs.items()
                if len(inputs) > 1
            ]

        # Автоматическая синхронизация кода общего риска
        if not getattr(self, "overall_risk_code", None):
            counts = getattr(self, "summary_counts", {}) or {}
            dups = getattr(self, "duplicates_structured", []) or getattr(self, "duplicates_detected", []) or []
            if counts.get("Major", 0) > 0 or len(dups) > 0:
                self.overall_risk_code = "HIGH"
            elif counts.get("Moderate", 0) > 0:
                self.overall_risk_code = "MODERATE"
            elif counts.get("Minor", 0) > 0:
                self.overall_risk_code = "LOW"
            elif counts.get("Unknown", 0) > 0:
                self.overall_risk_code = "UNDETERMINED"
            elif getattr(self, "overall_risk", ""):
                risk_upper = str(self.overall_risk).upper()
                if "ВЫСОК" in risk_upper or "HIGH" in risk_upper:
                    self.overall_risk_code = "HIGH"
                elif "УМЕРЕН" in risk_upper or "MODERATE" in risk_upper:
                    self.overall_risk_code = "MODERATE"
                elif "НИЗК" in risk_upper or "LOW" in risk_upper:
                    self.overall_risk_code = "LOW"
                elif "НЕОПРЕДЕЛ" in risk_upper or "UNDETERMINED" in risk_upper:
                    self.overall_risk_code = "UNDETERMINED"
                else:
                    self.overall_risk_code = "NO_DATA"
            else:
                self.overall_risk_code = "NO_DATA"

    def __getattr__(self, name: str) -> Any:
        if name == "duplicates_structured":
            if hasattr(self, "drug_to_inputs") and self.drug_to_inputs:
                return [
                    (canon, list(inputs))
                    for canon, inputs in self.drug_to_inputs.items()
                    if len(inputs) > 1
                ]
            return []
        if name == "duplicates":
            return getattr(self, "duplicates_detected", [])
        if name == "duplicates_detected":
            return getattr(self, "duplicates", [])
        if name == "overall_risk_code":
            counts = getattr(self, "summary_counts", {}) or {}
            dups = getattr(self, "duplicates_structured", []) or getattr(self, "duplicates_detected", []) or []
            if counts.get("Major", 0) > 0 or len(dups) > 0:
                return "HIGH"
            if counts.get("Moderate", 0) > 0:
                return "MODERATE"
            if counts.get("Minor", 0) > 0:
                return "LOW"
            if counts.get("Unknown", 0) > 0:
                return "UNDETERMINED"
            risk_upper = str(getattr(self, "overall_risk", "")).upper()
            if "ВЫСОК" in risk_upper or "HIGH" in risk_upper:
                return "HIGH"
            if "УМЕРЕН" in risk_upper or "MODERATE" in risk_upper:
                return "MODERATE"
            if "НИЗК" in risk_upper or "LOW" in risk_upper:
                return "LOW"
            if "НЕОПРЕДЕЛ" in risk_upper or "UNDETERMINED" in risk_upper:
                return "UNDETERMINED"
            return "NO_DATA"
        if name == "safety_disclaimer_code":
            return "disclaimer_text"
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def to_dataframe(self) -> pd.DataFrame:
        """Формирует структурированную таблицу результатов для отображения в UI."""
        rows = []
        for p in self.pairs:
            rows.append({
                "Препарат A": p.display_a,
                "Препарат B": p.display_b,
                "Уровень риска": SEVERITY_BADGES.get(p.level, p.level),
                "Статус базы": "Запись DDInter" if p.in_ddinter else "Нет записи (требует проверки)",
                "Пояснение": p.explanation
            })
        return pd.DataFrame(rows)


class MultiDrugChecker:
    """Движок анализа списка препаратов."""

    def __init__(self, pairs_df: pd.DataFrame, normalizer: DrugNormalizer):
        self.normalizer = normalizer
        # Быстрый словарь пар: tuple(sorted([a, b])) -> Level
        self.interaction_map: dict[tuple[str, str], str] = {}
        for _, row in pairs_df.iterrows():
            a, b, lvl = row["Drug_A"], row["Drug_B"], row["Level"]
            pair_key = (min(a, b), max(a, b))
            self.interaction_map[pair_key] = lvl

    def check_list(self, raw_drug_queries: list[str]) -> MultiCheckReport:
        """Выполняет комплексный анализ списка лекарственных средств."""
        # 1. Нормализация и валидация ввода
        cleaned_queries = [q.strip() for q in raw_drug_queries if q and q.strip()]
        resolved_map: dict[str, list[str]] = {}  # canonical -> list of raw queries
        unresolved: list[NormalizationResult] = []

        for q in cleaned_queries:
            norm_res = self.normalizer.normalize(q)
            if norm_res.is_resolved and norm_res.canonical_name:
                canon = norm_res.canonical_name
                resolved_map.setdefault(canon, []).append(q)
            elif norm_res.is_combination:
                # Для комбинаций включаем все активные компоненты
                for comp in norm_res.components:
                    comp_norm = self.normalizer.normalize(comp)
                    if comp_norm.is_resolved and comp_norm.canonical_name:
                        resolved_map.setdefault(comp_norm.canonical_name, []).append(f"{q} ({comp})")
                    else:
                        unresolved.append(comp_norm)
            else:
                unresolved.append(norm_res)

        # 2. Обнаружение опасного дублирования активных веществ
        duplicates: list[str] = []
        duplicates_structured: list[tuple[str, list[str]]] = []
        for canon, inputs in resolved_map.items():
            if len(inputs) > 1:
                duplicates.append(
                    f"Терапевтическое дублирование: действующее вещество «{canon}» входит одновременно в несколько выбранных позиций: {', '.join(inputs)}."
                )
                duplicates_structured.append((canon, inputs))

        # 3. Анализ всех уникальных пар
        canonical_list = sorted(resolved_map.keys())
        pairwise_results: list[PairwiseInteraction] = []
        counts = {"Major": 0, "Moderate": 0, "Minor": 0, "Unknown": 0, "Not in DB": 0}

        for drug_a, drug_b in itertools.combinations(canonical_list, 2):
            key = (min(drug_a, drug_b), max(drug_a, drug_b))
            level = self.interaction_map.get(key, "Not in DB")
            in_db = level != "Not in DB"
            counts[level] = counts.get(level, 0) + 1

            disp_a = f"{drug_a.title()} ({', '.join(resolved_map[drug_a])})"
            disp_b = f"{drug_b.title()} ({', '.join(resolved_map[drug_b])})"

            if level == "Major":
                exp = "Высокий риск клинически значимого взаимодействия. Требует оценки врачом."
                exp_code = "exp_major"
            elif level == "Moderate":
                exp = "Умеренный риск. Возможно изменение терапевтической концентрации или эффекта."
                exp_code = "exp_moderate"
            elif level == "Minor":
                exp = "Незначительный риск по классификации DDInter."
                exp_code = "exp_minor"
            elif level == "Unknown":
                exp = "Запись зарегистрирована в исследовательской базе, но степень тяжести не указана."
                exp_code = "exp_unknown"
            else:
                exp = "Запись в DDInter не найдена. Отсутствие записи НЕ подтверждает безопасность."
                exp_code = "exp_not_in_db"

            pairwise_results.append(PairwiseInteraction(
                drug_a=drug_a,
                drug_b=drug_b,
                display_a=disp_a,
                display_b=disp_b,
                level=level,
                in_ddinter=in_db,
                explanation=exp,
                explanation_code=exp_code,
                severity_rank=LEVEL_RANK.get(level, 0)
            ))

        # Сортировка по тяжести: Major в первую очередь
        pairwise_results.sort(key=lambda x: x.severity_rank, reverse=True)

        # Оценка общего уровня риска профиля
        if counts["Major"] > 0 or len(duplicates) > 0:
            overall = "ВЫСОКИЙ РИСК"
            overall_code = "HIGH"
        elif counts["Moderate"] > 0:
            overall = "УМЕРЕННЫЙ РИСК"
            overall_code = "MODERATE"
        elif counts["Minor"] > 0:
            overall = "НИЗКИЙ РИСК"
            overall_code = "LOW"
        elif counts["Unknown"] > 0:
            overall = "НЕОПРЕДЕЛЁННЫЙ РИСК"
            overall_code = "UNDETERMINED"
        else:
            overall = "ДАННЫЕ В DDINTER ОТСУТСТВУЮТ"
            overall_code = "NO_DATA"

        disclaimer = (
            "Внимание: Анализ основан исключительно на сопоставлении с научной базой DDInter. "
            "Отсутствие записи для комбинации не гарантирует её фармакологическую безопасность. "
            "Проект не заменяет консультацию врача и клинического фармаколога."
        )

        return MultiCheckReport(
            raw_inputs=cleaned_queries,
            resolved_drugs=canonical_list,
            drug_to_inputs=resolved_map,
            duplicates_detected=duplicates,
            unresolved_inputs=unresolved,
            pairs=pairwise_results,
            summary_counts=counts,
            overall_risk=overall,
            safety_disclaimer=disclaimer,
            overall_risk_code=overall_code,
            safety_disclaimer_code="disclaimer_text",
            duplicates_structured=duplicates_structured,
            duplicates=duplicates
        )
