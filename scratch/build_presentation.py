"""
Скрипт генерации презентации PPTX для защиты проекта PHARMA SENTINEL.
Университет: КРМУ (Казахстанско-Российский Медицинский Университет).
Группа: 107 Б
Авторы: Накипов Адилжан, Серік Мерей, Ернур Аханаев.
Формат: 16:9 Widescreen, 7 слайдов, глубокая научная стилистика, без воды, без нейрослопа.
Включает: 3D модель препарата, графики DDInter, ROC-AUC бенчмарк, интеграцию с DariKz, логотип КРМУ.
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml

# Цветовая палитра Qgen Dark Obsidian & Emerald
COLOR_BG_DARK = RGBColor(7, 14, 18)         # #070E12
COLOR_CARD_BG = RGBColor(17, 27, 32)        # #111B20
COLOR_CARD_BORDER = RGBColor(38, 57, 64)    # #263940
COLOR_EMERALD = RGBColor(54, 214, 176)      # #36D6B0
COLOR_CYAN = RGBColor(103, 183, 209)        # #67B7D1
COLOR_WHITE = RGBColor(234, 242, 242)       # #EAF2F2
COLOR_MUTED = RGBColor(145, 165, 170)       # #91A5AA
COLOR_ROSE = RGBColor(244, 63, 94)          # #F43F5E
COLOR_GOLD = RGBColor(245, 158, 11)         # #F59E0B

FONT_TITLE = "Trebuchet MS"
FONT_BODY = "Calibri"
FONT_MONO = "Consolas"

def add_slide_fade_transition(slide):
    """Добавляет плавный переход Fade между слайдами в OpenXML PPTX."""
    try:
        transition_xml = '<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:fade/></p:transition>'
        slide._element.append(parse_xml(transition_xml))
    except Exception as e:
        print(f"Warning: could not add transition: {e}")

def create_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER, border_width=1):
    """Создает элегантную карточку с темным фоном и тонкой границей."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(border_width)
    else:
        shape.line.fill.background()
    return shape

def add_badge(slide, left, top, width, height, text, bg_color=COLOR_EMERALD, text_color=COLOR_BG_DARK, font_size=10):
    """Создает компактный полукруглый бейдж статуса/тега."""
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    badge.fill.solid()
    badge.fill.fore_color.rgb = bg_color
    badge.line.fill.background()
    tf = badge.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = FONT_TITLE
    p.font.size = Pt(font_size)
    p.font.bold = True
    p.font.color.rgb = text_color
    p.alignment = PP_ALIGN.CENTER
    return badge

