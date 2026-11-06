"""Интерактивные научные визуализации для Молекулярной лаборатории (Molecular Intelligence Lab).

Концепция дизайна: "Futuristic Scientific Intelligence" (Qgen / High-Craft Medical Tech)
Палитра:
- Background: #0B1114
- Primary surface: #111B20
- Secondary surface: #17252B
- Primary accent: #36D6B0 (Bioluminescent Emerald)
- Secondary accent: #67B7D1 (Restrained Cyan)
- Text: #EAF2F2
- Muted text: #91A5AA
- Borders: #263940

Реализует три научно обоснованных режима:
1. Mode 1: 3D-молекулярный вьюер (Three.js + OrbitControls, переключение 3D / 2D+Radar, CPK-атомы, телеметрия).
2. Mode 2: Анимация каскада «Препарат -> Мишень -> Эффект» (пошаговый / непрерывный биохимический механизм).
3. Mode 3: Визуализация конвергенции механизмов (сочетанный гемодинамический / гемостатический конфликт без ложного прямого столкновения молекул).
"""
import json
from data.verified_molecules import VerifiedMolecule, get_verified_molecule


CPK_COLORS = {
    "C": "#36D6B0",   # Bioluminescent Emerald Carbon
    "O": "#F43F5E",   # High-Contrast Rose/Crimson Oxygen
    "N": "#67B7D1",   # Scientific Cyan Nitrogen
    "S": "#F59E0B",   # Amber Sulfur
    "Cl": "#10B981",  # Deep Emerald Chlorine
    "F": "#2DD4BF",   # Teal Fluorine
    "I": "#A855F7",   # Violet Iodine
    "H": "#CBD5E1"    # Crisp Ice Hydrogen
}

ATOM_RADII = {
    "C": 0.55,
    "O": 0.48,
    "N": 0.52,
    "S": 0.65,
    "Cl": 0.62,
    "F": 0.42,
    "I": 0.78,
    "H": 0.30
}


