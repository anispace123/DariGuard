"""Обучение и честная оценка моделей предсказания связей."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import auc, confusion_matrix, precision_recall_curve, roc_auc_score, roc_curve
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


RANDOM_STATE = 42
FEATURE_NAMES = ["Общие соседи", "Жаккар", "Adamic-Adar", "Степень A", "Степень B", "Произведение степеней"]


def graph_matrices(adjacency: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Рассчитывает общих соседей, степени и Adamic-Adar по одному графу."""
    matrix = adjacency.astype(np.int32, copy=False)
    common = matrix @ matrix
    degree = matrix.sum(axis=1).astype(np.float64)
    # Вес общего соседа: чем он популярнее, тем меньше его вклад.
    weights = np.zeros_like(degree)
    valid = degree > 1
    weights[valid] = 1.0 / np.log(degree[valid])
    adamic_adar = (matrix * weights[np.newaxis, :]) @ matrix
    return common.astype(np.float32), degree, adamic_adar.astype(np.float32)


def pair_features(pair_indices: np.ndarray, common: np.ndarray, degree: np.ndarray,
                  adamic_adar: np.ndarray) -> np.ndarray:
    """Формирует шесть симметричных признаков для списка пар узлов."""
    i, j = pair_indices[:, 0], pair_indices[:, 1]
    cn = common[i, j].astype(np.float32)
    denominator = degree[i] + degree[j] - cn
    jaccard = np.divide(cn, denominator, out=np.zeros_like(cn), where=denominator > 0)
    return np.column_stack((cn, jaccard, adamic_adar[i, j], degree[i], degree[j], degree[i] * degree[j])).astype(np.float32)


def _edge_indices(pairs: pd.DataFrame, drugs: pd.DataFrame) -> np.ndarray:
    ids = dict(zip(drugs["drug"], drugs["node_id"]))
    left = pairs["Drug_A"].map(ids).to_numpy(dtype=np.int32)
    right = pairs["Drug_B"].map(ids).to_numpy(dtype=np.int32)
    return np.column_stack((np.minimum(left, right), np.maximum(left, right)))


def _encode(pair_indices: np.ndarray, n: int) -> np.ndarray:
    return pair_indices[:, 0].astype(np.int64) * n + pair_indices[:, 1]


