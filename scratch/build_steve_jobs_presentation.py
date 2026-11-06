"""
Скрипт генерации презентации в стиле Стива Джобса (Apple Keynote Style).
Тема: PHARMA SENTINEL — Научно-исследовательский дипломный проект.
Университет: КРМУ (Казахстанско-Российский Медицинский Университет).
Группа: 107 Б
Авторы: Накипов Адилжан, Ернур Аханаев.
(Серік Мерей исключена из проекта по запросу руководителя).

Обязательные разделы:
1. Актуальность проекта (Айсберг полипрагмазии, DDInter 160 235 связей).
2. Цель проекта и научная новизна исследования (Leakage-Free, топологический ML).
3. Распределение обязанностей и ролей (Накипов Адилжан & Ернур Аханаев).
4. Представление продукта в стиле Стива Джобса (3 в 1, Pharma Sentinel).
5. 3D-визуализация каскадов (Варфарин × Кордарон, Triple Whammy).
6. Честный бенчмарк ML (Случайный лес 0.911 против baseline 0.892).
7. План развития и дорожная карта (Roadmap: DariKz и пилот в КРМУ).
8. Заключение (The Finale: «Будущее принадлежит тем, кто предотвращает ошибки»).
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml

# Цветовая палитра Apple Keynote Dark
COLOR_BLACK = RGBColor(0, 0, 0)             # #000000 Чистый глубокий черный
COLOR_CARD_DARK = RGBColor(9, 15, 18)       # #090F12 Тонкая карточка
COLOR_CARD_BORDER = RGBColor(28, 42, 48)    # #1C2A30 Граница
COLOR_EMERALD = RGBColor(0, 245, 160)       # #00F5A0 Яркий неоновый изумруд
COLOR_CYAN = RGBColor(0, 210, 255)          # #00D2FF Чистый неоновый циан
COLOR_WHITE = RGBColor(255, 255, 255)       # #FFFFFF Белоснежный
COLOR_MUTED = RGBColor(142, 142, 147)       # #8E8E93 Apple Grey
COLOR_CORAL = RGBColor(255, 69, 58)         # #FF453A Предупреждающий алый
COLOR_ORANGE = RGBColor(255, 159, 10)       # #FF9F0A Янтарный
COLOR_PURPLE = RGBColor(191, 90, 242)       # #BF5AF2 Фиолетовый акцент

FONT_HERO = "Trebuchet MS"
FONT_BODY = "Calibri"
FONT_MONO = "Consolas"

def add_slide_fade_transition(slide):
    """Добавляет плавный кинематографичный переход Fade."""
    try:
        xml = '<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:fade/></p:transition>'
        slide._element.append(parse_xml(xml))
    except Exception as e:
        print(f"Transition warning: {e}")

def create_card(slide, left, top, width, height, bg_color=COLOR_CARD_DARK, border_color=COLOR_CARD_BORDER, border_width=1):
    """Создает карточку с глубоким темным фоном и тонкой границей."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(border_width)
    else:
        shape.line.fill.background()
    return shape

