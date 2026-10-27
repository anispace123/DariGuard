"""Функции построения графа и его описательных таблиц."""
import numpy as np
import pandas as pd


def build_adjacency(pairs: pd.DataFrame, drugs: pd.DataFrame) -> np.ndarray:
    """Строит симметричную матрицу связей без петель."""
    ids = dict(zip(drugs["drug"], drugs["node_id"]))
    n = len(drugs)
    adjacency = np.zeros((n, n), dtype=np.uint8)
    left = pairs["Drug_A"].map(ids).to_numpy(dtype=int)
    right = pairs["Drug_B"].map(ids).to_numpy(dtype=int)
    adjacency[left, right] = 1
    adjacency[right, left] = 1
    return adjacency


def major_hubs(pairs: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Считает число Major-связей у каждого препарата."""
    major = pairs.loc[pairs["Level"] == "Major", ["Drug_A", "Drug_B"]]
    counts = pd.concat([major["Drug_A"], major["Drug_B"]]).value_counts()
    return counts.rename_axis("Препарат").rename("Major-связи").head(limit).reset_index()


def interaction_color(level: str) -> str:
    """Цвет линии для уровня DDInter."""
    return {"Major": "#fb7185", "Moderate": "#fbbf24", "Minor": "#34d399", "Unknown": "#94a3b8"}.get(level, "#94a3b8")