def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    assets_dir = os.path.abspath("assets/presentation")
    logo_path = os.path.join(assets_dir, "krmu_logo.png")
    drug_3d_path = os.path.join(assets_dir, "3d_drug_model.png")
    roc_auc_path = os.path.join(assets_dir, "roc_auc_benchmark.png")
    hubs_path = os.path.join(assets_dir, "ddinter_hubs_chart.png")
    darikz_path = os.path.join(assets_dir, "darikz_integration.png")

    # =========================================================================
    # СЛАЙД 1: ТИТУЛЬНЫЙ СЛАЙД (КРМУ · Группа 107 Б · Накипов, Серік, Аханаев)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s1)

    # Фоновая подложка
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_BG_DARK
    bg1.line.fill.background()

    # Карточка-контейнер титула
    create_card(s1, Inches(0.8), Inches(0.7), Inches(11.733), Inches(6.1), border_color=COLOR_CARD_BORDER)

    # Логотип КРМУ слева вверху карточки
    if os.path.exists(logo_path):
        s1.shapes.add_picture(logo_path, Inches(1.15), Inches(0.95), width=Inches(1.2), height=Inches(1.2))

    # Шапка университета
    uni_box = s1.shapes.add_textbox(Inches(2.5), Inches(0.98), Inches(9.5), Inches(0.9))
    tf = uni_box.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    p0.text = "КАЗАХСТАНСКО-РОССИЙСКИЙ МЕДИЦИНСКИЙ УНИВЕРСИТЕТ (КРМУ)"
    p0.font.name = FONT_TITLE
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN

    p1 = tf.add_paragraph()
    p1.text = "Кафедра клинической фармакологии и доказательной медицины"
    p1.font.name = FONT_BODY
    p1.font.size = Pt(11)
    p1.font.color.rgb = COLOR_MUTED

    # Центральный заголовок проекта
    title_box = s1.shapes.add_textbox(Inches(1.15), Inches(2.2), Inches(11.0), Inches(2.3))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True

    p_badge = tf_t.paragraphs[0]
    p_badge.text = "ДИПЛОМНЫЙ НАУЧНО-ИССЛЕДОВАТЕЛЬСКИЙ ПРОЕКТ · 2026"
    p_badge.font.name = FONT_MONO
    p_badge.font.size = Pt(11)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_EMERALD

    p_main = tf_t.add_paragraph()
    p_main.text = "PHARMA SENTINEL"
    p_main.font.name = FONT_TITLE
    p_main.font.size = Pt(44)
    p_main.font.bold = True
    p_main.font.color.rgb = COLOR_WHITE
    p_main.space_before = Pt(8)
    p_main.space_after = Pt(8)

    p_sub = tf_t.add_paragraph()
    p_sub.text = "Интеллектуальная предиктивная платформа фармакоинформатики, молекулярного анализа полипрагмазии и графового аудита лекарственных взаимодействий"
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(15)
    p_sub.font.color.rgb = COLOR_CYAN

    # Нижняя плашка авторов и метаданных
    author_card = create_card(s1, Inches(1.15), Inches(4.7), Inches(11.0), Inches(1.75), bg_color=RGBColor(11, 20, 24), border_color=COLOR_EMERALD, border_width=1)

    auth_box = s1.shapes.add_textbox(Inches(1.35), Inches(4.8), Inches(10.6), Inches(1.5))
    tf_a = auth_box.text_frame
    tf_a.word_wrap = True

    pa1 = tf_a.paragraphs[0]
    pa1.text = "АВТОРСКИЙ КОЛЛЕКТИВ ИССЛЕДОВАТЕЛЕЙ:"
    pa1.font.name = FONT_TITLE
    pa1.font.size = Pt(11)
    pa1.font.bold = True
    pa1.font.color.rgb = COLOR_EMERALD

    pa2 = tf_a.add_paragraph()
    pa2.text = "Студенты группы 107 Б:   Накипов Адилжан  ·  Серік Мерей  ·  Ернур Аханаев"
    pa2.font.name = FONT_TITLE
    pa2.font.size = Pt(16)
    pa2.font.bold = True
    pa2.font.color.rgb = COLOR_WHITE
    pa2.space_before = Pt(4)

    pa3 = tf_a.add_paragraph()
    pa3.text = "Научно-практическая специализация: клиническая фармакология, топологический анализ DDInter, фармакогеномика CYP450 и предиктивный искусственный интеллект\nЛокация: г. Алматы, Республика Казахстан — 2026 г."
    pa3.font.name = FONT_BODY
    pa3.font.size = Pt(10.5)
    pa3.font.color.rgb = COLOR_MUTED
    pa3.space_before = Pt(4)

    # =========================================================================
    # СЛАЙД 2: КОНЦЕПТУАЛЬНАЯ ЦЕЛЬ И ФИЛОСОФИЯ ПЛАТФОРМЫ
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s2)

    bg2 = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg2.fill.solid()
    bg2.fill.fore_color.rgb = COLOR_BG_DARK
    bg2.line.fill.background()

    # Шапка слайда
    add_badge(s2, Inches(0.8), Inches(0.55), Inches(2.2), Inches(0.35), "СТРАТЕГИЧЕСКАЯ МИССИЯ", bg_color=COLOR_EMERALD, text_color=COLOR_BG_DARK)
    h2_box = s2.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.7), Inches(0.7))
    tf2 = h2_box.text_frame
    p_h2 = tf2.paragraphs[0]
    p_h2.text = "Концептуальная цель проекта: преэмптивный онтолого-графовый контур"
    p_h2.font.name = FONT_TITLE
    p_h2.font.size = Pt(22)
    p_h2.font.bold = True
    p_h2.font.color.rgb = COLOR_WHITE

    # Большая карточка академической цели
    goal_card = create_card(s2, Inches(0.8), Inches(1.75), Inches(11.733), Inches(1.65), bg_color=RGBColor(14, 25, 30), border_color=COLOR_CYAN, border_width=1.5)
    goal_box = s2.shapes.add_textbox(Inches(1.05), Inches(1.85), Inches(11.2), Inches(1.4))
    tf_g = goal_box.text_frame
    tf_g.word_wrap = True
    pg0 = tf_g.paragraphs[0]
    pg0.text = "АКАДЕМИЧЕСКАЯ ФОРМУЛИРОВКА ЦЕЛИ ПЛАТФОРМЫ:"
    pg0.font.name = FONT_MONO
    pg0.font.size = Pt(10)
    pg0.font.bold = True
    pg0.font.color.rgb = COLOR_CYAN

    pg1 = tf_g.add_paragraph()
    pg1.text = "«Формирование суверенного преэмптивного онтолого-графового контура фармакологической безопасности и системного купирования ятрогенных рисков при полиморбидных назначениях на базе топологического моделирования многокомпонентных сетей и энзиматических каскадов»"
    pg1.font.name = FONT_TITLE
    pg1.font.size = Pt(15.5)
    pg1.font.bold = True
    pg1.font.color.rgb = COLOR_EMERALD
    pg1.space_before = Pt(6)

    # 3 фундаментальных столпа
    col_w = Inches(3.75)
    gap = Inches(0.24)
    y_cols = Inches(3.65)
    h_cols = Inches(3.3)

    # Столп 1
    create_card(s2, Inches(0.8), y_cols, col_w, h_cols)
    b1 = s2.shapes.add_textbox(Inches(0.95), y_cols + Inches(0.15), col_w - Inches(0.3), h_cols - Inches(0.3))
    tb1 = b1.text_frame
    tb1.word_wrap = True
    p = tb1.paragraphs[0]
    p.text = "01 · ТОПОЛОГИЯ БЕЗ УТЕЧКИ"
    p.font.name = FONT_TITLE
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb1.add_paragraph()
    p.text = "• Анализ графовых связей 160 235 верифицированных клинических пар DDInter.\n• Принцип строгого разделения обучающего и тестового графов: полное исключение фиктивных предсказаний (Leakage-Free Validation).\n• Вычисление метрик близости узлов: Adamic-Adar, Jaccard, Preferential Attachment."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(8)

    # Столп 2
    create_card(s2, Inches(0.8) + col_w + gap, y_cols, col_w, h_cols)
    b2 = s2.shapes.add_textbox(Inches(0.95) + col_w + gap, y_cols + Inches(0.15), col_w - Inches(0.3), h_cols - Inches(0.3))
    tb2 = b2.text_frame
    tb2.word_wrap = True
    p = tb2.paragraphs[0]
    p.text = "02 · ФАРМАКОГЕНОМИКА CYP450"
    p.font.name = FONT_TITLE
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = tb2.add_paragraph()
    p.text = "• Предиктивный учет метаболической конкуренции за изоферменты CYP2C9, CYP3A4, CYP2D6 и P-гликопротеин.\n• Выявление непрямых каскадных токсичностей (органотоксическая конвергенция без прямого физического связывания молекул).\n• Моделирование фатальных клинических триад: Triple Whammy, CYP2C9 ингибирование."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(8)

    # Столп 3
    create_card(s2, Inches(0.8) + (col_w + gap) * 2, y_cols, col_w, h_cols)
    b3 = s2.shapes.add_textbox(Inches(0.95) + (col_w + gap) * 2, y_cols + Inches(0.15), col_w - Inches(0.3), h_cols - Inches(0.3))
    tb3 = b3.text_frame
    tb3.word_wrap = True
    p = tb3.paragraphs[0]
    p.text = "03 · НАЦИОНАЛЬНЫЙ КОНТУР"
    p.font.name = FONT_TITLE
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD

    p = tb3.add_paragraph()
    p.text = "• Создание мобильного приложения для лечащих врачей и амбулаторных пациентов Казахстана.\n• Стратегическая интеграция с Государственным реестром DariKz (НЦЭЛС МЗ РК).\n• Переход от реактивной коррекции врачебных ошибок к проактивному преэмптивному контролю безопасности."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(8)

    # =========================================================================
    # СЛАЙД 3: 3D МОДЕЛИРОВАНИЕ ПРЕПАРАТА И КАСКАДЫ МЕТАБОЛИЗМА
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s3)

    bg3 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg3.fill.solid()
    bg3.fill.fore_color.rgb = COLOR_BG_DARK
    bg3.line.fill.background()

    add_badge(s3, Inches(0.8), Inches(0.55), Inches(2.3), Inches(0.35), "МОЛЕКУЛЯРНЫЙ УРОВЕНЬ", bg_color=COLOR_CYAN, text_color=COLOR_BG_DARK)
    h3_box = s3.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.7), Inches(0.7))
    tf3 = h3_box.text_frame
    p_h3 = tf3.paragraphs[0]
    p_h3.text = "3D Моделирование препарата: конформеры, изоферменты и органная конвергенция"
    p_h3.font.name = FONT_TITLE
    p_h3.font.size = Pt(22)
    p_h3.font.bold = True
    p_h3.font.color.rgb = COLOR_WHITE

    # Левая колонка: 3D визуализация
    card_img = create_card(s3, Inches(0.8), Inches(1.75), Inches(6.5), Inches(5.2), border_color=COLOR_EMERALD)
    if os.path.exists(drug_3d_path):
        s3.shapes.add_picture(drug_3d_path, Inches(0.9), Inches(1.85), width=Inches(6.3), height=Inches(5.0))

    # Правая колонка: 3 научных карточки
    rx = Inches(7.55)
    rw = Inches(5.0)

    # Карточка 1: Конформеры
    create_card(s3, rx, Inches(1.75), rw, Inches(1.6))
    tb_c1 = s3.shapes.add_textbox(rx + Inches(0.15), Inches(1.82), rw - Inches(0.3), Inches(1.4)).text_frame
    tb_c1.word_wrap = True
    p = tb_c1.paragraphs[0]
    p.text = "ПРОСТРАНСТВЕННАЯ КОНФОРМАЦИЯ И ФАРМАКОФОР"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p = tb_c1.add_paragraph()
    p.text = "• 3D микрогранулы с активным веществом и моделирование стерического связывания.\n• Аллостерическое взаимодействие с активным центром энзимов печени и рецепторными мишенями."
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    # Карточка 2: Конкуренция CYP450
    create_card(s3, rx, Inches(3.55), rw, Inches(1.6))
    tb_c2 = s3.shapes.add_textbox(rx + Inches(0.15), Inches(3.62), rw - Inches(0.3), Inches(1.4)).text_frame
    tb_c2.word_wrap = True
    p = tb_c2.paragraphs[0]
    p.text = "КОНКУРЕНЦИЯ ЗА ИЗОФЕРМЕНТЫ ЦИТОХРОМА P450"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p = tb_c2.add_paragraph()
    p.text = "• CYP2C9 и CYP3A4 каскады: Варфарин метаболизируется CYP2C9. Амиодарон или Флуконазол мощно ингибируют CYP2C9.\n• Результат: кумуляция варфарина в плазме, взлет МНО > 6.0 и фатальные кровотечения."
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    # Карточка 3: Органная конвергенция
    create_card(s3, rx, Inches(5.35), rw, Inches(1.6))
    tb_c3 = s3.shapes.add_textbox(rx + Inches(0.15), Inches(5.42), rw - Inches(0.3), Inches(1.4)).text_frame
    tb_c3.word_wrap = True
    p = tb_c3.paragraphs[0]
    p.text = "ОРГАННАЯ КОНВЕРГЕНЦИЯ БЕЗ СВЯЗЫВАНИЯ МОЛЕКУЛ"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_ROSE
    p = tb_c3.add_paragraph()
    p.text = "• Синдром Triple Whammy (иАПФ + Фуросемид + НПВП): нет прямой химической реакции между молекулами, но сочетанное действие вызывает спазм афферентной артериолы и острую почечную недостаточность."
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    # =========================================================================
    # СЛАЙД 4: ДОКАЗАТЕЛЬНАЯ БАЗА ДАННЫХ DDINTER v2024.11 И PUBMED
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s4)

    bg4 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg4.fill.solid()
    bg4.fill.fore_color.rgb = COLOR_BG_DARK
    bg4.line.fill.background()

    add_badge(s4, Inches(0.8), Inches(0.55), Inches(2.2), Inches(0.35), "ФАРМАКОЭПИДЕМИОЛОГИЯ", bg_color=COLOR_EMERALD, text_color=COLOR_BG_DARK)
    h4_box = s4.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.7), Inches(0.7))
    tf4 = h4_box.text_frame
    p_h4 = tf4.paragraphs[0]
    p_h4.text = "Доказательная база: 160 235 пар взаимодействий DDInter и фито-онтология"
    p_h4.font.name = FONT_TITLE
    p_h4.font.size = Pt(22)
    p_h4.font.bold = True
    p_h4.font.color.rgb = COLOR_WHITE

    # Левая колонка: График базы данных
    create_card(s4, Inches(0.8), Inches(1.75), Inches(6.8), Inches(5.2), border_color=COLOR_CARD_BORDER)
    if os.path.exists(hubs_path):
        s4.shapes.add_picture(hubs_path, Inches(0.9), Inches(1.85), width=Inches(6.6), height=Inches(5.0))

    # Правая колонка: Цифры и факты
    rx4 = Inches(7.85)
    rw4 = Inches(4.7)

    # Карточка 1: Градация тяжести
    create_card(s4, rx4, Inches(1.75), rw4, Inches(2.5))
    tb_d1 = s4.shapes.add_textbox(rx4 + Inches(0.15), Inches(1.85), rw4 - Inches(0.3), Inches(2.3)).text_frame
    tb_d1.word_wrap = True
    p = tb_d1.paragraphs[0]
    p.text = "СТРУКТУРА БАЗЫ ДАННЫХ DDINTER (160 235 ПАР)"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb_d1.add_paragraph()
    p.text = "• Major (26 914 пар): жизнеугрожающие взаимодействия с риском летальности, требуют абсолютной отмены или смены тактики.\n• Moderate (96 675 пар): клинически значимые конфликты, требуют мониторинга дозы и анализов крови.\n• Minor (6 833 пар): легкие взаимодействия без изменения исхода.\n• Unknown (29 813 пар): потенциальные взаимодействия на базе изоферментов."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(6)

    # Карточка 2: Хабы и фитотоксикология
    create_card(s4, rx4, Inches(4.45), rw4, Inches(2.5))
    tb_d2 = s4.shapes.add_textbox(rx4 + Inches(0.15), Inches(4.55), rw4 - Inches(0.3), Inches(2.3)).text_frame
    tb_d2.word_wrap = True
    p = tb_d2.paragraphs[0]
    p.text = "ФАРМАКОЛОГИЧЕСКИЕ ХАБЫ И БАДЫ"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = tb_d2.add_paragraph()
    p.text = "• Топ-хабы полипрагмазии: Варфарин (1 318 связей), Аспирин (1 190), Флуконазол, Амиодарон, Омепразол.\n• Фито-токсикологический модуль: интеграция с базой PubMed/NCBI Entrez (Зверобой — индуктор CYP3A4/P-gp, Грейпфрут — блокатор CYP3A4, Гинко билоба — риск геморрагий).\n• 1 939 канонических субстанций МНН с синонимами."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(6)

    # =========================================================================
    # СЛАЙД 5: PHARMA SENTINEL AI — ГРАФОВАЯ МОДЕЛЬ И ВАЛИДАЦИЯ
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s5)

    bg5 = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg5.fill.solid()
    bg5.fill.fore_color.rgb = COLOR_BG_DARK
    bg5.line.fill.background()

    add_badge(s5, Inches(0.8), Inches(0.55), Inches(2.4), Inches(0.35), "МАШИННОЕ ОБУЧЕНИЕ И AI", bg_color=COLOR_EMERALD, text_color=COLOR_BG_DARK)
    h5_box = s5.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.7), Inches(0.7))
    tf5 = h5_box.text_frame
    p_h5 = tf5.paragraphs[0]
    p_h5.text = "Pharma Sentinel AI: Leakage-Free граф-модель и ROC-AUC = 0.962"
    p_h5.font.name = FONT_TITLE
    p_h5.font.size = Pt(22)
    p_h5.font.bold = True
    p_h5.font.color.rgb = COLOR_WHITE

    # Левая колонка: ROC-AUC кривые
    create_card(s5, Inches(0.8), Inches(1.75), Inches(6.8), Inches(5.2), border_color=COLOR_CARD_BORDER)
    if os.path.exists(roc_auc_path):
        s5.shapes.add_picture(roc_auc_path, Inches(0.9), Inches(1.85), width=Inches(6.6), height=Inches(5.0))

    # Правая колонка: Бенчмарки и архитектура
    rx5 = Inches(7.85)
    rw5 = Inches(4.7)

    create_card(s5, rx5, Inches(1.75), rw5, Inches(2.5))
    tb_m1 = s5.shapes.add_textbox(rx5 + Inches(0.15), Inches(1.85), rw5 - Inches(0.3), Inches(2.3)).text_frame
    tb_m1.word_wrap = True
    p = tb_m1.paragraphs[0]
    p.text = "ЧЕСТНЫЙ БЕНЧМАРК (LEAKAGE-FREE AUDIT)"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb_m1.add_paragraph()
    p.text = "• В традиционных моделях граф строится со всеми ребрами, вызывая 100% утечку (data leakage).\n• В Pharma Sentinel граф строится строго на обучающем срезе (68% графа), а тестовые ребра (20%) физически скрыты.\n• Результаты на независимом тесте:\n   - Pharma Sentinel AI (RF Ensemble): ROC-AUC = 0.962\n   - Logistic Regression: ROC-AUC = 0.894\n   - Adamic-Adar Link Prediction: ROC-AUC = 0.865"
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(6)

    create_card(s5, rx5, Inches(4.45), rw5, Inches(2.5))
    tb_m2 = s5.shapes.add_textbox(rx5 + Inches(0.15), Inches(4.55), rw5 - Inches(0.3), Inches(2.3)).text_frame
    tb_m2.word_wrap = True
    p = tb_m2.paragraphs[0]
    p.text = "ГИБРИДНЫЙ ИИ-АССИСТЕНТ (RAG + DDINTER)"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = tb_m2.add_paragraph()
    p.text = "• Двухуровневая верификация: ML предсказывает топологический риск, а нейросетевой модуль Pharma Sentinel AI синтезирует клинический протокол на трех языках (KK/RU/EN).\n• Защита от медицинских галлюцинаций: нейросеть получает фактологический контекст из DDInter и PubMed, формируя юридически выверенные рекомендации."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(6)

    # =========================================================================
    # СЛАЙД 6: СТРАТЕГИЧЕСКИЙ ПОТЕНЦИАЛ: МОБИЛЬНОЕ ПРИЛОЖЕНИЕ И DARIKZ
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s6)

    bg6 = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg6.fill.solid()
    bg6.fill.fore_color.rgb = COLOR_BG_DARK
    bg6.line.fill.background()

    add_badge(s6, Inches(0.8), Inches(0.55), Inches(2.7), Inches(0.35), "СТРАТЕГИЧЕСКИЙ ПОТЕНЦИАЛ", bg_color=COLOR_GOLD, text_color=COLOR_BG_DARK)
    h6_box = s6.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.7), Inches(0.7))
    tf6 = h6_box.text_frame
    p_h6 = tf6.paragraphs[0]
    p_h6.text = "Потенциал продукта: Мобильное приложение и интеграция с DariKz"
    p_h6.font.name = FONT_TITLE
    p_h6.font.size = Pt(22)
    p_h6.font.bold = True
    p_h6.font.color.rgb = COLOR_WHITE

    # Левая колонка: Архитектура DariKz
    create_card(s6, Inches(0.8), Inches(1.75), Inches(6.8), Inches(5.2), border_color=COLOR_CARD_BORDER)
    if os.path.exists(darikz_path):
        s6.shapes.add_picture(darikz_path, Inches(0.9), Inches(1.85), width=Inches(6.6), height=Inches(5.0))

    # Правая колонка: Стратегические направления
    rx6 = Inches(7.85)
    rw6 = Inches(4.7)

    create_card(s6, rx6, Inches(1.75), rw6, Inches(2.5))
    tb_s1 = s6.shapes.add_textbox(rx6 + Inches(0.15), Inches(1.85), rw6 - Inches(0.3), Inches(2.3)).text_frame
    tb_s1.word_wrap = True
    p = tb_s1.paragraphs[0]
    p.text = "КЛИНИЧЕСКИЙ МОБИЛЬНЫЙ КЛИЕНТ (iOS / ANDROID)"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb_s1.add_paragraph()
    p.text = "• Для врача на обходе: мгновенное сканирование листа назначений или штрихкодов упаковок, мгновенный аудит полипрагмазии за 0.3 секунды.\n• Для пациента: мониторинг совместимости выписанных таблеток с БАДами и продуктами питания прямо из аптеки.\n• Оффлайн-кэш ключевых взаимодействий для работы в условиях нестабильной связи."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(6)

    create_card(s6, rx6, Inches(4.45), rw6, Inches(2.5))
    tb_s2 = s6.shapes.add_textbox(rx6 + Inches(0.15), Inches(4.55), rw6 - Inches(0.3), Inches(2.3)).text_frame
    tb_s2.word_wrap = True
    p = tb_s2.paragraphs[0]
    p.text = "ИНТЕГРАЦИЯ С DARIKZ (НЦЭЛС МЗ РК)"
    p.font.name = FONT_TITLE
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD

    p = tb_s2.add_paragraph()
    p.text = "• Синхронизация с Государственным реестром лекарственных средств Республики Казахстан (DariKz).\n• Учет специфических торговых наименований, зарегистрированных в РК, с автоматическим маппингом на МНН DDInter.\n• Перспектива шлюза в КМИС (ДамуМед, Надежда) для преэмптивного блокирования опасных назначений в электронной медкарте."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(6)

    # =========================================================================
    # СЛАЙД 7: ДОРОЖНАЯ КАРТА ВНЕДРЕНИЯ И ЗАКЛЮЧЕНИЕ
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s7)

    bg7 = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg7.fill.solid()
    bg7.fill.fore_color.rgb = COLOR_BG_DARK
    bg7.line.fill.background()

    add_badge(s7, Inches(0.8), Inches(0.55), Inches(2.2), Inches(0.35), "ФИНАЛ И ПЕРСПЕКТИВЫ", bg_color=COLOR_EMERALD, text_color=COLOR_BG_DARK)
    h7_box = s7.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.7), Inches(0.7))
    tf7 = h7_box.text_frame
    p_h7 = tf7.paragraphs[0]
    p_h7.text = "Дорожная карта реализации и заключение исследовательской группы"
    p_h7.font.name = FONT_TITLE
    p_h7.font.size = Pt(22)
    p_h7.font.bold = True
    p_h7.font.color.rgb = COLOR_WHITE

    # 3 этапа дорожной карты
    cw7 = Inches(3.75)
    gap7 = Inches(0.24)
    y7 = Inches(1.75)
    h7 = Inches(3.2)

    # Фаза 1
    create_card(s7, Inches(0.8), y7, cw7, h7, border_color=COLOR_EMERALD)
    tb_r1 = s7.shapes.add_textbox(Inches(0.95), y7 + Inches(0.15), cw7 - Inches(0.3), h7 - Inches(0.3)).text_frame
    tb_r1.word_wrap = True
    p = tb_r1.paragraphs[0]
    p.text = "ФАЗА I · ЗАВЕРШЕНО\n(Ядро и Граф-аналитика)"
    p.font.name = FONT_TITLE
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb_r1.add_paragraph()
    p.text = "✔ Индексация 160 235 пар DDInter\n✔ Обучение модели Pharma Sentinel AI с ROC-AUC 0.962 (без утечки)\n✔ 3D Molecular Lab с конформерами\n✔ Трехъязычный интерфейс (KK/RU/EN)\n✔ Фито-токсикологический модуль"
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(8)

    # Фаза 2
    create_card(s7, Inches(0.8) + cw7 + gap7, y7, cw7, h7, border_color=COLOR_CYAN)
    tb_r2 = s7.shapes.add_textbox(Inches(0.95) + cw7 + gap7, y7 + Inches(0.15), cw7 - Inches(0.3), h7 - Inches(0.3)).text_frame
    tb_r2.word_wrap = True
    p = tb_r2.paragraphs[0]
    p.text = "ФАЗА II · В РАЗРАБОТКЕ\n(DariKz и Мобильный клиент)"
    p.font.name = FONT_TITLE
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = tb_r2.add_paragraph()
    p.text = "⏳ API-интеграция с базой DariKz (НЦЭЛС)\n⏳ Мобильное приложение iOS / Android\n⏳ Сканер штрихкодов упаковок лекарств\n⏳ Push-уведомления о критических сочетаниях для пациентов\n⏳ Оффлайн-модуль экстренной помощи"
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(8)

    # Фаза 3
    create_card(s7, Inches(0.8) + (cw7 + gap7) * 2, y7, cw7, h7, border_color=COLOR_GOLD)
    tb_r3 = s7.shapes.add_textbox(Inches(0.95) + (cw7 + gap7) * 2, y7 + Inches(0.15), cw7 - Inches(0.3), h7 - Inches(0.3)).text_frame
    tb_r3.word_wrap = True
    p = tb_r3.paragraphs[0]
    p.text = "ФАЗА III · ПЛАН 2026–2027\n(Клинический пилот в КРМУ)"
    p.font.name = FONT_TITLE
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD

    p = tb_r3.add_paragraph()
    p.text = "🎯 Пилотное внедрение в университетских клиниках КРМУ\n🎯 Интеграция с ДамуМед / ЕИСЗ РК\n🎯 Проспективная оценка снижения ятрогенных осложнений на 25–40%\n🎯 Подача заявки на включение в клинические протоколы МЗ РК"
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(8)

    # Итоговая карточка-заключение
    final_card = create_card(s7, Inches(0.8), Inches(5.15), Inches(11.733), Inches(1.8), bg_color=RGBColor(11, 20, 24), border_color=COLOR_EMERALD, border_width=1.5)
    tb_f = s7.shapes.add_textbox(Inches(1.05), Inches(5.25), Inches(11.2), Inches(1.6)).text_frame
    tb_f.word_wrap = True

    pf0 = tb_f.paragraphs[0]
    pf0.text = "ИТОГОВЫЙ ВЫВОД ЗАЩИТЫ:"
    pf0.font.name = FONT_MONO
    pf0.font.size = Pt(10)
    pf0.font.bold = True
    pf0.font.color.rgb = COLOR_EMERALD

    pf1 = tb_f.add_paragraph()
    pf1.text = "«Pharma Sentinel переводит клиническую фармакологию Республики Казахстан из реактивного режима фиксации ошибок в проактивную систему цифровой защиты здоровья граждан на базе доказательной медицины, топологии сетей и отечественного реестра DariKz»"
    pf1.font.name = FONT_TITLE
    pf1.font.size = Pt(14)
    pf1.font.bold = True
    pf1.font.color.rgb = COLOR_WHITE
    pf1.space_before = Pt(4)

    pf2 = tb_f.add_paragraph()
    pf2.text = "Благодарим за внимание! Доклад окончен. Готовы ответить на вопросы государственной экзаменационной комиссии.\nАвторы: Накипов Адилжан, Серік Мерей, Ернур Аханаев | Группа 107 Б | КРМУ, 2026 г."
    pf2.font.name = FONT_BODY
    pf2.font.size = Pt(10.5)
    pf2.font.color.rgb = COLOR_CYAN
    pf2.space_before = Pt(4)

    # Сохраняем файл
    output_path = os.path.abspath("Pharma_Sentinel_Defense_KRMU.pptx")
    prs.save(output_path)
    print(f"SUCCESS: Presentation successfully created at {output_path}")

if __name__ == "__main__":
    main()
