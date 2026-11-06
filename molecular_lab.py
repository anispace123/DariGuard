"""PHARMA SENTINEL — Molecular Intelligence Lab (Futuristic Scientific Intelligence).

Научный модуль молекулярного моделирования и биохимической фармакодинамики:
1. Единый надежный селектор препаратов (Drug A, Drug B, Swap ⇄, Reset ↺, выпадающий список эталонных пар).
2. Интерактивная строка токенов и верификации данных (DDInter статус + статус 3D-структуры PubChem/PDB).
3. Режим 1: Двухоконный и полноэкранный 3D/2D молекулярный вьюер (Three.js WebGL + 2D Topology & Radar).
4. Режим 2: Доказательная пошаговая анимация каскада «Препарат -> Мишень -> Эффект».
5. Режим 3: Визуализация конвергенции путей без прямого столкновения молекул.
6. Интегрированное доказательное клиническое досье и ИИ-копилот.
"""
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from components.molecular_viewer import (
    render_3d_molecule_viewer_html,
    render_mechanism_animation_html,
    render_convergence_visualization_html,
)
from data.verified_molecules import (
    get_verified_molecule,
)
from i18n import get_lang, t
from local_ai import (
    ask_local_model,
    generate_clinical_intelligence_brief,
    get_local_ai_status,
    make_evidence_prompt,
)
from normalization import DrugNormalizer
from state_manager import (
    REFERENCE_COMBINATIONS,
    find_catalog_label,
    get_active_pair,
    reset_active_pair,
    set_active_pair,
    swap_active_pair,
)

# Сохраняем экспорт для обратной совместимости
SHOWCASE_PAIRS = REFERENCE_COMBINATIONS


