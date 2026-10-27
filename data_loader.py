"""Загрузка и проверка исходных CSV-файлов DDInter."""
from pathlib import Path
import glob

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "data"
CSV_PATTERN = "ddinter_downloads_code_*.csv"
REQUIRED_COLUMNS = ["DDInterID_A", "Drug_A", "DDInterID_B", "Drug_B", "Level"]
LEVEL_WEIGHT = {"Unknown": 0, "Minor": 1, "Moderate": 2, "Major": 3}


class DataValidationError(ValueError):
    """Ошибка формата исходных данных, которую можно показать пользователю."""


def load_ddinter(data_dir: str | Path = DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Читает восемь CSV DDInter и возвращает пары и справочник препаратов."""
    folder = Path(data_dir)
    paths = sorted(glob.glob(str(folder / CSV_PATTERN)))
    if not paths:
        raise FileNotFoundError(
            f"В папке {folder} не найдены файлы {CSV_PATTERN}. Скачайте CSV-файлы "
            "с сайта ddinter.scbdd.com в разделе Download и поместите их в папку data/."
        )

    parts = []
    for path in paths:
        try:
            part = pd.read_csv(path)
        except Exception as exc:
            raise DataValidationError(f"Не удалось прочитать файл {Path(path).name}: {exc}") from exc
        missing = [column for column in REQUIRED_COLUMNS if column not in part.columns]
        if missing:
            raise DataValidationError(
                f"В файле {Path(path).name} отсутствуют колонки: {', '.join(missing)}. "
                f"Ожидаются: {', '.join(REQUIRED_COLUMNS)}."
            )
        parts.append(part[REQUIRED_COLUMNS].copy())

    raw = pd.concat(parts, ignore_index=True)
    raw["Drug_A"] = raw["Drug_A"].astype("string").str.strip().str.lower()
    raw["Drug_B"] = raw["Drug_B"].astype("string").str.strip().str.lower()
    raw["Level"] = raw["Level"].astype("string").str.strip().str.title()
    bad_levels = sorted(set(raw["Level"].dropna()) - set(LEVEL_WEIGHT))
    if bad_levels:
        raise DataValidationError("Неизвестные значения Level: " + ", ".join(bad_levels))
    raw = raw.dropna(subset=["Drug_A", "Drug_B", "Level"])

    # Каноническая пара хранится один раз, независимо от порядка A и B.
    original_a, original_b = raw["Drug_A"].copy(), raw["Drug_B"].copy()
    raw["Drug_A"] = original_a.where(original_a <= original_b, original_b)
    raw["Drug_B"] = original_b.where(original_a <= original_b, original_a)
    raw = raw.loc[raw["Drug_A"] != raw["Drug_B"]].copy()
    raw["_weight"] = raw["Level"].map(LEVEL_WEIGHT)
    raw = raw.sort_values("_weight").drop_duplicates(["Drug_A", "Drug_B"], keep="last")
    pairs = raw[REQUIRED_COLUMNS].reset_index(drop=True)

    names = sorted(set(pairs["Drug_A"]).union(pairs["Drug_B"]))
    drugs = pd.DataFrame({"drug": names, "node_id": range(len(names))})
    return pairs, drugs
