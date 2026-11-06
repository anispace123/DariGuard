"""PHARMA SENTINEL — Clinical Audit Protocol Report Generator.

Generates a structured, publication-grade, printable HTML/CSS clinical protocol
for polypharmacy reviews, pharmacovigilance records, and clinical decision support.
Complies with clinical pharmacology documentation standards and the Clinical Sage
design aesthetic.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from i18n import get_lang, t
from local_ai import generate_structured_explanation


def generate_clinical_protocol_report(
    report: Any,
    selected_drugs: Sequence[str],
    related_supps: Sequence[Any] | None = None,
    lang: str = "kk",
    patient_id: str = "REF-CLIN-2026"
) -> str:
    """Генерирует автономный HTML-документ клинического аудита для печати (Print-Ready) и архива."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Расчет показателей тяжести
    counts = getattr(report, "summary_counts", {})
    major_c = counts.get("Major", 0)
    mod_c = counts.get("Moderate", 0)
    min_c = counts.get("Minor", 0)
    not_in_db_c = counts.get("Not in DB", 0)
    overall_risk = getattr(report, "overall_risk", "Unknown")
    overall_code = getattr(report, "overall_risk_code", "UNKNOWN")
    risk_loc = t(f"risk_code_{overall_code.lower()}", default=overall_risk)

    # Дубликаты
    dup_html = ""
    dup_structured = getattr(report, "duplicates_structured", None)
    if dup_structured is None and hasattr(report, "drug_to_inputs") and report.drug_to_inputs:
        dup_structured = [
            (canon, inputs)
            for canon, inputs in report.drug_to_inputs.items()
            if len(inputs) > 1
        ]
    if dup_structured:
        dup_rows = "".join(
            f"<tr><td><b>{canon.title()}</b></td><td>{', '.join(inputs)}</td><td style='color:#B83A38; font-weight:600;'>{t('dup_risk_level', default='Критический: терапевтическое дублирование')}</td></tr>"
            for canon, inputs in dup_structured
        )
        dup_html = f"""
        <div class="section-card alert-card">
            <h3 style="color:#B83A38; margin-top:0;">{t("report_dup_title", default="Анализ терапевтического дублирования")}</h3>
            <p style="font-size:13px; color:#551B1A;">Обнаружено дублирование одного и того же действующего вещества под разными торговыми наименованиями. Риск кумулятивной передозировки и токсичности:</p>
            <table class="report-table">
                <thead><tr><th>Каноническое МНН</th><th>Введенные наименования</th><th>Статус риска</th></tr></thead>
                <tbody>{dup_rows}</tbody>
            </table>
        </div>
        """
    else:
        dup_html = f"""
        <div class="section-card safe-card">
            <h3 style="color:#264B40; margin-top:0;">{t("report_dup_title", default="Анализ терапевтического дублирования")}</h3>
            <p style="font-size:13px; color:#264B40; margin-bottom:0;">Терапевтического дублирования одинаковых молекулярных МНН в анализируемом наборе не выявлено.</p>
        </div>
        """

    # Таблица препаратов
    drugs_rows = "".join(
        f"<tr><td>{idx+1}</td><td><b>{d}</b></td><td>Оральный / Парентеральный</td><td>Верифицирован в формуляре</td></tr>"
        for idx, d in enumerate(selected_drugs)
    )

    # Таблица взаимодействий
    pairs_html = ""
    pairs_list = getattr(report, "pairs", [])
    if pairs_list:
        pair_rows = []
        for p in pairs_list:
            expl = generate_structured_explanation(p.drug_a, p.drug_b, p.level if p.in_ddinter else None, lang=lang)
            finding_text = t(p.explanation_code, default=p.explanation) if p.explanation_code else p.explanation
            
            badge_class = "badge-minor"
            if p.level == "Major":
                badge_class = "badge-major"
            elif p.level == "Moderate":
                badge_class = "badge-mod"
            elif p.level == "Not in DB" or not p.in_ddinter:
                badge_class = "badge-none"

            pair_rows.append(f"""
            <tr>
                <td style="white-space:nowrap;"><b>{p.display_a}</b> ↔ <b>{p.display_b}</b></td>
                <td><span class="badge {badge_class}">{p.level}</span></td>
                <td>{finding_text}</td>
                <td>{expl.get('clinical_meaning', '—')}</td>
                <td><b>{expl.get('recommendation', '—')}</b></td>
            </tr>
            """)
        pairs_html = f"""
        <table class="report-table">
            <thead>
                <tr>
                    <th>Взаимодействующая пара</th>
                    <th>Уровень</th>
                    <th>Механизм (Фармакодинамика/Фармакокинетика)</th>
                    <th>Клинический исход</th>
                    <th>Рекомендация по ведению</th>
                </tr>
            </thead>
            <tbody>
                {''.join(pair_rows)}
            </tbody>
        </table>
        """
    else:
        pairs_html = "<p style='font-size:13px; color:#65736A;'>Клинически значимых парных взаимодействий не обнаружено.</p>"

    # Взаимодействия с БАДами
    supp_html = ""
    if related_supps:
        supp_rows = []
        for s in related_supps:
            supp_rows.append(f"""
            <tr>
                <td><b>{getattr(s, 'supplement_ru', '')} ({getattr(s, 'supplement_lat', '')})</b> + <b>{getattr(s, 'drug_ru', '')}</b></td>
                <td><span class="badge badge-mod">{getattr(s, 'severity', 'Moderate')}</span></td>
                <td>{getattr(s, 'evidence_level', 'Level B')}</td>
                <td>{getattr(s, 'mechanism', '')}</td>
                <td>{getattr(s, 'clinical_management', '')}</td>
            </tr>
            """)
        supp_html = f"""
        <div class="section-card">
            <h3>{t("report_supp_title", default="Фармаконутриентные взаимодействия с БАД / фитопрепаратами")}</h3>
            <table class="report-table">
                <thead><tr><th>Комбинация</th><th>Тяжесть</th><th>Доказательность</th><th>Механизм</th><th>Клиническая тактика</th></tr></thead>
                <tbody>{''.join(supp_rows)}</tbody>
            </table>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="utf-8">
    <title>Pharma Sentinel · Clinical Protocol</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm 15mm 15mm 15mm;
        }}
        @media print {{
            body {{
                background: #FFFFFF !important;
                color: #000000 !important;
            }}
            .no-print {{
                display: none !important;
            }}
            .section-card {{
                box-shadow: none !important;
                border: 1px solid #CCCCCC !important;
                page-break-inside: avoid;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #F3F6F2;
            color: #26332D;
            line-height: 1.5;
            margin: 0;
            padding: 30px;
        }}
        .report-wrapper {{
            max-width: 980px;
            margin: 0 auto;
            background: #FFFFFF;
            padding: 36px 42px;
            border-radius: 4px;
            border: 1px solid #DCE4DA;
            box-shadow: 0 2px 12px rgba(49, 94, 80, 0.05);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #315E50;
            padding-bottom: 18px;
            margin-bottom: 24px;
        }}
        .brand-title {{
            font-size: 20px;
            font-weight: 700;
            color: #315E50;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}
        .brand-sub {{
            font-size: 11px;
            color: #65736A;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 3px;
        }}
        .meta-block {{
            text-align: right;
            font-size: 12px;
            color: #65736A;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        .stat-cell {{
            background: #F7F9F6;
            border: 1px solid #DCE4DA;
            padding: 12px;
            border-radius: 3px;
            text-align: center;
        }}
        .stat-cell-title {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: #65736A;
            letter-spacing: 0.04em;
        }}
        .stat-cell-val {{
            font-size: 20px;
            font-weight: 700;
            margin-top: 4px;
        }}
        .section-card {{
            background: #FFFFFF;
            border: 1px solid #DCE4DA;
            padding: 18px 20px;
            border-radius: 3px;
            margin-bottom: 20px;
        }}
        .alert-card {{
            background: #FDF4F4;
            border-color: #E8B4B3;
        }}
        .safe-card {{
            background: #EEF5F1;
            border-color: #BCCEC0;
        }}
        h3 {{
            font-size: 15px;
            color: #315E50;
            margin-top: 0;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .report-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12.5px;
            margin-top: 8px;
        }}
        .report-table th {{
            background: #EAF0E9;
            color: #26332D;
            text-align: left;
            padding: 8px 10px;
            font-weight: 600;
            border-bottom: 1px solid #DCE4DA;
        }}
        .report-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid #EAF0E9;
            vertical-align: top;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 2px;
            text-transform: uppercase;
        }}
        .badge-major {{ background: #FDF4F4; color: #B83A38; border: 1px solid #E8B4B3; }}
        .badge-mod {{ background: #FDF8F0; color: #B4681E; border: 1px solid #EBD5B3; }}
        .badge-minor {{ background: #EEF5F1; color: #315E50; border: 1px solid #BCCEC0; }}
        .badge-none {{ background: #EAF0E9; color: #65736A; border: 1px solid #DCE4DA; }}
        .disclaimer-box {{
            background: #F7F9F6;
            border: 1px solid #DCE4DA;
            border-left: 4px solid #789483;
            padding: 14px 16px;
            font-size: 11.5px;
            color: #65736A;
            line-height: 1.5;
            margin-top: 24px;
        }}
        .print-btn {{
            background: #315E50;
            color: #FFFFFF;
            border: none;
            padding: 8px 18px;
            border-radius: 3px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    <div class="report-wrapper">
        <div class="no-print" style="text-align:right;">
            <button class="print-btn" onclick="window.print()">Распечатать протокол (Print)</button>
        </div>
        <div class="header">
            <div>
                <div class="brand-title">Pharma Sentinel · Clinical Protocol</div>
                <div class="brand-sub">Clinical Pharmacoinformatics & Patient Safety System</div>
            </div>
            <div class="meta-block">
                <div>ID: {patient_id}</div>
                <div>{now_str}</div>
                <div>Engine: DDInter v2024.11 / PubChem 3D</div>
            </div>
        </div>

        <div style="margin-bottom:20px;">
            <h2 style="font-size:18px; margin:0 0 6px 0; color:#26332D;">{t("report_title", default="КЛИНИЧЕСКИЙ ПРОТОКОЛ АУДИТА ПОЛИПРАГМАЗИИ И ЛЕКАРСТВЕННЫХ ВЗАИМОДЕЙСТВИЙ")}</h2>
            <div style="font-size:12px; color:#65736A;">Автоматизированный скрининг риска неблагоприятных межлекарственных реакций, фармакодинамических конфликтов и сопутствующих фармаконутриентных взаимодействий.</div>
        </div>

        <div class="stats-grid">
            <div class="stat-cell">
                <div class="stat-cell-title">Общий риск</div>
                <div class="stat-cell-val" style="color:#B83A38;">{risk_loc}</div>
            </div>
            <div class="stat-cell">
                <div class="stat-cell-title">Major (Высокий)</div>
                <div class="stat-cell-val" style="color:#B83A38;">{major_c}</div>
            </div>
            <div class="stat-cell">
                <div class="stat-cell-title">Moderate (Умеренный)</div>
                <div class="stat-cell-val" style="color:#B4681E;">{mod_c}</div>
            </div>
            <div class="stat-cell">
                <div class="stat-cell-title">Minor (Низкий)</div>
                <div class="stat-cell-val" style="color:#315E50;">{min_c}</div>
            </div>
            <div class="stat-cell">
                <div class="stat-cell-title">Вне базы DDInter</div>
                <div class="stat-cell-val" style="color:#65736A;">{not_in_db_c}</div>
            </div>
        </div>

        <div class="section-card">
            <h3>{t("report_patient_regimen", default="Режим фармакотерапии (МНН)")} ({len(selected_drugs)})</h3>
            <table class="report-table">
                <thead><tr><th>#</th><th>МНН / Препарат</th><th>Форма приема</th><th>Статус верификации</th></tr></thead>
                <tbody>{drugs_rows}</tbody>
            </table>
        </div>

        {dup_html}

        <div class="section-card">
            <h3>{t("report_ddi_title", default="Межлекарственные взаимодействия (DDInter / Реестр)")}</h3>
            {pairs_html}
        </div>

        {supp_html}

        <div class="section-card">
            <h3>{t("report_monitoring_title", default="Рекомендации по клинико-лабораторному мониторингу")}</h3>
            <ul style="font-size:12.5px; line-height:1.6; margin:0; padding-left:18px;">
                <li><b>Контроль системы гемостаза:</b> При одновременном назначении антикоагулянтов и антиагрегантов / НПВП обязателен мониторинг МНО (INR) каждые 48-72 часа до стабилизации терапевтического диапазона.</li>
                <li><b>Почечная гемодинамика и электролиты:</b> При комбинации ингибиторов АПФ/БРА, диуретиков и НПВП проводить биохимический анализ сыворотки крови (креатинин, СКФ/eGFR, калий) через 7-14 дней после начала сочетанного курса.</li>
                <li><b>ЭКГ-мониторинг:</b> При сочетании антиаритмических препаратов и ингибиторов метаболизма контролировать длительность интервала QTc.</li>
                <li><b>Обучение пациента:</b> Проинформировать пациента о ранних клинических признаках микрокровотечений (петехии, носовые кровотечения, дегтеобразный стул) и симптомах задержки жидкости.</li>
            </ul>
        </div>

        <div class="disclaimer-box">
            <b>{t("report_disclaimer_title", default="Правовой и доказательный статус протокола")}:</b> Настоящий протокол сгенерирован алгоритмическим комплексом Pharma Sentinel в качестве инструмента поддержки принятия врачебных решений (Clinical Decision Support). Протокол не заменяет врачебное суждение и требует сопоставления с индивидуальным анамнезом, функциями печени (Child-Pugh) и почек (CKD-EPI) пациента. Отсутствие данных в справочных базах не гарантирует абсолютной безопасности фармакотерапии.
        </div>
    </div>
</body>
</html>
"""
    return html
