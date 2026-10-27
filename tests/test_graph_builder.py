"""Тесты модуля построения графа."""
import unittest
import numpy as np
import pandas as pd
from graph_builder import build_adjacency, major_hubs, interaction_color


class TestGraphBuilder(unittest.TestCase):
    """Проверка создания матрицы смежности и расчета хабов."""

    def setUp(self):
        self.drugs = pd.DataFrame({
            "drug": ["aspirin", "warfarin", "ibuprofen", "paracetamol"],
            "node_id": [0, 1, 2, 3]
        })
        self.pairs = pd.DataFrame({
            "DDInterID_A": ["D1", "D1", "D2"],
            "Drug_A": ["aspirin", "aspirin", "ibuprofen"],
            "DDInterID_B": ["D2", "D3", "D4"],
            "Drug_B": ["ibuprofen", "warfarin", "paracetamol"],
            "Level": ["Major", "Major", "Moderate"]
        })

    def test_build_adjacency_symmetry(self):
        """Матрица смежности должна быть симметричной и не иметь петель на диагонали."""
        adj = build_adjacency(self.pairs, self.drugs)
        self.assertEqual(adj.shape, (4, 4))
        # Симметрия
        np.testing.assert_array_equal(adj, adj.T)
        # Отсутствие петель
        self.assertEqual(np.diag(adj).sum(), 0)
        # Проверка ребер
        self.assertEqual(adj[0, 1], 1)  # aspirin - warfarin
        self.assertEqual(adj[0, 2], 1)  # aspirin - ibuprofen
        self.assertEqual(adj[1, 3], 0)  # warfarin - paracetamol (нет связи)

    def test_major_hubs(self):
        """Подсчет препаратов с наибольшим числом Major связей."""
        hubs = major_hubs(self.pairs, limit=2)
        self.assertIsInstance(hubs, pd.DataFrame)
        self.assertIn("Препарат", hubs.columns)
        self.assertIn("Major-связи", hubs.columns)
        # aspirin имеет 2 Major связи
        top_drug = hubs.iloc[0]["Препарат"]
        top_count = hubs.iloc[0]["Major-связи"]
        self.assertEqual(top_drug, "aspirin")
        self.assertEqual(top_count, 2)

    def test_interaction_color(self):
        """Проверка сопоставления цветов для уровней."""
        self.assertEqual(interaction_color("Major"), "#fb7185")
        self.assertEqual(interaction_color("Moderate"), "#fbbf24")
        self.assertEqual(interaction_color("Minor"), "#34d399")
        self.assertEqual(interaction_color("Unknown"), "#94a3b8")
        self.assertEqual(interaction_color("NonExistent"), "#94a3b8")


if __name__ == "__main__":
    unittest.main()