def render_3d_molecule_viewer_html(
    mol_a: VerifiedMolecule,
    mol_b: VerifiedMolecule | None = None,
    active_molecule_key: str = "a",
    lang: str = "ru",
    height: int = 490
) -> str:
    """Генерирует HTML/JS для интерактивного вращаемого 3D/2D-молекулярного вьюера в эстетике Qgen."""
    target_mol = mol_b if active_molecule_key == "b" and mol_b else mol_a

    atoms_data = [
        {
            "idx": i,
            "el": a.element,
            "x": a.x,
            "y": a.y,
            "z": a.z,
            "label": a.label,
            "role": a.role,
            "color": CPK_COLORS.get(a.element, "#67B7D1"),
            "radius": ATOM_RADII.get(a.element, 0.5)
        }
        for i, a in enumerate(target_mol.atoms)
    ]

    bonds_data = [
        {"a1": b.atom1_idx, "a2": b.atom2_idx, "order": b.order}
        for b in target_mol.bonds
    ]

    atoms_json = json.dumps(atoms_data)
    bonds_json = json.dumps(bonds_data)

    disp_name = target_mol.display_names.get(lang, target_mol.display_names.get("ru", target_mol.canonical_inn.title()))

    title_label = "3D ВЕРИФИЦИРОВАННАЯ СТРУКТУРА" if lang == "ru" else ("3D ВЕРИФИКАЦИЯЛАНҒАН ҚҰРЫЛЫМ" if lang == "kk" else "3D VERIFIED STRUCTURE")
    rotate_hint = "Вращение: мышь · Зум: колесо · Клик: фокус" if lang == "ru" else ("Айналдыру: тінтуір · Масштаб: дөңгелек" if lang == "kk" else "Rotate: drag · Zoom: wheel · Hover: inspect")
    spacefill_btn = "vdW Сферы" if lang == "ru" else ("vdW Сфералар" if lang == "kk" else "vdW Spheres")
    ballstick_btn = "3D Каркас" if lang == "ru" else ("3D Қаңқа" if lang == "kk" else "3D Ball & Stick")
    view2d_btn = "2D + Радар" if lang == "ru" else ("2D + Радар" if lang == "kk" else "2D + Radar")
    reset_btn = "Сброс" if lang == "ru" else ("Қалпына келтіру" if lang == "kk" else "Reset")
    hover_hint = "Наведите курсор на атом для инспекции биохимической роли и связывания" if lang == "ru" else ("Биохимиялық рөлін көру үшін атомға бағыттаңыз" if lang == "kk" else "Hover over any atom to inspect its biochemical role and pocket interaction")

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body, html {{
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0B1114;
      color: #EAF2F2;
    }}
    #viewer-container {{
      position: relative;
      width: 100%;
      height: {height}px;
      background:
        radial-gradient(circle at 50% 48%, rgba(54, 214, 176, 0.14) 0%, rgba(23, 37, 43, 0.55) 46%, #0B1114 85%),
        linear-gradient(rgba(38, 57, 64, 0.25) 1px, transparent 1px),
        linear-gradient(90deg, rgba(38, 57, 64, 0.25) 1px, transparent 1px);
      background-size: 100% 100%, 28px 28px, 28px 28px;
      border: 1px solid #263940;
      border-radius: 8px;
      overflow: hidden;
    }}
    canvas {{ display: block; width: 100%; height: 100%; cursor: grab; }}
    canvas:active {{ cursor: grabbing; }}

    #overlay-2d {{
      position: absolute;
      inset: 0;
      display: none;
      background:
        radial-gradient(circle at 38% 50%, rgba(54, 214, 176, 0.11) 0%, #0B1114 70%),
        linear-gradient(rgba(38, 57, 64, 0.22) 1px, transparent 1px),
        linear-gradient(90deg, rgba(38, 57, 64, 0.22) 1px, transparent 1px);
      background-size: 100% 100%, 24px 24px, 24px 24px;
      z-index: 5;
      padding: 58px 16px 54px 16px;
      grid-template-columns: 1.25fr 0.95fr;
      gap: 14px;
      align-items: center;
    }}
    #overlay-2d.visible {{
      display: grid;
    }}
    .panel-2d-box {{
      height: 100%;
      background: rgba(17, 27, 32, 0.82);
      border: 1px solid #263940;
      border-radius: 6px;
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 10px;
    }}
    .panel-2d-label {{
      position: absolute;
      top: 8px;
      left: 10px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      color: #91A5AA;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .ui-top-bar {{
      position: absolute;
      top: 10px;
      left: 12px;
      right: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      pointer-events: none;
      z-index: 10;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .mol-badge {{
      background: rgba(17, 27, 32, 0.90);
      backdrop-filter: blur(8px);
      border: 1px solid #263940;
      border-left: 3px solid #36D6B0;
      padding: 6px 12px;
      border-radius: 6px;
      pointer-events: auto;
    }}
    .mol-badge-sub {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 9.5px;
      font-weight: 600;
      letter-spacing: 0.09em;
      text-transform: uppercase;
      color: #36D6B0;
    }}
    .mol-badge-title {{
      font-size: 13.5px;
      font-weight: 700;
      color: #EAF2F2;
      margin-top: 2px;
    }}
    .controls-overlay {{
      display: flex;
      gap: 5px;
      pointer-events: auto;
      background: rgba(17, 27, 32, 0.9);
      padding: 3px;
      border-radius: 6px;
      border: 1px solid #263940;
    }}
    .btn-ctrl {{
      background: transparent;
      border: 1px solid transparent;
      color: #91A5AA;
      font-size: 11px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 4px;
      cursor: pointer;
      transition: transform 0.15s ease, background 0.15s ease, color 0.15s ease;
    }}
    .btn-ctrl:hover {{
      color: #EAF2F2;
      background: rgba(54, 214, 176, 0.10);
    }}
    .btn-ctrl.active {{
      background: #36D6B0;
      color: #0B1114;
      font-weight: 700;
    }}

    .ui-bottom-bar {{
      position: absolute;
      bottom: 10px;
      left: 12px;
      right: 12px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      pointer-events: none;
      z-index: 10;
      gap: 8px;
    }}
    .atom-inspector {{
      background: rgba(17, 27, 32, 0.92);
      backdrop-filter: blur(8px);
      border: 1px solid #263940;
      border-left: 3px solid #36D6B0;
      padding: 7px 12px;
      border-radius: 6px;
      font-size: 11px;
      color: #EAF2F2;
      max-width: 66%;
      pointer-events: auto;
    }}
    .inspector-title {{
      font-weight: 700;
      color: #36D6B0;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .inspector-desc {{
      color: #91A5AA;
      margin-top: 2px;
      font-size: 10.5px;
      line-height: 1.35;
    }}
    .hint-chip {{
      background: rgba(17, 27, 32, 0.88);
      border: 1px solid #263940;
      padding: 4px 9px;
      border-radius: 4px;
      font-size: 10px;
      color: #91A5AA;
      font-family: 'JetBrains Mono', monospace;
      pointer-events: none;
    }}
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div id="viewer-container">
    <div class="ui-top-bar">
      <div class="mol-badge">
        <div class="mol-badge-sub">{title_label} · CID {target_mol.pubchem_cid} · PDB {target_mol.target.pdb_id}</div>
        <div class="mol-badge-title">{disp_name} <span style="font-weight:400; font-size:11.5px; color:#91A5AA; font-family:'JetBrains Mono',monospace;">({target_mol.formula} · {target_mol.molecular_weight:.1f} g/mol)</span></div>
      </div>
      <div class="controls-overlay">
        <button id="btn-mode-stick" class="btn-ctrl active" onclick="setMode('stick')">{ballstick_btn}</button>
        <button id="btn-mode-vdW" class="btn-ctrl" onclick="setMode('vdw')">{spacefill_btn}</button>
        <button id="btn-mode-2d" class="btn-ctrl" onclick="setMode('2d')">{view2d_btn}</button>
        <button class="btn-ctrl" onclick="resetCamera()">{reset_btn}</button>
      </div>
    </div>

    <!-- Qgen 2D Skeletal Structure + Multiparameter Radar Overlay -->
    <div id="overlay-2d">
      <div class="panel-2d-box">
        <div class="panel-2d-label">2D SKELETAL TOPOLOGY · {target_mol.formula}</div>
        <svg id="svg-2d-graph" viewBox="-160 -130 320 260" style="width:100%; height:100%; max-height:310px;"></svg>
      </div>
      <div class="panel-2d-box">
        <div class="panel-2d-label">PHYSICOCHEMICAL RADAR · {target_mol.target.gene_symbol}</div>
        <svg id="svg-radar" viewBox="-120 -120 240 240" style="width:100%; height:100%; max-height:280px;"></svg>
      </div>
    </div>

    <div class="ui-bottom-bar">
      <div id="inspector-box" class="atom-inspector">
        <div id="inspector-name" class="inspector-title">
          <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#36D6B0;"></span>
          {disp_name}
        </div>
        <div id="inspector-text" class="inspector-desc">{hover_hint}</div>
      </div>
      <div class="hint-chip">{rotate_hint}</div>
    </div>
  </div>

  <script>
    (function() {{
      const container = document.getElementById('viewer-container');
      const overlay2d = document.getElementById('overlay-2d');
      const width = container.clientWidth || window.innerWidth;
      const height = {height};

      const atomsData = {atoms_json};
      const bondsData = {bonds_json};

      // Centering offset
      let cx = 0, cy = 0, cz = 0;
      atomsData.forEach(a => {{ cx += a.x; cy += a.y; cz += a.z; }});
      cx /= Math.max(1, atomsData.length);
      cy /= Math.max(1, atomsData.length);
      cz /= Math.max(1, atomsData.length);

      // Build 2D SVG Graph & Radar
      function render2DAndRadar() {{
        const svg2d = document.getElementById('svg-2d-graph');
        if (svg2d) {{
          let maxSpan = 1;
          atomsData.forEach(a => {{
            maxSpan = Math.max(maxSpan, Math.abs(a.x - cx), Math.abs(a.y - cy));
          }});
          const scale = 105 / (maxSpan + 0.8);
          let html = '';
          bondsData.forEach(b => {{
            const a1 = atomsData[b.a1];
            const a2 = atomsData[b.a2];
            if (!a1 || !a2) return;
            const x1 = (a1.x - cx) * scale;
            const y1 = -(a1.y - cy) * scale;
            const x2 = (a2.x - cx) * scale;
            const y2 = -(a2.y - cy) * scale;
            html += `<line x1="${{x1}}" y1="${{y1}}" x2="${{x2}}" y2="${{y2}}" stroke="#36D6B0" stroke-width="${{b.order > 1 ? 2.8 : 1.8}}" stroke-opacity="0.78" />`;
          }});
          atomsData.forEach(a => {{
            const x = (a.x - cx) * scale;
            const y = -(a.y - cy) * scale;
            html += `<circle cx="${{x}}" cy="${{y}}" r="9" fill="#111B20" stroke="${{a.color}}" stroke-width="2" />`;
            html += `<text x="${{x}}" y="${{y + 3.5}}" text-anchor="middle" fill="${{a.color}}" font-family="JetBrains Mono, monospace" font-size="8.5" font-weight="700">${{a.el}}</text>`;
          }});
          svg2d.innerHTML = html;
        }}

        const svgRadar = document.getElementById('svg-radar');
        if (svgRadar) {{
          const axes = [
            {{ label: 'MW', val: Math.min(1, {target_mol.molecular_weight} / 700) }},
            {{ label: 'Atoms', val: Math.min(1, atomsData.length / 32) }},
            {{ label: 'Bonds', val: Math.min(1, bondsData.length / 34) }},
            {{ label: 'Polarity', val: Math.min(1, atomsData.filter(a => a.el !== 'C' && a.el !== 'H').length / 10) }},
            {{ label: 'Pocket', val: Math.min(1, {len(target_mol.target.key_residues)} / 5) }}
          ];
          const R = 78;
          let rHtml = '';
          [0.33, 0.66, 1.0].forEach(level => {{
            let pts = [];
            axes.forEach((_, idx) => {{
              const ang = -Math.PI / 2 + (idx * 2 * Math.PI) / axes.length;
              pts.push(`${{(Math.cos(ang) * R * level).toFixed(1)}},${{(Math.sin(ang) * R * level).toFixed(1)}}`);
            }});
            rHtml += `<polygon points="${{pts.join(' ')}}" fill="none" stroke="#263940" stroke-width="1" />`;
          }});
          let dataPts = [];
          axes.forEach((ax, idx) => {{
            const ang = -Math.PI / 2 + (idx * 2 * Math.PI) / axes.length;
            const xEnd = Math.cos(ang) * R;
            const yEnd = Math.sin(ang) * R;
            rHtml += `<line x1="0" y1="0" x2="${{xEnd.toFixed(1)}}" y2="${{yEnd.toFixed(1)}}" stroke="#263940" stroke-width="1" />`;
            const lx = Math.cos(ang) * (R + 22);
            const ly = Math.sin(ang) * (R + 18);
            rHtml += `<text x="${{lx.toFixed(1)}}" y="${{ly.toFixed(1)}}" text-anchor="middle" fill="#91A5AA" font-family="JetBrains Mono, monospace" font-size="8.5">${{ax.label}}</text>`;
            const vx = Math.cos(ang) * R * Math.max(0.2, ax.val);
            const vy = Math.sin(ang) * R * Math.max(0.2, ax.val);
            dataPts.push(`${{vx.toFixed(1)}},${{vy.toFixed(1)}}`);
          }});
          rHtml += `<polygon points="${{dataPts.join(' ')}}" fill="rgba(54, 214, 176, 0.22)" stroke="#36D6B0" stroke-width="2" />`;
          dataPts.forEach(pt => {{
            const [px, py] = pt.split(',');
            rHtml += `<circle cx="${{px}}" cy="${{py}}" r="3.5" fill="#67B7D1" stroke="#0B1114" stroke-width="1" />`;
          }});
          svgRadar.innerHTML = rHtml;
        }}
      }}
      render2DAndRadar();

      if (typeof THREE === 'undefined') return;

      // 1. Scene & Camera
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 1000);
      camera.position.set(0, 0, 15.5);

      const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(renderer.domElement);

      const controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.06;
      controls.rotateSpeed = 0.85;
      controls.zoomSpeed = 1.0;
      controls.minDistance = 4;
      controls.maxDistance = 38;

      // 2. Lighting (Bioluminescent studio lighting)
      scene.add(new THREE.AmbientLight(0xEAF2F2, 0.72));
      const dirLight1 = new THREE.DirectionalLight(0xFFFFFF, 0.90);
      dirLight1.position.set(12, 18, 15);
      scene.add(dirLight1);

      const dirLight2 = new THREE.DirectionalLight(0x36D6B0, 0.45);
      dirLight2.position.set(-15, -12, -10);
      scene.add(dirLight2);

      const molGroup = new THREE.Group();
      scene.add(molGroup);

      const atomMeshes = [];
      const bondMeshes = [];

      const sphereGeo = new THREE.SphereGeometry(1, 32, 32);
      const cylGeo = new THREE.CylinderGeometry(0.11, 0.11, 1, 16);
      const bondMat = new THREE.MeshPhongMaterial({{ color: 0x67B7D1, shininess: 55, specular: 0x36D6B0 }});

      atomsData.forEach((a) => {{
        const mat = new THREE.MeshPhongMaterial({{
          color: a.color,
          shininess: 80,
          specular: 0xEAF2F2
        }});
        const mesh = new THREE.Mesh(sphereGeo, mat);
        mesh.position.set(a.x - cx, a.y - cy, a.z - cz);
        mesh.scale.setScalar(a.radius * 0.92);
        mesh.userData = {{ atom: a, origScale: a.radius * 0.92, origColor: a.color }};
        molGroup.add(mesh);
        atomMeshes.push(mesh);
      }});

      bondsData.forEach(b => {{
        const a1 = atomsData[b.a1];
        const a2 = atomsData[b.a2];
        if (!a1 || !a2) return;
        const v1 = new THREE.Vector3(a1.x - cx, a1.y - cy, a1.z - cz);
        const v2 = new THREE.Vector3(a2.x - cx, a2.y - cy, a2.z - cz);
        const distance = v1.distanceTo(v2);
        const mesh = new THREE.Mesh(cylGeo, bondMat);
        mesh.position.copy(v1.clone().add(v2).multiplyScalar(0.5));
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), v2.clone().sub(v1).normalize());
        mesh.scale.set(1, distance, 1);
        molGroup.add(mesh);
        bondMeshes.push(mesh);
      }});

      window.setMode = function(mode) {{
        document.getElementById('btn-mode-stick').classList.toggle('active', mode === 'stick');
        document.getElementById('btn-mode-vdW').classList.toggle('active', mode === 'vdw');
        const btn2d = document.getElementById('btn-mode-2d');
        if (btn2d) btn2d.classList.toggle('active', mode === '2d');

        if (mode === '2d') {{
          overlay2d.classList.add('visible');
          return;
        }}
        overlay2d.classList.remove('visible');

        atomMeshes.forEach(m => {{
          const mult = mode === 'vdw' ? 2.35 : 0.92;
          const s = m.userData.atom.radius * mult;
          m.scale.set(s, s, s);
          m.userData.origScale = s;
        }});
        bondMeshes.forEach(b => {{
          b.visible = (mode === 'stick');
        }});
      }};

      window.resetCamera = function() {{
        overlay2d.classList.remove('visible');
        window.setMode('stick');
        camera.position.set(0, 0, 15.5);
        controls.target.set(0, 0, 0);
        controls.reset();
      }};

      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2(-999, -999);
      let hoveredMesh = null;

      function onMouseMove(e) {{
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      }}

      renderer.domElement.addEventListener('mousemove', onMouseMove);
      renderer.domElement.addEventListener('pointerdown', onMouseMove);

      const inspName = document.getElementById('inspector-name');
      const inspText = document.getElementById('inspector-text');

      function updateRaycaster() {{
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(atomMeshes);

        if (intersects.length > 0) {{
          const hit = intersects[0].object;
          if (hoveredMesh !== hit) {{
            if (hoveredMesh) {{
              hoveredMesh.scale.setScalar(hoveredMesh.userData.origScale);
              hoveredMesh.material.emissive.setHex(0x000000);
            }}
            hoveredMesh = hit;
            hoveredMesh.scale.setScalar(hoveredMesh.userData.origScale * 1.25);
            hoveredMesh.material.emissive.setHex(0x1E4D40);

            const a = hoveredMesh.userData.atom;
            inspName.innerHTML = `<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${{a.color}};"></span> ${{a.label}} (${{a.el}})`;
            inspText.innerText = a.role || "Структурный каркас фармакофора";
          }}
        }} else if (hoveredMesh) {{
          hoveredMesh.scale.setScalar(hoveredMesh.userData.origScale);
          hoveredMesh.material.emissive.setHex(0x000000);
          hoveredMesh = null;
          inspName.innerHTML = `<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#36D6B0;"></span> {disp_name}`;
          inspText.innerText = "{hover_hint}";
        }}
      }}

      const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

      function animate() {{
        requestAnimationFrame(animate);
        controls.update();
        if (!reducedMotion && (!controls.state || controls.state === -1)) {{
          molGroup.rotation.y += 0.0022;
        }}
        updateRaycaster();
        renderer.render(scene, camera);
      }}

      animate();

      window.addEventListener('resize', () => {{
        const newW = container.clientWidth || window.innerWidth;
        camera.aspect = newW / height;
        camera.updateProjectionMatrix();
        renderer.setSize(newW, height);
      }});
    }})();
  </script>
