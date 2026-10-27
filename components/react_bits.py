"""Модуль визуальных эффектов Pharma Sentinel — Clinical Sage.

Компоненты:
1. <TechText /> — интерактивный заголовок в эстетике Clinical Sage (темный текст #26332D, медицинский зелёный акцент #315E50).
2. <MolecularNetwork /> — утонченный, низкоконтрастный фон молекулярной сети в тонах Clinical Sage (#315E50, #789483) на фоне #F3F6F2.
3. <AnimatedContent /> — плавный переход карточек и контента при навигации и обновлении данных в Streamlit.

Архитектура:
- Постоянный фоновый слой и наблюдатель переходов инжектируются один раз в `window.parent.document.head`,
  благодаря чему анимация никогда не сбрасывается, не мигает и не дублируется при переходах между страницами в Streamlit.
- `pointer-events: none` гарантирует отсутствие любых помех для кликов, ввода текста, прокрутки и выбора препаратов.
- Полная поддержка `prefers-reduced-motion` и оптимизация энергопотребления (idle при скрытой вкладке).
"""


def render_tech_text_and_effects_html(
    text: str = "PHARMA SENTINEL",
    subtitle: str = "КЛИНИЧЕСКАЯ ФАРМАКОЛОГИЯ · DDINTER v2024.11",
    height: int = 74,
) -> str:
    """Рендерит заголовок <TechText /> и обеспечивает фоновую молекулярную сеть в window.parent."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&family=JetBrains+Mono:wght@500&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 100%;
    height: {height}px;
    overflow: hidden;
    background: transparent;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }}

  .header-shell {{
    position: relative;
    width: 100%;
    height: {height}px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    user-select: none;
  }}

  .tech-text {{
    position: relative;
    width: 100%;
    height: 48px;
    touch-action: pan-y;
    user-select: none;
  }}

  .tech-text-canvas {{
    display: block;
    width: 100%;
    height: 100%;
  }}

  .header-sub {{
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #65736A;
    padding-left: 2px;
    margin-top: -2px;
    pointer-events: none;
  }}
</style>
</head>
<body>
  <div class="header-shell">
    <div id="tech-text-root" class="tech-text" role="img" aria-label="{text}">
      <canvas id="tech-text-canvas" class="tech-text-canvas"></canvas>
    </div>
    <div id="tech-text-sub" class="header-sub">{subtitle}</div>
  </div>

<script>
/* ==========================================================================
   1. <TechText /> — Интерактивный заголовок (Палитра Clinical Sage)
   ========================================================================== */
(function initTechText() {{
  const container = document.getElementById('tech-text-root');
  const canvas = document.getElementById('tech-text-canvas');
  if (!container || !canvas) return;
  const ctx = canvas.getContext('2d');
  const scratch = document.createElement('canvas');
  const scratchCtx = scratch.getContext('2d');
  if (!ctx || !scratchCtx) return;

  const LABEL_FONT = '9px "JetBrains Mono", ui-monospace, SFMono-Regular, monospace';
  const SPRING = 340;
  const INHERIT = /^(currentcolor|inherit)$/i;
  const KICK_DECAY = 0.6;

  const settings = {{
    text: {text!r},
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    fontWeight: 600,
    fontSize: 32,
    letterSpacing: -0.03,
    color: '#26332D',
    accentColor: '#315E50',
    align: 'left',
    reach: 180,
    softness: 0.7,
    dashLength: 4,
    dashGap: 2,
    strokeWidth: 1.5,
    lineStyle: 'dashed',
    reveal: 'letter',
    specks: 10,
    selection: true,
    labels: true,
    draggable: true,
    bounce: 0.35,
    sweep: true,
    speed: 0.8,
    clickKick: true,
    intro: 'none'
  }};

  const approach = (current, target, dt, seconds) =>
    current + (target - current) * (1 - Math.exp(-dt / seconds));
  const clamp01 = value => Math.min(1, Math.max(0, Number(value) || 0));
  const noise = (...values) => {{
    let h = 2166136261;
    for (const value of values) {{
      h = Math.imul(h ^ (value | 0), 16777619);
      h ^= h >>> 13;
      h = Math.imul(h, 0x5bd1e995);
      h ^= h >>> 15;
    }}
    return (h >>> 0) / 4294967296;
  }};
  const signed = value => (value > 0 ? `+${{value}}` : value < 0 ? `−${{-value}}` : '0');

  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;
  let width = 1;
  let height = 1;
  let dpr = 1;
  let raf = 0;
  let last = performance.now();
  let visible = true;
  let alive = true;
  let layoutKey = '';
  let word = null;
  let glyphs = [];
  let clock = 0;
  let pulse = 0;
  let placed = false;
  let dragging = -1;
  let cursor = '';
  const kicks = [];
  const press = {{ x: 0, y: 0, time: 0, index: -1 }};
  const pointer = {{ x: 0, y: 0, inside: false }};
  const grab = {{ x: 0, y: 0 }};
  const lens = {{ x: 0, y: 0 }};
  const frame = {{ x1: 0, y1: 0, x2: 0, y2: 0, alpha: 0, index: -1 }};

  const family = s => s.fontFamily || getComputedStyle(container).fontFamily || 'sans-serif';
  const fontFor = (s, size) => `${{s.fontWeight}} ${{size}}px ${{family(s)}}`;
  const palette = s => {{
    const current = getComputedStyle(container).color || '#26332D';
    const pick = value => (!value || INHERIT.test(String(value).trim()) ? current : value);
    return {{ ink: pick(s.color), accent: pick(s.accentColor) }};
  }};
  const setFont = (target, s, size) => {{
    target.font = fontFor(s, size);
    if ('letterSpacing' in target) target.letterSpacing = `${{s.letterSpacing * size}}px`;
    target.textAlign = 'left';
    target.textBaseline = 'alphabetic';
  }};

  const sprite = (s, view, glyph, stroke, ink) => {{
    const pad = Math.ceil(s.strokeWidth * 2 + 4);
    const left = glyph.box.x1 - pad;
    const top = glyph.box.y1 - pad;
    const w = glyph.box.x2 - glyph.box.x1 + pad * 2;
    const h = glyph.box.y2 - glyph.box.y1 + pad * 2;
    const image = document.createElement('canvas');
    image.width = Math.max(1, Math.ceil(w * dpr));
    image.height = Math.max(1, Math.ceil(h * dpr));
    const c = image.getContext('2d');
    if (!c) return {{ image, left, top }};
    c.setTransform(dpr, 0, 0, dpr, -left * dpr, -top * dpr);
    setFont(c, s, view.size);
    if (stroke) {{
      c.lineJoin = 'round';
      c.lineWidth = s.strokeWidth * 2;
      c.lineCap = 'butt';
      c.strokeStyle = s.accentColor || ink;
      if (s.lineStyle !== 'solid') c.setLineDash([Math.max(1, s.dashLength), Math.max(1, s.dashGap)]);
      c.strokeText(glyph.char, glyph.x, view.baseline);
      c.setLineDash([]);
      c.globalCompositeOperation = 'destination-out';
      c.fillStyle = '#000000';
      c.fillText(glyph.char, glyph.x, view.baseline);
      c.globalCompositeOperation = 'source-over';
    }} else {{
      c.fillStyle = ink;
      c.fillText(glyph.char, glyph.x, view.baseline);
    }}
    return {{ image, left, top }};
  }};

  const ensureLayout = (s, ink) => {{
    const key = [
      s.text, family(s), s.fontWeight, s.fontSize, s.letterSpacing,
      s.align, ink, s.dashLength, s.dashGap, s.strokeWidth, s.lineStyle,
      width, height, dpr
    ].join('|');
    if (key === layoutKey && word) return word;
    layoutKey = key;

    const probe = scratchCtx;
    setFont(probe, s, s.fontSize);
    let m = probe.measureText(s.text);
    const fit = Math.min(
      1,
      (width * 0.96) / Math.max(m.actualBoundingBoxLeft + m.actualBoundingBoxRight, 1),
      (height * 0.72) / Math.max(m.actualBoundingBoxAscent + m.actualBoundingBoxDescent, 1)
    );
    const size = s.fontSize * fit;
    setFont(probe, s, size);
    m = probe.measureText(s.text);
    const inkHeight = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
    const start = 2;
    const x = start + m.actualBoundingBoxLeft;
    const baseline = (height - inkHeight) / 2 + m.actualBoundingBoxAscent + 3;
    const top = baseline - m.actualBoundingBoxAscent;
    const bottom = baseline + m.actualBoundingBoxDescent;
    const next = {{
      size, baseline,
      left: x - m.actualBoundingBoxLeft,
      right: x + m.actualBoundingBoxRight,
      top, bottom
    }};
    word = next;

    const chars = Array.from(s.text);
    const previous = glyphs;
    glyphs = [];
    let prefix = '';
    chars.forEach((char, i) => {{
      prefix += char;
      const own = probe.measureText(char);
      const gx = x + probe.measureText(prefix).width - own.width;
      if (!char.trim()) return;
      const base = {{
        char, x: gx,
        box: {{
          x1: gx - own.actualBoundingBoxLeft,
          y1: baseline - own.actualBoundingBoxAscent,
          x2: gx + own.actualBoundingBoxRight,
          y2: baseline + own.actualBoundingBoxDescent
        }}
      }};
      const kept = previous[glyphs.length];
      glyphs.push({{
        ...base,
        offset: kept?.char === char ? kept.offset : {{ x: 0, y: 0 }},
        velocity: {{ x: 0, y: 0 }},
        outline: 0,
        shown: 1,
        index: i,
        fill: sprite(s, next, base, false, ink),
        dashes: sprite(s, next, base, true, ink)
      }});
    }});
    dragging = -1;
    frame.index = -1;
    return next;
  }};

  const glyphAt = (x, y) => {{
    if (!word || y < word.top - 24 || y > word.bottom + 24) return -1;
    let best = -1;
    let bestDistance = Infinity;
    glyphs.forEach((glyph, i) => {{
      const x1 = glyph.box.x1 + glyph.offset.x;
      const x2 = glyph.box.x2 + glyph.offset.x;
      const d = x < x1 ? x1 - x : x > x2 ? x - x2 : 0;
      if (d < bestDistance) {{
        bestDistance = d;
        best = i;
      }}
    }});
    return bestDistance < 28 ? best : -1;
  }};

  const blit = (target, art, dx, dy, originX, originY) => {{
    target.drawImage(
      art.image,
      Math.round((art.left + dx) * dpr - originX),
      Math.round((art.top + dy) * dpr - originY)
    );
  }};

  const crisp = value => (Math.round(value * dpr) + 0.5) / dpr;

  const drawFrame = (s, accent) => {{
    const glyph = glyphs[frame.index];
    if (!glyph || frame.alpha < 0.01) return;
    const a = frame.alpha;
    const x1 = crisp(frame.x1);
    const y1 = crisp(frame.y1);
    const x2 = crisp(frame.x2);
    const y2 = crisp(frame.y2);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = accent;
    ctx.strokeStyle = accent;
    ctx.lineWidth = 1;

    const moved = Math.hypot(glyph.offset.x, glyph.offset.y);
    if (moved > 1) {{
      const hx = (glyph.box.x1 + glyph.box.x2) / 2;
      const hy = (glyph.box.y1 + glyph.box.y2) / 2;
      ctx.beginPath();
      ctx.moveTo(hx, hy);
      ctx.lineTo(hx + glyph.offset.x, hy + glyph.offset.y);
      ctx.setLineDash([3, 4]);
      ctx.globalAlpha = 0.35 * a;
      ctx.stroke();
      ctx.setLineDash([]);
    }}

    ctx.beginPath();
    ctx.rect(x1, y1, x2 - x1, y2 - y1);
    ctx.globalAlpha = 0.3 * a;
    ctx.stroke();

    ctx.beginPath();
    for (const [cx, cy] of [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]) {{
      ctx.rect(Math.round(cx) - 2, Math.round(cy) - 2, 4, 4);
    }}
    ctx.globalAlpha = 0.8 * a;
    ctx.fill();
    ctx.globalAlpha = 1;

    if (!s.labels) return;
    ctx.font = LABEL_FONT;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillStyle = accent;
    ctx.globalAlpha = 0.8 * a;
    const label = moved > 1
      ? `${{signed(Math.round(glyph.offset.x))}}, ${{signed(Math.round(-glyph.offset.y))}}`
      : `${{glyph.char}} ${{Math.round(glyph.box.x2 - glyph.box.x1)}}×${{Math.round(glyph.box.y2 - glyph.box.y1)}}`;
    ctx.fillText(label, Math.round(frame.x2) + 6, Math.round(frame.y1));
    ctx.globalAlpha = 1;
  }};

  const kick = index => {{
    const strength = (word ? word.size : 38) * 8.0;
    kicks.push({{ index, at: pulse, velocity: strength }});
    for (let d = 1; d < glyphs.length; d++) {{
      const velocity = strength * Math.pow(KICK_DECAY, d);
      if (velocity < 20) break;
      for (const j of [index - d, index + d]) {{
        if (j >= 0 && j < glyphs.length) kicks.push({{ index: j, at: pulse + d * 0.045, velocity }});
      }}
    }}
    wake();
  }};

  const tick = now => {{
    raf = 0;
    const s = settings;
    const dt = Math.min(0.05, Math.max(0.001, (now - last) / 1000));
    last = now;
    const {{ ink, accent }} = palette(s);
    const view = ensureLayout(s, ink);
    const damping = 2 * Math.sqrt(SPRING) * (1 - clamp01(s.bounce) * 0.96);

    const sweeping = s.sweep && !reducedMotion && !pointer.inside && dragging < 0;
    if (sweeping) clock += dt * s.speed;
    pulse += dt;
    let targetX = pointer.x;
    let targetY = pointer.y;
    if (sweeping) {{
      targetX = view.left + (view.right - view.left) * (0.5 - 0.5 * Math.cos(clock * 0.45));
      targetY = view.top + (view.bottom - view.top) * (0.45 + 0.1 * Math.sin(clock * 0.8));
    }}
    const active = pointer.inside || sweeping || dragging >= 0;
    if (active && !placed) {{
      lens.x = targetX;
      lens.y = targetY;
    }}
    if (active) {{
      const lag = pointer.inside ? 0.05 : 0.22;
      lens.x = approach(lens.x, targetX, dt, lag);
      lens.y = approach(lens.y, targetY, dt, lag);
    }}
    placed = active;

    for (let k = kicks.length - 1; k >= 0; k--) {{
      if (kicks[k].at > pulse) continue;
      const glyph = glyphs[kicks[k].index];
      if (glyph) glyph.velocity.y -= kicks[k].velocity;
      kicks.splice(k, 1);
    }}

    let moving = false;
    glyphs.forEach((glyph, i) => {{
      if (i === dragging) {{
        glyph.offset.x = approach(glyph.offset.x, pointer.x - grab.x, dt, 0.03);
        glyph.offset.y = approach(glyph.offset.y, pointer.y - grab.y, dt, 0.03);
        glyph.velocity.x = 0;
        glyph.velocity.y = 0;
        moving = true;
        return;
      }}
      const {{ offset, velocity }} = glyph;
      if (Math.abs(offset.x) < 0.05 && Math.abs(offset.y) < 0.05 && Math.hypot(velocity.x, velocity.y) < 0.5) {{
        offset.x = 0;
        offset.y = 0;
        velocity.x = 0;
        velocity.y = 0;
        return;
      }}
      velocity.x += (-SPRING * offset.x - damping * velocity.x) * dt;
      velocity.y += (-SPRING * offset.y - damping * velocity.y) * dt;
      offset.x += velocity.x * dt;
      offset.y += velocity.y * dt;
      moving = true;
    }});

    const focus = dragging >= 0 ? dragging : active ? glyphAt(lens.x, lens.y) : -1;
    if (focus >= 0 && s.selection) {{
      const glyph = glyphs[focus];
      const bx1 = glyph.box.x1 + glyph.offset.x - 4;
      const by1 = glyph.box.y1 + glyph.offset.y - 4;
      const bx2 = glyph.box.x2 + glyph.offset.x + 4;
      const by2 = glyph.box.y2 + glyph.offset.y + 4;
      if (frame.index < 0 || frame.alpha < 0.02) {{
        frame.x1 = bx1; frame.y1 = by1; frame.x2 = bx2; frame.y2 = by2;
      }}
      const glide = focus === dragging ? 0.02 : 0.08;
      frame.x1 = approach(frame.x1, bx1, dt, glide);
      frame.y1 = approach(frame.y1, by1, dt, glide);
      frame.x2 = approach(frame.x2, bx2, dt, glide);
      frame.y2 = approach(frame.y2, by2, dt, glide);
      frame.index = focus;
    }}
    frame.alpha = approach(frame.alpha, focus >= 0 && s.selection ? 1 : 0, dt, 0.1);

    glyphs.forEach((glyph, i) => {{
      const target = (s.reveal === 'letter' && i === focus && i !== dragging) ? 1 : 0;
      glyph.outline = approach(glyph.outline, target, dt, 0.09);
      if (Math.abs(glyph.outline - target) > 0.002) moving = true;
      else glyph.outline = target;
    }});

    const hovering = focus >= 0 && pointer.inside;
    const nextCursor = dragging >= 0 ? 'grabbing' : hovering && s.draggable ? 'grab' : hovering && s.clickKick ? 'pointer' : '';
    if (nextCursor !== cursor) {{
      cursor = nextCursor;
      container.style.cursor = nextCursor;
    }}

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const glyph of glyphs) {{
      const moved = Math.hypot(glyph.offset.x, glyph.offset.y);
      if (moved > 1) {{
        ctx.globalAlpha = Math.min(1, moved / 18) * 0.4;
        blit(ctx, glyph.dashes, 0, 0, 0, 0);
        ctx.globalAlpha = 1;
      }}
    }}

    glyphs.forEach(glyph => {{
      if (glyph.outline < 0.999) {{
        ctx.globalAlpha = 1 - glyph.outline;
        blit(ctx, glyph.fill, glyph.offset.x, glyph.offset.y, 0, 0);
      }}
      if (glyph.outline > 0.001) {{
        ctx.globalAlpha = glyph.outline;
        blit(ctx, glyph.dashes, glyph.offset.x, glyph.offset.y, 0, 0);
      }}
      ctx.globalAlpha = 1;
    }});

    drawFrame(s, accent);

    const settling = moving || kicks.length > 0 || (frame.alpha > 0.01 && frame.alpha < 0.99);
    if ((active || settling) && visible && alive) raf = requestAnimationFrame(tick);
  }};

  function wake() {{
    if (raf || !visible || !alive) return;
    last = performance.now();
    raf = requestAnimationFrame(tick);
  }}

  const resize = () => {{
    width = Math.max(1, container.clientWidth);
    height = Math.max(1, container.clientHeight);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    layoutKey = '';
    wake();
  }};

  const locate = e => {{
    const rect = container.getBoundingClientRect();
    pointer.x = e.clientX - rect.left;
    pointer.y = e.clientY - rect.top;
  }};

  container.addEventListener('pointermove', e => {{ locate(e); pointer.inside = true; wake(); }}, {{ passive: true }});
  container.addEventListener('pointerenter', e => {{ locate(e); pointer.inside = true; wake(); }}, {{ passive: true }});
  container.addEventListener('pointerleave', () => {{ if (dragging < 0) {{ pointer.inside = false; wake(); }} }}, {{ passive: true }});
  container.addEventListener('pointerdown', e => {{
    locate(e);
    pointer.inside = true;
    const index = glyphAt(pointer.x, pointer.y);
    press.x = pointer.x; press.y = pointer.y; press.time = performance.now(); press.index = index;
    if (settings.draggable && index >= 0) {{
      dragging = index;
      grab.x = pointer.x - glyphs[index].offset.x;
      grab.y = pointer.y - glyphs[index].offset.y;
      container.setPointerCapture?.(e.pointerId);
    }}
    wake();
  }}, {{ passive: true }});

  const onUp = e => {{
    if (dragging >= 0) {{
      dragging = -1;
      container.releasePointerCapture?.(e.pointerId);
    }}
    if (e.type === 'pointerup' && press.index >= 0 && settings.clickKick && !reducedMotion && performance.now() - press.time < 450) {{
      const rect = container.getBoundingClientRect();
      if (Math.hypot(e.clientX - rect.left - press.x, e.clientY - rect.top - press.y) < 6) kick(press.index);
    }}
    press.index = -1;
    wake();
  }};
  container.addEventListener('pointerup', onUp, {{ passive: true }});
  container.addEventListener('pointercancel', onUp, {{ passive: true }});

  new ResizeObserver(resize).observe(container);
  if (document.fonts) document.fonts.ready.then(() => {{ layoutKey = ''; wake(); }});
  resize();
}})();


/* ==========================================================================
   2. <MolecularNetwork /> — Постоянная фоновая молекулярная сеть (Clinical Sage)
      Инжектируется в глобальный контекст window.parent и работает непрерывно.
   ========================================================================== */
function initPharmaSentinelPersistentEngine() {{
  if (window.__PS_PERSISTENT_ENGINE_ACTIVE__) return;
  window.__PS_PERSISTENT_ENGINE_ACTIVE__ = true;

  const doc = document;
  const win = window;
  const reducedMotion = win.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

  /* ------------------------------------------------------------------------
     Базовые стили Clinical Sage для фона #F3F6F2 и прозрачности контейнера
     ------------------------------------------------------------------------ */
  let styleTag = doc.getElementById('ps-persistent-layer-styles');
  if (!styleTag) {{
    styleTag = doc.createElement('style');
    styleTag.id = 'ps-persistent-layer-styles';
    styleTag.textContent = `
      html, body {{
        background-color: #F3F6F2 !important;
        color: #26332D !important;
      }}
      .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{
        background: transparent !important;
      }}
      [data-testid="stMainBlockContainer"], .block-container {{
        position: relative !important;
        z-index: 2 !important;
      }}
      #ps-molecular-layer {{
        position: fixed !important;
        inset: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 0 !important;
        pointer-events: none !important;
        overflow: hidden !important;
        background: #F3F6F2 !important;
      }}
      #ps-molecular-canvas {{
        position: absolute !important;
        inset: 0 !important;
        display: block !important;
        width: 100% !important;
        height: 100% !important;
        pointer-events: none !important;
      }}
    `;
    doc.head.appendChild(styleTag);
  }}

  // Удаляем устаревшие слои темной темы, если они были в DOM
  const oldLayers = ['ps-galaxy-layer', 'ps-splash-layer', 'ps-galaxy-bg-container'];
  oldLayers.forEach(id => {{
    const el = doc.getElementById(id);
    if (el) el.remove();
  }});

  /* ------------------------------------------------------------------------
     Молекулярная сеть: 45 узлов в тонах шалфея (#315E50, #789483),
     деликатные соединительные связи и мягкая реакция на курсор
     ------------------------------------------------------------------------ */
  let wrap = doc.getElementById('ps-molecular-layer');
  if (!wrap) {{
    wrap = doc.createElement('div');
    wrap.id = 'ps-molecular-layer';
    wrap.setAttribute('aria-hidden', 'true');
    const canvas = doc.createElement('canvas');
    canvas.id = 'ps-molecular-canvas';
    wrap.appendChild(canvas);
    doc.body.prepend(wrap);
  }}

  const canvas = doc.getElementById('ps-molecular-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const NODE_COUNT = 48;
  const MAX_DISTANCE = 120;
  const nodes = [];

  const mouse = {{ x: -9999, y: -9999, active: false }};
  let width = win.innerWidth;
  let height = win.innerHeight;
  let dpr = Math.min(win.devicePixelRatio || 1, 2);
  let rafId = 0;

  const SAGE_COLORS = [
    'rgba(49, 94, 80, 0.16)',   // Medical green
    'rgba(120, 148, 131, 0.20)', // Secondary sage
    'rgba(162, 183, 168, 0.22)', // Soft sage
    'rgba(101, 115, 106, 0.14)'  // Neutral slate
  ];

  function resizeCanvas() {{
    width = Math.max(1, win.innerWidth);
    height = Math.max(1, win.innerHeight);
    dpr = Math.min(win.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }}

  function initNodes() {{
    nodes.length = 0;
    for (let i = 0; i < NODE_COUNT; i++) {{
      nodes.push({{
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.32,
        vy: (Math.random() - 0.5) * 0.32,
        radius: 1.6 + Math.random() * 1.6,
        color: SAGE_COLORS[Math.floor(Math.random() * SAGE_COLORS.length)],
        phase: Math.random() * Math.PI * 2
      }});
    }}
  }}

  function updateAndDraw() {{
    rafId = 0;
    if (doc.hidden) return;

    ctx.clearRect(0, 0, width, height);

    // Отрисовка тонких соединительных связей между близкими молекулами
    ctx.lineWidth = 0.75;
    for (let i = 0; i < nodes.length; i++) {{
      const a = nodes[i];
      for (let j = i + 1; j < nodes.length; j++) {{
        const b = nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.hypot(dx, dy);

        if (dist < MAX_DISTANCE) {{
          const alpha = (1 - dist / MAX_DISTANCE) * 0.08;
          ctx.strokeStyle = `rgba(49, 94, 80, ${{alpha.toFixed(4)}})`;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }}
      }}
    }}

    // Отрисовка узлов
    for (let i = 0; i < nodes.length; i++) {{
      const n = nodes[i];

      if (!reducedMotion) {{
        n.x += n.vx;
        n.y += n.vy;

        // Отскок от краев экрана
        if (n.x < 0) {{ n.x = 0; n.vx *= -1; }}
        else if (n.x > width) {{ n.x = width; n.vx *= -1; }}
        if (n.y < 0) {{ n.y = 0; n.vy *= -1; }}
        else if (n.y > height) {{ n.y = height; n.vy *= -1; }}

        // Мягкое отклонение от курсора (радиус 110px)
        if (mouse.active) {{
          const mdx = n.x - mouse.x;
          const mdy = n.y - mouse.y;
          const mdist = Math.hypot(mdx, mdy);
          if (mdist < 110 && mdist > 1) {{
            const force = (1 - mdist / 110) * 0.55;
            n.x += (mdx / mdist) * force;
            n.y += (mdy / mdist) * force;
          }}
        }}
      }}

      ctx.fillStyle = n.color;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fill();
    }}

    if (!reducedMotion) {{
      rafId = win.requestAnimationFrame(updateAndDraw);
    }}
  }}

  function startLoop() {{
    if (!rafId && !doc.hidden) {{
      rafId = win.requestAnimationFrame(updateAndDraw);
    }}
  }}

  win.addEventListener('pointermove', ev => {{
    mouse.x = ev.clientX;
    mouse.y = ev.clientY;
    mouse.active = true;
    startLoop();
  }}, {{ passive: true }});

  doc.documentElement.addEventListener('pointerleave', () => {{
    mouse.active = false;
  }});

  doc.addEventListener('visibilitychange', () => {{
    if (doc.hidden) {{
      if (rafId) win.cancelAnimationFrame(rafId);
      rafId = 0;
    }} else {{
      startLoop();
    }}
  }});

  win.addEventListener('resize', () => {{
    resizeCanvas();
    updateAndDraw();
  }}, {{ passive: true }});

  resizeCanvas();
  initNodes();
  updateAndDraw();

  /* ========================================================================
     3. <AnimatedContent /> — Плавный переход при смене страниц Streamlit
     ======================================================================== */
  const runAnimatedContent = () => {{
    if (reducedMotion) return;
    const mainBlock = doc.querySelector('[data-testid="stMainBlockContainer"], .block-container');
    if (!mainBlock) return;

    const candidates = Array.from(
      mainBlock.querySelectorAll(
        '.ps-anim-item, .ps-stat-box, .ps-card-finding, .ps-supp-row, [data-testid="stDataFrame"], [data-testid="stPlot"]'
      )
    );

    const unAnimated = candidates.filter(el => !el.dataset.psAnimatedDone);
    if (!unAnimated.length) return;

    unAnimated.forEach((el, idx) => {{
      el.dataset.psAnimatedDone = '1';
      const delay = Math.min(idx * 45, 360);
      el.style.opacity = '0';
      el.style.transform = 'translate3d(0, 18px, 0)';
      el.style.transition = 'none';
      setTimeout(() => {{
        win.requestAnimationFrame(() => {{
          el.style.transition = 'opacity 420ms cubic-bezier(0.16, 1, 0.3, 1), transform 420ms cubic-bezier(0.16, 1, 0.3, 1)';
          el.style.opacity = '1';
          el.style.transform = 'translate3d(0, 0, 0)';
        }});
      }}, 16 + delay);
    }});
  }};

  win.__PS_TRIGGER_ANIMATED_CONTENT__ = runAnimatedContent;
  runAnimatedContent();

  const appContainer = doc.querySelector('[data-testid="stAppViewContainer"]') || doc.body;
  const domObserver = new MutationObserver(() => {{
    runAnimatedContent();
  }});
  domObserver.observe(appContainer, {{ childList: true, subtree: true }});
}}


(function ensurePersistentParentEngine() {{
  let parentWin, parentDoc;
  try {{
    parentWin = window.parent;
    parentDoc = window.parent.document;
    if (!parentDoc || !parentDoc.body || !parentDoc.head) return;
  }} catch (e) {{
    return;
  }}

  if (parentWin.__PS_PERSISTENT_ENGINE_ACTIVE__) {{
    if (typeof parentWin.__PS_TRIGGER_ANIMATED_CONTENT__ === 'function') {{
      parentWin.__PS_TRIGGER_ANIMATED_CONTENT__();
    }}
    return;
  }}

  const legacyScript = parentDoc.getElementById('ps-persistent-engine-script');
  if (legacyScript) legacyScript.remove();

  const engineScript = parentDoc.createElement('script');
  engineScript.id = 'ps-persistent-engine-script';
  engineScript.textContent = '(' + initPharmaSentinelPersistentEngine.toString() + ')();';
  parentDoc.head.appendChild(engineScript);
}})();
</script>
</body>
</html>"""
