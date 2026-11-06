import os
import numpy as np
import pandas as pd
import matplotlib
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import FancyBboxPatch

from data_loader import load_ddinter
from model import train_and_evaluate

os.makedirs("assets/presentation", exist_ok=True)

# -----------------------------------------------------------------------------
# 1. GENERATE ACCURATE REAL ROC-AUC BENCHMARK FROM MODEL.PY RUN
# -----------------------------------------------------------------------------
print("Running train_and_evaluate to get genuine Colab / model.py curves...")
pairs, drugs = load_ddinter()
metrics_dict = train_and_evaluate(pairs, drugs)
metrics_df = metrics_dict["metrics"]
roc_data = metrics_dict["roc"]
print("Metrics dataframe:")
print(metrics_df)

fig, ax = plt.subplots(figsize=(7.8, 5.0), dpi=250, facecolor="#000000")
ax.set_facecolor("#070E12")

# Distinct Apple-Keynote colors for lines
color_map = {
    "Случайный лес": ("#00F5A0", 2.8, "-"),
    "Только общие соседи": ("#00D2FF", 2.2, "-"),
    "Логистическая регрессия": ("#BF5AF2", 2.0, "-"),
    "Только степень": ("#FF9F0A", 1.8, "--"),
    "Случайное угадывание": ("#636366", 1.2, ":")
}

for _, row in metrics_df.iterrows():
    name = row["Метод"]
    auc_val = row["ROC-AUC"]
    if name in roc_data:
        fpr, tpr = roc_data[name]
        col, lw, ls = color_map.get(name, ("#FFFFFF", 1.5, "-"))
        ax.plot(fpr, tpr, label=f"{name} · ROC-AUC {auc_val:.3f}", color=col, linewidth=lw, linestyle=ls)

ax.set_title("РЕАЛЬНЫЙ LEAKAGE-FREE БЕНЧМАРК (ЭТАЛОННЫЙ ПРОГОН ИЗ КОДА)", color="#FFFFFF", fontsize=11, fontweight="bold", pad=12)
ax.set_xlabel("False Positive Rate (FPR)", color="#8E8E93", fontsize=9, fontweight="bold")
ax.set_ylabel("True Positive Rate (TPR)", color="#8E8E93", fontsize=9, fontweight="bold")
ax.tick_params(colors="#8E8E93", labelsize=8.5)
for spine in ax.spines.values():
    spine.set_color("#263940")
ax.grid(True, color="#162730", alpha=0.6, linestyle=":")
leg = ax.legend(loc="lower right", facecolor="#0B151A", edgecolor="#263940", fontsize=8.5)
for t in leg.get_texts():
    t.set_color("#FFFFFF")

plt.tight_layout()
roc_path = "assets/presentation/roc_auc_benchmark.png"
plt.savefig(roc_path, bbox_inches='tight', pad_inches=0.1, facecolor="#000000")
plt.close()
print(f"Genuine ROC-AUC benchmark saved to {roc_path}")

# -----------------------------------------------------------------------------
# 2. GENERATE ACCURATE DDINTER STATS & REAL TOP-10 MAJOR HUBS
# -----------------------------------------------------------------------------
print("Calculating real top-10 major hubs from DDInter...")
major_df = pairs[pairs["Level"].str.lower() == "major"]
real_major_hubs = pd.concat([major_df["Drug_A"], major_df["Drug_B"]]).value_counts().head(10)
print("Top 10 major hubs:")
print(real_major_hubs)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.8), dpi=250, facecolor="#000000")
ax1.set_facecolor("#000000")
ax2.set_facecolor("#070E12")

# Left Donut: Exact verified counts
labels = ['Moderate\n96 675 (60%)', 'Unknown\n29 813 (19%)', 'Major\n26 914 (17%)', 'Minor\n6 833 (4%)']
sizes = [96675, 29813, 26914, 6833]
colors = ['#FF9F0A', '#48484A', '#FF453A', '#00F5A0']
wedges, texts = ax1.pie(sizes, labels=labels, colors=colors, startangle=140, 
                        wedgeprops=dict(width=0.42, edgecolor='#000000', linewidth=2.5),
                        textprops=dict(color="#FFFFFF", fontsize=8.5, fontweight='bold'))
ax1.set_title("СТРУКТУРА 160 235 ПАР В DDINTER", color="#FFFFFF", fontsize=10.5, fontweight="bold")

# Right: Real Top 10 Major Hubs
hubs_names = list(real_major_hubs.index)
hubs_counts = list(real_major_hubs.values)
y_pos = np.arange(len(hubs_names))