def add_pill_badge(slide, left, top, width, height, text, bg_color=COLOR_EMERALD, text_color=COLOR_BLACK, font_size=10):
    """Создает компактный капсульный бейдж."""
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    badge.fill.solid()
    badge.fill.fore_color.rgb = bg_color
    badge.line.fill.background()
    tf = badge.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_MONO
    p.font.size = Pt(font_size)
    p.font.bold = True
    p.font.color.rgb = text_color
    return badge

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Пути к проверенным визуальным активам
    logo_path = "assets/presentation/krmu_logo.png"
    iceberg_path = "assets/presentation/iceberg_metaphor.png"
    drug_3d_path = "assets/presentation/3d_drug_model.png"
    roc_auc_path = "assets/presentation/roc_auc_benchmark.png"
    darikz_path = "assets/presentation/darikz_integration.png"

    # =========================================================================
    # СЛАЙД 1: ВСТУПЛЕНИЕ (ДРАМАТИЧЕСКИЙ ХУК — АНАЛОГИЯ ТИТАНИКА)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s1)

    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_BLACK
    bg1.line.fill.background()

    # Официальный логотип КРМУ
    if os.path.exists(logo_path):
        s1.shapes.add_picture(logo_path, Inches(0.9), Inches(0.6), width=Inches(1.2), height=Inches(1.2))

    uni_tb = s1.shapes.add_textbox(Inches(2.3), Inches(0.65), Inches(10.0), Inches(1.1)).text_frame
    uni_tb.word_wrap = True
    p = uni_tb.paragraphs[0]
    p.text = "КАЗАХСТАНСКО-РОССИЙСКИЙ МЕДИЦИНСКИЙ УНИВЕРСИТЕТ (КРМУ)"
    p.font.name = FONT_HERO
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = uni_tb.add_paragraph()
    p.text = "Кафедра клинической фармакологии и доказательной медицины  ·  Алматы, 2026"
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_MUTED

    # Центральный хук
    hook_tb = s1.shapes.add_textbox(Inches(0.9), Inches(2.0), Inches(11.533), Inches(3.2)).text_frame
    hook_tb.word_wrap = True

    p = hook_tb.paragraphs[0]
    p.text = "«КОГДА ТИТАНИК СТОЛКНУЛСЯ С АЙСБЕРГОМ,"
    p.font.name = FONT_HERO
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = hook_tb.add_paragraph()
    p.text = "ОРКЕСТР ПРОДОЛЖАЛ ИГРАТЬ.»"
    p.font.name = FONT_HERO
    p.font.size = Pt(46)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_before = Pt(4)

    p = hook_tb.add_paragraph()
    p.text = "Пассажиры первого класса пили шампанское и отказывались садиться в шлюпки — ведь палуба казалась непотопляемой. В трюмах в этот момент уже бурлила ледяная вода.\n\nВ полипрагмазии происходит то же самое: пациент выпивает утром 5–7 таблеток, улыбается, давление 120/80... Музыка играет. А на молекулярном уровне — в цитохромах печени и микрососудах почек — корабль уже идет ко дну."
    p.font.name = FONT_BODY
    p.font.size = Pt(15.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(16)

    # Нижняя плашка авторов и научного руководителя
    auth_card = create_card(s1, Inches(0.9), Inches(5.35), Inches(11.533), Inches(1.75), bg_color=RGBColor(8, 14, 18), border_color=COLOR_EMERALD, border_width=1.5)

    badge_tb = s1.shapes.add_textbox(Inches(1.15), Inches(5.42), Inches(11.0), Inches(0.35)).text_frame
    badge_tb.word_wrap = True
    p = badge_tb.paragraphs[0]
    p.text = "МЫ НАЗВАЛИ ЭТОТ НЕВИДИМЫЙ АЙСБЕРГ: СКРЫТАЯ ПОЛИПРАГМАЗИЯ. И СЕГОДНЯ МЫ ПОКАЖЕМ ШЛЮПКУ."
    p.font.name = FONT_MONO
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    # Левая колонка: Авторы проекта
    col1_tb = s1.shapes.add_textbox(Inches(1.15), Inches(5.82), Inches(5.2), Inches(1.15)).text_frame
    col1_tb.word_wrap = True
    p = col1_tb.paragraphs[0]
    p.text = "АВТОРЫ ПРОЕКТА / ОРЫНДАҒАНДАР:"
    p.font.name = FONT_MONO
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = col1_tb.add_paragraph()
    p.text = "Накипов Адилжан  ·  Ернур Аханаев"
    p.font.name = FONT_HERO
    p.font.size = Pt(14.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(2)

    p = col1_tb.add_paragraph()
    p.text = "Студенты группы 107 Б, КРМУ"
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(2)

    # Правая колонка: Ғылыми жетекші
    col2_tb = s1.shapes.add_textbox(Inches(6.6), Inches(5.82), Inches(5.6), Inches(1.15)).text_frame
    col2_tb.word_wrap = True
    p = col2_tb.paragraphs[0]
    p.text = "ҒЫЛЫМИ ЖЕТЕКШІ / НАУЧНЫЙ РУКОВОДИТЕЛЬ:"
    p.font.name = FONT_MONO
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = col2_tb.add_paragraph()
    p.text = "Баймаханова Айгуль Бекмолдаевна"
    p.font.name = FONT_HERO
    p.font.size = Pt(14.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(2)

    p = col2_tb.add_paragraph()
    p.text = "«Қоғамдық пәндер» кафедрасының аға оқытушысы, педагогика ғылымдарының магистрі"
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(2)

    # =========================================================================
    # СЛАЙД 2: АКТУАЛЬНОСТЬ ПРОЕКТА (АЙСБЕРГ ПОЛИПРАГМАЗИИ)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s2)

    bg2 = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg2.fill.solid()
    bg2.fill.fore_color.rgb = COLOR_BLACK
    bg2.line.fill.background()

    # Левая колонка: Инфографика айсберга
    create_card(s2, Inches(0.8), Inches(0.8), Inches(6.8), Inches(5.9), border_color=COLOR_CARD_BORDER)
    if os.path.exists(iceberg_path):
        s2.shapes.add_picture(iceberg_path, Inches(0.9), Inches(0.9), width=Inches(6.6), height=Inches(5.7))

    # Правая колонка: Актуальность проблемы
    rx2 = Inches(7.85)
    rw2 = Inches(4.7)

    add_pill_badge(s2, rx2, Inches(0.8), Inches(2.8), Inches(0.35), "АКТУАЛЬНОСТЬ ПРОЕКТА", bg_color=COLOR_CORAL, text_color=COLOR_WHITE)

    stat_tb = s2.shapes.add_textbox(rx2, Inches(1.3), rw2, Inches(5.4)).text_frame
    stat_tb.word_wrap = True

    p = stat_tb.paragraphs[0]
    p.text = "160 235"
    p.font.name = FONT_HERO
    p.font.size = Pt(54)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = stat_tb.add_paragraph()
    p.text = "записей о лекарственных взаимодействиях в базе DDInter (1 939 препаратов)."
    p.font.name = FONT_BODY
    p.font.size = Pt(13.5)
    p.font.color.rgb = COLOR_CYAN
    p.space_before = Pt(2)

    p = stat_tb.add_paragraph()
    p.text = "ПРЕДЕЛ ПАМЯТИ ВРАЧА НА ОБХОДЕ:"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_CORAL
    p.space_before = Pt(18)

    p = stat_tb.add_paragraph()
    p.text = "• В терапевтических и гериатрических отделениях пациенты получают по 5–9 препаратов одновременно.\n• Комбинаторный взрыв превышает 2 000 000 потенциальных триад. Человеческий мозг врача физически не может удержать этот объем.\n• Листание бумажных формуляров отнимает 20 минут на одного пациента и не защищает от субклинических токсических каскадов."
    p.font.name = FONT_BODY
    p.font.size = Pt(11.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(4)

    p = stat_tb.add_paragraph()
    p.text = "РАСПРЕДЕЛЕНИЕ ТЯЖЕСТИ В DDINTER:"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_before = Pt(16)

    p = stat_tb.add_paragraph()
    p.text = "Major (тяжелые): 26 914 (17%) · Moderate: 96 675 (60%). Топ-хаб: siponimod (504 связи). Необходим автоматизированный аудит."
    p.font.name = FONT_BODY
    p.font.size = Pt(11.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    # =========================================================================
    # СЛАЙД 3: ЦЕЛЬ ПРОЕКТА И НАУЧНАЯ НОВИЗНА ИССЛЕДОВАНИЯ
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s3)

    bg3 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg3.fill.solid()
    bg3.fill.fore_color.rgb = COLOR_BLACK
    bg3.line.fill.background()

    add_pill_badge(s3, Inches(0.8), Inches(0.6), Inches(3.2), Inches(0.35), "МИССИЯ И НАУЧНАЯ НОВИЗНА", bg_color=COLOR_EMERALD, text_color=COLOR_BLACK)

    s3_head = s3.shapes.add_textbox(Inches(0.8), Inches(1.05), Inches(11.7), Inches(0.8)).text_frame
    p = s3_head.paragraphs[0]
    p.text = "От пассивного поиска по справочникам — к преэмптивному графовому аудиту."
    p.font.name = FONT_HERO
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    col_w3 = Inches(5.7)
    gap3 = Inches(0.33)
    y3 = Inches(2.0)
    h3 = Inches(4.8)

    # Левая карточка: ЦЕЛЬ ПРОЕКТА
    create_card(s3, Inches(0.8), y3, col_w3, h3, border_color=COLOR_EMERALD, border_width=1.5)
    tb_goal = s3.shapes.add_textbox(Inches(1.0), y3 + Inches(0.25), col_w3 - Inches(0.4), h3 - Inches(0.4)).text_frame
    tb_goal.word_wrap = True

    p = tb_goal.paragraphs[0]
    p.text = "ЦЕЛЬ ИССЛЕДОВАТЕЛЬСКОГО ПРОЕКТА"
    p.font.name = FONT_MONO
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb_goal.add_paragraph()
    p.text = "Создать научно обоснованную платформу для преэмптивного аудита полипрагмазии и воспроизводимого предсказания связей в графе DDInter."
    p.font.name = FONT_HERO
    p.font.size = Pt(15.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(8)

    p = tb_goal.add_paragraph()
    p.text = "КЛЮЧЕВЫЕ ЗАДАЧИ:"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.space_before = Pt(16)

    p = tb_goal.add_paragraph()
    p.text = "1. Собрать, очистить и нормализовать 160 235 пар взаимодействий без петель и дубликатов.\n2. Построить топологический граф 1 939 субстанций с интерактивной навигацией.\n3. Обучить модели ML (Random Forest, LogReg) и строго сравнить с эвристиками.\n4. Предоставить клиницисту персональное досье рисков с разбором цитохромов CYP450 и доказательствами PubMed."
    p.font.name = FONT_BODY
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(6)

    # Правая карточка: НАУЧНАЯ НОВИЗНА
    create_card(s3, Inches(0.8) + col_w3 + gap3, y3, col_w3, h3, border_color=COLOR_CYAN, border_width=1.5)
    tb_nov = s3.shapes.add_textbox(Inches(1.0) + col_w3 + gap3, y3 + Inches(0.25), col_w3 - Inches(0.4), h3 - Inches(0.4)).text_frame
    tb_nov.word_wrap = True

    p = tb_nov.paragraphs[0]
    p.text = "НАУЧНАЯ НОВИЗНА ИССЛЕДОВАНИЯ"
    p.font.name = FONT_MONO
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = tb_nov.add_paragraph()
    p.text = "1. Исключение Data Leakage (Утечки данных)"
    p.font.name = FONT_HERO
    p.font.size = Pt(13.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(8)

    p = tb_nov.add_paragraph()
    p.text = "В отличие от распространенных работ, где модель подсматривает в полный граф, в Pharma Sentinel train (12%) и test (20%) физически исключены из графа признаков (68%)."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(2)

    p = tb_nov.add_paragraph()
    p.text = "2. Топологический ансамбль Adamic-Adar + ML"
    p.font.name = FONT_HERO
    p.font.size = Pt(13.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(12)

    p = tb_nov.add_paragraph()
    p.text = "Доказано преимущество ансамбля над простыми правилами (+0.019 ROC-AUC над общими соседями) при ранжировании гипотез неизвестных связей."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(2)

    p = tb_nov.add_paragraph()
    p.text = "3. Комплексный мультимодальный аудит"
    p.font.name = FONT_HERO
    p.font.size = Pt(13.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(12)

    p = tb_nov.add_paragraph()
    p.text = "Совмещение графового анализа DDInter, фитотоксикологии БАДов по PubMed и интерактивной 3D-демонстрации микросомальных ферментов."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(2)

    # =========================================================================
    # СЛАЙД 4: ОБЯЗАННОСТИ И РАСПРЕДЕЛЕНИЕ РОЛЕЙ В КОМАНДЕ
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s4)

    bg4 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg4.fill.solid()
    bg4.fill.fore_color.rgb = COLOR_BLACK
    bg4.line.fill.background()

    add_pill_badge(s4, Inches(0.8), Inches(0.6), Inches(3.0), Inches(0.35), "КОМАНДА И ОБЯЗАННОСТИ", bg_color=COLOR_PURPLE, text_color=COLOR_WHITE)

    s4_head = s4.shapes.add_textbox(Inches(0.8), Inches(1.05), Inches(11.7), Inches(0.8)).text_frame
    p = s4_head.paragraphs[0]
    p.text = "Специализация исследователей: от алгоритмического графа до клиники."
    p.font.name = FONT_HERO
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    col_w4 = Inches(5.7)
    gap4 = Inches(0.33)
    y4 = Inches(2.0)
    h4 = Inches(4.8)

    # Карточка 1: НАКИПОВ АДИЛЖАН
    create_card(s4, Inches(0.8), y4, col_w4, h4, border_color=COLOR_EMERALD, border_width=1.5)
    tb_adil = s4.shapes.add_textbox(Inches(1.0), y4 + Inches(0.25), col_w4 - Inches(0.4), h4 - Inches(0.4)).text_frame
    tb_adil.word_wrap = True

    p = tb_adil.paragraphs[0]
    p.text = "НАКИПОВ АДИЛЖАН"
    p.font.name = FONT_HERO
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb_adil.add_paragraph()
    p.text = "Ведущий разработчик платформы & ML-исследователь · Группа 107 Б"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(2)

    p = tb_adil.add_paragraph()
    p.text = "ОБЯЗАННОСТИ И ВЫПОЛНЕННЫЕ ЗАДАЧИ:"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.space_before = Pt(18)

    p = tb_adil.add_paragraph()
    p.text = "• Разработка архитектуры полного цикла обработки данных DDInter: объединение 8 CSV-массивов, очистка дубликатов, нормализация регистра и МНН-синонимов.\n\n• Построение матриц графа и расчет шести топологических признаков: Common Neighbors, Jaccard, Adamic-Adar, степеней узлов.\n\n• Проектирование эксперимента без утечки данных (Leakage-Free), обучение ансамбля Random Forest и Logistic Regression со строгой валидацией.\n\n• Реализация интерактивного веб-интерфейса Streamlit, включая WebAudio-сопровождение, мобильную адаптивность и компоненты React Bits."
    p.font.name = FONT_BODY
    p.font.size = Pt(11.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(6)

    # Карточка 2: ЕРНУР АХАНАЕВ
    create_card(s4, Inches(0.8) + col_w4 + gap4, y4, col_w4, h4, border_color=COLOR_CYAN, border_width=1.5)
    tb_ernur = s4.shapes.add_textbox(Inches(1.0) + col_w4 + gap4, y4 + Inches(0.25), col_w4 - Inches(0.4), h4 - Inches(0.4)).text_frame
    tb_ernur.word_wrap = True

    p = tb_ernur.paragraphs[0]
    p.text = "ЕРНУР АХАНАЕВ"
    p.font.name = FONT_HERO
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = tb_ernur.add_paragraph()
    p.text = "Клинический фармаколог & Аналитик доказательной базы · Группа 107 Б"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(2)

    p = tb_ernur.add_paragraph()
    p.text = "ОБЯЗАННОСТИ И ВЫПОЛНЕННЫЕ ЗАДАЧИ:"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p.space_before = Pt(18)

    p = tb_ernur.add_paragraph()
    p.text = "• Клинико-фармакологический аудит ключевых когортных сценариев: каскада блокады цитохрома CYP2C9 (Варфарин + Кордарон) и почечной триады Triple Whammy.\n\n• Формирование доказательной базы взаимодействий лекарств с нутрицевтиками и БАДами на основе верифицированных исследований PubMed.\n\n• Разработка клинических рекомендаций по мониторингу (МНО, креатинин, СКФ) и симптомов тревоги («красных флагов») для врача.\n\n• Анализ структуры Государственного реестра ЛС РК и формирование дорожной карты (Roadmap) интеграции платформы с DariKz."
    p.font.name = FONT_BODY
    p.font.size = Pt(11.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(6)

    # =========================================================================
    # СЛАЙД 5: ПРЕДСТАВЛЕНИЕ ПРОДУКТА (СТИЛЬ СТИВА ДЖОБСА · ПРАВИЛО ТРЁХ)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s5)

    bg5 = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg5.fill.solid()
    bg5.fill.fore_color.rgb = COLOR_BLACK
    bg5.line.fill.background()

    add_pill_badge(s5, Inches(0.8), Inches(0.6), Inches(2.8), Inches(0.35), "ПРЕДСТАВЛЕНИЕ ПРОДУКТА", bg_color=COLOR_EMERALD, text_color=COLOR_BLACK)

    s5_head = s5.shapes.add_textbox(Inches(0.8), Inches(1.05), Inches(11.7), Inches(0.8)).text_frame
    p = s5_head.paragraphs[0]
    p.text = "Каждые несколько лет появляется технология, меняющая правила игры."
    p.font.name = FONT_HERO
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    cw5 = Inches(3.75)
    gap5 = Inches(0.24)
    y5 = Inches(2.05)
    h5 = Inches(3.3)

    # 1. 3D Визуализация
    create_card(s5, Inches(0.8), y5, cw5, h5, border_color=COLOR_EMERALD)
    tb1 = s5.shapes.add_textbox(Inches(1.0), y5 + Inches(0.2), cw5 - Inches(0.4), h5 - Inches(0.4)).text_frame
    tb1.word_wrap = True
    p = tb1.paragraphs[0]
    p.text = "01"
    p.font.name = FONT_HERO
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb1.add_paragraph()
    p.text = "3D-ВИЗУАЛИЗАЦИЯ КАСКАДОВ (ИЛЛЮСТРАЦИЯ)"
    p.font.name = FONT_HERO
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb1.add_paragraph()
    p.text = "Наглядная концептуальная демонстрация пространственного поведения молекул и аллостерической блокады цитохромов печени."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(8)

    # 2. Graph ML
    create_card(s5, Inches(0.8) + cw5 + gap5, y5, cw5, h5, border_color=COLOR_CYAN)
    tb2 = s5.shapes.add_textbox(Inches(1.0) + cw5 + gap5, y5 + Inches(0.2), cw5 - Inches(0.4), h5 - Inches(0.4)).text_frame
    tb2.word_wrap = True
    p = tb2.paragraphs[0]
    p.text = "02"
    p.font.name = FONT_HERO
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = tb2.add_paragraph()
    p.text = "ЧЕСТНЫЙ ГРАФОВЫЙ ML (ROC-AUC 0.911)"
    p.font.name = FONT_HERO
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb2.add_paragraph()
    p.text = "Научно выверенная предиктивная модель связей на скрытых записях без Data Leakage, восстанавливающая структуру базы."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(8)

    # 3. Roadmap
    create_card(s5, Inches(0.8) + (cw5 + gap5) * 2, y5, cw5, h5, border_color=COLOR_ORANGE)
    tb3 = s5.shapes.add_textbox(Inches(1.0) + (cw5 + gap5) * 2, y5 + Inches(0.2), cw5 - Inches(0.4), h5 - Inches(0.4)).text_frame
    tb3.word_wrap = True
    p = tb3.paragraphs[0]
    p.text = "03"
    p.font.name = FONT_HERO
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = COLOR_ORANGE

    p = tb3.add_paragraph()
    p.text = "ПЕРСПЕКТИВА DARIKZ В СМАРТФОНЕ ВРАЧА"
    p.font.name = FONT_HERO
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb3.add_paragraph()
    p.text = "Дорожная карта интеграции с Государственным реестром Казахстана и мобильное рабочее место врача на утреннем обходе."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(8)

    # Панчлайн
    p_card = create_card(s5, Inches(0.8), Inches(5.6), Inches(11.733), Inches(1.3), bg_color=RGBColor(8, 16, 20), border_color=COLOR_WHITE, border_width=1.5)
    tb_punch = s5.shapes.add_textbox(Inches(1.0), Inches(5.68), Inches(11.3), Inches(1.1)).text_frame
    tb_punch.word_wrap = True
    p = tb_punch.paragraphs[0]
    p.text = "«Это не три отдельных инструмента. Это один целостный продукт:»"
    p.font.name = FONT_BODY
    p.font.size = Pt(13)
    p.font.color.rgb = COLOR_MUTED

    p = tb_punch.add_paragraph()
    p.text = "PHARMA SENTINEL  ·  THE CLINICAL INTELLIGENCE PLATFORM"
    p.font.name = FONT_HERO
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_before = Pt(2)

    # =========================================================================
    # СЛАЙД 6: 3D МОДЕЛЬ КАСКАДОВ (ВАРФАРИН × КОРДАРОН, TRIPLE WHAMMY)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s6)

    bg6 = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg6.fill.solid()
    bg6.fill.fore_color.rgb = COLOR_BLACK
    bg6.line.fill.background()

    create_card(s6, Inches(0.8), Inches(0.8), Inches(6.8), Inches(5.9), border_color=COLOR_EMERALD)
    if os.path.exists(drug_3d_path):
        s6.shapes.add_picture(drug_3d_path, Inches(0.9), Inches(0.9), width=Inches(6.6), height=Inches(5.7))

    rx6 = Inches(7.85)
    rw6 = Inches(4.7)

    add_pill_badge(s6, rx6, Inches(0.8), Inches(3.2), Inches(0.35), "КОНЦЕПТУАЛЬНАЯ 3D-ИЛЛЮСТРАЦИЯ", bg_color=COLOR_EMERALD, text_color=COLOR_BLACK)

    s6_tb = s6.shapes.add_textbox(rx6, Inches(1.3), rw6, Inches(5.4)).text_frame
    s6_tb.word_wrap = True

    p = s6_tb.paragraphs[0]
    p.text = "Органам не нужно прямое связывание молекул, чтобы возник токсический эффект."
    p.font.name = FONT_HERO
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = s6_tb.add_paragraph()
    p.text = "1. Каскад Варфарин × Амиодарон (CYP2C9)"
    p.font.name = FONT_HERO
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.space_before = Pt(14)

    p = s6_tb.add_paragraph()
    p.text = "Они не реагируют в пробирке. Но в организме амиодарон ингибирует изофермент CYP2C9. Итог: метаболизм варфарина замедляется, МНО поднимается выше 6.0, риск массивного кровотечения."
    p.font.name = FONT_BODY
    p.font.size = Pt(11.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(4)

    p = s6_tb.add_paragraph()
    p.text = "2. Феномен Triple Whammy (Почечная триада)"
    p.font.name = FONT_HERO
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_CORAL
    p.space_before = Pt(14)

    p = s6_tb.add_paragraph()
    p.text = "иАПФ + диуретик + НПВП (ибупрофен). Спазм приносящей артериолы почки и падение фильтрации вызывают острую почечную дисфункцию без боли в первые дни."
    p.font.name = FONT_BODY
    p.font.size = Pt(11.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(4)

    p = s6_tb.add_paragraph()
    p.text = "Примечание: 3D-модель является концептуальной визуализацией каскада (докинг в учебном проекте не рассчитывался)."
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.italic = True
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(14)

    # =========================================================================
    # СЛАЙД 7: ЧЕСТНЫЙ БЕНЧМАРК МОДЕЛИ (LEAKAGE-FREE ML · 0.911)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s7)

    bg7 = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg7.fill.solid()
    bg7.fill.fore_color.rgb = COLOR_BLACK
    bg7.line.fill.background()

    create_card(s7, Inches(0.8), Inches(0.8), Inches(6.8), Inches(5.9), border_color=COLOR_CARD_BORDER)
    if os.path.exists(roc_auc_path):
        s7.shapes.add_picture(roc_auc_path, Inches(0.9), Inches(0.9), width=Inches(6.6), height=Inches(5.7))

    rx7 = Inches(7.85)
    rw7 = Inches(4.7)

    add_pill_badge(s7, rx7, Inches(0.8), Inches(2.6), Inches(0.35), "ЧЕСТНЫЙ БЕНЧМАРК ML", bg_color=COLOR_CYAN, text_color=COLOR_BLACK)

    num_tb = s7.shapes.add_textbox(rx7, Inches(1.25), rw7, Inches(5.4)).text_frame
    num_tb.word_wrap = True

    p = num_tb.paragraphs[0]
    p.text = "0.911"
    p.font.name = FONT_HERO
    p.font.size = Pt(62)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = num_tb.add_paragraph()
    p.text = "ROC-AUC Случайного леса (Random Forest) на независимом тесте"
    p.font.name = FONT_HERO
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(2)

    p = num_tb.add_paragraph()
    p.text = "ЛЕГИТИМНЫЙ LEAKAGE-FREE ЭКСПЕРИМЕНТ"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.space_before = Pt(16)

    p = num_tb.add_paragraph()
    p.text = "• 12% связей — обучение, 20% — тест (строго исключены из графа).\n• Признаки рассчитываются только по оставшимся 68% ребер.\n• В тест включены сбалансированные отрицательные пары (без записей в базе)."
    p.font.name = FONT_BODY
    p.font.size = Pt(11.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(6)

    comp_card = create_card(s7, rx7, Inches(4.75), rw7, Inches(1.95), bg_color=RGBColor(10, 18, 22), border_color=COLOR_EMERALD, border_width=1)
    comp_tb = s7.shapes.add_textbox(rx7 + Inches(0.15), Inches(4.8), rw7 - Inches(0.3), Inches(1.8)).text_frame
    comp_tb.word_wrap = True
    p = comp_tb.paragraphs[0]
    p.text = "РЕЗУЛЬТАТЫ ЭТАЛОННОГО ПРОГОНА:"
    p.font.name = FONT_MONO
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p = comp_tb.add_paragraph()
    p.text = "• Случайный лес: 0.911 ROC-AUC (PR-AUC 0.905)\n• Только общие соседи: 0.892 ROC-AUC (базовый ориентир)\n• Логистическая регрессия: 0.887 ROC-AUC\n• Произведение степеней: 0.875 ROC-AUC\n• Случайное угадывание: 0.500 ROC-AUC"
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    # =========================================================================
    # СЛАЙД 8: ДОРОЖНАЯ КАРТА (ROADMAP · DARIKZ И ПИЛОТ В КРМУ)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s8)

    bg8 = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg8.fill.solid()
    bg8.fill.fore_color.rgb = COLOR_BLACK
    bg8.line.fill.background()

    create_card(s8, Inches(0.8), Inches(0.8), Inches(6.8), Inches(5.9), border_color=COLOR_CARD_BORDER)
    if os.path.exists(darikz_path):
        s8.shapes.add_picture(darikz_path, Inches(0.9), Inches(0.9), width=Inches(6.6), height=Inches(5.7))

    rx8 = Inches(7.85)
    rw8 = Inches(4.7)

    add_pill_badge(s8, rx8, Inches(0.8), Inches(2.8), Inches(0.35), "ПЛАН РАЗВИТИЯ (ROADMAP)", bg_color=COLOR_ORANGE, text_color=COLOR_BLACK)

    s8_tb = s8.shapes.add_textbox(rx8, Inches(1.3), rw8, Inches(5.4)).text_frame
    s8_tb.word_wrap = True

    p = s8_tb.paragraphs[0]
    p.text = "От прототипа — к клинике."
    p.font.name = FONT_HERO
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = s8_tb.add_paragraph()
    p.text = "Перспективная дорожная карта внедрения инструмента в систему здравоохранения РК."
    p.font.name = FONT_BODY
    p.font.size = Pt(13)
    p.font.color.rgb = COLOR_CYAN
    p.space_before = Pt(4)

    p = s8_tb.add_paragraph()
    p.text = "ЭТАП 1: ТЕКУЩИЙ СТАТУС (РЕАЛИЗОВАНО)"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_before = Pt(16)

    p = s8_tb.add_paragraph()
    p.text = "• Очищенный датасет 160 235 пар DDInter и граф 1 939 препаратов.\n• Leakage-free ML-оценка (Random Forest 0.911).\n• Интерактивная веб-платформа на Streamlit."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(4)

    p = s8_tb.add_paragraph()
    p.text = "ЭТАП 2: ИНТЕГРАЦИЯ С DARIKZ (ПЛАН)"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.space_before = Pt(14)

    p = s8_tb.add_paragraph()
    p.text = "• Сопоставление торговых наименований РК с международными МНН.\n• Мобильный ассистент врача для экспресс-проверки на обходе."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(4)

    p = s8_tb.add_paragraph()
    p.text = "ЭТАП 3: КЛИНИЧЕСКИЙ ПИЛОТ В КРМУ (ПЕРСПЕКТИВА)"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p.space_before = Pt(14)

    p = s8_tb.add_paragraph()
    p.text = "• Апробация преэмптивного скрининга в клиниках университета.\n• Интеграция с КМИС ДамуМед."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(4)

    # =========================================================================
    # СЛАЙД 9: ПРИМЕНЕННЫЕ ИСТОЧНИКИ И ДОКАЗАТЕЛЬНАЯ БАЗА
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s9)

    bg9 = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg9.fill.solid()
    bg9.fill.fore_color.rgb = COLOR_BLACK
    bg9.line.fill.background()

    add_pill_badge(s9, Inches(0.8), Inches(0.55), Inches(3.4), Inches(0.35), "ПРИМЕНЕННЫЕ ИСТОЧНИКИ", bg_color=COLOR_EMERALD, text_color=COLOR_BLACK)

    s9_head = s9.shapes.add_textbox(Inches(0.8), Inches(0.98), Inches(11.7), Inches(0.75)).text_frame
    p = s9_head.paragraphs[0]
    p.text = "Научно-доказательный фундамент проекта Pharma Sentinel"
    p.font.name = FONT_HERO
    p.font.size = Pt(23)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = s9_head.add_paragraph()
    p.text = "Все алгоритмические выводы, топология графа и клинические риски опираются на верифицированные источники."
    p.font.name = FONT_BODY
    p.font.size = Pt(11.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(2)

    cw9 = Inches(5.7)
    gap9_x = Inches(0.33)
    h9 = Inches(2.55)
    y9_row1 = Inches(1.85)
    y9_row2 = Inches(4.55)

    # 1. Базы данных DDI
    create_card(s9, Inches(0.8), y9_row1, cw9, h9, border_color=COLOR_EMERALD, border_width=1.5)
    tb_src1 = s9.shapes.add_textbox(Inches(0.95), y9_row1 + Inches(0.15), cw9 - Inches(0.3), h9 - Inches(0.3)).text_frame
    tb_src1.word_wrap = True
    p = tb_src1.paragraphs[0]
    p.text = "01. БАЗЫ МЕЖЛЕКАРСТВЕННЫХ ВЗАИМОДЕЙСТВИЙ"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD

    p = tb_src1.add_paragraph()
    p.text = "• Xiong, G. et al. (2022). DDInter: an online drug-drug interaction database toward improving clinical medication safety. Nucleic Acids Res., 50(D1), D1200-D1207."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb_src1.add_paragraph()
    p.text = "  160 235 верифицированных записей, 1 939 субстанций, валидированные уровни Major/Moderate/Minor."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(1)

    p = tb_src1.add_paragraph()
    p.text = "• Государственный реестр ЛС Республики Казахстан (НЦЭЛС МЗ РК / DariKz)."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb_src1.add_paragraph()
    p.text = "  Официальный национальный классификатор зарегистрированных торговых форм и дозировок."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(1)

    # 2. Клиническая фармакогенетика
    create_card(s9, Inches(0.8) + cw9 + gap9_x, y9_row1, cw9, h9, border_color=COLOR_CYAN, border_width=1.5)
    tb_src2 = s9.shapes.add_textbox(Inches(0.95) + cw9 + gap9_x, y9_row1 + Inches(0.15), cw9 - Inches(0.3), h9 - Inches(0.3)).text_frame
    tb_src2.word_wrap = True
    p = tb_src2.paragraphs[0]
    p.text = "02. КЛИНИЧЕСКИЕ РУКОВОДСТВА И ФАРМАКОПЕЯ"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = tb_src2.add_paragraph()
    p.text = "• Goodman & Gilman’s The Pharmacological Basis of Therapeutics (14th Ed., McGraw-Hill, 2022)."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb_src2.add_paragraph()
    p.text = "  Фундаментальные механизмы печеночного клиренса и ингибирования цитохромов CYP2C9 / CYP3A4."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(1)

    p = tb_src2.add_paragraph()
    p.text = "• CPIC Guidelines (Clinical Pharmacogenetics Implementation Consortium)."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb_src2.add_paragraph()
    p.text = "  Международные стандарты дозирования и мониторинга полиморфизма генов CYP2C9 и VKORC1."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(1)

    # 3. Доказательная биомедицина PubMed
    create_card(s9, Inches(0.8), y9_row2, cw9, h9, border_color=COLOR_ORANGE, border_width=1.5)
    tb_src3 = s9.shapes.add_textbox(Inches(0.95), y9_row2 + Inches(0.15), cw9 - Inches(0.3), h9 - Inches(0.3)).text_frame
    tb_src3.word_wrap = True
    p = tb_src3.paragraphs[0]
    p.text = "03. ДОКАЗАТЕЛЬНАЯ МЕДИЦИНА (PUBMED / NLM)"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ORANGE

    p = tb_src3.add_paragraph()
    p.text = "• Lapi, F. et al. (2013). Concurrent use of diuretics, ACE inhibitors, and NSAIDs and risk of acute kidney injury: nested case-control study. BMJ, 346, e8525."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb_src3.add_paragraph()
    p.text = "  Клиническое когортное обоснование феномена почечной недостаточности Triple Whammy."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(1)

    p = tb_src3.add_paragraph()
    p.text = "• PubMed Phytotherapy Reviews (2019–2024): Взаимодействия БАДов."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb_src3.add_paragraph()
    p.text = "  Фитотоксикология зверобоя (Hypericum), гинкго билобы и женьшеня через P-gp и CYP3A4."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(1)

    # 4. Топология графов и ML
    create_card(s9, Inches(0.8) + cw9 + gap9_x, y9_row2, cw9, h9, border_color=COLOR_PURPLE, border_width=1.5)
    tb_src4 = s9.shapes.add_textbox(Inches(0.95) + cw9 + gap9_x, y9_row2 + Inches(0.15), cw9 - Inches(0.3), h9 - Inches(0.3)).text_frame
    tb_src4.word_wrap = True
    p = tb_src4.paragraphs[0]
    p.text = "04. ТЕОРИЯ ГРАФОВ И МАШИННОЕ ОБУЧЕНИЕ"
    p.font.name = FONT_MONO
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE

    p = tb_src4.add_paragraph()
    p.text = "• Liben-Nowell, D. & Kleinberg, J. (2007). The link-prediction problem for social networks. JASIST, 58(7), 1019-1031."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb_src4.add_paragraph()
    p.text = "  Математическая база топологического предсказания связей в комплексных графовых сетях."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(1)

    p = tb_src4.add_paragraph()
    p.text = "• Adamic, L. A. & Adar, E. (2003). Friends and neighbors on the Web. Social Networks."
    p.font.name = FONT_BODY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(4)

    p = tb_src4.add_paragraph()
    p.text = "  Библиотеки Scikit-learn (Random Forest) и NetworkX с защитой от Data Leakage."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(1)

    # =========================================================================
    # СЛАЙД 10: ЗАКЛЮЧЕНИЕ (THE FINALE)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_slide_fade_transition(s10)

    bg10 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg10.fill.solid()
    bg10.fill.fore_color.rgb = COLOR_BLACK
    bg10.line.fill.background()

    quote_tb = s10.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(10.933), Inches(3.2)).text_frame
    quote_tb.word_wrap = True

    p = quote_tb.paragraphs[0]
    p.text = "«БУДУЩЕЕ МЕДИЦИНЫ ПРИНАДЛЕЖИТ НЕ ТЕМ, КТО ИСПРАВЛЯЕТ ОШИБКИ,"
    p.font.name = FONT_HERO
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = quote_tb.add_paragraph()
    p.text = "А ТЕМ, КТО ДЕЛАЕТ ИХ НЕВОЗМОЖНЫМИ.»"
    p.font.name = FONT_HERO
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_before = Pt(6)

    fin_tb = s10.shapes.add_textbox(Inches(1.2), Inches(5.2), Inches(10.933), Inches(1.6)).text_frame
    fin_tb.word_wrap = True

    p = fin_tb.paragraphs[0]
    p.text = "PHARMA SENTINEL  ·  КАЗАХСТАНСКО-РОССИЙСКИЙ МЕДИЦИНСКИЙ УНИВЕРСИТЕТ"
    p.font.name = FONT_MONO
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    p = fin_tb.add_paragraph()
    p.text = "Накипов Адилжан  ·  Ернур Аханаев   |   Группа 107 Б"
    p.font.name = FONT_HERO
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_before = Pt(3)

    p = fin_tb.add_paragraph()
    p.text = "Ғылыми жетекші: «Қоғамдық пәндер» каф. аға оқытушысы, пед. ғ. магистрі Баймаханова А. Б."
    p.font.name = FONT_BODY
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_EMERALD
    p.space_before = Pt(3)

    p = fin_tb.add_paragraph()
    p.text = "Благодарим за внимание. Мы готовы ответить на вопросы комиссии."
    p.font.name = FONT_BODY
    p.font.size = Pt(13)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(5)

    output_path = "Pharma_Sentinel_Steve_Jobs_Keynote.pptx"
    prs.save(output_path)
    print(f"SUCCESS: Steve Jobs Keynote (10 slides, with Sources, without Serik Merey) created at {os.path.abspath(output_path)}")

if __name__ == "__main__":
    build_presentation()