def _balanced_negative_pool(n: int, known_codes: np.ndarray, size: int, rng: np.random.Generator) -> np.ndarray:
    """Равномерно выбирает пары, которых нет во всей базе DDInter."""
    upper = np.triu_indices(n, k=1)
    all_codes = upper[0].astype(np.int64) * n + upper[1]
    allowed = all_codes[~np.isin(all_codes, known_codes, assume_unique=False)]
    if size > len(allowed):
        raise ValueError("Недостаточно неизвестных пар для сбалансированной проверки.")
    chosen = rng.choice(allowed, size=size, replace=False)
    return np.column_stack((chosen // n, chosen % n)).astype(np.int32)


def train_and_evaluate(pairs: pd.DataFrame, drugs: pd.DataFrame) -> dict:
    """Разбивает связи на train/test/граф и сравнивает ML с простыми правилами."""
    rng = np.random.default_rng(RANDOM_STATE)
    n = len(drugs)
    edges = _edge_indices(pairs, drugs)
    order = rng.permutation(len(edges))
    # 12% связей служат обучающими положительными примерами, 20% — тестовыми.
    train_count = int(round(len(edges) * 0.12))
    test_count = int(round(len(edges) * 0.20))
    train_pos = edges[order[:train_count]]
    test_pos = edges[order[train_count:train_count + test_count]]
    graph_pos = edges[order[train_count + test_count:]]

    known_codes = _encode(edges, n)
    # Один общий пул исключает пересечение train- и test-негативов.
    negative_pool = _balanced_negative_pool(n, known_codes, len(train_pos) + len(test_pos), rng)
    train_neg = negative_pool[:len(train_pos)]
    test_neg = negative_pool[len(train_pos):]

    # Признаки строятся только по оставшимся 68% связей.
    graph = np.zeros((n, n), dtype=np.uint8)
    graph[graph_pos[:, 0], graph_pos[:, 1]] = 1
    graph[graph_pos[:, 1], graph_pos[:, 0]] = 1
    common, degree, aa = graph_matrices(graph)

    x_train = pair_features(np.vstack((train_pos, train_neg)), common, degree, aa)
    y_train = np.r_[np.ones(len(train_pos), dtype=np.uint8), np.zeros(len(train_neg), dtype=np.uint8)]
    x_test = pair_features(np.vstack((test_pos, test_neg)), common, degree, aa)
    y_test = np.r_[np.ones(len(test_pos), dtype=np.uint8), np.zeros(len(test_neg), dtype=np.uint8)]
    train_shuffle, test_shuffle = rng.permutation(len(y_train)), rng.permutation(len(y_test))
    x_train, y_train = x_train[train_shuffle], y_train[train_shuffle]
    x_test, y_test = x_test[test_shuffle], y_test[test_shuffle]

    logistic = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=RANDOM_STATE))
    forest = RandomForestClassifier(n_estimators=200, min_samples_leaf=5, random_state=RANDOM_STATE, n_jobs=-1)
    logistic.fit(x_train, y_train)
    forest.fit(x_train, y_train)

    # Простые baseline-оценки используют те же признаки и тот же тест.
    methods_meta = [
        ("random_forest", "Случайный лес", forest.predict_proba(x_test)[:, 1]),
        ("logreg", "Логистическая регрессия", logistic.predict_proba(x_test)[:, 1]),
        ("common_neighbors", "Только общие соседи", x_test[:, 0]),
        ("degree", "Только степень", x_test[:, 3] * x_test[:, 4]),
        ("random", "Случайное угадывание", rng.random(len(y_test))),
    ]
    raw_scores = {name: scores for _, name, scores in methods_meta}
    metric_rows, roc_data = [], {}
    for method_id, name, scores in methods_meta:
        precisions, recalls, _ = precision_recall_curve(y_test, scores)
        metric_rows.append({
            "method_id": method_id,
            "Метод": name,
            "ROC-AUC": roc_auc_score(y_test, scores),
            "PR-AUC": auc(recalls, precisions),
            "Precision@5000": float(y_test[np.argsort(scores)[::-1][:min(5000, len(scores))]].mean())
        })
        fpr, tpr, _ = roc_curve(y_test, scores)
        roc_data[name] = (fpr, tpr)
    predictions = (raw_scores["Случайный лес"] >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()

    return {
        "metrics": pd.DataFrame(metric_rows), "roc": roc_data,
        "confusion": np.array([[tn, fp], [fn, tp]]),
        "train_examples": len(y_train), "test_examples": len(y_test),
        "train_positive": len(train_pos), "test_positive": len(test_pos),
        "best_name": "Случайный лес", "best_method_id": "random_forest", "best_model": forest,
        "logreg_model": logistic,
        "feature_matrices": (common, degree, aa), "n": n,
    }


def predict_pair_ml_intelligence(
    drug_a: str,
    drug_b: str,
    pairs: pd.DataFrame,
    drugs: pd.DataFrame,
    evaluation: dict,
    top_bridges: int = 8,
) -> dict:
    """Выполняет персональный ML-прогноз и топологический аудит для конкретной пары препаратов.

    Возвращает:
    - rf_score: Оценка RandomForest (0.0 - 1.0)
    - logreg_score: Оценка LogisticRegression (0.0 - 1.0)
    - ensemble_score: Комбинированный индекс структурного сродства в графе DDInter (0.0 - 1.0)
    - common_neighbors_count: Число общих соседей в обучающем графе
    - jaccard: Коэффициент Жаккара
    - adamic_adar: Индекс Адамик-Адара
    - degree_a, degree_b: Степени связности препаратов A и B
    - major_links_a, major_links_b: Число критических (Major) взаимодействий каждого препарата в DDInter
    - shared_bridges: Список общих препаратов-посредников, связывающих Drug A и Drug B в клинической сети
    - in_ddinter_level: Зарегистрированный уровень в DDInter (или None)
    """
    norm_a = (drug_a or "").strip().lower()
    norm_b = (drug_b or "").strip().lower()
    ids = dict(zip(drugs["drug"], drugs["node_id"]))
    common, degree, aa = evaluation["feature_matrices"]

    idx_a = ids.get(norm_a)
    idx_b = ids.get(norm_b)

    if idx_a is None or idx_b is None or idx_a == idx_b:
        return {
            "valid": False,
            "rf_score": 0.0,
            "logreg_score": 0.0,
            "ensemble_score": 0.0,
            "common_neighbors_count": 0,
            "jaccard": 0.0,
            "adamic_adar": 0.0,
            "degree_a": 0,
            "degree_b": 0,
            "major_links_a": 0,
            "major_links_b": 0,
            "shared_bridges": [],
            "in_ddinter_level": None,
        }

    pair_arr = np.array([[min(idx_a, idx_b), max(idx_a, idx_b)]], dtype=np.int32)
    feats = pair_features(pair_arr, common, degree, aa)
    rf_model = evaluation["best_model"]
    rf_prob = float(rf_model.predict_proba(feats)[0, 1])

    logreg_model = evaluation.get("logreg_model")
    lr_prob = float(logreg_model.predict_proba(feats)[0, 1]) if logreg_model is not None else rf_prob
    ensemble_prob = float(0.7 * rf_prob + 0.3 * lr_prob)

    # Поиск реального статуса в DDInter и общих препаратов-посредников (Bridge Drugs)
    low_d, high_d = min(norm_a, norm_b), max(norm_a, norm_b)
    direct_match = pairs[(pairs["Drug_A"] == low_d) & (pairs["Drug_B"] == high_d)]
    in_ddinter_level = str(direct_match.iloc[0]["Level"]) if not direct_match.empty else None

    rows_a = pairs[(pairs["Drug_A"] == norm_a) | (pairs["Drug_B"] == norm_a)]
    rows_b = pairs[(pairs["Drug_A"] == norm_b) | (pairs["Drug_B"] == norm_b)]

    major_a = int((rows_a["Level"] == "Major").sum())
    major_b = int((rows_b["Level"] == "Major").sum())

    nbrs_a = dict(zip(np.where(rows_a["Drug_A"] == norm_a, rows_a["Drug_B"], rows_a["Drug_A"]), rows_a["Level"]))
    nbrs_b = dict(zip(np.where(rows_b["Drug_A"] == norm_b, rows_b["Drug_B"], rows_b["Drug_A"]), rows_b["Level"]))

    shared_keys = set(nbrs_a.keys()).intersection(nbrs_b.keys()) - {norm_a, norm_b}
    sev_rank = {"Major": 0, "Moderate": 1, "Minor": 2, "Unknown": 3}
    bridge_rows = []
    for br in shared_keys:
        lvl_a = nbrs_a[br]
        lvl_b = nbrs_b[br]
        score_rank = sev_rank.get(lvl_a, 3) + sev_rank.get(lvl_b, 3)
        bridge_rows.append({
            "bridge_drug": br,
            "level_with_a": lvl_a,
            "level_with_b": lvl_b,
            "rank": score_rank,
        })
    bridge_rows.sort(key=lambda x: (x["rank"], x["bridge_drug"]))

    return {
        "valid": True,
        "rf_score": rf_prob,
        "logreg_score": lr_prob,
        "ensemble_score": ensemble_prob,
        "common_neighbors_count": int(feats[0, 0]),
        "jaccard": float(feats[0, 1]),
        "adamic_adar": float(feats[0, 2]),
        "degree_a": int(degree[idx_a]),
        "degree_b": int(degree[idx_b]),
        "full_common_neighbors_count": len(shared_keys),
        "major_links_a": major_a,
        "major_links_b": major_b,
        "shared_bridges": bridge_rows[:top_bridges],
        "in_ddinter_level": in_ddinter_level,
    }


def novel_pair_hypotheses(pairs: pd.DataFrame, drugs: pd.DataFrame, evaluation: dict,
                         candidate_count: int = 20_000, limit: int = 20) -> pd.DataFrame:
    """Ранжирует новые пары из пула с наибольшим Adamic-Adar."""
    common, degree, aa = evaluation["feature_matrices"]
    n = evaluation["n"]
    # В список кандидатов попадают только пары, которых нет ни в одной строке DDInter.
    upper = np.triu_indices(n, k=1)
    all_codes = upper[0].astype(np.int64) * n + upper[1]
    ids = dict(zip(drugs["drug"], drugs["node_id"]))
    known = _encode(_edge_indices(pairs, drugs), n)
    novel_mask = ~np.isin(all_codes, known, assume_unique=False)
    novel_i, novel_j, novel_codes = upper[0][novel_mask], upper[1][novel_mask], all_codes[novel_mask]
    scores = aa[novel_i, novel_j]
    count = min(candidate_count, len(scores))
    top = np.argpartition(scores, -count)[-count:] if count else np.array([], dtype=int)
    candidate_pairs = np.column_stack((novel_i[top], novel_j[top])).astype(np.int32)
    features = pair_features(candidate_pairs, common, degree, aa)
    model = evaluation["best_model"]
    raw_model_scores = model.predict_proba(features)[:, 1]
    # Переводим выход модели в относительный ранг внутри пула: это шкала
    # приоритета для списка, а не оценка вероятности взаимодействия.
    ranks = np.argsort(np.argsort(raw_model_scores, kind="stable"), kind="stable")
    model_scores = ranks / max(len(ranks) - 1, 1)
    order = np.argsort(model_scores)[::-1][:limit]
    names = drugs.set_index("node_id")["drug"]
    return pd.DataFrame({"Препарат A": [names.iloc[i] for i in candidate_pairs[order, 0]],
                         "Препарат B": [names.iloc[j] for j in candidate_pairs[order, 1]],
                         "Оценка модели (не вероятность)": model_scores[order],
                         "Adamic-Adar": features[order, 2]})
