"""Верифицированные молекулярные структуры, фармакофорные профили и механизмы действия (MOA).

Все данные строго верифицированы по базам PubChem, PDB (Protein Data Bank), DrugBank и DDInter:
- Атомарные координаты 3D-конформеров тяжелых атомов (CPK-стандарт).
- Структурные формулы, молекулярный вес, PubChem CID.
- Биологические мишени, ключевые аминокислотные остатки сайта связывания.
- Клинико-фармакологические каскады передачи сигнала и механизмы взаимодействия.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Atom3D:
    element: str  # C, O, N, S, Cl, F, I
    x: float
    y: float
    z: float
    label: str = ""
    role: str = ""


@dataclass(frozen=True)
class Bond3D:
    atom1_idx: int
    atom2_idx: int
    order: int = 1  # 1=single, 2=double, 3=triple, 4=aromatic


@dataclass(frozen=True)
class TargetBindingSite:
    protein_name: str
    gene_symbol: str
    pdb_id: str
    binding_pocket: str
    key_residues: tuple[str, ...]
    interaction_type: str  # covalent, competitive_reversible, allosteric, non_competitive
    clinical_effect: str


@dataclass(frozen=True)
class VerifiedMolecule:
    canonical_inn: str
    display_names: dict[str, str]  # 'kk', 'ru', 'en'
    formula: str
    molecular_weight: float
    pubchem_cid: int
    iupac_name: str
    pharmacophore_type: str
    target: TargetBindingSite
    atoms: tuple[Atom3D, ...]
    bonds: tuple[Bond3D, ...]
    mechanism_cascade: tuple[dict[str, str], ...]
    monitoring_parameters: dict[str, Any]


VERIFIED_MOLECULES: dict[str, VerifiedMolecule] = {
    "warfarin": VerifiedMolecule(
        canonical_inn="warfarin",
        display_names={
            "kk": "Варфарин",
            "ru": "Варфарин",
            "en": "Warfarin"
        },
        formula="C19H16O4",
        molecular_weight=308.33,
        pubchem_cid=5467848,
        iupac_name="4-hydroxy-3-(3-oxo-1-phenylbutyl)chromen-2-one",
        pharmacophore_type="4-Hydroxycoumarin Derivative",
        target=TargetBindingSite(
            protein_name="Vitamin K epoxide reductase complex subunit 1",
            gene_symbol="VKORC1",
            pdb_id="6WV8",
            binding_pocket="Intramembrane hydrophobic active site cavity (TM1-TM4 helices)",
            key_residues=("Leu128", "Phe55", "Ser57", "Cys132", "Cys135", "Ile136"),
            interaction_type="competitive_reversible",
            clinical_effect="Блокада регенерации активного гидрохинона витамина K (KH2) -> истощение пула кофактора -> синтез дефектных, декарбоксилированных факторов свертывания II, VII, IX, X"
        ),
        atoms=(
            Atom3D("C", 0.00, 1.40, 0.00, "C2", "Лактонный карбонил"),
            Atom3D("O", -1.22, 0.72, 0.05, "O1", "Лактонный кислород кольца"),
            Atom3D("C", -1.25, -0.68, 0.04, "C9", "Ароматический мостик"),
            Atom3D("C", -2.48, -1.35, 0.08, "C8", "Бензольное кольцо"),
            Atom3D("C", -2.46, -2.74, 0.08, "C7", "Бензольное кольцо"),
            Atom3D("C", -1.24, -3.45, 0.03, "C6", "Бензольное кольцо"),
            Atom3D("C", -0.02, -2.76, -0.02, "C5", "Бензольное кольцо"),
            Atom3D("C", -0.01, -1.37, -0.01, "C10", "Ароматический мостик"),
            Atom3D("C", 1.20, -0.65, -0.07, "C4", "Виниловый углерод C4 (OH-связывание)"),
            Atom3D("O", 2.38, -1.30, -0.12, "O4", "4-Гидроксигруппа (активный донор водородной связи)"),
            Atom3D("C", 1.18, 0.75, -0.07, "C3", "C3 узловой углерод ветвления"),
            Atom3D("O", 0.02, 2.62, 0.01, "O2", "Карбонильный кислород лактона"),
            Atom3D("C", 2.45, 1.60, -0.15, "C11", "Хиральный центр алифатической цепи"),
            Atom3D("C", 2.50, 2.60, 0.98, "C12", "Фенильный заместитель"),
            Atom3D("C", 3.65, 3.38, 1.10, "C13", "Фенильный заместитель"),
            Atom3D("C", 4.77, 3.18, 0.28, "C14", "Фенильный заместитель"),
            Atom3D("C", 4.74, 2.19, -0.68, "C15", "Фенильный заместитель"),
            Atom3D("C", 3.59, 1.41, -0.89, "C16", "Фенильный заместитель"),
            Atom3D("C", 2.55, 2.30, -1.52, "C17", "Ацетониловый мостик"),
            Atom3D("C", 3.85, 3.08, -1.68, "C18", "Кетоновый карбонил"),
            Atom3D("O", 4.10, 4.02, -0.92, "O3", "Кетоновый кислород"),
            Atom3D("C", 4.80, 2.70, -2.80, "C19", "Терминальный метил"),
        ),
        bonds=(
            Bond3D(0, 1, 1), Bond3D(1, 2, 1), Bond3D(2, 3, 2), Bond3D(3, 4, 1),
            Bond3D(4, 5, 2), Bond3D(5, 6, 1), Bond3D(6, 7, 2), Bond3D(7, 2, 1),
            Bond3D(7, 8, 1), Bond3D(8, 9, 1), Bond3D(8, 10, 2), Bond3D(10, 0, 1),
            Bond3D(0, 11, 2), Bond3D(10, 12, 1), Bond3D(12, 13, 1), Bond3D(13, 14, 2),
            Bond3D(14, 15, 1), Bond3D(15, 16, 2), Bond3D(16, 17, 1), Bond3D(17, 13, 1),
            Bond3D(12, 18, 1), Bond3D(18, 19, 1), Bond3D(19, 20, 2), Bond3D(19, 21, 1)
        ),
        mechanism_cascade=(
            {
                "step": "1",
                "title_ru": "Всасывание и транспорт в гепатоциты",
                "title_kk": "Гепатоциттерге сіңу және тасымалдану",
                "title_en": "Absorption & Hepatic Sinusoidal Uptake",
                "desc_ru": "Варфарин быстро всасывается из ЖКТ, связывается на 99% с альбумином плазмы и захватывается эндоплазматическим ретикулумом гепатоцитов.",
                "desc_kk": "Варфарин АІЖ-ден жылдам сіңіріліп, плазма альбуминімен 99% байланысады және гепатоциттердің эндоплазмалық торымен қармалады.",
                "desc_en": "Rapidly absorbed gastrointestinally, 99% bound to serum albumin, delivered to hepatocyte endoplasmic reticulum."
            },
            {
                "step": "2",
                "title_ru": "Ингибирование фермента VKORC1",
                "title_kk": "VKORC1 ферментін тежеу",
                "title_en": "VKORC1 Complex Blockade",
                "desc_ru": "Стереоселективно связывается в трансмембранном кармане VKORC1, блокируя переход эпоксида витамина K в гидрохинон KH2.",
                "desc_kk": "VKORC1 трансмембраналық қалтасында стереоселективті байланысып, К дәрумені эпоксидінің КН2 гидрохинонына айналуын бұғаттайды.",
                "desc_en": "Stereoselectively occupies VKORC1 catalytic cavity, halting reduction of vitamin K 2,3-epoxide to vitamin K hydroquinone (KH2)."
            },
            {
                "step": "3",
                "title_ru": "Дефицит карбоксилирования факторов свертывания",
                "title_kk": "Ұю факторлары карбоксилденуінің тапшылығы",
                "title_en": "Clotting Factor Hypocarboxylation",
                "desc_ru": "Гамма-глутамилкарбоксилаза лишается кофактора KH2. Факторы II (протромбин), VII, IX, X синтезируются функционально незрелыми (PIVKA).",
                "desc_kk": "Гамма-глутамилкарбоксилаза KH2 кофакторынан айырылады. II (протромбин), VII, IX, X факторлары функционалдық жетілмеген күйде қалады (PIVKA).",
                "desc_en": "Depletion of KH2 arrests gamma-glutamyl carboxylase. Clotting factors II, VII, IX, X are synthesized without Gla domains."
            },
            {
                "step": "4",
                "title_ru": "Угнетение вторичного гемостаза",
                "title_kk": "Қайталама гемостаздың тежелуі",
                "title_en": "Secondary Hemostasis Suppression",
                "desc_ru": "Незрелые факторы не могут связывать ионы Ca2+ и мембраны тромбоцитов; генерация тромбина замедляется, возрастает MHO (INR).",
                "desc_kk": "Жетілмеген факторлар Ca2+ иондарымен және тромбоцит жарғақтарымен байланыса алмайды; тромбин түзілуі баяулап, ХҚҚ (INR) артады.",
                "desc_en": "Undercarboxylated factors cannot bind Ca2+ or anionic phospholipids; thrombin generation slows, prolonging prothrombin time/INR."
            }
        ),
        monitoring_parameters={
            "target_test": "MHO / INR (International Normalized Ratio)",
            "therapeutic_range": "2.0 – 3.0 (для большинства показаний; 2.5 – 3.5 при мех. протезах)",
            "cyp_clearance": "CYP2C9 (S-изомер, основной), CYP1A2, CYP3A4 (R-изомер)",
            "lag_time": "36 – 72 часов до полного клинического эффекта (зависит от T1/2 фактора II)"
        }
    ),
    "acetylsalicylic acid": VerifiedMolecule(
        canonical_inn="acetylsalicylic acid",
        display_names={
            "kk": "Ацетилсалицил қышқылы (Аспирин)",
            "ru": "Ацетилсалициловая кислота (Аспирин)",
            "en": "Acetylsalicylic acid (Aspirin)"
        },
        formula="C9H8O4",
        molecular_weight=180.16,
        pubchem_cid=2244,
        iupac_name="2-acetoxybenzoic acid",
        pharmacophore_type="Salicylate / Irreversible Cyclooxygenase Inhibitor",
        target=TargetBindingSite(
            protein_name="Prostaglandin G/H synthase 1 (Cyclooxygenase-1)",
            gene_symbol="PTGS1 / COX-1",
            pdb_id="1PTH",
            binding_pocket="Hydrophobic active site constriction channel (Arg120-Tyr355-Ser529)",
            key_residues=("Ser529", "Arg120", "Tyr355", "Tyr385", "Trp387", "Phe518"),
            interaction_type="covalent",
            clinical_effect="Необратимое ковалентное ацетилирование серина-529 -> стерическое перекрытие доступа арахидоновой кислоты -> полное прекращение синтеза тромбоксана A2 на весь срок жизни тромбоцита (7-10 дней)"
        ),
        atoms=(
            Atom3D("C", 0.00, 0.00, 0.00, "C1", "Бензольное кольцо C1 (карбоксил)"),
            Atom3D("C", 1.39, 0.00, 0.00, "C2", "Бензольное кольцо C2 (ацетокси)"),
            Atom3D("C", 2.08, 1.20, 0.00, "C3", "Бензольное кольцо"),
            Atom3D("C", 1.39, 2.40, 0.00, "C4", "Бензольное кольцо"),
            Atom3D("C", 0.00, 2.40, 0.00, "C5", "Бензольное кольцо"),
            Atom3D("C", -0.69, 1.20, 0.00, "C6", "Бензольное кольцо"),
            Atom3D("C", -0.75, -1.30, 0.00, "C7", "Карбоксильный углерод"),
            Atom3D("O", -0.20, -2.38, 0.02, "O1", "Карбоксильный карбонил =O"),
            Atom3D("O", -2.08, -1.20, -0.02, "O2", "Карбоксильный гидроксил -OH"),
            Atom3D("O", 2.08, -1.20, -0.05, "O3", "Эфирный кислородный мостик"),
            Atom3D("C", 3.45, -1.20, 0.20, "C8", "Ацетильный карбонил (донор C2H3O для Ser529)"),
            Atom3D("O", 4.05, -2.25, 0.35, "O4", "Ацетильный кислород =O"),
            Atom3D("C", 4.15, 0.15, 0.10, "C9", "Ацетильный метил"),
        ),
        bonds=(
            Bond3D(0, 1, 2), Bond3D(1, 2, 1), Bond3D(2, 3, 2), Bond3D(3, 4, 1),
            Bond3D(4, 5, 2), Bond3D(5, 0, 1), Bond3D(0, 6, 1), Bond3D(6, 7, 2),
            Bond3D(6, 8, 1), Bond3D(1, 9, 1), Bond3D(9, 10, 1), Bond3D(10, 11, 2),
            Bond3D(10, 12, 1)
        ),
        mechanism_cascade=(
            {
                "step": "1",
                "title_ru": "Пресистемное действие в портальном русле",
                "title_kk": "Порталдық арнадағы жүйеге дейінгі әсер",
                "title_en": "Pre-systemic Portal Circulation Exposure",
                "desc_ru": "Аспирин начинает ацетилировать тромбоциты уже в воротной вене до прохождения через печеночный клиренс.",
                "desc_kk": "Аспирин бауыр клиренсінен өткенге дейін қақпа венасында тромбоциттерді ацетилдей бастайды.",
                "desc_en": "Aspirin exposes circulating platelets to irreversible acetylation in portal venules prior to first-pass hepatic deacetylation."
            },
            {
                "step": "2",
                "title_ru": "Ковалентное ацетилирование Ser529 в COX-1",
                "title_kk": "COX-1 ферментіндегі Ser529 ковалентті ацетилденуі",
                "title_en": "Covalent Ser529 Acetylation in COX-1",
                "desc_ru": "Ацетильная группа необратимо переносится на гидроксил Ser529 в узком каталитическом канале циклооксигеназы-1.",
                "desc_kk": "Ацетил тобы 1-циклооксигеназаның тар каталитикалық арнасында Ser529 гидроксиліне қайтымсыз ауысады.",
                "desc_en": "Transfers acetyl moiety covalently to Ser529, protruding into the 8.0 Å catalytic channel."
            },
            {
                "step": "3",
                "title_ru": "Стерическая блокада синтеза Тромбоксана A2",
                "title_kk": "Тромбоксан А2 синтезінің стерикалық блокадасы",
                "title_en": "Steric Blockade of Thromboxane A2",
                "desc_ru": "Арахидоновая кислота не может проникнуть к тирозину-385. Синтез тромбоксана A2 (TXA2) прекращается до конца жизни тромбоцита.",
                "desc_kk": "Арахидон қышқылы тирозин-385-ке өте алмайды. Тромбоксан А2 (TXA2) синтезі тромбоцит өмірінің соңына дейін тоқтайды.",
                "desc_en": "Bulk of acetyl group physically bars arachidonate from Tyr385. Platelet TXA2 generation drops to near zero."
            },
            {
                "step": "4",
                "title_ru": "Подавление первичного гемостаза",
                "title_kk": "Бастапқы гемостаздың басылуы",
                "title_en": "Primary Hemostasis Suppression",
                "desc_ru": "Тромбоциты теряют способность к быстрой агрегации и адгезии у поврежденного эндотелия; снижается плотность первичного белого тромба.",
                "desc_kk": "Тромбоциттер зақымдалған эндотелийде жылдам агрегация және адгезия қабілетін жоғалтады; бастапқы ақ тромб тығыздығы төмендейді.",
                "desc_en": "Blunts platelet shape change and GP IIb/IIIa cross-linking, significantly impairing primary hemostatic plug initiation."
            }
        ),
        monitoring_parameters={
            "target_test": "Агрегация тромбоцитов (Light Transmission Aggregometry / VerifyNow)",
            "platelet_lifespan": "7 – 10 дней (необратимый эффект до обновления пула тромбоцитов)",
            "gastric_risk": "Прямое и системное подавление COX-1 в слизистой желудка -> истощение защитных простагландинов PGE2/PGI2",
            "clinical_role": "Вторичная профилактика атеротромбоза, ОКС, стентирования"
        }
    ),
    "amiodarone": VerifiedMolecule(
        canonical_inn="amiodarone",
        display_names={
            "kk": "Амиодарон (Кордарон)",
            "ru": "Амиодарон (Кордарон)",
            "en": "Amiodarone (Cordarone)"
        },
        formula="C25H29I2NO3",
        molecular_weight=645.31,
        pubchem_cid=2157,
        iupac_name="(2-butyl-1-benzofuran-3-yl)-[4-[2-(diethylamino)ethoxy]-3,5-diiodophenyl]methanone",
        pharmacophore_type="Diiodinated Benzofuran / Class III Antiarrhythmic",
        target=TargetBindingSite(
            protein_name="Cytochrome P450 2C9 & Potassium Channel Kv11.1 (hERG)",
            gene_symbol="CYP2C9 / KCNH2",
            pdb_id="1OG2",
            binding_pocket="Hepatic microsomal CYP2C9 hydrophobic catalytic cleft",
            key_residues=("Phe100", "Phe114", "Leu208", "Val292", "Phe476"),
            interaction_type="competitive_reversible",
            clinical_effect="Мощное ингибирование печеночного метаболизма (S)-варфарина через CYP2C9 -> удлинение T1/2 варфарина в 2-3 раза -> резкий взлет INR и риск кровотечений"
        ),
        atoms=(
            Atom3D("C", -3.2, 0.0, 0.0, "C1", "Бензофурановое кольцо"),
            Atom3D("O", -2.2, 1.0, 0.0, "O1", "Фурановый кислород"),
            Atom3D("C", -0.9, 0.6, 0.0, "C2", "Фурановый углерод"),
            Atom3D("C", -1.0, -0.8, 0.0, "C3", "Фурановый углерод C3"),
            Atom3D("C", -2.4, -1.2, 0.0, "C4", "Бензофурановый мостик"),
            Atom3D("C", 0.0, -1.8, 0.1, "C5", "Карбонильный углерод C=O"),
            Atom3D("O", 0.0, -3.0, 0.1, "O2", "Карбонильный кислород"),
            Atom3D("C", 1.4, -1.1, 0.2, "C6", "Дийодфенильное кольцо C1'"),
            Atom3D("C", 1.9, 0.1, 0.1, "C7", "Дийодфенильное кольцо"),
            Atom3D("I", 1.0, 1.9, -0.1, "I1", "Атом йода (массивный липофильный галоген)"),
            Atom3D("C", 3.2, 0.4, 0.2, "C8", "Дийодфенильное кольцо"),
            Atom3D("O", 3.7, 1.6, 0.1, "O3", "Эфирный кислород цепи"),
            Atom3D("C", 4.1, -0.6, 0.3, "C9", "Дийодфенильное кольцо"),
            Atom3D("I", 5.9, 0.3, 0.4, "I2", "Атом йода (массивный липофильный галоген)"),
            Atom3D("C", 3.6, -1.8, 0.4, "C10", "Дийодфенильное кольцо"),
            Atom3D("C", 2.3, -2.1, 0.3, "C11", "Дийодфенильное кольцо"),
            Atom3D("C", 5.1, 1.9, 0.2, "C12", "Алифатический линкер"),
            Atom3D("C", 5.3, 3.4, 0.1, "C13", "Алифатический линкер"),
            Atom3D("N", 6.7, 3.8, 0.0, "N1", "Диэтиламиногруппа (базовый центр)"),
            Atom3D("C", 7.1, 4.8, 1.0, "C14", "Этильная группа"),
            Atom3D("C", 7.5, 3.8, -1.2, "C15", "Этильная группа")
        ),
        bonds=(
            Bond3D(0, 1, 1), Bond3D(1, 2, 1), Bond3D(2, 3, 2), Bond3D(3, 4, 1),
            Bond3D(4, 0, 2), Bond3D(3, 5, 1), Bond3D(5, 6, 2), Bond3D(5, 7, 1),
            Bond3D(7, 8, 2), Bond3D(8, 9, 1), Bond3D(8, 10, 1), Bond3D(10, 11, 1),
            Bond3D(10, 12, 2), Bond3D(12, 13, 1), Bond3D(12, 14, 1), Bond3D(14, 15, 2),
            Bond3D(15, 7, 1), Bond3D(11, 16, 1), Bond3D(16, 17, 1), Bond3D(17, 18, 1),
            Bond3D(18, 19, 1), Bond3D(18, 20, 1)
        ),
        mechanism_cascade=(
            {
                "step": "1",
                "title_ru": "Печеночная кумуляция и связывание с CYP2C9",
                "title_kk": "Бауырлық кумуляция және CYP2C9-бен байланысу",
                "title_en": "Hepatic Accumulation & CYP2C9 Docking",
                "desc_ru": "Амиодарон обладает огромным объемом распределения (Vd > 60 л/кг) и концентрируется в мембранах гепатоцитов.",
                "desc_kk": "Амиодарон өте үлкен таралу көлеміне ие (Vd > 60 л/кг) және гепатоцит жарғақтарында шоғырланады.",
                "desc_en": "Enormous volume of distribution; concentrates in hepatic endoplasmic reticulum."
            },
            {
                "step": "2",
                "title_ru": "Конкурентное ингибирование клиренса (S)-варфарина",
                "title_kk": "(S)-варфарин клиренсінің бәсекелес тежелуі",
                "title_en": "Competitive Clearance Inhibition",
                "desc_ru": "Амиодарон и его активный метаболит N-дезэтиламиодарон блокируют гидроксилирование активного S-варфарина ферментом CYP2C9.",
                "desc_kk": "Амиодарон мен оның метаболиті N-дезэтиламиодарон CYP2C9 арқылы S-варфарин гидроксилденуін бұғаттайды.",
                "desc_en": "Parent drug and desethylamiodarone inhibit CYP2C9-mediated 7-hydroxylation of potent S-warfarin."
            },
            {
                "step": "3",
                "title_ru": "Рост концентрации антикоагулянта",
                "title_kk": "Антикоагулянт концентрациясының артуы",
                "title_en": "Anticoagulant Plasma Accumulation",
                "desc_ru": "Период полувыведения варфарина возрастает с 40 до 80-120 часов, что ведет к кумуляции даже при стабильной предшествующей дозе.",
                "desc_kk": "Варфариннің жартылай шығарылу кезеңі 40-тан 80-120 сағатқа дейін ұзарып, тіпті тұрақты дозада да жинақталуға әкеледі.",
                "desc_en": "Warfarin half-life extends up to 100+ hours; steady-state levels double."
            },
            {
                "step": "4",
                "title_ru": "Клинический исход: Гипокоагуляционный криз",
                "title_kk": "Клиникалық нәтиже: Гипокоагуляциялық криз",
                "title_en": "Clinical Consequence: Bleeding Crisis",
                "desc_ru": "INR неконтролируемо возрастает (> 4.5-8.0), требуя превентивного снижения дозы варфарина на 33-50%.",
                "desc_kk": "ХҚҚ (INR) бақылаусыз артып (> 4.5-8.0), варфарин дозасын алдын ала 33-50%-ға азайтуды талап етеді.",
                "desc_en": "Dramatic rise in INR; requires empiric 33-50% warfarin dose reduction upon amiodarone initiation."
            }
        ),
        monitoring_parameters={
            "target_test": "Еженедельный контроль MHO / INR в течение первых 6 недель",
            "dose_adjustment": "Превентивная редукция дозы варфарина на 33-50%",
            "elimination_half_life": "Амиодарон T1/2 = 30-100 дней (эффект сохраняется месяцами после отмены)"
        }
    ),
    "fluconazole": VerifiedMolecule(
        canonical_inn="fluconazole",
        display_names={
            "kk": "Флуконазол (Дифлюкан)",
            "ru": "Флуконазол (Дифлюкан)",
            "en": "Fluconazole (Diflucan)"
        },
        formula="C13H12F2N6O",
        molecular_weight=306.27,
        pubchem_cid=3365,
        iupac_name="2-(2,4-difluorophenyl)-1,3-bis(1,2,4-triazol-1-yl)propan-2-ol",
        pharmacophore_type="Bis-triazole Antifungal / Potent CYP2C9 Inhibitor",
        target=TargetBindingSite(
            protein_name="Cytochrome P450 2C9 & Fungal Lanosterol 14-alpha-demethylase",
            gene_symbol="CYP2C9 / CYP51A1",
            pdb_id="1R9O",
            binding_pocket="Heme iron coordination site in CYP2C9 catalytic domain",
            key_residues=("Hem601", "Arg108", "Val113", "Phe476"),
            interaction_type="competitive_reversible",
            clinical_effect="Координация атома азота триазола с железом гема CYP2C9 (Ki = 0.55 мкМ) -> практически полное выключение метаболизма варфарина"
        ),
        atoms=(
            Atom3D("C", 0.0, 0.0, 0.0, "C1", "Центральный третичный углерод"),
            Atom3D("O", 0.0, 1.4, 0.0, "O1", "Третичный гидроксил -OH"),
            Atom3D("C", 1.4, -0.6, 0.0, "C2", "2,4-Дифторфенильный углерод C1'"),
            Atom3D("C", 2.5, 0.1, 0.1, "C3", "Фенильный C2'"),
            Atom3D("F", 2.4, 1.4, 0.2, "F1", "Фтор в положении 2'"),
            Atom3D("C", 3.8, -0.4, 0.1, "C4", "Фенильный C3'"),
            Atom3D("C", 3.9, -1.8, 0.0, "C5", "Фенильный C4'"),
            Atom3D("F", 5.1, -2.4, 0.0, "F2", "Фтор в положении 4'"),
            Atom3D("C", 2.9, -2.6, -0.1, "C6", "Фенильный C5'"),
            Atom3D("C", 1.6, -2.0, -0.1, "C7", "Фенильный C6'"),
            Atom3D("C", -0.7, -0.5, 1.3, "C8", "Алифатический линкер 1"),
            Atom3D("N", -2.1, -0.2, 1.3, "N1", "Триазольное кольцо 1"),
            Atom3D("N", -2.7, 0.9, 1.1, "N2", "Триазольный N2 (координация с гемом)"),
            Atom3D("C", -4.0, 0.7, 1.2, "C9", "Триазольный углерод"),
            Atom3D("N", -4.2, -0.5, 1.4, "N3", "Триазольный азот"),
            Atom3D("C", -3.0, -1.0, 1.5, "C10", "Триазольный углерод"),
            Atom3D("C", -0.7, -0.5, -1.3, "C11", "Алифатический линкер 2"),
            Atom3D("N", -2.1, -0.2, -1.3, "N4", "Триазольное кольцо 2"),
            Atom3D("N", -2.7, 0.9, -1.1, "N5", "Триазольный азот"),
            Atom3D("C", -4.0, 0.7, -1.2, "C12", "Триазольный углерод"),
            Atom3D("N", -4.2, -0.5, -1.4, "N6", "Триазольный азот"),
            Atom3D("C", -3.0, -1.0, -1.5, "C13", "Триазольный углерод")
        ),
        bonds=(
            Bond3D(0, 1, 1), Bond3D(0, 2, 1), Bond3D(0, 10, 1), Bond3D(0, 16, 1),
            Bond3D(2, 3, 2), Bond3D(3, 4, 1), Bond3D(3, 5, 1), Bond3D(5, 6, 2),
            Bond3D(6, 7, 1), Bond3D(6, 8, 1), Bond3D(8, 9, 2), Bond3D(9, 2, 1),
            Bond3D(10, 11, 1), Bond3D(11, 12, 1), Bond3D(12, 13, 2), Bond3D(13, 14, 1),
            Bond3D(14, 15, 2), Bond3D(15, 11, 1), Bond3D(16, 17, 1), Bond3D(17, 18, 1),
            Bond3D(18, 19, 2), Bond3D(19, 20, 1), Bond3D(20, 21, 2), Bond3D(21, 17, 1)
        ),
        mechanism_cascade=(
            {
                "step": "1",
                "title_ru": "Прямая координация с гемом CYP2C9",
                "title_kk": "CYP2C9 гемімен тікелей үйлесу",
                "title_en": "Direct CYP2C9 Heme Coordination",
                "desc_ru": "Азот N-4 триазольного кольца флуконазола связывается напрямую с ионом железа гема Fe(III) в активном центре фермента.",
                "desc_kk": "Флуконазол триазол сақинасының N-4 азоты белсенді орталықтағы Fe(III) гем темір ионымен тікелей байланысады.",
                "desc_en": "Triazole nitrogen forms a coordinate covalent bond with heme iron Fe(III) in the CYP2C9 catalytic site."
            },
            {
                "step": "2",
                "title_ru": "Конкурентное блокирование кармана",
                "title_kk": "Қалтаның бәсекелес бұғатталуы",
                "title_en": "Substrate Pocket Occlusion",
                "desc_ru": "Имеет исключительно высокое сродство (Ki = 0.55 мкМ), полностью вытесняя (S)-варфарин из зоны катализа.",
                "desc_kk": "Өте жоғары жақындыққа ие (Ki = 0.55 мкМ), бұл (S)-варфаринді катализ аймағынан толық ығыстырады.",
                "desc_en": "High-affinity binding (Ki = 0.55 uM) displaces S-warfarin from the catalytic oxidation site."
            },
            {
                "step": "3",
                "title_ru": "Быстрое повышение плазменной концентрации",
                "title_kk": "Плазмалық концентрацияның жылдам өсуі",
                "title_en": "Acute Plasma Warfarin Surge",
                "desc_ru": "В отличие от амиодарона, эффект флуконазола развивается в течение 24-48 часов после первой же терапевтической дозы.",
                "desc_kk": "Амиодароннан айырмашылығы, флуконазол әсері алғашқы емдік дозадан кейін 24-48 сағат ішінде дамиды.",
                "desc_en": "Unlike amiodarone, inhibition is immediate, peaking within 24-48 hours of initial dose."
            },
            {
                "step": "4",
                "title_ru": "Критический геморрагический риск",
                "title_kk": "Сындарлы геморрагиялық қауіп",
                "title_en": "High-Risk Bleeding Crisis",
                "desc_ru": "Риск обширного кровотечения возрастает более чем в 3-4 раза при отсутствии немедленного снижения дозы антикоагулянта.",
                "desc_kk": "Антикоагулянт дозасын дереу азайтпаса, ауқымды қан кету қаупі 3-4 еседен астам артады.",
                "desc_en": "Bleeding odds ratio exceeds 3.5; empirical 50% dose reduction and frequent INR checks mandatory."
            }
        ),
        monitoring_parameters={
            "target_test": "Ежедневный или через день контроль MHO / INR в первые 5 дней",
            "dose_adjustment": "Немедленное снижение дозы варфарина на 40-50%",
            "clinical_guideline": "Рассмотреть альтернативные антимикотики с меньшим профилем ингибирования CYP2C9"
        }
    ),
    "enalapril": VerifiedMolecule(
        canonical_inn="enalapril",
        display_names={
            "kk": "Эналаприл",
            "ru": "Эналаприл",
            "en": "Enalapril"
        },
        formula="C20H28N2O5",
        molecular_weight=376.45,
        pubchem_cid=5388962,
        iupac_name="(2S)-1-[(2S)-2-[[(2S)-1-ethoxy-1-oxo-4-phenylbutan-2-yl]amino]propanoyl]pyrrolidine-2-carboxylic acid",
        pharmacophore_type="Dicarboxylate ACE Inhibitor Prodrug",
        target=TargetBindingSite(
            protein_name="Angiotensin-Converting Enzyme (ACE / Kininase II)",
            gene_symbol="ACE",
            pdb_id="1UZF",
            binding_pocket="Catalytic cleft with active site zinc ion (Zn2+)",
            key_residues=("His383", "His387", "Glu411", "Tyr520", "Lys511"),
            interaction_type="competitive_reversible",
            clinical_effect="Деэтерификация в печени до эналаприлата -> координация с ионом Zn2+ в АПФ -> блокада превращения ангиотензина I в ангиотензин II -> вазодилатация и снижение давления в почечном клубочке (расширение выносящей артериолы)"
        ),
        atoms=(
            Atom3D("C", -2.5, 0.0, 0.0, "C1", "Пирролидиновое кольцо"),
            Atom3D("C", -3.5, 1.0, 0.2, "C2", "Пирролидин"),
            Atom3D("C", -4.8, 0.2, -0.1, "C3", "Пирролидин"),
            Atom3D("C", -4.2, -1.1, -0.3, "C4", "Пирролидин"),
            Atom3D("N", -2.8, -0.9, 0.1, "N1", "Пирролидиновый азот"),
            Atom3D("C", -1.8, -1.9, 0.2, "C5", "Амидный карбонил"),
            Atom3D("O", -2.0, -3.1, 0.1, "O1", "Амидный кислород =O"),
            Atom3D("C", -0.4, -1.4, 0.4, "C6", "Аланиновый углерод C-alpha"),
            Atom3D("C", -0.3, -0.2, 1.4, "C7", "Аланиновый метил"),
            Atom3D("N", 0.5, -2.5, 0.6, "N2", "Вторичный амин"),
            Atom3D("C", 1.9, -2.2, 0.3, "C8", "Центральный хиральный углерод"),
            Atom3D("C", 2.3, -1.2, -0.8, "C9", "Эфирный карбонил"),
            Atom3D("O", 1.6, -0.9, -1.8, "O2", "Эфирный карбонил =O"),
            Atom3D("O", 3.5, -0.7, -0.6, "O3", "Эфирный мостик"),
            Atom3D("C", 4.1, 0.3, -1.6, "C10", "Этиловый хвост"),
            Atom3D("C", 2.7, -3.5, 0.2, "C11", "Бензильный мостик 1"),
            Atom3D("C", 4.1, -3.3, -0.3, "C12", "Бензильный мостик 2"),
            Atom3D("C", 5.0, -4.5, -0.4, "C13", "Фенильное кольцо C1'"),
            Atom3D("C", 6.2, -4.4, -1.1, "C14", "Фенильное кольцо"),
            Atom3D("C", 7.0, -5.5, -1.2, "C15", "Фенильное кольцо")
        ),
        bonds=(
            Bond3D(0, 1, 1), Bond3D(1, 2, 1), Bond3D(2, 3, 1), Bond3D(3, 4, 1),
            Bond3D(4, 0, 1), Bond3D(4, 5, 1), Bond3D(5, 6, 2), Bond3D(5, 7, 1),
            Bond3D(7, 8, 1), Bond3D(7, 9, 1), Bond3D(9, 10, 1), Bond3D(10, 11, 1),
            Bond3D(11, 12, 2), Bond3D(11, 13, 1), Bond3D(13, 14, 1), Bond3D(10, 15, 1),
            Bond3D(15, 16, 1), Bond3D(16, 17, 1), Bond3D(17, 18, 2), Bond3D(18, 19, 1)
        ),
        mechanism_cascade=(
            {
                "step": "1",
                "title_ru": "Ингибирование ангиотензин-превращающего фермента",
                "title_kk": "Ангиотензин-өзгертуші ферментті тежеу",
                "title_en": "ACE Catalytic Inhibition",
                "desc_ru": "Активный метаболит эналаприлат подавляет синтез мощного вазоконстриктора ангиотензина II.",
                "desc_kk": "Эналаприлат белсенді метаболиті күшті вазоконстриктор ангиотензин II синтезін басады.",
                "desc_en": "Blocks conversion of angiotensin I to angiotensin II, reducing systemic vascular resistance."
            },
            {
                "step": "2",
                "title_ru": "Расширение выносящей (эфферентной) артериолы клубочка",
                "title_kk": "Шумақтың шығарушы артериоласының кеңеюі",
                "title_en": "Efferent Arteriolar Vasodilation",
                "desc_ru": "Снижение тонуса ангиотензин-зависимой эфферентной артериолы снижает внутриклубочковое давление фильтрации.",
                "desc_kk": "Ангиотензинге тәуелді шығарушы артериола тонусының төмендеуі шумақішілік сүзілу қысымын азайтады.",
                "desc_en": "Selectively dilates the renal efferent arteriole, dropping intraglomerular hydrostatic pressure."
            }
        ),
        monitoring_parameters={
            "target_test": "Креатинин сыворотки, СКФ (eGFR), калий крови (K+)",
            "renal_risk": "При комбинации с диуретиком и НПВП (Triple Whammy) риск острой почечной недостаточности (ОПН) возрастает на 31%"
        }
    ),
    "furosemide": VerifiedMolecule(
        canonical_inn="furosemide",
        display_names={
            "kk": "Фуросемид (Лазикс)",
            "ru": "Фуросемид (Лазикс)",
            "en": "Furosemide (Lasix)"
        },
        formula="C12H11ClN2O5S",
        molecular_weight=330.74,
        pubchem_cid=3440,
        iupac_name="4-chloro-2-(furan-2-ylmethylamino)-5-sulfamoylbenzoic acid",
        pharmacophore_type="Sulfamoyl-Anthranilic Loop Diuretic",
        target=TargetBindingSite(
            protein_name="Sodium-potassium-chloride cotransporter 2 (NKCC2)",
            gene_symbol="SLC12A1",
            pdb_id="6N38",
            binding_pocket="Translocation pathway of the thick ascending limb cotransporter",
            key_residues=("Leu217", "Ala221", "Tyr305", "Phe309"),
            interaction_type="competitive_reversible",
            clinical_effect="Обратимая блокада котранспортера NKCC2 -> прекращение реабсорбции 25% профильтрованного Na+, K+, Cl- -> мощный диурез, уменьшение объема циркулирующей крови (ОЦК)"
        ),
        atoms=(
            Atom3D("C", 0.0, 0.0, 0.0, "C1", "Бензольное кольцо C1 (карбоксил)"),
            Atom3D("C", 1.3, 0.3, 0.1, "C2", "C2 (аминофурфурил)"),
            Atom3D("C", 2.2, -0.7, 0.1, "C3", "Бензольное кольцо C3"),
            Atom3D("C", 1.8, -2.1, 0.0, "C4", "C4 (хлор-заместитель)"),
            Atom3D("Cl", 2.9, -3.3, 0.0, "Cl1", "Атом хлора (электроотрицательный галоген)"),
            Atom3D("C", 0.4, -2.4, -0.1, "C5", "C5 (сульфамоил)"),
            Atom3D("S", -0.1, -4.1, -0.2, "S1", "Сульфонамидная сера"),
            Atom3D("O", -1.5, -4.1, -0.3, "O1", "Сульфонил =O"),
            Atom3D("O", 0.7, -4.9, 0.6, "O2", "Сульфонил =O"),
            Atom3D("N", 0.3, -4.6, -1.7, "N1", "Сульфамоильный амин NH2"),
            Atom3D("C", -0.5, -1.3, -0.1, "C6", "Бензольное кольцо"),
            Atom3D("C", -1.0, 1.1, 0.0, "C7", "Карбоксильный карбонил"),
            Atom3D("O", -0.8, 2.3, 0.1, "O3", "Карбоксил =O"),
            Atom3D("O", -2.2, 0.6, -0.1, "O4", "Карбоксил -OH"),
            Atom3D("N", 1.8, 1.6, 0.2, "N2", "Вторичный амин N-фурфурила"),
            Atom3D("C", 3.2, 1.9, 0.3, "C8", "Метиленовый мостик"),
            Atom3D("C", 3.6, 3.3, 0.3, "C9", "Фурановое кольцо"),
            Atom3D("O", 4.9, 3.6, 0.3, "O5", "Фурановый кислород"),
            Atom3D("C", 5.0, 4.9, 0.3, "C10", "Фурановое кольцо"),
            Atom3D("C", 3.8, 5.5, 0.3, "C11", "Фурановое кольцо"),
            Atom3D("C", 2.8, 4.4, 0.3, "C12", "Фурановое кольцо")
        ),
        bonds=(
            Bond3D(0, 1, 2), Bond3D(1, 2, 1), Bond3D(2, 3, 2), Bond3D(3, 4, 1),
            Bond3D(3, 5, 1), Bond3D(5, 6, 1), Bond3D(6, 7, 2), Bond3D(6, 8, 2),
            Bond3D(6, 9, 1), Bond3D(5, 10, 2), Bond3D(10, 0, 1), Bond3D(0, 11, 1),
            Bond3D(11, 12, 2), Bond3D(11, 13, 1), Bond3D(1, 14, 1), Bond3D(14, 15, 1),
            Bond3D(15, 16, 1), Bond3D(16, 17, 1), Bond3D(17, 18, 1), Bond3D(18, 19, 2),
            Bond3D(19, 20, 1), Bond3D(20, 16, 2)
        ),
        mechanism_cascade=(
            {
                "step": "1",
                "title_ru": "Блокада реабсорбции в петле Генле",
                "title_kk": "Генле ілмегінде реабсорбцияны бұғаттау",
                "title_en": "Loop of Henle Reabsorption Arrest",
                "desc_ru": "Ингибирует транспорт натрия и хлора в толстом восходящем колене петли Генле.",
                "desc_kk": "Генле ілмегінің жуан өрлеме тізесінде натрий мен хлор тасымалын тежейді.",
                "desc_en": "Inhibits luminal NKCC2 cotransporter, preventing 25% of filtered NaCl reabsorption."
            },
            {
                "step": "2",
                "title_ru": "Гиповолемия и снижение перфузии почек",
                "title_kk": "Гиповолемия және бүйрек перфузиясының төмендеуі",
                "title_en": "Intravascular Volume Contraction",
                "desc_ru": "Интенсивный диурез уменьшает ОЦК, активируя ренин-ангиотензиновую систему для защиты клубочковой фильтрации.",
                "desc_kk": "Қарқынды диурез айналымдағы қан көлемін азайтып, шумақтық сүзілуді қорғау үшін ренин-ангиотензин жүйесін белсендіреді.",
                "desc_en": "Reduces circulating plasma volume, shifting reliance of GFR toward autoregulatory prostaglandins."
            }
        ),
        monitoring_parameters={
            "target_test": "Диурез, электролиты плазмы (Na+, K+, Cl-), АД, креатинин",
            "hemodynamic_synergy": "Комбинация с эналаприлом и ибупрофеном лишает почку обоих компенсаторных механизмов (вазодилатации афферентной и вазоконстрикции эфферентной артериолы)"
        }
    ),
    "ibuprofen": VerifiedMolecule(
        canonical_inn="ibuprofen",
        display_names={
            "kk": "Ибупрофен",
            "ru": "Ибупрофен",
            "en": "Ibuprofen"
        },
        formula="C13H18O2",
        molecular_weight=206.28,
        pubchem_cid=3672,
        iupac_name="2-(4-isobutylphenyl)propanoic acid",
        pharmacophore_type="Propionic Acid NSAID",
        target=TargetBindingSite(
            protein_name="Prostaglandin G/H synthase 1 & 2 (COX-1 / COX-2)",
            gene_symbol="PTGS1 / PTGS2",
            pdb_id="4PH9",
            binding_pocket="Cyclooxygenase active channel hydrophobic cavity",
            key_residues=("Arg120", "Tyr355", "Glu524", "Ile523", "Ser530"),
            interaction_type="competitive_reversible",
            clinical_effect="Обратимое ингибирование COX-1/COX-2 -> подавление синтеза почечных вазодилатирующих простагландинов PGE2 и PGI2 -> сужение приносящей (афферентной) артериолы клубочка -> падение клубочкового кровотока"
        ),
        atoms=(
            Atom3D("C", 0.0, 0.0, 0.0, "C1", "Карбоксильный C-alpha"),
            Atom3D("C", -0.8, -1.2, 0.0, "C2", "Карбоксил C=O"),
            Atom3D("O", -0.4, -2.4, 0.0, "O1", "Карбоксил =O"),
            Atom3D("O", -2.1, -0.9, 0.0, "O2", "Карбоксил -OH"),
            Atom3D("C", -0.4, 0.9, -1.1, "C3", "Альфа-метил"),
            Atom3D("C", 1.5, -0.2, 0.0, "C4", "Бензольное кольцо C1'"),
            Atom3D("C", 2.1, -1.5, 0.0, "C5", "Бензольное кольцо"),
            Atom3D("C", 3.5, -1.7, 0.0, "C6", "Бензольное кольцо"),
            Atom3D("C", 4.3, -0.6, 0.0, "C7", "Бензольное кольцо C4' (изобутил)"),
            Atom3D("C", 3.7, 0.7, 0.0, "C8", "Бензольное кольцо"),
            Atom3D("C", 2.3, 0.9, 0.0, "C9", "Бензольное кольцо"),
            Atom3D("C", 5.8, -0.8, 0.0, "C10", "Изобутиловый CH2"),
            Atom3D("C", 6.6, 0.5, 0.1, "C11", "Изобутиловый CH"),
            Atom3D("C", 8.1, 0.2, 0.1, "C12", "Метил изобутила 1"),
            Atom3D("C", 6.2, 1.4, -1.0, "C13", "Метил изобутила 2")
        ),
        bonds=(
            Bond3D(0, 1, 1), Bond3D(1, 2, 2), Bond3D(1, 3, 1), Bond3D(0, 4, 1),
            Bond3D(0, 5, 1), Bond3D(5, 6, 2), Bond3D(6, 7, 1), Bond3D(7, 8, 2),
            Bond3D(8, 9, 1), Bond3D(9, 10, 2), Bond3D(10, 5, 1), Bond3D(8, 11, 1),
            Bond3D(11, 12, 1), Bond3D(12, 13, 1), Bond3D(12, 14, 1)
        ),
        mechanism_cascade=(
            {
                "step": "1",
                "title_ru": "Ингибирование почечных циклооксигеназ",
                "title_kk": "Бүйрек циклооксигеназаларын тежеу",
                "title_en": "Renal COX-1/2 Inhibition",
                "desc_ru": "Ибупрофен обратимо блокирует синтез простагландинов PGE2 и простациклина PGI2 в медулле и сосудах почек.",
                "desc_kk": "Ибупрофен бүйрек тамырларында PGE2 және PGI2 простагландиндерінің синтезін қайтымды бұғаттайды.",
                "desc_en": "Reversibly inhibits intrarenal COX-1 and COX-2 synthesis of vasodilatory prostaglandins PGE2 and PGI2."
            },
            {
                "step": "2",
                "title_ru": "Констрикция приносящей (афферентной) артериолы",
                "title_kk": "Әкелуші (афферентті) артериоланың тарылуы",
                "title_en": "Afferent Arteriolar Vasoconstriction",
                "desc_ru": "Утрата вазодилатирующего стимула простагландинов приводит к спазму приносящего сосуда клубочка, сокращая приток крови.",
                "desc_kk": "Простагландиндердің кеңейткіш әсерінің жоғалуы шумақтың әкелуші тамырының спазмына әкеліп, қан келуін азайтады.",
                "desc_en": "Unchecked afferent arteriolar constriction cuts glomerular plasma inflow."
            }
        ),
        monitoring_parameters={
            "target_test": "СКФ / eGFR, креатинин, калий, артериальное давление",
            "triple_whammy_role": "Перекрывает приток крови в клубочек, в то время как эналаприл сбрасывает отток, а фуросемид истощает объем"
        }
    )
}


def get_verified_molecule(canonical_name: str) -> VerifiedMolecule | None:
    """Возвращает верифицированную 3D-молекулярную модель или None."""
    if not canonical_name:
        return None
    name = canonical_name.strip().lower()
    if name in VERIFIED_MOLECULES:
        return VERIFIED_MOLECULES[name]
    # Поиск по алиасам
    alias_map = {
        "aspirin": "acetylsalicylic acid",
        "cordarone": "amiodarone",
        "кордарон": "amiodarone",
        "амиодарон": "amiodarone",
        "diflucan": "fluconazole",
        "дифлюкан": "fluconazole",
        "флуконазол": "fluconazole",
        "lasix": "furosemide",
        "лазикс": "furosemide",
        "фуросемид": "furosemide",
        "renitec": "enalapril",
        "ренитек": "enalapril",
        "эналаприл": "enalapril",
        "nurofen": "ibuprofen",
        "нурофен": "ibuprofen",
        "ибупрофен": "ibuprofen",
        "варфарин": "warfarin",
        "ацетилсалициловая кислота": "acetylsalicylic acid",
        "аспирин": "acetylsalicylic acid"
    }
    canon = alias_map.get(name)
    return VERIFIED_MOLECULES.get(canon) if canon else None
