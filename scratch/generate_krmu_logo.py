import os
import matplotlib
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Wedge

fig, ax = plt.subplots(figsize=(4, 4), dpi=300, facecolor='none')
ax.set_facecolor('none')
ax.axis('off')

# Outer gold shield border
circle_outer = Circle((0.5, 0.5), 0.46, facecolor='#0D1D28', edgecolor='#36D6B0', linewidth=3)
circle_inner = Circle((0.5, 0.5), 0.41, facecolor='#112532', edgecolor='#67B7D1', linewidth=1.5)
ax.add_patch(circle_outer)
ax.add_patch(circle_inner)

# Medical cross & snake bowl abstract motif
cross_v = plt.Rectangle((0.47, 0.32), 0.06, 0.36, facecolor='#36D6B0', edgecolor='none')
cross_h = plt.Rectangle((0.36, 0.47), 0.28, 0.06, facecolor='#36D6B0', edgecolor='none')
ax.add_patch(cross_v)
ax.add_patch(cross_h)

# Asclepius snake spiral
theta = [0.38, 0.44, 0.50, 0.56, 0.62]
for y in theta:
    circle_node = Circle((0.5, y), 0.016, facecolor='#EAF2F2', edgecolor='#36D6B0', linewidth=0.8)
    ax.add_patch(circle_node)

ax.text(0.5, 0.82, "К Р М У", color='#EAF2F2', fontsize=15, fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
ax.text(0.5, 0.72, "KAZAKH-RUSSIAN MEDICAL UNIVERSITY", color='#67B7D1', fontsize=4.8, fontweight='bold', ha='center', va='center')
ax.text(0.5, 0.22, "1992 · ALMATY", color='#91A5AA', fontsize=5.5, fontweight='bold', ha='center', va='center')

plt.xlim(0, 1)
plt.ylim(0, 1)
plt.savefig("assets/presentation/krmu_logo.png", transparent=True, bbox_inches='tight', pad_inches=0.05)
plt.close()
print("KRMU emblem generated!")
