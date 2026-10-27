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
    "Major": "🔴 Major (Высокий риск)",
    "Moderate": "🟠 Moderate (Умеренный)",
    "Minor": "🟢 Minor (Незначительный)",
    "Unknown": "⚪ Unknown (Не классифицирован)",
    "Not in DB": "⚠️ В базе нет записи"
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
    severity_rank: int = 0


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
        for canon, inputs in resolved_map.items():
            if len(inputs) > 1:
                duplicates.append(
                    f"Терапевтическое дублирование: действующее вещество «{canon}» входит одновременно в несколько выбранных позиций: {', '.join(inputs)}."
                )

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
            elif level == "Moderate":
                exp = "Умеренный риск. Возможно изменение терапевтической концентрации или эффекта."
            elif level == "Minor":
                exp = "Незначительный риск по классификации DDInter."
            elif level == "Unknown":
                exp = "Запись зарегистрирована в исследовательской базе, но степень тяжести не указана."
            else:
                exp = "Запись в DDInter не найдена. Отсутствие записи НЕ подтверждает безопасность."

            pairwise_results.append(PairwiseInteraction(
                drug_a=drug_a,
                drug_b=drug_b,
                display_a=disp_a,
                display_b=disp_b,
                level=level,
                in_ddinter=in_db,
                explanation=exp,
                severity_rank=LEVEL_RANK.get(level, 0)
            ))

        # Сортировка по тяжести: Major в первую очередь
        pairwise_results.sort(key=lambda x: x.severity_rank, reverse=True)

        # Оценка общего уровня риска профиля
        if counts["Major"] > 0 or len(duplicates) > 0:
            overall = "ВЫСОКИЙ РИСК"
        elif counts["Moderate"] > 0:
            overall = "УМЕРЕННЫЙ РИСК"
        elif counts["Minor"] > 0:
            overall = "НИЗКИЙ РИСК"
        elif counts["Unknown"] > 0:
            overall = "НЕОПРЕДЕЛЁННЫЙ РИСК"
        else:
            overall = "ДАННЫЕ В DDINTER ОТСУТСТВУЮТ"

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
            safety_disclaimer=disclaimer
        )
