"""
Скрипт генерации кинематографичной инфографики: «Айсберг полипрагмазии / Аналогия Титаника»
в стиле Apple Keynote (Pure Black, Emerald & Coral Red, Crisp Typography).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

fig, ax = plt.subplots(figsize=(12, 6.75), dpi=250)
fig.patch.set_facecolor("#030709")
ax.set_facecolor("#030709")

# Рисуем линию воды (Waterline)
x = np.linspace(0, 10, 500)
water_y = np.ones_like(x) * 4.2 + 0.05 * np.sin(x * 3.5)
ax.plot(x, water_y, color="#00D2FF", linewidth=2.0, alpha=0.85, label="Ватерлиния видимых симптомов")
ax.fill_between(x, -0.5, water_y, color="#05151D", alpha=0.9)

# Рисуем надводную часть айсберга (Маленький пик)
tip_x = [4.2, 5.0, 5.8]
tip_y = [4.2, 5.6, 4.2]
ax.fill(tip_x, tip_y, color="#163842", edgecolor="#00F5A0", linewidth=2.0, alpha=0.95)

# Рисуем подводную гигантскую часть айсберга (Скрытая масса)
ice_poly_x = [4.2, 3.1, 1.8, 2.5, 5.0, 7.5, 8.2, 6.9, 5.8]
ice_poly_y = [4.2, 3.2, 1.2, 0.2, 0.0, 0.4, 1.8, 3.4, 4.2]
ax.fill(ice_poly_x, ice_poly_y, color="#0B1F27", edgecolor="#FF3B30", linewidth=2.2, alpha=0.85)

# Свечение и градиент под водой
ax.scatter([5.0], [1.8], s=12000, color="#FF3B30", alpha=0.07, edgecolors="none")
ax.scatter([5.0], [5.0], s=6000, color="#00F5A0", alpha=0.08, edgecolors="none")

# Текстовые аннотации в стиле Apple Keynote
# Над водой:
ax.text(5.0, 6.1, "ВИДИМАЯ ЗОНА (ПАЛУБА «ТИТАНИКА»)", color="#00F5A0", fontsize=11, fontweight="bold",
        ha="center", fontfamily="sans-serif")
ax.text(5.0, 5.8, "«Музыка играет, пациент улыбается, давление 120/80»", color="#FFFFFF", fontsize=12,
        fontweight="bold", ha="center", fontfamily="sans-serif")
ax.text(5.0, 4.7, "5–7 выписанных таблеток\nВнешне всё стабильно", color="#86868B", fontsize=9.5,
        ha="center", fontfamily="sans-serif", style="italic")

# Под водой (Айсберг):
ax.text(5.0, 3.6, "ПОДВОДНАЯ СМЕРТЕЛЬНАЯ МАССА (ТРЮМ)", color="#FF3B30", fontsize=12, fontweight="bold",
        ha="center", fontfamily="sans-serif")

threats = [
    ("1. Блокада цитохрома CYP2C9 / CYP3A4", 2.9, "#FFFFFF"),
    ("2. Кумуляция токсинов и взлет МНО > 6.0", 2.4, "#FFD1D5"),
    ("3. Скрытый ишемический спазм афферентной артериолы (Triple Whammy)", 1.9, "#FFFFFF"),
    ("4. Субклинический некроз канальцев почек без боли и симптомов", 1.4, "#FFD1D5"),
    ("5. Органотоксическая конвергенция без прямого связывания молекул", 0.9, "#FF3B30"),
]

for txt, y_pos, col in threats:
    ax.text(5.0, y_pos, f"⚠  {txt}", color=col, fontsize=10, fontweight="bold",
            ha="center", fontfamily="sans-serif")

# Нижний вердикт
ax.text(5.0, 0.25, "160 235 ВЕРИФИЦИРОВАННЫХ КЛИНИЧЕСКИХ КАТАСТРОФ DDINTER",
        color="#00D2FF", fontsize=10, fontweight="bold", ha="center", fontfamily="sans-serif")

ax.set_xlim(0, 10)
ax.set_ylim(-0.2, 6.6)
ax.axis("off")

plt.tight_layout(pad=0)
os.makedirs("assets/presentation", exist_ok=True)
output_path = "assets/presentation/iceberg_metaphor.png"
plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight", dpi=250)
plt.close()
print(f"Iceberg graphic created successfully at {output_path}")