</body>
</html>
"""


def render_mechanism_animation_html(
    mol_a: VerifiedMolecule,
    mol_b: VerifiedMolecule,
    lang: str = "ru",
    height: int = 540
) -> str:
    """Генерирует интерактивную доказательную анимацию каскада 'Препарат -> Мишень -> Эффект' в теме Qgen."""
    steps_a = mol_a.mechanism_cascade
    steps_b = mol_b.mechanism_cascade

    title_a = mol_a.display_names.get(lang, mol_a.canonical_inn.title())
    title_b = mol_b.display_names.get(lang, mol_b.canonical_inn.title())

    header_title = "ДОКАЗАТЕЛЬНЫЙ ФАРМАКОДИНАМИЧЕСКИЙ КАСКАД" if lang == "ru" else ("ДӘЛЕЛДІ ФАРМАКОДИНАМИКАЛЫҚ КАСКАД" if lang == "kk" else "EVIDENCE-BASED PHARMACODYNAMIC CASCADE")
    target_label = "Биологическая мишень" if lang == "ru" else ("Биологиялық нысана" if lang == "kk" else "Biological Target")
    pocket_label = "Сайт связывания" if lang == "ru" else ("Байланысу сайты" if lang == "kk" else "Binding Pocket")
    residues_label = "Ключевые остатки" if lang == "ru" else ("Негізгі қалдықтар" if lang == "kk" else "Key Residues")
    play_btn = "Воспроизвести каскад" if lang == "ru" else ("Каскадты ойнату" if lang == "kk" else "Play Cascade")
    pause_btn = "Пауза" if lang == "ru" else ("Кідірту" if lang == "kk" else "Pause")
    reset_btn = "В начало" if lang == "ru" else ("Басына" if lang == "kk" else "Reset")
    step_btn = "Следующий этап" if lang == "ru" else ("Келесі кезең" if lang == "kk" else "Step Forward")

    stages_data = []
    max_steps = max(len(steps_a), len(steps_b))
    for i in range(max_steps):
        s_a = steps_a[i] if i < len(steps_a) else steps_a[-1]
        s_b = steps_b[i] if i < len(steps_b) else steps_b[-1]
        stages_data.append({
            "idx": i + 1,
            "title_a": s_a.get(f"title_{lang}", s_a.get("title_ru", "")),
            "desc_a": s_a.get(f"desc_{lang}", s_a.get("desc_ru", "")),
            "title_b": s_b.get(f"title_{lang}", s_b.get("title_ru", "")),
            "desc_b": s_b.get(f"desc_{lang}", s_b.get("desc_ru", "")),
        })

    stages_json = json.dumps(stages_data)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body, html {{
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: 'Inter', -apple-system, sans-serif;
      background: #0B1114;
      color: #EAF2F2;
    }}
    .cascade-root {{
      width: 100%;
      height: {height}px;
      display: flex;
      flex-direction: column;
      border: 1px solid #263940;
      border-radius: 8px;
      background: #111B20;
      overflow: hidden;
    }}
    .cascade-header {{
      padding: 10px 16px;
      background: #17252B;
      border-bottom: 1px solid #263940;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .cascade-title {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #36D6B0;
    }}
    .cascade-controls {{
      display: flex;
      gap: 6px;
      align-items: center;
    }}
    .btn-act {{
      background: #111B20;
      border: 1px solid #263940;
      color: #EAF2F2;
      font-size: 11px;
      font-weight: 600;
      padding: 5px 11px;
      border-radius: 5px;
      cursor: pointer;
      transition: transform 0.15s ease, background 0.15s ease;
    }}
    .btn-act:hover {{
      border-color: #36D6B0;
      color: #36D6B0;
    }}
    .btn-act.primary {{
      background: #36D6B0;
      color: #0B1114;
      border-color: #36D6B0;
      font-weight: 700;
    }}

    .timeline-nav {{
      display: flex;
      background: #0B1114;
      border-bottom: 1px solid #263940;
      padding: 7px 16px;
      gap: 8px;
      overflow-x: auto;
    }}
    .step-pill {{
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      background: #17252B;
      border: 1px solid #263940;
      color: #91A5AA;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.18s ease;
    }}
    .step-pill.active {{
      background: rgba(54, 214, 176, 0.16);
      color: #36D6B0;
      border-color: #36D6B0;
    }}

    .cascade-content {{
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      padding: 16px;
      overflow-y: auto;
    }}
    @media (max-width: 640px) {{
      .cascade-content {{ grid-template-columns: 1fr; }}
    }}

    .track-col {{
      background: #17252B;
      border: 1px solid #263940;
      border-radius: 6px;
      padding: 14px;
      display: flex;
      flex-direction: column;
    }}
    .track-head {{
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 1px solid #263940;
      padding-bottom: 10px;
      margin-bottom: 12px;
    }}
    .track-drug {{
      font-size: 14px;
      font-weight: 700;
      color: #36D6B0;
    }}
    .target-box {{
      background: #111B20;
      border: 1px solid #263940;
      border-left: 3px solid #36D6B0;
      padding: 8px 10px;
      border-radius: 4px;
      font-size: 11px;
      margin-bottom: 12px;
      color: #EAF2F2;
    }}
    .stage-card {{
      background: #0B1114;
      border: 1px solid #263940;
      border-radius: 6px;
      padding: 12px;
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .stage-title {{
      font-size: 13px;
      font-weight: 700;
      color: #EAF2F2;
      margin-bottom: 6px;
    }}
    .stage-desc {{
      font-size: 12px;
      color: #91A5AA;
      line-height: 1.55;
    }}
    .signal-beam {{
      height: 3px;
      width: 100%;
      background: #17252B;
      border-radius: 2px;
      margin-top: 12px;
      overflow: hidden;
    }}
    .signal-pulse {{
      height: 100%;
      width: 35%;
      background: #36D6B0;
      border-radius: 2px;
      animation: pulseMove 1.8s infinite ease-in-out;
    }}
    @keyframes pulseMove {{
      0% {{ transform: translateX(-100%); }}
      100% {{ transform: translateX(350%); }}
    }}
  </style>
</head>
<body>
  <div class="cascade-root">
    <div class="cascade-header">
      <div class="cascade-title">{header_title}</div>
      <div class="cascade-controls">
        <button id="btn-play" class="btn-act primary" onclick="togglePlay()">{play_btn}</button>
        <button class="btn-act" onclick="stepForward()">{step_btn}</button>
        <button class="btn-act" onclick="resetCascade()">{reset_btn}</button>
      </div>
    </div>

    <div class="timeline-nav" id="timeline-pills"></div>

    <div class="cascade-content">
      <div class="track-col">
        <div class="track-head">
          <div style="width:9px; height:9px; border-radius:50%; background:#36D6B0;"></div>
          <div class="track-drug">{title_a}</div>
        </div>
        <div class="target-box">
          <div><b>{target_label}:</b> {mol_a.target.protein_name} ({mol_a.target.gene_symbol}, PDB: {mol_a.target.pdb_id})</div>
          <div style="margin-top:3px; color:#91A5AA;"><b>{pocket_label}:</b> {mol_a.target.binding_pocket}</div>
          <div style="margin-top:3px; color:#91A5AA;"><b>{residues_label}:</b> {", ".join(mol_a.target.key_residues)}</div>
        </div>
        <div class="stage-card">
          <div id="step-title-a" class="stage-title"></div>
          <div id="step-desc-a" class="stage-desc"></div>
          <div class="signal-beam"><div class="signal-pulse"></div></div>
        </div>
      </div>

      <div class="track-col">
        <div class="track-head">
          <div style="width:9px; height:9px; border-radius:50%; background:#67B7D1;"></div>
          <div class="track-drug" style="color:#67B7D1;">{title_b}</div>
        </div>
        <div class="target-box" style="border-left-color:#67B7D1;">
          <div><b>{target_label}:</b> {mol_b.target.protein_name} ({mol_b.target.gene_symbol}, PDB: {mol_b.target.pdb_id})</div>
          <div style="margin-top:3px; color:#91A5AA;"><b>{pocket_label}:</b> {mol_b.target.binding_pocket}</div>
          <div style="margin-top:3px; color:#91A5AA;"><b>{residues_label}:</b> {", ".join(mol_b.target.key_residues)}</div>
        </div>
        <div class="stage-card">
          <div id="step-title-b" class="stage-title"></div>
          <div id="step-desc-b" class="stage-desc"></div>
          <div class="signal-beam"><div class="signal-pulse" style="background:#67B7D1;"></div></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    (function() {{
      const stages = {stages_json};
      let curStageIdx = 0;
      let isPlaying = false;
      let timer = null;

      const pillsContainer = document.getElementById('timeline-pills');
      const titleA = document.getElementById('step-title-a');
      const descA = document.getElementById('step-desc-a');
      const titleB = document.getElementById('step-title-b');
      const descB = document.getElementById('step-desc-b');
      const playBtn = document.getElementById('btn-play');

      stages.forEach((s, idx) => {{
        const btn = document.createElement('button');
        btn.className = 'step-pill' + (idx === 0 ? ' active' : '');
        btn.innerText = `Stage 0${{s.idx}}`;
        btn.onclick = () => setStage(idx);
        pillsContainer.appendChild(btn);
      }});

      function updateUI() {{
        const s = stages[curStageIdx];
        titleA.innerText = s.title_a;
        descA.innerText = s.desc_a;
        titleB.innerText = s.title_b;
        descB.innerText = s.desc_b;

        const pills = pillsContainer.querySelectorAll('.step-pill');
        pills.forEach((p, idx) => {{
          p.classList.toggle('active', idx === curStageIdx);
        }});
      }}

      window.setStage = function(idx) {{
        curStageIdx = idx;
        updateUI();
      }};

      window.stepForward = function() {{
        curStageIdx = (curStageIdx + 1) % stages.length;
        updateUI();
      }};

      window.resetCascade = function() {{
        curStageIdx = 0;
        updateUI();
        if (isPlaying) togglePlay();
      }};

      window.togglePlay = function() {{
        isPlaying = !isPlaying;
        playBtn.innerText = isPlaying ? "{pause_btn}" : "{play_btn}";
        playBtn.classList.toggle('primary', !isPlaying);

        if (isPlaying) {{
          timer = setInterval(() => {{
            curStageIdx = (curStageIdx + 1) % stages.length;
            updateUI();
          }}, 2800);
        }} else {{
          if (timer) clearInterval(timer);
        }}
      }};

      updateUI();
    }})();
  </script>
</body>
</html>
"""


