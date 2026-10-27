"""Интерактивный учебный проект Pharma Sentinel на Streamlit."""
from difflib import get_close_matches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from data_loader import DataValidationError, load_ddinter
from graph_builder import interaction_color, major_hubs
from local_ai import ask_local_model, list_local_models, make_evidence_prompt
from model import novel_pair_hypotheses, train_and_evaluate


st.set_page_config(page_title="Pharma Sentinel", page_icon="✳️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#182638; --muted:#748296; --line:#e2e8ed; --teal:#0f9b8e; --navy:#102a43; --paper:#f7f8f6; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:var(--paper); color:var(--ink); }
.block-container { max-width:1440px; padding-top:1.7rem; padding-bottom:3rem; }
@keyframes page-arrive { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
section[data-testid="stMain"] .block-container { animation:page-arrive .55s cubic-bezier(.2,.7,.2,1) both; }
h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:-.04em; color:var(--ink); }
h1 { font-size:2.15rem !important; }
h2 { font-size:1.4rem !important; }
.hero { position:relative; overflow:hidden; padding:1.45rem 1.7rem 1.55rem; border:1px solid #dce5e5; border-radius:4px 22px 4px 22px; background:#fff; margin-bottom:1.15rem; }
.hero:after { content:'PS'; position:absolute; right:2rem; top:-2.5rem; color:#f1f5f2; font:800 11rem/1 'Manrope',sans-serif; letter-spacing:-.12em; pointer-events:none; }
.eyebrow { color:var(--teal); font-weight:700; text-transform:uppercase; letter-spacing:.17em; font-size:.7rem; }
.hero h1 { font-size:2.55rem !important; margin:.25rem 0 .25rem; position:relative; z-index:1; }
.hero p { color:#647386; margin:0; font-size:.98rem; position:relative; z-index:1; }
.hero-meta { display:flex; gap:.55rem; margin-top:1rem; color:#617184; font-size:.7rem; text-transform:uppercase; letter-spacing:.11em; font-weight:700; }
.hero-meta span { border:1px solid #e0e9e6; padding:.32rem .55rem; border-radius:99px; background:#fbfdfc; }
.safety { background:#fff7e9; border-left:4px solid #dfa43c; color:#6b4b17; padding:.75rem 1rem; border-radius:2px 10px 10px 2px; margin:.7rem 0 1.35rem; font-weight:600; font-size:.9rem; }
.metric-card { background:#fff; border:1px solid var(--line); border-radius:4px 15px 4px 15px; padding:1.05rem 1.15rem; box-shadow:0 10px 30px #233a4b08; }
div[data-testid="stImage"] img { border-radius:4px 22px 4px 22px; object-fit:cover; box-shadow:0 18px 48px #1737501a; }
.stButton>button, div[data-testid="stDataFrame"], .metric-card { transition:transform .22s ease, box-shadow .22s ease, border-color .22s ease; }
.metric-card:hover { transform:translateY(-3px); box-shadow:0 16px 36px #233a4b12; border-color:#b8d7d2; }
.metric-label { color:#78899b; font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.11em; }
.metric-value { font-family:'Manrope',sans-serif; color:#1c3550; font-size:1.65rem; font-weight:800; margin-top:.2rem; }
section[data-testid="stSidebar"] { background:var(--navy); border-right:0; }
section[data-testid="stSidebar"] * { color:#eaf1f3; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label { font-weight:600; }
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap:.2rem; }
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label { padding:.48rem .6rem; border-radius:7px; }
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover { background:#ffffff12; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#b7c6cf; }
.stButton>button { border-radius:8px; border:1px solid #d7e2e1; font-weight:700; }
.stButton>button:hover { transform:translateY(-1px); border-color:#0f9b8e; color:#08786f; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:4px 13px 4px 13px; overflow:hidden; background:#fff; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:4px 15px 4px 15px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Читаю и очищаю DDInter…")
def cached_data():
    """Кэширует очистку исходных CSV до следующего изменения данных."""
    return load_ddinter()


@st.cache_data(show_spinner="Проверяю модели на скрытых связях…")
def cached_evaluation(pairs: pd.DataFrame, drugs: pd.DataFrame):
    """Кэширует весь воспроизводимый цикл обучения и оценки."""
    return train_and_evaluate(pairs, drugs)


def safety_note():
    st.markdown('<div class="safety">Учебный прототип. Не заменяет врача или фармацевта. Не меняйте лечение самостоятельно.</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)


def header():
    copy, photo = st.columns([1.55, 1], gap="large", vertical_alignment="center")
    with copy:
        st.markdown('<div class="hero"><div class="eyebrow">Лаборатория лекарственных данных · DDInter</div><h1>Pharma Sentinel</h1><p>Учебный инструмент для поиска записей о сочетаниях препаратов и исследования связей между ними.</p><div class="hero-meta"><span>01 · поиск DDInter</span><span>02 · карта сети</span><span>03 · ML-эксперимент</span></div></div>', unsafe_allow_html=True)
    with photo:
        st.markdown('<div class="photo-card">', unsafe_allow_html=True)
        st.image("https://images.unsplash.com/photo-1576091160651-e028ca26a943?auto=format&fit=crop&w=1400&q=82", caption="Лабораторный анализ · National Cancer Institute / Unsplash")
        st.markdown('</div>', unsafe_allow_html=True)


def page_ai(pairs: pd.DataFrame, names: list[str]):
    st.title("Локальный ИИ-помощник")
    st.write("Попросите объяснить, что означает найденная строка DDInter. Текст генерируется на вашем компьютере локальной моделью Ollama.")
    left, right = st.columns([1.1, .9], gap="large")
    with left:
        st.markdown("#### Сначала выберите пару")
        drug_a = st.selectbox("Препарат A", names, key="ai_pair_a")
        drug_b = st.selectbox("Препарат B", names, key="ai_pair_b", index=min(1, len(names) - 1))
        question = st.text_area("Что вы хотите понять?", placeholder="Например: что показывает запись в базе и чего из неё нельзя заключить?", height=110)
        st.caption("Не вводите имена, даты рождения и другие сведения о пациенте.")
        st.markdown('<div class="safety">Ответ ИИ — только пояснение данных. Он не оценивает пациента и не даёт советов по лечению.</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="photo-card">', unsafe_allow_html=True)
        st.image("https://images.unsplash.com/photo-1748182448174-30c6b83443b9?auto=format&fit=crop&w=1200&q=82", caption="Лаборатория · Nathan Rimoux / Unsplash")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("#### Как устроен этот ИИ")
        st.markdown("**Ollama + локальная языковая модель** формулируют ответ по факту DDInter, который уже есть в приложении. Запрос идёт на `localhost`; облачный ключ и платный API не нужны. Модель может ошибиться: это не модель взаимодействий и не медицинский эксперт.")

    with st.expander("Бесплатная настройка на компьютере", expanded=False):
        st.markdown("1. Установите Ollama с [ollama.com/download](https://ollama.com/download) и запустите приложение.\n2. В терминале выполните `ollama pull qwen2.5:3b` — модель загрузится на компьютер.\n3. Вернитесь сюда: приложение обнаружит установленную модель автоматически.\n4. Для ответа нажмите кнопку ниже. Первый ответ может быть медленнее, пока модель загружается в память.")
        st.caption("Загрузка модели требует интернет-соединения и свободного места на диске; после неё генерация выполняется локально.")

    installed: list[str] = []
    try:
        installed = list_local_models()
    except ConnectionError as exc:
        st.info(f"{exc} После установки Ollama остальные возможности Pharma Sentinel работают и без неё.")
    if installed:
        preferred = next((name for name in installed if name.startswith("qwen2.5:3b")), installed[0])
        model = st.selectbox("Локальная модель", installed, index=installed.index(preferred), help="Выбирается только модель, установленная на этом компьютере.")
        if st.button("Объяснить данные", type="primary", disabled=(not question.strip())):
            if drug_a == drug_b:
                st.warning("Выберите два разных препарата.")
            else:
                match = pairs[(pairs.Drug_A == min(drug_a, drug_b)) & (pairs.Drug_B == max(drug_a, drug_b))]
                level = None if match.empty else str(match.iloc[0]["Level"])
                prompt = make_evidence_prompt(question.strip(), drug_a, drug_b, level)
                with st.spinner("Локальная модель готовит ответ…"):
                    try:
                        answer = ask_local_model(prompt, model)
                        st.markdown("### Ответ помощника")
                        st.markdown(answer)
                        if level is None:
                            st.warning("В выбранном наборе DDInter запись этой пары не найдена. Это не доказывает безопасность.")
                        else:
                            st.caption(f"Фактическая строка базы: {drug_a} — {drug_b} · {level} · источник DDInter.")
                    except RuntimeError as exc:
                        st.error(str(exc))
    else:
        st.warning("Установленная локальная модель пока не обнаружена. Следуйте шагам выше и перезагрузите страницу после `ollama pull qwen2.5:3b`.")
    st.markdown("#### Два разных вида модели")
    st.dataframe(pd.DataFrame([
        {"Компонент": "Графовая ML-модель", "Что делает": "Ранжирует возможные отсутствующие рёбра в структуре DDInter", "Чего не делает": "Не доказывает эффект и не оценивает клинический риск"},
        {"Компонент": "Локальный языковой ИИ", "Что делает": "Пересказывает и поясняет переданную строку DDInter", "Чего не делает": "Не ищет взаимодействия и не заменяет специалиста"},
    ]), hide_index=True, use_container_width=True)


def show_pair_examples(pairs: pd.DataFrame):
    """Показывает короткие примеры пар, которые действительно есть в CSV."""
    examples = [("chloroquine", "ceritinib"), ("chloroquine", "fingolimod"),
                ("hydroxychloroquine", "cabozantinib"), ("leflunomide", "metronidazole")]
    rows = []
    for drug_a, drug_b in examples:
        row = pairs[(pairs.Drug_A == min(drug_a, drug_b)) & (pairs.Drug_B == max(drug_a, drug_b))]
        if not row.empty:
            rows.append({"Препарат A": drug_a, "Препарат B": drug_b, "Уровень DDInter": row.iloc[0]["Level"]})
    if rows:
        with st.expander("Примеры записей из загруженного набора DDInter"):
            st.caption("Это примеры строк базы, а не персональная оценка риска и не рекомендация по лечению.")
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def severity(level: str) -> str:
    return {"Major": "🔴 Major", "Moderate": "🟠 Moderate", "Minor": "🟢 Minor", "Unknown": "⚪ Unknown"}.get(level, level)


def page_pair(pairs: pd.DataFrame, names: list[str]):
    st.title("Проверка пары")
    st.write("Учебный обзор того, есть ли для двух препаратов запись в DDInter. Сервис не проверяет назначения пациента и не определяет, можно ли принимать препараты вместе.")
    left, right = st.columns(2)
    drug_a = left.selectbox("Препарат A", names, key="pair_a")
    drug_b = right.selectbox("Препарат B", names, key="pair_b", index=min(1, len(names) - 1))
    if drug_a == drug_b:
        st.info("Выберите два разных препарата, чтобы проверить пару.")
        show_pair_examples(pairs)
        return
    row = pairs[((pairs.Drug_A == min(drug_a, drug_b)) & (pairs.Drug_B == max(drug_a, drug_b)))]
    if row.empty:
        st.warning("В базе не найдено. Это НЕ значит, что сочетание безопасно.")
        typed = st.text_input("Ищете препарат с опечаткой? Введите его название")
        if typed:
            suggestions = get_close_matches(typed.strip().lower(), names, n=5, cutoff=0.55)
            if suggestions:
                st.caption("Возможные совпадения: " + " · ".join(suggestions))
        show_pair_examples(pairs)
        return
    level = row.iloc[0]["Level"]
    color = {"Major": "#be3455", "Moderate": "#a86808", "Minor": "#16836e", "Unknown": "#63758a"}[level]
    st.markdown(f'<div class="metric-card"><div class="metric-label">Источник: DDInter</div><div class="metric-value" style="color:{color}">{severity(level)}</div><div style="color:#6f8095">Запись найдена для пары <b>{drug_a} — {drug_b}</b>.</div></div>', unsafe_allow_html=True)
    st.caption("Уровень приведён из источника DDInter и не является индивидуальной медицинской рекомендацией.")
    show_pair_examples(pairs)


def page_map(pairs: pd.DataFrame, drugs: pd.DataFrame, names: list[str]):
    st.title("Карта взаимодействий")
    st.write("Выберите препарат и исследуйте его связи в DDInter.")
    c1, c2, c3 = st.columns([1.3, 1.1, 1.2])
    center = c1.selectbox("Центральный препарат", names, key="map_center")
    levels = c2.multiselect("Уровни", ["Major", "Moderate", "Minor", "Unknown"], default=["Major", "Moderate", "Minor", "Unknown"])
    max_edges = c3.slider("Максимум связей", 1, 80, 25)
    near = pairs[((pairs.Drug_A == center) | (pairs.Drug_B == center)) & pairs.Level.isin(levels)].copy()
    near["Сосед"] = np.where(near.Drug_A == center, near.Drug_B, near.Drug_A)
    # Приоритет тяжёлых уровней, затем алфавитная стабильность результатов.
    order = {"Major": 0, "Moderate": 1, "Minor": 2, "Unknown": 3}
    near["_order"] = near.Level.map(order)
    near = near.sort_values(["_order", "Сосед"]).head(max_edges)
    if near.empty:
        st.info("Для выбранного препарата и уровней связей не найдено.")
    else:
        try:
            from pyvis.network import Network
            network = Network(height="510px", width="100%", bgcolor="#fbfdff", font_color="#22334b", directed=False, cdn_resources="in_line")
            network.set_options('''{"physics":{"solver":"forceAtlas2Based","forceAtlas2Based":{"gravitationalConstant":-55,"centralGravity":0.02,"springLength":145,"springConstant":0.08},"stabilization":{"iterations":100}},"nodes":{"font":{"size":16,"face":"DM Sans"},"borderWidth":1,"shadow":true},"edges":{"smooth":{"type":"continuous"},"width":2,"color":{"inherit":false}}}''')
            network.add_node(center, label=center, color={"background":"#2478c8","border":"#175a9b"}, font={"color":"#ffffff"}, size=30, title=f"Центр карты: {center}")
            for _, item in near.iterrows():
                neighbor, level = item["Сосед"], item["Level"]
                network.add_node(neighbor, label=neighbor, color={"background":"#ffffff","border":"#cbd8e4"}, size=17, title=neighbor)
                network.add_edge(center, neighbor, color=interaction_color(level), title=severity(level), width=3 if level == "Major" else 2)
            components.html(network.generate_html(), height=530, scrolling=False)
        except Exception as exc:
            st.error(f"Не удалось отобразить граф: {exc}")
        st.dataframe(near[["Сосед", "Level"]].rename(columns={"Level": "Уровень DDInter"}), use_container_width=True, hide_index=True)
    st.subheader("Топ-10 препаратов по числу Major-связей")
    st.dataframe(major_hubs(pairs), use_container_width=True, hide_index=True)


def page_hypotheses(pairs: pd.DataFrame, drugs: pd.DataFrame):
    st.title("Гипотезы модели")
    st.write("Пары без записи в DDInter, отобранные по Adamic-Adar и ранжированные лучшей моделью.")
    st.info("Непроверенное предположение модели. Не доказанный эффект.")
    st.markdown("Многие пары принадлежат одному фармакологическому классу. Это может означать терапевтическое дублирование, а не новый эффект.")
    evaluation = cached_evaluation(pairs, drugs)
    table = novel_pair_hypotheses(pairs, drugs, evaluation, candidate_count=20_000, limit=20)
    table["Оценка модели (не вероятность)"] = table["Оценка модели (не вероятность)"].map(lambda v: f"{v:.3f}")
    st.dataframe(table[["Препарат A", "Препарат B", "Оценка модели (не вероятность)"]], use_container_width=True, hide_index=True)


def page_model(pairs: pd.DataFrame, drugs: pd.DataFrame):
    st.title("Проверка модели")
    st.write("Тест содержит связи, скрытые от графа признаков и модели во время обучения.")
    result = cached_evaluation(pairs, drugs)
    metrics = result["metrics"]
    st.dataframe(metrics.style.format({"ROC-AUC": "{:.3f}", "Precision@5000": "{:.3f}"}), use_container_width=True, hide_index=True)
    st.caption(f"Обучение: {result['train_examples']:,} сбалансированных примеров · тест: {result['test_examples']:,} сбалансированных примеров · Precision@5000 оценивается среди тестовых примеров.".replace(",", " "))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    palette = ["#168f83", "#597fa8", "#d69538", "#be5971", "#9aa8b8"]
    for (name, (fpr, tpr)), color in zip(result["roc"].items(), palette):
        auc = metrics.loc[metrics["Метод"] == name, "ROC-AUC"].iloc[0]
        ax.plot(fpr, tpr, label=f"{name} · AUC {auc:.3f}", color=color, linewidth=2)
    ax.plot([0, 1], [0, 1], "--", color="#cbd5df", linewidth=1)
    ax.set(xlabel="Ложноположительная доля", ylabel="Истинноположительная доля", title="ROC-кривые на скрытом тесте")
    ax.grid(alpha=.16)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    st.subheader("Матрица ошибок случайного леса · порог 0.5")
    tn, fp, fn, tp = result["confusion"].ravel()
    conf_df = pd.DataFrame([[tn, fp], [fn, tp]], index=["В базе нет записи", "Связь DDInter скрыта"], columns=["Модель: нет связи", "Модель: связь"])
    st.dataframe(conf_df, use_container_width=True)
    cn_auc = metrics.loc[metrics["Метод"] == "Только общие соседи", "ROC-AUC"].iloc[0]
    forest_auc = metrics.loc[metrics["Метод"] == "Случайный лес", "ROC-AUC"].iloc[0]
    delta = forest_auc - cn_auc
    if delta > 0.03:
        st.success(f"На этом тесте случайный лес лучше правила общих соседей на {delta:.3f} ROC-AUC. Он различает отложенные записи лучше простого правила, но это не подтверждает клинические эффекты.")
    elif delta > 0:
        st.info(f"Выигрыш леса над общими соседями небольшой: {delta:.3f} ROC-AUC. Простое правило уже даёт близкий результат.")
    else:
        st.info(f"Случайный лес не превзошёл общих соседей на этом тесте (разница {delta:.3f} ROC-AUC). Сложная модель здесь не показала преимуществ.")
    st.caption("Важно: положительная тестовая метка означает запись в скрытой части DDInter, а отрицательная — случайную пару без записи. Отрицательные пары не подтверждены как клинически безопасные.")


def page_about(pairs: pd.DataFrame, drugs: pd.DataFrame):
    st.title("О проекте")
    st.markdown("""
**Учебная цель.** Показать, как изучать записи базы лекарственных взаимодействий, строить граф связей и честно оценивать алгоритмы поиска пропущенных рёбер. Предполагаемый сценарий обучения — исследователь или студент сравнивает данные источника и метрики модели; приложение не используется для выбора лечения конкретному пациенту.

**Источник данных.** DDInter: Xiong G. et al., *DDInter: an online drug–drug interaction database towards improving clinical decision-making and patient safety*, Nucleic Acids Research. CSV-файлы берутся в разделе Download на [ddinter.scbdd.com](https://ddinter.scbdd.com/).

**Метод.** Названия приводятся к нижнему регистру; петли удаляются; направление пары нормализуется сортировкой; дубликаты сворачиваются до наиболее тяжёлого уровня (Unknown=0, Minor=1, Moderate=2, Major=3). Графовые признаки считаются по оставшимся связям после отложения train и test.

**Модель.** Сравниваются логистическая регрессия со StandardScaler, случайный лес и три простых ориентира. Деление воспроизводимо (`random_state=42`). ROC-AUC и Precision@5000 измеряют восстановление записей базы, а не риск для конкретного пациента.

**Локальный языковой ИИ.** Дополнительный экран использует Ollama на компьютере пользователя и получает только выбранный факт DDInter и текст вопроса. Он помогает сформулировать пояснение, но может допустить ошибку; это отдельный компонент, не обученный предсказывать взаимодействия. Настройка необязательна, платные сервисы не используются.

### Ограничения

- Данные могут быть неполными; мало данных по БАДам.
- «Нет записи» не значит «нет взаимодействия».
- Ложные срабатывания на тесте могут быть реальными, но не описанными взаимодействиями.
- Модель предсказывает структуру сети, а не клинический эффект.
- 29 813 пар имеют уровень `Unknown` в исходной базе после очистки.
- Результат не является медицинской рекомендацией и не должен использоваться для самостоятельного изменения лечения.
""")
    st.image("https://images.unsplash.com/photo-1582560475093-ba66accbc424?auto=format&fit=crop&w=1800&q=82", caption="Лабораторный анализ · Centers for Disease Control and Prevention / Unsplash")
    c1, c2, c3 = st.columns(3)
    c1.metric("Препаратов", f"{len(drugs):,}".replace(",", " "))
    c2.metric("Уникальных пар", f"{len(pairs):,}".replace(",", " "))
    c3.metric("Unknown", f"{(pairs.Level == 'Unknown').sum():,}".replace(",", " "))
    st.caption("После очистки ожидаются 1 939 препаратов и 160 235 уникальных пар. Фактические числа показаны выше и вычисляются из предоставленных CSV.")


header()
safety_note()
page_name = st.sidebar.radio("Раздел", ["Проверка пары", "Карта", "Гипотезы", "Проверка модели", "ИИ-помощник", "О проекте"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption("DDInter · графовый ML · локальный ИИ")
st.sidebar.caption("Учебный проект · не для клинических решений")

try:
    with st.spinner("Подготавливаю данные DDInter…"):
        pairs, drugs = cached_data()
    names = drugs["drug"].tolist()
    if len(names) < 2:
        st.error("В CSV недостаточно уникальных препаратов для работы приложения.")
    elif page_name == "Проверка пары":
        page_pair(pairs, names)
    elif page_name == "Карта":
        page_map(pairs, drugs, names)
    elif page_name == "Гипотезы":
        page_hypotheses(pairs, drugs)
    elif page_name == "Проверка модели":
        page_model(pairs, drugs)
    elif page_name == "ИИ-помощник":
        page_ai(pairs, names)
    else:
        page_about(pairs, drugs)
except FileNotFoundError as exc:
    st.warning(str(exc))
    st.markdown("### Как подключить данные\n1. Откройте [ddinter.scbdd.com](https://ddinter.scbdd.com/) и перейдите в раздел **Download**.\n2. Скачайте CSV-файлы DDInter.\n3. Поместите все восемь `ddinter_downloads_code_*.csv` в папку `data/` рядом с `app.py`.\n4. Перезапустите приложение.")
except DataValidationError as exc:
    st.error(f"Ошибка в данных DDInter: {exc}")
except Exception as exc:
    st.error(f"Не удалось подготовить приложение: {exc}")
    st.caption("Проверьте формат CSV и установку библиотек из requirements.txt.")