bars = ax2.barh(y_pos, hubs_counts, color='#00D2FF', edgecolor='#00F5A0', height=0.62)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(hubs_names, color='#FFFFFF', fontsize=9, fontweight='bold')
ax2.invert_yaxis()
ax2.set_xlabel("Число критических (Major) связей в DDInter (макс. 504)", color="#8E8E93", fontsize=8.5)
ax2.set_title("РЕАЛЬНЫЙ ТОП-10 ФАРМАКОЛОГИЧЕСКИХ ХАБОВ (MAJOR)", color="#FFFFFF", fontsize=10.5, fontweight="bold")
ax2.tick_params(colors="#8E8E93", labelsize=8)
for spine in ax2.spines.values():
    spine.set_color("#263940")
ax2.grid(True, axis='x', color="#162730", alpha=0.5, linestyle=":")

for bar in bars:
    w = bar.get_width()
    ax2.text(w + 12, bar.get_y() + bar.get_height()/2, f'{int(w)}', 
             va='center', ha='left', color='#00F5A0', fontsize=8.5, fontweight='bold')

plt.tight_layout()
hubs_path = "assets/presentation/ddinter_hubs_chart.png"
plt.savefig(hubs_path, bbox_inches='tight', pad_inches=0.1, facecolor="#000000")
plt.close()
print(f"Genuine hubs chart saved to {hubs_path}")

# -----------------------------------------------------------------------------
# 3. GENERATE ACCURATE ICEBERG GRAPHIC (NOT "CATASTROPHES", BUT "INTERACTIONS")
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6.75), dpi=250)
fig.patch.set_facecolor("#000000")
ax.set_facecolor("#000000")

x = np.linspace(0, 10, 500)
water_y = np.ones_like(x) * 4.2 + 0.05 * np.sin(x * 3.5)
ax.plot(x, water_y, color="#00D2FF", linewidth=2.0, alpha=0.85)
ax.fill_between(x, -0.5, water_y, color="#05151D", alpha=0.9)

# Tip of iceberg
tip_x = [4.2, 5.0, 5.8]
tip_y = [4.2, 5.6, 4.2]
ax.fill(tip_x, tip_y, color="#163842", edgecolor="#00F5A0", linewidth=2.0, alpha=0.95)

# Underwater iceberg
ice_poly_x = [4.2, 3.1, 1.8, 2.5, 5.0, 7.5, 8.2, 6.9, 5.8]
ice_poly_y = [4.2, 3.2, 1.2, 0.2, 0.0, 0.4, 1.8, 3.4, 4.2]
ax.fill(ice_poly_x, ice_poly_y, color="#0B1F27", edgecolor="#FF453A", linewidth=2.2, alpha=0.85)

ax.scatter([5.0], [1.8], s=12000, color="#FF453A", alpha=0.07, edgecolors="none")
ax.scatter([5.0], [5.0], s=6000, color="#00F5A0", alpha=0.08, edgecolors="none")

# Labels
ax.text(5.0, 6.1, "ВИДИМАЯ ЗОНА (ПАЛУБА «ТИТАНИКА»)", color="#00F5A0", fontsize=11, fontweight="bold", ha="center")
ax.text(5.0, 5.8, "«Музыка играет, пациент улыбается, давление 120/80»", color="#FFFFFF", fontsize=12, fontweight="bold", ha="center")
ax.text(5.0, 4.7, "5–7 выписанных таблеток\nВнешне всё стабильно", color="#86868B", fontsize=9.5, ha="center", style="italic")

ax.text(5.0, 3.6, "ПОДВОДНАЯ СКРЫТАЯ МАССА (ТРЮМ)", color="#FF453A", fontsize=12, fontweight="bold", ha="center")

threats = [
    ("1. Блокада цитохрома CYP2C9 / CYP3A4", 2.9, "#FFFFFF"),
    ("2. Кумуляция препарата и скачок токсичности", 2.4, "#FFD1D5"),
    ("3. Скрытый спазм почечных артериол (Triple Whammy)", 1.9, "#FFFFFF"),
    ("4. Субклиническое повреждение нефронов без боли и жалоб", 1.4, "#FFD1D5"),
    ("5. Органотоксическая конвергенция без химической реакции в крови", 0.9, "#FF453A"),
]

for txt, y_pos, col in threats:
    ax.text(5.0, y_pos, f"⚠  {txt}", color=col, fontsize=10, fontweight="bold", ha="center")