def render_convergence_visualization_html(
    mol_a: VerifiedMolecule,
    mol_b: VerifiedMolecule,
    lang: str = "ru",
    height: int = 560
) -> str:
    """Генерирует визуализацию конвергенции независимых фармакологических путей на конечном исходе."""
    name_a = mol_a.display_names.get(lang, mol_a.canonical_inn.title())
    name_b = mol_b.display_names.get(lang, mol_b.canonical_inn.title())

    header = "КОНВЕРГЕНЦИЯ МЕХАНИЗМОВ И КЛИНИЧЕСКИЙ ИСХОД" if lang == "ru" else ("МЕХАНИЗМДЕР КОНВЕРГЕНЦИЯСЫ ЖӘНЕ КЛИНИКАЛЫҚ НӘТИЖЕ" if lang == "kk" else "MECHANISTIC CONVERGENCE & CLINICAL OUTCOME")
    no_collision_note = "Внимание: Взаимодействие НЕ обусловлено прямым молекулярным столкновением в кровотоке. Препараты действуют на разные физиологические мишени, конвергируя на итоговом функциональном ответе." if lang == "ru" else ("Назар аударыңыз: Өзара әрекеттесу қан ағымындағы тікелей молекулалық соқтығысудан туындамайды. Дәрілер әртүрлі физиологиялық нысаналарға әсер етіп, соңғы функционалдық жауапта тоғысады." if lang == "kk" else "Note: Interaction does NOT arise from direct molecular collision. Drugs engage independent biological targets, converging downstream upon physiological function.")
    mitigation_title = "Клинический регламент мониторинга:" if lang == "ru" else ("Клиникалық мониторинг регламенті:" if lang == "kk" else "Clinical Monitoring Protocol:")
    mitigation_text = "1. Регулярный лабораторный и клинический мониторинг (MHO/INR, креатинин, калий, ЭКГ по показаниям). 2. Оценка гастропротекции и функции почек. 3. Информирование пациента о ранних симптомах декомпенсации. 4. Категорический запрет на самостоятельную отмену назначенных препаратов без согласования с лечащим врачом." if lang == "ru" else ("1. Тұрақты зертханалық және клиникалық бақылау (ХҚҚ/INR, креатинин, калий). 2. Асқазан мен бүйрек қызметін бағалау. 3. Науқасқа ерте белгілер туралы ескерту. 4. Тағайындалған дәрілерді дәрігермен келіспей өз бетінше тоқтатуға қатаң тыйым салу." if lang == "kk" else "1. Rigorous laboratory monitoring (INR, serum creatinine, electrolytes as indicated). 2. Organ-specific protective measures. 3. Patient education regarding early warning signs. 4. Never abruptly discontinue prescribed therapy without physician consultation.")

    step_a_final = mol_a.mechanism_cascade[-1] if mol_a.mechanism_cascade else {}
    step_b_final = mol_b.mechanism_cascade[-1] if mol_b.mechanism_cascade else {}
    title_branch_a = step_a_final.get(f"title_{lang}", step_a_final.get("title_ru", mol_a.target.protein_name))
    desc_branch_a = step_a_final.get(f"desc_{lang}", step_a_final.get("desc_ru", ""))
    title_branch_b = step_b_final.get(f"title_{lang}", step_b_final.get("title_ru", mol_b.target.protein_name))
    desc_branch_b = step_b_final.get(f"desc_{lang}", step_b_final.get("desc_ru", ""))

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body, html {{
      width: 100%;
      height: 100%;
      font-family: 'Inter', -apple-system, sans-serif;
      background: #0B1114;
      color: #EAF2F2;
      overflow-x: hidden;
    }}
    .conv-root {{
      width: 100%;
      border: 1px solid #263940;
      border-radius: 8px;
      background: #111B20;
      padding: 18px;
    }}
    .conv-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #263940;
      padding-bottom: 12px;
      margin-bottom: 14px;
    }}
    .conv-title {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #36D6B0;
    }}
    .no-collision-banner {{
      background: #17252B;
      border: 1px solid #263940;
      border-left: 3px solid #36D6B0;
      padding: 9px 12px;
      border-radius: 6px;
      font-size: 11.5px;
      color: #EAF2F2;
      line-height: 1.45;
      margin-bottom: 16px;
    }}
    .tree-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    @media (max-width: 640px) {{
      .tree-grid {{ grid-template-columns: 1fr; }}
    }}
    .branch-card {{
      background: #17252B;
      border: 1px solid #263940;
      border-radius: 6px;
      padding: 14px;
    }}
    .branch-tag {{
      display: inline-block;
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: 2px 8px;
      border-radius: 4px;
      margin-bottom: 8px;
    }}
    .tag-a {{ background: rgba(54, 214, 176, 0.14); color: #36D6B0; border: 1px solid rgba(54, 214, 176, 0.35); }}
    .tag-b {{ background: rgba(103, 183, 209, 0.14); color: #67B7D1; border: 1px solid rgba(103, 183, 209, 0.35); }}
    .branch-title {{
      font-size: 13px;
      font-weight: 700;
      color: #EAF2F2;
      margin-bottom: 6px;
    }}
    .branch-desc {{
      font-size: 11.5px;
      color: #91A5AA;
      line-height: 1.5;
    }}
    .convergence-hub {{
      margin-top: 16px;
      background: rgba(244, 63, 94, 0.08);
      border: 1px solid rgba(244, 63, 94, 0.35);
      border-left: 4px solid #F43F5E;
      border-radius: 6px;
      padding: 14px 16px;
    }}
    .hub-title {{
      font-size: 13px;
      font-weight: 700;
      color: #F43F5E;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .mitigation-box {{
      margin-top: 14px;
      background: #17252B;
      border: 1px solid #263940;
      border-left: 3px solid #67B7D1;
      border-radius: 6px;
      padding: 12px 14px;
      font-size: 11.5px;
      color: #EAF2F2;
      line-height: 1.55;
    }}
  </style>
</head>
<body>
  <div class="conv-root">
    <div class="conv-header">
      <div class="conv-title">{header}</div>
      <div style="font-size:11px; font-weight:600; color:#67B7D1; font-family:'JetBrains Mono',monospace;">{mol_a.target.gene_symbol} × {mol_b.target.gene_symbol}</div>
    </div>

    <div class="no-collision-banner">
      <b>{no_collision_note}</b>
    </div>

    <div class="tree-grid">
      <div class="branch-card" style="border-top:3px solid #36D6B0;">
        <span class="branch-tag tag-a">{name_a} · {mol_a.target.gene_symbol} (PDB {mol_a.target.pdb_id})</span>
        <div class="branch-title">{title_branch_a}</div>
        <div class="branch-desc">{desc_branch_a}</div>
      </div>

      <div class="branch-card" style="border-top:3px solid #67B7D1;">
        <span class="branch-tag tag-b">{name_b} · {mol_b.target.gene_symbol} (PDB {mol_b.target.pdb_id})</span>
        <div class="branch-title">{title_branch_b}</div>
        <div class="branch-desc">{desc_branch_b}</div>
      </div>
    </div>

    <div class="convergence-hub">
      <div class="hub-title">
        <span style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#F43F5E; background:rgba(244, 63, 94, 0.16); padding:2px 7px; border-radius:4px;">CONVERGENCE</span>
        {name_a} + {name_b} ({mol_a.target.gene_symbol} / {mol_b.target.gene_symbol})
      </div>
      <div style="font-size:11.5px; color:#EAF2F2; margin-top:6px; line-height:1.5;">
        Системное наложение фармакодинамических и фармакокинетических эффектов на уровне органов-мишеней ({mol_a.target.protein_name} и {mol_b.target.protein_name}) усиливает итоговый клинический отклик.
      </div>
    </div>

    <div class="mitigation-box">
      <div style="font-weight:700; color:#36D6B0; margin-bottom:4px;">{mitigation_title}</div>
      <div style="color:#91A5AA;">{mitigation_text}</div>
    </div>
  </div>
</body>
</html>
"""