def _render_unverified_molecule_card(drug_name: str, lang: str) -> None:
    """Отображает честную карточку статуса для препарата без верифицированных 3D-координат."""
    st.markdown(
        f'<div class="ps-stat-box" style="border-left:3px solid #67B7D1; background:#111B20; padding:18px; border-radius:8px; height:390px; display:flex; flex-direction:column; justify-content:center;">'
        f'<div style="font-family:var(--font-mono); font-size:0.70rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#67B7D1;">'
        f'STRUCTURE PROVENANCE · HONEST FALLBACK</div>'
        f'<div style="font-size:1.15rem; font-weight:700; color:#EAF2F2; margin:6px 0 8px 0;">'
        f'{drug_name.title()}</div>'
        f'<div style="font-size:0.84rem; color:#91A5AA; line-height:1.55;">'
        f'{t("mol_fallback_desc", default="Верифицированные трехмерные атомные координаты и профили связывания PDB подготовлены для 7 эталонных фармакофоров (Варфарин, Ацетилсалициловая кислота, Амиодарон, Флуконазол, Эналаприл, Фуросемид, Ибупрофен). Для препарата «{drug}» 3D-координаты не подменяются демонстрационной моделью.", drug=drug_name.title())}'
        f'</div>'
        f'<div style="margin-top:12px; padding-top:10px; border-top:1px solid #263940; font-size:0.76rem; color:#36D6B0;">'
        f'{t("mol_fallback_safety_note", default="Отсутствие 3D-структуры или записи в DDInter не означает биологической безопасности комбинации.")}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def view_molecular_lab(
    pairs: pd.DataFrame,
    drugs: pd.DataFrame,
    normalizer: DrugNormalizer,
) -> None:
    """Отображает интерфейс Молекулярной лаборатории (Molecular Intelligence Lab)."""
    lang = get_lang()

    catalog = normalizer.get_search_catalog()
    catalog_labels = [label for label, _ in catalog]
    catalog_map = dict(catalog)

    active_a, active_b = get_active_pair()

    lbl_a = find_catalog_label(active_a, normalizer, catalog_labels, catalog_map) or catalog_labels[0]
    lbl_b = find_catalog_label(active_b, normalizer, catalog_labels, catalog_map) or (catalog_labels[1] if len(catalog_labels) > 1 else catalog_labels[0])

    # Гарантируем синхронизацию ключей селекторов с единым состоянием active_pair
    if st.session_state.get("mol_sel_a") != lbl_a:
        st.session_state["mol_sel_a"] = lbl_a
    if st.session_state.get("mol_sel_b") != lbl_b:
        st.session_state["mol_sel_b"] = lbl_b

    # Построение списка эталонных примеров для надежного выпадающего меню
    custom_option_label = (
        "— Выбрать эталонный клинический пример —"
        if lang == "ru"
        else ("— Эталондық клиникалық жұпты таңдау —" if lang == "kk" else "— Load Verified Reference Combination —")
    )
    ref_label_to_item = {
        ref.get(f"label_{lang}", ref["label_ru"]): ref for ref in REFERENCE_COMBINATIONS
    }
    ref_options = [custom_option_label] + list(ref_label_to_item.keys())

    cur_pair_set = {active_a, active_b}
    matched_ref_label = custom_option_label
    for r_lbl, r_item in ref_label_to_item.items():
        if {r_item["a"], r_item["b"]} == cur_pair_set:
            matched_ref_label = r_lbl
            break

    if st.session_state.get("mol_ref_dropdown") != matched_ref_label:
        st.session_state["mol_ref_dropdown"] = matched_ref_label

    # Обработчики единого рабочего процесса выбора препаратов
    def _on_select_drug_change() -> None:
        sel_lbl_a = st.session_state.get("mol_sel_a", lbl_a)
        sel_lbl_b = st.session_state.get("mol_sel_b", lbl_b)
        new_a = catalog_map.get(sel_lbl_a, active_a)
        new_b = catalog_map.get(sel_lbl_b, active_b)
        set_active_pair(
            new_a,
            new_b,
            normalizer=normalizer,
            catalog_labels=catalog_labels,
            catalog_map=catalog_map,
        )

    def _on_reference_dropdown_change() -> None:
        chosen_ref = st.session_state.get("mol_ref_dropdown")
        if chosen_ref and chosen_ref in ref_label_to_item:
            item = ref_label_to_item[chosen_ref]
            set_active_pair(
                item["a"],
                item["b"],
                showcase_id=item["id"],
                normalizer=normalizer,
                catalog_labels=catalog_labels,
                catalog_map=catalog_map,
            )

    def _on_swap_click() -> None:
        swap_active_pair(
            normalizer=normalizer,
            catalog_labels=catalog_labels,
            catalog_map=catalog_map,
        )

    def _on_reset_click() -> None:
        reset_active_pair(
            normalizer=normalizer,
            catalog_labels=catalog_labels,
            catalog_map=catalog_map,
        )

    # ── Компактный научный заголовок ──
    st.markdown(
        f'<div class="ps-animated-page-root ps-page-molecular">'
        f'<div style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:8px; margin-bottom:0.85rem;">'
        f'<div>'
        f'<div style="font-family:var(--font-mono); font-size:0.70rem; font-weight:600; text-transform:uppercase; letter-spacing:0.10em; color:#36D6B0;">'
        f'IN SILICO STRUCTURAL PHARMACOLOGY · PUBCHEM / PDB</div>'
        f'<h1 style="margin:2px 0 0 0; font-size:1.55rem;">{t("mol_title", default="Molecular Intelligence Lab")}</h1>'
        f'</div>'
        f'<div style="font-family:var(--font-mono); font-size:0.74rem; color:#91A5AA;">'
        f'ACTIVE PAIR: <b style="color:#36D6B0;">{active_a.upper()}</b> × <b style="color:#67B7D1;">{active_b.upper()}</b>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── ЕДИНЫЙ НАДЕЖНЫЙ КОМПОНЕНТ ВЫБОРА ПРЕПАРАТОВ (UNIFIED MEDICATION SELECTOR) ──
    c_sel_a, c_actions, c_sel_b, c_preset = st.columns([1.35, 0.45, 1.35, 1.45], gap="small")

    with c_sel_a:
        st.selectbox(
            "Drug A (МНН / Торговое название)" if lang != "en" else "Drug A (INN / Brand Alias)",
            options=catalog_labels,
            key="mol_sel_a",
            on_change=_on_select_drug_change,
        )

    with c_actions:
        st.markdown('<div style="height:26px;"></div>', unsafe_allow_html=True)
        b_col1, b_col2 = st.columns(2, gap="small")
        with b_col1:
            st.button(
                "⇄",
                key="mol_btn_swap_drugs",
                help="Поменять местами Препарат A и Препарат B / Swap Drugs",
                use_container_width=True,
                on_click=_on_swap_click,
            )
        with b_col2:
            st.button(
                "↺",
                key="mol_btn_reset_drugs",
                help="Сбросить к эталонной паре / Reset Pair",
                use_container_width=True,
                on_click=_on_reset_click,
            )

    with c_sel_b:
        st.selectbox(
            "Drug B (МНН / Торговое название)" if lang != "en" else "Drug B (INN / Brand Alias)",
            options=catalog_labels,
            key="mol_sel_b",
            on_change=_on_select_drug_change,
        )

    with c_preset:
        st.selectbox(
            "Эталонные комбинации (Быстрая загрузка)" if lang != "en" else "Verified Reference Combinations",
            options=ref_options,
            key="mol_ref_dropdown",
            on_change=_on_reference_dropdown_change,
        )

    # Перечитываем актуальную пару после возможных колбэков
    active_a, active_b = get_active_pair()

    # Поиск взаимодействия в DDInter
    match = pairs[
        (pairs.Drug_A == min(active_a, active_b))
        & (pairs.Drug_B == max(active_a, active_b))
    ]
    level = None if match.empty else str(match.iloc[0]["Level"])

    mol_a = get_verified_molecule(active_a)
    mol_b = get_verified_molecule(active_b)

    disp_a = mol_a.display_names.get(lang, active_a.title()) if mol_a else active_a.title()
    disp_b = mol_b.display_names.get(lang, active_b.title()) if mol_b else active_b.title()

    # ── СТРОКА ТОКЕНОВ И ВЕРИФИКАЦИИ ДАННЫХ (PROVENANCE & TOKEN BAR) ──
    status_a_badge = (
        f'<span style="color:#36D6B0; font-family:var(--font-mono); font-size:0.70rem;">● 3D Verified (CID {mol_a.pubchem_cid} · PDB {mol_a.target.pdb_id})</span>'
        if mol_a
        else '<span style="color:#F59E0B; font-family:var(--font-mono); font-size:0.70rem;">○ 3D Structure Pending (DDInter Active)</span>'
    )
    status_b_badge = (
        f'<span style="color:#67B7D1; font-family:var(--font-mono); font-size:0.70rem;">● 3D Verified (CID {mol_b.pubchem_cid} · PDB {mol_b.target.pdb_id})</span>'
        if mol_b
        else '<span style="color:#F59E0B; font-family:var(--font-mono); font-size:0.70rem;">○ 3D Structure Pending (DDInter Active)</span>'
    )

    if level == "Major":
        ddinter_badge = '<span style="background:rgba(244,63,94,0.16); color:#F43F5E; border:1px solid rgba(244,63,94,0.4); padding:3px 10px; border-radius:20px; font-family:var(--font-mono); font-size:0.72rem; font-weight:700;">DDInter: MAJOR INTERACTION</span>'
    elif level == "Moderate":
        ddinter_badge = '<span style="background:rgba(245,158,11,0.16); color:#F59E0B; border:1px solid rgba(245,158,11,0.4); padding:3px 10px; border-radius:20px; font-family:var(--font-mono); font-size:0.72rem; font-weight:700;">DDInter: MODERATE INTERACTION</span>'
    elif level == "Minor":
        ddinter_badge = '<span style="background:rgba(103,183,209,0.16); color:#67B7D1; border:1px solid rgba(103,183,209,0.4); padding:3px 10px; border-radius:20px; font-family:var(--font-mono); font-size:0.72rem; font-weight:700;">DDInter: MINOR INTERACTION</span>'
    else:
        ddinter_badge = '<span style="background:rgba(145,165,170,0.14); color:#91A5AA; border:1px solid #263940; padding:3px 10px; border-radius:20px; font-family:var(--font-mono); font-size:0.72rem; font-weight:600;">ABSENT FROM DDINTER · MECHANISTIC EVAL</span>'

    st.markdown(
        f'<div class="ps-token-bar" style="background:#111B20; border:1px solid #263940; border-radius:8px; padding:10px 14px; margin:0.35rem 0 0.85rem 0; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">'
        f'<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">'
        f'<div style="background:#17252B; border:1px solid #263940; border-left:3px solid #36D6B0; padding:5px 11px; border-radius:6px;">'
        f'<div style="font-size:0.86rem; font-weight:700; color:#EAF2F2;">A: {disp_a} <code style="font-size:0.72rem; color:#91A5AA;">[{active_a}]</code></div>'
        f'<div>{status_a_badge}</div>'
        f'</div>'
        f'<div style="font-family:var(--font-mono); font-size:0.9rem; color:#91A5AA;">⇄</div>'
        f'<div style="background:#17252B; border:1px solid #263940; border-left:3px solid #67B7D1; padding:5px 11px; border-radius:6px;">'
        f'<div style="font-size:0.86rem; font-weight:700; color:#EAF2F2;">B: {disp_b} <code style="font-size:0.72rem; color:#91A5AA;">[{active_b}]</code></div>'
        f'<div>{status_b_badge}</div>'
        f'</div>'
        f'</div>'
        f'<div>{ddinter_badge}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── QGEN BIOLOGICAL TARGET & PATHWAY AFFINITY HEATMAP STRIP ──
    if mol_a or mol_b:
        t_a_gene = mol_a.target.gene_symbol if mol_a else "N/A"
        t_b_gene = mol_b.target.gene_symbol if mol_b else "N/A"
        mw_a = f"{mol_a.molecular_weight:.1f} g/mol" if mol_a else "Pending"
        mw_b = f"{mol_b.molecular_weight:.1f} g/mol" if mol_b else "Pending"
        f_a = mol_a.formula if mol_a else "—"
        f_b = mol_b.formula if mol_b else "—"
        st.markdown(
            f'<div style="display:grid; grid-template-columns:repeat(6, 1fr); gap:8px; margin-bottom:0.85rem;">'
            f'<div style="background:#111B20; border:1px solid #263940; border-top:2px solid #36D6B0; padding:7px 10px; border-radius:6px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.65rem; color:#91A5AA;">FORMULA A</div>'
            f'<div style="font-family:var(--font-mono); font-size:0.84rem; font-weight:700; color:#36D6B0;">{f_a}</div>'
            f'</div>'
            f'<div style="background:#111B20; border:1px solid #263940; border-top:2px solid #36D6B0; padding:7px 10px; border-radius:6px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.65rem; color:#91A5AA;">MOLAR MASS A</div>'
            f'<div style="font-family:var(--font-mono); font-size:0.84rem; font-weight:700; color:#EAF2F2;">{mw_a}</div>'
            f'</div>'
            f'<div style="background:#111B20; border:1px solid #263940; border-top:2px solid #36D6B0; padding:7px 10px; border-radius:6px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.65rem; color:#91A5AA;">TARGET A</div>'
            f'<div style="font-family:var(--font-mono); font-size:0.84rem; font-weight:700; color:#36D6B0;">{t_a_gene}</div>'
            f'</div>'
            f'<div style="background:#111B20; border:1px solid #263940; border-top:2px solid #67B7D1; padding:7px 10px; border-radius:6px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.65rem; color:#91A5AA;">FORMULA B</div>'
            f'<div style="font-family:var(--font-mono); font-size:0.84rem; font-weight:700; color:#67B7D1;">{f_b}</div>'
            f'</div>'
            f'<div style="background:#111B20; border:1px solid #263940; border-top:2px solid #67B7D1; padding:7px 10px; border-radius:6px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.65rem; color:#91A5AA;">MOLAR MASS B</div>'
            f'<div style="font-family:var(--font-mono); font-size:0.84rem; font-weight:700; color:#EAF2F2;">{mw_b}</div>'
            f'</div>'
            f'<div style="background:#111B20; border:1px solid #263940; border-top:2px solid #67B7D1; padding:7px 10px; border-radius:6px;">'
            f'<div style="font-family:var(--font-mono); font-size:0.65rem; color:#91A5AA;">TARGET B</div>'
            f'<div style="font-family:var(--font-mono); font-size:0.84rem; font-weight:700; color:#67B7D1;">{t_b_gene}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Переключатель 3 научных режимов исследования ──
    mode_labels = [
        t("mol_mode_3d", default="1. 3D / 2D Структурный вьюер"),
        t("mol_mode_cascade", default="2. Фармакодинамический каскад"),
        t("mol_mode_convergence", default="3. Конвергенция исходов"),
    ]
    chosen_mode = st.radio(
        "Mode",
        options=mode_labels,
        horizontal=True,
        label_visibility="collapsed",
        key="mol_mode_radio",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # РЕЖИМ 1: ДВУХОКОННЫЙ 3D / 2D МОЛЕКУЛЯРНЫЙ ВЬЮЕР (QGEN DUAL VIEWPORT)
    # ─────────────────────────────────────────────────────────────────────────
    if chosen_mode == mode_labels[0]:
        col_view_a, col_view_b = st.columns(2, gap="medium")

        with col_view_a:
            if mol_a:
                html_a = render_3d_molecule_viewer_html(mol_a, lang=lang, height=400)
                components.html(html_a, height=410, scrolling=False)
                st.markdown(
                    f'<div class="ps-stat-box" style="margin-top:0.4rem; padding:10px 14px;">'
                    f'<div style="font-family:var(--font-mono); font-size:0.70rem; color:#36D6B0;">TARGET POCKET A · {mol_a.target.gene_symbol} (PDB {mol_a.target.pdb_id})</div>'
                    f'<div style="font-size:0.82rem; color:#EAF2F2; margin-top:2px;"><b>{mol_a.target.protein_name}</b> — {mol_a.target.binding_pocket}</div>'
                    f'<div style="font-size:0.76rem; color:#91A5AA; margin-top:2px;">Ключевые остатки: <code>{", ".join(mol_a.target.key_residues)}</code> · {mol_a.pharmacophore_type}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                _render_unverified_molecule_card(active_a, lang)

        with col_view_b:
            if mol_b:
                html_b = render_3d_molecule_viewer_html(mol_b, lang=lang, height=400)
                components.html(html_b, height=410, scrolling=False)
                st.markdown(
                    f'<div class="ps-stat-box" style="margin-top:0.4rem; padding:10px 14px;">'
                    f'<div style="font-family:var(--font-mono); font-size:0.70rem; color:#67B7D1;">TARGET POCKET B · {mol_b.target.gene_symbol} (PDB {mol_b.target.pdb_id})</div>'
                    f'<div style="font-size:0.82rem; color:#EAF2F2; margin-top:2px;"><b>{mol_b.target.protein_name}</b> — {mol_b.target.binding_pocket}</div>'
                    f'<div style="font-size:0.76rem; color:#91A5AA; margin-top:2px;">Ключевые остатки: <code>{", ".join(mol_b.target.key_residues)}</code> · {mol_b.pharmacophore_type}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                _render_unverified_molecule_card(active_b, lang)

    # ─────────────────────────────────────────────────────────────────────────
    # РЕЖИМ 2: Доказательный механизм действия (Анимация каскада)
    # ─────────────────────────────────────────────────────────────────────────
    elif chosen_mode == mode_labels[1]:
        if mol_a and mol_b:
            html_cascade = render_mechanism_animation_html(mol_a, mol_b, lang=lang, height=500)
            components.html(html_cascade, height=510, scrolling=False)
        else:
            missing = [d.title() for d, m in ((active_a, mol_a), (active_b, mol_b)) if not m]
            st.markdown(
                f'<div class="ps-stat-box" style="border-left:3px solid #67B7D1; padding:18px;">'
                f'<div style="font-family:var(--font-mono); font-size:0.72rem; color:#67B7D1;">PHARMACODYNAMIC CASCADE · HONEST FALLBACK</div>'
                f'<h3 style="margin-top:6px; color:#EAF2F2;">{active_a.title()} ↔ {active_b.title()}</h3>'
                f'<p style="font-size:0.85rem; color:#91A5AA; line-height:1.55;">'
                f'Пошаговая анимация рецепторного каскада требует верифицированных профилей связывания PDB для обоих компонентов. '
                f'Для ({", ".join(missing)}) кристаллографический профиль не подменяется шаблоном.'
                f'</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # РЕЖИМ 3: Визуализация конвергенции путей взаимодействия
    # ─────────────────────────────────────────────────────────────────────────
    else:
        if mol_a and mol_b:
            html_convergence = render_convergence_visualization_html(mol_a, mol_b, lang=lang, height=520)
            components.html(html_convergence, height=530, scrolling=False)
        else:
            missing = [d.title() for d, m in ((active_a, mol_a), (active_b, mol_b)) if not m]
            st.markdown(
                f'<div class="ps-stat-box" style="border-left:3px solid #67B7D1; padding:18px;">'
                f'<div style="font-family:var(--font-mono); font-size:0.72rem; color:#67B7D1;">PATHWAY CONVERGENCE · HONEST FALLBACK</div>'
                f'<h3 style="margin-top:6px; color:#EAF2F2;">{active_a.title()} ↔ {active_b.title()}</h3>'
                f'<p style="font-size:0.85rem; color:#91A5AA; line-height:1.55;">'
                f'Карта биохимической конвергенции без прямого столкновения молекул требует подтвержденных рецепторных мишеней для ({", ".join(missing)}). '
                f'Изучите доказательное клиническое досье ниже.'
                f'</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # СЕКЦИЯ: Компактное доказательное досье и быстрый переход к ИИ-копилоту
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:1.1rem;"></div>', unsafe_allow_html=True)
    brief = generate_clinical_intelligence_brief(active_a, active_b, level, lang=lang)

    col_brief, col_copilot = st.columns([1.35, 0.85], gap="medium")

    with col_brief:
        st.markdown(
            f'<div class="ps-card-finding" style="margin-bottom:0;">'
            f'<div class="ps-finding-head">'
            f'<div class="ps-finding-drugs">{disp_a} ↔ {disp_b}</div>'
            f'<div style="font-family:var(--font-mono); font-weight:700; color:#36D6B0; font-size:0.80rem;">{brief["finding"]}</div>'
            f'</div>'
            f'<div style="padding:8px 0; font-size:0.84rem; line-height:1.55; color:#EAF2F2;">'
            f'<div style="margin-bottom:6px;"><b style="color:#36D6B0;">MOA ({disp_a}):</b> {brief["moa_a"]}</div>'
            f'<div style="margin-bottom:6px;"><b style="color:#67B7D1;">MOA ({disp_b}):</b> {brief["moa_b"]}</div>'
            f'<div style="margin-bottom:6px;"><b>Системная конвергенция:</b> {brief["why_matters"]}</div>'
            f'<div style="background:#17252B; border:1px solid #263940; border-left:3px solid #36D6B0; padding:8px 12px; border-radius:6px; margin-top:8px;">'
            f'<b style="color:#36D6B0;">Протокол мониторинга:</b> {brief["monitoring"]}'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.expander("Развернуть вариабельность, исходы и первоисточники / Evidence Details", expanded=False):
            st.markdown(
                f"- **Клинические исходы:** {brief['clinical_consequence']}\n"
                f"- **Фармакогенетика и неопределенность:** {brief['uncertainty']}\n"
                f"- **Источники:** {'; '.join(brief['sources'])}"
            )

    with col_copilot:
        status = get_local_ai_status()
        engine_badge = (
            f'<span style="color:#36D6B0;">● PHARMA SENTINEL AI · ONLINE</span>'
            if status.available
            else '<span style="color:#67B7D1;">● DETERMINISTIC EVIDENCE ENGINE</span>'
        )
        st.markdown(
            f'<div class="ps-stat-box" style="margin-bottom:0.6rem; padding:10px 14px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            f'<span class="ps-stat-label">INLINE AI COPILOT</span>'
            f'<span style="font-family:var(--font-mono); font-size:0.68rem;">{engine_badge}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        user_q = st.text_input(
            t("ai_followup_label", default="Клинический вопрос по активной паре:"),
            placeholder="Например: Как скорректировать контроль МНО?",
            key="mol_user_question",
        )

        if st.button(
            t("ai_btn_generate", default="Сгенерировать ответ"),
            key="mol_btn_ask_inline",
            type="primary",
            use_container_width=True,
            disabled=not user_q.strip(),
        ):
            prompt = make_evidence_prompt(user_q.strip(), active_a, active_b, level, lang=lang, brief=brief)
            with st.spinner("Анализ доказательной базы…"):
                if status.available and status.models:
                    model = status.models[0]
                    try:
                        ans = ask_local_model(prompt, model)
                        st.markdown(f"**Ответ Pharma Sentinel AI:**\n\n{ans}")
                    except Exception:
                        st.markdown(f"**Детерминированная справка:**\n\n{brief['why_matters']}\n\n**Мониторинг:** {brief['monitoring']}")
                else:
                    st.markdown(
                        f'<div style="background:#17252B; border:1px solid #263940; border-left:3px solid #36D6B0; padding:10px 12px; border-radius:6px; font-size:0.82rem; line-height:1.5;">'
                        f'<b style="color:#36D6B0;">Доказательный ответ (Deterministic Fallback):</b><br>'
                        f'{brief["why_matters"]}<br><br>'
                        f'<b style="color:#67B7D1;">Мониторинг:</b> {brief["monitoring"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("</div>", unsafe_allow_html=True)