# Bottom caption corrected exactly as requested:
ax.text(5.0, 0.25, "160 235 ЗАПИСЕЙ О ВЗАИМОДЕЙСТВИЯХ В DDINTER (ИЗ НИХ 26 914 CRITICAL / MAJOR)",
        color="#00D2FF", fontsize=9.5, fontweight="bold", ha="center")

ax.set_xlim(0, 10)
ax.set_ylim(-0.2, 6.6)
ax.axis("off")

plt.tight_layout(pad=0)
iceberg_path = "assets/presentation/iceberg_metaphor.png"
plt.savefig(iceberg_path, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight", dpi=250)
plt.close()
print(f"Corrected iceberg graphic saved to {iceberg_path}")

# -----------------------------------------------------------------------------
# 4. GENERATE 3D DRUG MODEL ILLUSTRATION (CLEARLY LABELED AS ILLUSTRATION)
# -----------------------------------------------------------------------------
fig = plt.figure(figsize=(10, 6.2), dpi=250, facecolor="#000000")
ax = fig.add_subplot(111, projection='3d', facecolor="#000000")
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor('#000000')
ax.yaxis.pane.set_edgecolor('#000000')
ax.zaxis.pane.set_edgecolor('#000000')
ax.grid(False)
ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])

u = np.linspace(0, 2 * np.pi, 50)
v = np.linspace(-np.pi/2, 0, 30)
r = 1.3
z_cyl = np.linspace(-1.8, 0, 30)
U, Z_c = np.meshgrid(u, z_cyl)
X_c = r * np.cos(U) - 1.2
Y_c = r * np.sin(U)
ax.plot_surface(X_c, Y_c, Z_c, color='#142830', alpha=0.88, shade=True, edgecolor='#263940', linewidth=0.2)

U_d, V_d = np.meshgrid(u, v)
X_d = r * np.cos(V_d) * np.cos(U_d) - 1.2
Y_d = r * np.cos(V_d) * np.sin(U_d)
Z_d = r * np.sin(V_d) - 1.8
ax.plot_surface(X_d, Y_d, Z_d, color='#142830', alpha=0.92, shade=True)

v_top = np.linspace(0, np.pi/2, 30)
z_cyl2 = np.linspace(0.8, 2.4, 30)
U2, Z_c2 = np.meshgrid(u, z_cyl2)
X_c2 = (r * 1.04) * np.cos(U2) + 0.8
Y_c2 = (r * 1.04) * np.sin(U2) + 0.5
ax.plot_surface(X_c2, Y_c2, Z_c2, color='#00F5A0', alpha=0.75, shade=True, edgecolor='#00D2FF', linewidth=0.3)

U_d2, V_d2 = np.meshgrid(u, v_top)
X_d2 = (r * 1.04) * np.cos(V_d2) * np.cos(U2) + 0.8
Y_d2 = (r * 1.04) * np.cos(V_d2) * np.sin(U2) + 0.5
Z_d2 = (r * 1.04) * np.sin(V_d2) + 2.4
ax.plot_surface(X_d2, Y_d2, Z_d2, color='#00F5A0', alpha=0.82, shade=True)

np.random.seed(42)
n_pellets = 75
t_vals = np.linspace(0, 1, n_pellets)
px = -1.0 + t_vals * 3.8 + np.random.normal(0, 0.45, n_pellets)
py = np.random.normal(0, 0.55, n_pellets)
pz = -0.5 + t_vals * 2.6 + np.sin(t_vals * np.pi) * 1.2 + np.random.normal(0, 0.3, n_pellets)

colors = []
for i in range(n_pellets):
    if i % 7 == 0:
        colors.append('#FF453A')
    elif i % 3 == 0:
        colors.append('#00D2FF')
    elif i % 2 == 0:
        colors.append('#00F5A0')
    else:
        colors.append('#FFFFFF')

sizes = np.random.uniform(50, 160, n_pellets)
ax.scatter(px, py, pz, c=colors, s=sizes, alpha=0.88, edgecolors='#0B1114', linewidth=0.6)

ring_u = np.linspace(0, 2*np.pi, 7)
rx = 1.6 * np.cos(ring_u) - 2.8
ry = 1.6 * np.sin(ring_u) + 1.2
rz = np.zeros_like(ring_u) + 0.5
ax.plot(rx, ry, rz, color='#00D2FF', linewidth=2.5, alpha=0.7)
ax.scatter(rx, ry, rz, color='#00F5A0', s=90, edgecolors='#FFFFFF')

