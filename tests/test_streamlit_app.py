"""Автоматизированные сквозные тесты пользовательского интерфейса Streamlit (AppTest).

Проверяет:
1. Запуск приложения без исключений с дефолтным языком 'kk' (Казахский).
2. Работу кнопок всех 3 быстрых пресетов (CYP2C9, Triple Whammy, Bleeding).
3. Синхронизацию session_state между страницами (Workspace -> AI Assistant -> Molecular Lab).
4. Переход на страницу ML и рендеринг прозрачности модели без сбоев.
5. Переход на страницу AI Assistant и отображение доказательного контекста.
"""
import os
import unittest
from streamlit.testing.v1 import AppTest
from i18n import get_lang

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))


class TestStreamlitAppGUI(unittest.TestCase):
    """Сквозное тестирование Streamlit интерфейса через headless AppTest."""

    def test_app_initial_load(self):
        """Проверка инициализации приложения: язык по умолчанию 'kk', нет исключений."""
        at = AppTest.from_file(APP_PATH, default_timeout=60).run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on init: {[e.value for e in at.exception]}")
        # Язык по умолчанию казахский
        self.assertEqual(at.session_state.get("lang"), "kk")
        self.assertEqual(at.session_state.get("nav_page"), "workspace")
        self.assertEqual(len(at.session_state.get("workspace_multiselect", [])), 3)

    def test_preset_clicks_and_state_synchronization(self):
        """Проверка кликов по всем трем пресетам быстрого поиска."""
        at = AppTest.from_file(APP_PATH, default_timeout=60).run()
        self.assertEqual(len(at.exception), 0)

        # 1. Клик по пресету CYP Triad
        cyp_btns = [b for b in at.button if b.key == "btn_preset_cyp"]
        self.assertTrue(len(cyp_btns) > 0, "Button btn_preset_cyp not found")
        cyp_btns[0].click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("active_cohort"), "preset_cyp")
        self.assertEqual(at.session_state.get("active_pair"), ("warfarin", "amiodarone"))
        self.assertEqual(len(at.session_state.get("workspace_multiselect", [])), 3)

        # 2. Клик по пресету Triple Whammy
        whammy_btns = [b for b in at.button if b.key == "btn_preset_whammy"]
        self.assertTrue(len(whammy_btns) > 0, "Button btn_preset_whammy not found")
        whammy_btns[0].click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("active_cohort"), "preset_whammy")
        self.assertEqual(at.session_state.get("active_pair"), ("enalapril", "ibuprofen"))
        self.assertEqual(len(at.session_state.get("workspace_multiselect", [])), 3)

        # 3. Клик по пресету Bleeding Conflict
        bleeding_btns = [b for b in at.button if b.key == "btn_preset_bleeding"]
        self.assertTrue(len(bleeding_btns) > 0, "Button btn_preset_bleeding not found")
        bleeding_btns[0].click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("active_cohort"), "preset_bleeding")
        self.assertEqual(at.session_state.get("active_pair"), ("warfarin", "acetylsalicylic acid"))
        self.assertEqual(len(at.session_state.get("workspace_multiselect", [])), 2)

    def test_navigate_to_ml_page(self):
        """Проверка перехода на страницу машинного обучения и рендеринга метрик/важности признаков."""
        at = AppTest.from_file(APP_PATH, default_timeout=60).run()
        self.assertEqual(len(at.exception), 0)

        nav_radios = [r for r in at.radio if r.key == "main_nav_radio"]
        self.assertTrue(len(nav_radios) > 0, "main_nav_radio not found")
        
        # Индекс 4 соответствует странице ML
        nav_radios[0].set_value(nav_radios[0].options[4]).run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on ML page: {[e.value for e in at.exception]}")
        self.assertEqual(at.session_state.get("nav_page"), "ml")

    def test_navigate_to_ai_page(self):
        """Проверка перехода на страницу AI-ассистента и наличия селектора пар."""
        at = AppTest.from_file(APP_PATH, default_timeout=60).run()
        self.assertEqual(len(at.exception), 0)

        nav_radios = [r for r in at.radio if r.key == "main_nav_radio"]
        self.assertTrue(len(nav_radios) > 0, "main_nav_radio not found")

        # Индекс 5 соответствует странице AI
        nav_radios[0].set_value(nav_radios[0].options[5]).run()
        self.assertEqual(len(at.exception), 0, f"Exceptions on AI page: {[e.value for e in at.exception]}")
        self.assertEqual(at.session_state.get("nav_page"), "ai")

    def test_navigation_across_all_tabs_without_emojis(self):
        """Проверка переходов по ключевым разделам и отсутствия дешевых эмодзи в навигационных табах."""
        import re
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]')

        at = AppTest.from_file(APP_PATH, default_timeout=60).run()
        self.assertEqual(len(at.exception), 0)

        nav_radios = [r for r in at.radio if r.key == "main_nav_radio"]
        self.assertTrue(len(nav_radios) > 0)
        options = nav_radios[0].options
        self.assertEqual(len(options), 7)

        # Проверка отсутствия дешевых эмодзи в названиях разделов
        for opt in options:
            emojis = emoji_pattern.findall(opt)
            self.assertEqual(len(emojis), 0, f"Found emoji in navigation tab: {opt}")

        # Проверка перехода на молекулярную лабораторию (индекс 1)
        nav_radios[0].set_value(options[1]).run()
        self.assertEqual(len(at.exception), 0, f"Exception on navigating to molecular: {[e.value for e in at.exception]}")
        self.assertEqual(at.session_state.get("nav_page"), "molecular")

    def test_react_bits_animated_content_helper(self):
        """Проверка генерации HTML-обертки <AnimatedContent /> с корректными props."""
        from components.react_bits import render_animated_content
        html = render_animated_content(
            "<p>Clinical finding</p>",
            distance=50,
            direction="horizontal",
            reverse=True,
            duration=0.6,
            ease="power3.out",
            scale=0.97,
            stagger=0.07,
            wipe=True,
            container_class="clinical-section"
        )
        self.assertIn('data-animated-content="true"', html)
        self.assertIn('data-distance="50"', html)
        self.assertIn('data-direction="horizontal"', html)
        self.assertIn('data-reverse="true"', html)
        self.assertIn('data-duration="0.6"', html)
        self.assertIn('data-ease="power3.out"', html)
        self.assertIn('data-scale="0.97"', html)
        self.assertIn('data-stagger="0.07"', html)
        self.assertIn('data-wipe="true"', html)
        self.assertIn('clinical-section', html)
        self.assertIn('<p>Clinical finding</p>', html)

    def test_molecular_lab_showcase_pair_clicks(self):
        """Проверка нового надёжного селектора эталонных комбинаций, кнопки Swap и отсутствия сломанных кнопок в Молекулярной лаборатории."""
        at = AppTest.from_file(APP_PATH, default_timeout=60).run()
        # Переходим в Молекулярную лабораторию
        nav_radios = [r for r in at.radio if r.key == "main_nav_radio"]
        nav_radios[0].set_value(nav_radios[0].options[1]).run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("nav_page"), "molecular")

        # 0. Убеждаемся, что старые сломанные кнопки chip_pair_* полностью удалены
        old_chip_btns = [b for b in at.button if b.key and b.key.startswith("chip_pair_")]
        self.assertEqual(len(old_chip_btns), 0, "Legacy chip_pair_* buttons should be removed")

        # 1. Выбираем эталонную комбинацию enalapril_ibuprofen (индекс 4) через mol_ref_dropdown
        ref_dropdowns = [s for s in at.selectbox if s.key == "mol_ref_dropdown"]
        self.assertTrue(len(ref_dropdowns) > 0, "Selectbox mol_ref_dropdown not found")
        ref_dropdowns[0].set_value(ref_dropdowns[0].options[4]).run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("mol_active_pair"), "enalapril_ibuprofen")
        self.assertEqual(at.session_state.get("mol_custom_a"), "enalapril")
        self.assertEqual(at.session_state.get("mol_custom_b"), "ibuprofen")
        self.assertEqual(at.session_state.get("active_pair"), ("enalapril", "ibuprofen"))

        # 2. Выбираем эталонную комбинацию warfarin_amiodarone (индекс 2) через mol_ref_dropdown
        ref_dropdowns = [s for s in at.selectbox if s.key == "mol_ref_dropdown"]
        ref_dropdowns[0].set_value(ref_dropdowns[0].options[2]).run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("mol_active_pair"), "warfarin_amiodarone")
        self.assertEqual(at.session_state.get("mol_custom_a"), "warfarin")
        self.assertEqual(at.session_state.get("mol_custom_b"), "amiodarone")
        self.assertEqual(at.session_state.get("active_pair"), ("warfarin", "amiodarone"))

        # 3. Проверяем кнопку Swap (⇄)
        swap_btns = [b for b in at.button if b.key == "mol_btn_swap_drugs"]
        self.assertTrue(len(swap_btns) > 0, "Button mol_btn_swap_drugs not found")
        swap_btns[0].click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("active_pair"), ("amiodarone", "warfarin"))
        self.assertEqual(at.session_state.get("mol_custom_a"), "amiodarone")
        self.assertEqual(at.session_state.get("mol_custom_b"), "warfarin")

        # 4. Проверяем кнопку Reset (↺)
        reset_btns = [b for b in at.button if b.key == "mol_btn_reset_drugs"]
        self.assertTrue(len(reset_btns) > 0, "Button mol_btn_reset_drugs not found")
        reset_btns[0].click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("active_pair"), ("warfarin", "acetylsalicylic acid"))

    def test_workspace_severity_filter_and_report_download(self):
        """Проверка наличия фильтра тяжести, фильтрации карточек и кнопки скачивания отчета."""
        at = AppTest.from_file(APP_PATH, default_timeout=60).run()
        self.assertEqual(len(at.exception), 0)
        self.assertFalse(at.session_state.get("sound_enabled", False))

        # Проверка кнопки скачивания протокола аудита
        down_btns = [b for b in at.download_button if b.key == "btn_download_protocol"]
        self.assertTrue(len(down_btns) > 0, "Download button btn_download_protocol not found")

        # Проверка фильтров severity pills
        pills_widgets = [p for p in at.pills if p.key == "ws_severity_filter"]
        self.assertTrue(len(pills_widgets) > 0, "Pills widget ws_severity_filter not found")
        self.assertEqual(at.session_state.get("ws_severity_filter", "All"), "All")

        # Переключение фильтра на Major
        pills_widgets[0].set_value("Major").run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("ws_severity_filter"), "Major")

    def test_molecular_to_ai_cross_sync(self):
        """Проверка синхронизации: выбор пары в Молекулярной лаборатории -> переход в ИИ-ассистент."""
        at = AppTest.from_file(APP_PATH, default_timeout=60).run()
        # 1. Переход в Молекулярную лабораторию
        nav_radios = [r for r in at.radio if r.key == "main_nav_radio"]
        nav_radios[0].set_value(nav_radios[0].options[1]).run()
        self.assertEqual(len(at.exception), 0)

        # 2. Выбор пары warfarin_amiodarone (индекс 2) через mol_ref_dropdown
        ref_dropdowns = [s for s in at.selectbox if s.key == "mol_ref_dropdown"]
        ref_dropdowns[0].set_value(ref_dropdowns[0].options[2]).run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("active_pair"), ("warfarin", "amiodarone"))
        self.assertEqual(at.session_state.get("ai_b"), "amiodarone")

        # 3. Переход на страницу ИИ-ассистента (индекс 5)
        nav_radios_new = [r for r in at.radio if r.key == "main_nav_radio"]
        nav_radios_new[0].set_value(nav_radios_new[0].options[5]).run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state.get("nav_page"), "ai")
        self.assertEqual(at.session_state.get("ai_a"), "warfarin")
        self.assertEqual(at.session_state.get("ai_b"), "amiodarone")

    def test_pubmed_ml_and_3d_hero_components(self):
        """Проверка интеграции PubMed, детального анализа рисков, живого ML-предиктора и 3D Hero/BubbleMenu."""
        from local_ai import fetch_pubmed_evidence, generate_clinical_intelligence_brief
        from components.react_bits import (
            render_albus_fingent_hero_3d_html,
            render_albus_pipeline_and_hex_ring_html,
            render_tech_text_and_effects_html,
        )

        # 1. PubMed evidence lookup
        studies = fetch_pubmed_evidence("warfarin", "acetylsalicylic acid", lang="ru")
        self.assertTrue(len(studies) >= 1)
        self.assertTrue(any("pmid" in s and "url" in s for s in studies))

        # 2. Enriched deterministic brief with organ risks, red flags, and anti-self-medication warning
        brief = generate_clinical_intelligence_brief("warfarin", "acetylsalicylic acid", "Major", lang="ru")
        self.assertIn("detailed_risks", brief)
        self.assertTrue(len(brief["detailed_risks"]) >= 2)
        self.assertIn("red_flags", brief)
        self.assertTrue(len(brief["red_flags"]) >= 2)
        self.assertIn("self_medication_warning", brief)
        self.assertIn("pubmed_studies", brief)

        # 3. 3D Hero & Albus Pipeline / Hex Ring HTML
        hero_html = render_albus_fingent_hero_3d_html(
            lang="ru",
            active_drug_a="warfarin",
            active_drug_b="acetylsalicylic acid",
            major_count=1,
            mod_count=0,
            total_pairs_checked=1,
        )
        self.assertIn("hero-webgl-canvas", hero_html)
        self.assertIn("btn-scene-capsule", hero_html)
        self.assertIn("btn-scene-fingent", hero_html)
        self.assertIn("btn-scene-dna", hero_html)

        pipe_html = render_albus_pipeline_and_hex_ring_html(
            lang="ru",
            major_count=2,
            mod_count=1,
            minor_count=0,
            supp_count=1,
        )
        self.assertIn("polygon", pipe_html)

        engine_html = render_tech_text_and_effects_html(sound_enabled=False)
        self.assertIn("ps-reactbits-bubble-dock", engine_html)
        self.assertIn("ps-molecular-canvas", engine_html)


if __name__ == "__main__":
    unittest.main()
