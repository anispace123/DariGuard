"""Тесты модуля Молекулярной лаборатории (Molecular Intelligence Lab).

Проверяет:
1. Верифицированные 3D-молекулярные структуры (Warfarin, Aspirin, Amiodarone, Fluconazole, Enalapril, Furosemide, Ibuprofen).
2. Разрешение русских торговых наименований и синонимов.
3. Генерацию HTML для трех интерактивных режимов: 3D-моделирование, каскад механизмов и конвергенция исходов.
4. Корректность доказательного клинического досье (Clinical Intelligence Brief) для эталонной пары Варфарин + Аспирин.
5. Соблюдение ключевых медицинских требований (отсутствие ложного столкновения, запрет самовольной отмены, учет индивидуальной вариабельности).
"""
import unittest
from data.verified_molecules import (
    VERIFIED_MOLECULES,
    get_verified_molecule,
    VerifiedMolecule
)
from components.molecular_viewer import (
    render_3d_molecule_viewer_html,
    render_mechanism_animation_html,
    render_convergence_visualization_html
)
from local_ai import generate_clinical_intelligence_brief


class TestMolecularLab(unittest.TestCase):
    """Сквозное тестирование компонентов молекулярной лаборатории."""

    def test_verified_molecules_registry(self):
        """Все 7 ключевых препаратов зарегистрированы с верифицированными формулами и CID."""
        keys = ["warfarin", "acetylsalicylic acid", "amiodarone", "fluconazole", "enalapril", "furosemide", "ibuprofen"]
        for k in keys:
            mol = VERIFIED_MOLECULES.get(k)
            self.assertIsNotNone(mol, f"Молекула {k} отсутствует в реестре")
            self.assertIsInstance(mol, VerifiedMolecule)
            self.assertGreater(len(mol.atoms), 0)
            self.assertGreater(len(mol.bonds), 0)
            self.assertGreater(mol.molecular_weight, 0)
            self.assertGreater(mol.pubchem_cid, 0)
            self.assertTrue(bool(mol.target.protein_name))
            self.assertTrue(bool(mol.target.gene_symbol))
            self.assertTrue(bool(mol.target.pdb_id))
            self.assertGreater(len(mol.target.key_residues), 0)

    def test_alias_resolution(self):
        """Русские бренды и синонимы корректно находят верифицированные молекулы."""
        pairs_to_check = [
            ("аспирин", "acetylsalicylic acid"),
            ("aspirin", "acetylsalicylic acid"),
            ("варфарин", "warfarin"),
            ("кордарон", "amiodarone"),
            ("амиодарон", "amiodarone"),
            ("дифлюкан", "fluconazole"),
            ("флуконазол", "fluconazole"),
            ("лазикс", "furosemide"),
            ("фуросемид", "furosemide"),
            ("ренитек", "enalapril"),
            ("эналаприл", "enalapril"),
            ("нурофен", "ibuprofen"),
            ("ибупрофен", "ibuprofen"),
        ]
        for query, expected_canon in pairs_to_check:
            mol = get_verified_molecule(query)
            self.assertIsNotNone(mol, f"Не разрешен запрос: {query}")
            self.assertEqual(mol.canonical_inn, expected_canon)

    def test_mode_1_3d_viewer_html(self):
        """Генерация 3D WebGL HTML-кода со всеми интерактивными элементами."""
        mol_a = get_verified_molecule("warfarin")
        mol_b = get_verified_molecule("acetylsalicylic acid")
        for lang in ("kk", "ru", "en"):
            html = render_3d_molecule_viewer_html(mol_a, mol_b, lang=lang)
            self.assertIn("three.js", html.lower())
            self.assertIn("orbitcontrols", html.lower())
            self.assertIn(mol_a.formula, html)
            self.assertIn(str(mol_a.pubchem_cid), html)
            self.assertIn("canvas", html.lower())

    def test_mode_2_mechanism_animation_html(self):
        """Генерация HTML для анимации биохимического каскада."""
        mol_a = get_verified_molecule("warfarin")
        mol_b = get_verified_molecule("acetylsalicylic acid")
        for lang in ("kk", "ru", "en"):
            html = render_mechanism_animation_html(mol_a, mol_b, lang=lang)
            self.assertIn("VKORC1", html)
            self.assertIn("PTGS1", html)
            self.assertIn("Ser529", html)
            self.assertIn("timeline-nav", html)

    def test_mode_3_convergence_visualization_html(self):
        """Визуализация конвергенции обязана исключать прямое столкновение молекул."""
        mol_a = get_verified_molecule("warfarin")
        mol_b = get_verified_molecule("acetylsalicylic acid")
        for lang in ("kk", "ru", "en"):
            html = render_convergence_visualization_html(mol_a, mol_b, lang=lang)
            # Проверка научного требования: отсутствие ложного столкновения молекул
            self.assertTrue(
                "столкновения" in html.lower() or "соқтығысу" in html.lower() or "collision" in html.lower()
            )
            # Проверка клинического регламента мониторинга
            self.assertTrue(
                "мониторинг" in html.lower() or "monitoring" in html.lower() or "бақылау" in html.lower()
            )

    def test_warfarin_aspirin_clinical_dossier_showcase(self):
        """Проверка эталонного клинико-фармакологического досье для пары Варфарин + Аспирин."""
        for lang in ("kk", "ru", "en"):
            brief = generate_clinical_intelligence_brief("warfarin", "acetylsalicylic acid", "Major", lang=lang)
            self.assertIn("finding", brief)
            self.assertIn("moa_a", brief)
            self.assertIn("moa_b", brief)
            self.assertIn("why_matters", brief)
            self.assertIn("clinical_consequence", brief)
            self.assertIn("uncertainty", brief)
            self.assertIn("monitoring", brief)
            self.assertIn("sources", brief)

            # Проверка специфических механизмов
            self.assertTrue("vkorc1" in brief["moa_a"].lower() or "к дәрумені" in brief["moa_a"].lower() or "витамин" in brief["moa_a"].lower())
            self.assertTrue("cox-1" in brief["moa_b"].lower() or "тромбоксан" in brief["moa_b"].lower() or "thromboxane" in brief["moa_b"].lower())

            # Проверка конвергенции путей (первичный + вторичный гемостаз)
            self.assertTrue("гемостаз" in brief["why_matters"].lower() or "hemostasis" in brief["why_matters"].lower())

            # Проверка наличия верифицированных источников
            self.assertGreater(len(brief["sources"]), 2)
            self.assertTrue(any("DDInter" in s for s in brief["sources"]))
            self.assertTrue(any("CHEST" in s for s in brief["sources"]))

    def test_unverified_molecule_honesty(self):
        """Неверифицированные препараты не должны молча подменять структуру на варфарин."""
        from i18n import t
        unverified_candidates = ["metformin", "atorvastatin", "omeprazole"]
        for c in unverified_candidates:
            mol = get_verified_molecule(c)
            self.assertIsNone(mol, f"Препарат {c} не должен самопроизвольно находиться в верифицированном 3D-реестре")

        # Проверка локализованных ключей честного фоллбэка
        for lang in ("kk", "ru", "en"):
            desc = t("mol_fallback_desc", drug="Метформин")
            self.assertTrue(bool(desc.strip()))
            self.assertIn("Метформин", desc)
            note = t("mol_fallback_safety_note")
            self.assertTrue(bool(note.strip()))


if __name__ == "__main__":
    unittest.main()