ax.view_init(elev=24, azim=48)
ax.dist = 9.8
plt.title("3D-ВИЗУАЛИЗАЦИЯ КАСКАДА (КОНЦЕПТУАЛЬНАЯ ИЛЛЮСТРАЦИЯ)\nМеханизм блокады метаболических путей CYP2C9 и конвергенции", 
          color='#FFFFFF', fontsize=11, fontweight='bold', pad=-20, family='sans-serif')
model_path = "assets/presentation/3d_drug_model.png"
plt.savefig(model_path, bbox_inches='tight', pad_inches=0.1, facecolor="#000000")
plt.close()
print(f"3D drug illustration saved to {model_path}")

# -----------------------------------------------------------------------------
# 5. GENERATE DARIKZ ROADMAP FLOW DIAGRAM (CLEARLY LABELED AS ROADMAP)
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10.5, 4.8), dpi=250, facecolor="#000000")
ax.set_facecolor("#070E12")
ax.axis('off')

boxes = [
    {
        "x": 0.04, "y": 0.32, "w": 0.26, "h": 0.46,
        "tag": "ТЕКУЩИЙ ЭТАП (РЕАЛИЗОВАНО)",
        "title": "PHARMA SENTINEL CORE",
        "sub": "База DDInter: 160 235 связей\nПроверка выбранной пары препаратов\nИнтерактивная карта лекарств\nLeakage-free ML-оценка (Random Forest 0.911)",
        "col": "#00F5A0"
    },
    {
        "x": 0.37, "y": 0.28, "w": 0.28, "h": 0.54,
        "tag": "ПЛАН РАЗВИТИЯ (ЭТАП 2)",
        "title": "ПЕРСПЕКТИВНЫЙ DARIKZ КОНТУР",
        "sub": "Интеграция с Реестром ЛС РК (DariKz)\nМНН-маппинг коммерческих брендов РК\nМобильное рабочее место врача\nБыстрый аудит листа назначений на обходе",
        "col": "#00D2FF"
    },
    {
        "x": 0.70, "y": 0.32, "w": 0.26, "h": 0.46,
        "tag": "ПЛАН РАЗВИТИЯ (ЭТАП 3)",
        "title": "КЛИНИЧЕСКИЙ ПИЛОТ КРМУ",
        "sub": "Апробация в клиниках университета\nПерспектива связки с КМИС (ДамуМед)\nФормирование суверенной базы\nклинических фармако-рисков",
        "col": "#BF5AF2"
    }
]

for b in boxes:
    rect = FancyBboxPatch((b["x"], b["y"]), b["w"], b["h"], boxstyle="round,pad=0.03,rounding_size=0.04",
                          linewidth=1.8, edgecolor=b["col"], facecolor="#0E1920")
    ax.add_patch(rect)
    ax.text(b["x"] + b["w"]/2, b["y"] + b["h"] - 0.06, b["tag"], color=b["col"], 
            fontsize=7.5, fontweight='bold', ha='center', va='center')
    ax.text(b["x"] + b["w"]/2, b["y"] + b["h"] - 0.14, b["title"], color="#FFFFFF", 
            fontsize=9.5, fontweight='bold', ha='center', va='center')
    ax.text(b["x"] + b["w"]/2, b["y"] + b["h"]/2 - 0.07, b["sub"], color='#EAF2F2', 
            fontsize=8.0, ha='center', va='center', linespacing=1.35)

# Connecting arrows
ax.annotate("", xy=(0.36, 0.55), xytext=(0.31, 0.55),
            arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color="#00D2FF", lw=2.2))
ax.annotate("", xy=(0.69, 0.55), xytext=(0.66, 0.55),
            arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color="#BF5AF2", lw=2.2))

ax.text(0.335, 0.62, "ROADMAP\nВЕКТОР 1", color="#00D2FF", fontsize=7.2, fontweight='bold', ha='center')
ax.text(0.675, 0.62, "ROADMAP\nВЕКТОР 2", color="#BF5AF2", fontsize=7.2, fontweight='bold', ha='center')

plt.title("ПЛАН РАЗВИТИЯ ПРОЕКТА: ОТ ИССЛЕДОВАТЕЛЬСКОЙ МОДЕЛИ К ПРАКТИКЕ", 
          color="#FFFFFF", fontsize=11, fontweight="bold", pad=12)
plt.tight_layout()
darikz_path = "assets/presentation/darikz_integration.png"
plt.savefig(darikz_path, bbox_inches='tight', pad_inches=0.1, facecolor="#000000")
plt.close()
print(f"Roadmap graphic saved to {darikz_path}")

print("All accurate graphics successfully generated!")
