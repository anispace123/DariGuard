"""Модуль интеграции эффектов React Bits (<Galaxy />, <SplashCursor />, <TechText />, <AnimatedContent />).

Архитектурное решение проблемы жизненного цикла в Streamlit:
- Вместо запуска WebGL2-циклов внутри дочернего `<iframe>` (который уничтожается или перезагружается при
  смене параметров и rerun Streamlit), движок `<Galaxy />`, `<SplashCursor />` и наблюдатель `<AnimatedContent />`
  инжектируются как постоянный `<script id="ps-persistent-engine">` непосредственно в `window.parent.document.head`.
- Благодаря этому оба WebGL2-контекста, их `requestAnimationFrame` циклы и DOM-слои живут в глобальном
  окне браузера (`window.parent.__PS_PERSISTENT_ENGINE__`) и работают непрерывно при любых переходах между
  страницами, изменениях `st.session_state` и перезапусках скрипта Streamlit.
"""


def render_tech_text_and_effects_html(
    text: str = "PHARMA SENTINEL",
    subtitle: str = "КЛИНИЧЕСКАЯ ФАРМАКОЛОГИЯ · DDINTER v2024.11",
    height: int = 74,
) -> str:
    """Рендерит интерактивный заголовок <TechText /> и однократно инициализирует в родительском окне постоянные слои <Galaxy /> и <SplashCursor />."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

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
    height: 50px;
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
    font-size: 10.5px;
    font-weight: 500;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #93A4BF;
    padding-left: 2px;
    margin-top: -1px;
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
   1. <TechText /> — React Bits Interactive Wordmark (Dark Scientific Theme)
   ========================================================================== */
(function initTechText() {{
  const container = document.getElementById('tech-text-root');
  const canvas = document.getElementById('tech-text-canvas');
  if (!container || !canvas) return;
  const ctx = canvas.getContext('2d');
  const scratch = document.createElement('canvas');
  const scratchCtx = scratch.getContext('2d');
  if (!ctx || !scratchCtx) return;

  const LABEL_FONT = '10px "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
  const SPRING = 320;
  const INHERIT = /^(currentcolor|inherit)$/i;
  const KICK_DECAY = 0.62;

  const settings = {{
    text: {text!r},
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    fontWeight: 600,
    fontSize: 33,
    letterSpacing: -0.035,
    color: '#DCE7F7',
    accentColor: '#55D6E8',
    align: 'left',
    reach: 200,
    softness: 0.7,
    dashLength: 4,
    dashGap: 2,
    strokeWidth: 1.5,
    lineStyle: 'dashed',
    reveal: 'letter',
    specks: 12,
    selection: true,
    labels: true,
    draggable: true,
    bounce: 0.38,
    sweep: true,
    speed: 0.85,
    clickKick: true,
    intro: 'none',
    introDuration: 2.0,
    guides: false
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
    const current = getComputedStyle(container).color || '#DCE7F7';
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

  const perimeterPoint = (distance, w, h) => {{
    let d = ((distance % (2 * (w + h))) + 2 * (w + h)) % (2 * (w + h));
    if (d < w) return [frame.x1 + d, frame.y1, 0, -1];
    d -= w;
    if (d < h) return [frame.x2, frame.y1 + d, 1, 0];
    d -= h;
    if (d < w) return [frame.x2 - d, frame.y2, 0, 1];
    d -= w;
    return [frame.x1, frame.y2 - d, -1, 0];
  }};

  const drawSpecks = (s, a, accent) => {{
    const w = frame.x2 - frame.x1;
    const h = frame.y2 - frame.y1;
    if (w < 2 || h < 2) return;
    const perimeter = 2 * (w + h);
    const seed = frame.index + 1;
    const grid = 3;
    ctx.fillStyle = accent;
    ctx.strokeStyle = accent;

    for (let k = 0; k < s.specks; k++) {{
      const period = 0.5 + noise(seed, k, 11) * 1.2;
      const t = pulse / period + noise(seed, k, 17);
      const cycle = Math.floor(t);
      const life = t - cycle;
      if (life > 0.7) continue;
      const [px, py, nx, ny] = perimeterPoint(noise(seed, k, cycle) * perimeter, w, h);
      const pick = noise(seed, k, cycle, 2);
      const size = pick < 0.46 ? 2 : pick < 0.75 ? 3 : 4;
      const out = 3 + Math.floor(noise(seed, k, cycle, 1) * 3) * grid;
      const x = frame.x1 + Math.round((px + nx * out - frame.x1) / grid) * grid;
      const y = frame.y1 + Math.round((py + ny * out - frame.y1) / grid) * grid;
      const tone = noise(seed, k, cycle, 3);
      const blink = life < 0.06 || (life > 0.32 && life < 0.36) ? 0.35 : 1;
      ctx.globalAlpha = a * (0.3 + 0.55 * tone) * blink;
      ctx.fillRect(Math.round(x - size / 2), Math.round(y - size / 2), size, size);
    }}
    ctx.globalAlpha = 1;
  }};

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
      ctx.globalAlpha = 0.45 * a;
      ctx.stroke();
      ctx.setLineDash([]);
    }}

    ctx.beginPath();
    ctx.rect(x1, y1, x2 - x1, y2 - y1);
    ctx.globalAlpha = 0.45 * a;
    ctx.stroke();

    ctx.beginPath();
    for (const [cx, cy] of [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]) {{
      ctx.rect(Math.round(cx) - 2, Math.round(cy) - 2, 4, 4);
    }}
    ctx.globalAlpha = 0.9 * a;
    ctx.fill();
    ctx.globalAlpha = 1;

    if (s.specks > 0) drawSpecks(s, a, accent);

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
    const strength = (word ? word.size : 40) * 9.0;
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
        ctx.globalAlpha = Math.min(1, moved / 18) * 0.55;
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
   2. Постоянная инъекция <Galaxy />, <SplashCursor /> и <AnimatedContent />
      непосредственно в window.parent (жизненный цикл независим от iframe!)
   ========================================================================== */
function initPharmaSentinelPersistentEngine() {{
  if (window.__PS_PERSISTENT_ENGINE_ACTIVE__) return;
  window.__PS_PERSISTENT_ENGINE_ACTIVE__ = true;

  const doc = document;
  const win = window;
  const reducedMotion = win.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

  /* ------------------------------------------------------------------------
     Слой стилей для базового фона #0A1020 и прозрачности оболочки Streamlit
     ------------------------------------------------------------------------ */
  let styleTag = doc.getElementById('ps-persistent-layer-styles');
  if (!styleTag) {{
    styleTag = doc.createElement('style');
    styleTag.id = 'ps-persistent-layer-styles';
    styleTag.textContent = `
      html, body {{
        background-color: #0A1020 !important;
        color: #DCE7F7 !important;
      }}
      .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{
        background: transparent !important;
      }}
      [data-testid="stMainBlockContainer"], .block-container {{
        position: relative !important;
        z-index: 2 !important;
      }}
      #ps-galaxy-layer {{
        position: fixed !important;
        inset: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 0 !important;
        pointer-events: none !important;
        overflow: hidden !important;
        background: radial-gradient(ellipse at 50% 25%, #0D1628 0%, #0A1020 75%) !important;
      }}
      #ps-galaxy-canvas {{
        position: absolute !important;
        inset: 0 !important;
        display: block !important;
        width: 100% !important;
        height: 100% !important;
        pointer-events: none !important;
      }}
      #ps-splash-layer {{
        position: fixed !important;
        inset: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 1 !important;
        pointer-events: none !important;
        overflow: hidden !important;
      }}
      #ps-splash-canvas {{
        display: block !important;
        width: 100% !important;
        height: 100% !important;
        pointer-events: none !important;
      }}
    `;
    doc.head.appendChild(styleTag);
  }}

  /* ========================================================================
     СЛОЙ 1: <Galaxy /> — Постоянный фоновый слой WebGL2 (z-index: 0)
     Палитра: ['#527DFF', '#55D6E8', '#A8C7FF', '#E1E9FF']
     Параметры: прозрачный режим, умеренная плотность, мягкое свечение, без warp
     ======================================================================== */
  (function startPersistentGalaxy() {{
    let galaxyWrap = doc.getElementById('ps-galaxy-layer');
    if (!galaxyWrap) {{
      galaxyWrap = doc.createElement('div');
      galaxyWrap.id = 'ps-galaxy-layer';
      galaxyWrap.setAttribute('aria-hidden', 'true');
      const gCanvas = doc.createElement('canvas');
      gCanvas.id = 'ps-galaxy-canvas';
      galaxyWrap.appendChild(gCanvas);
      doc.body.prepend(galaxyWrap);
    }}
    const canvas = doc.getElementById('ps-galaxy-canvas');
    if (!canvas) return;

    const MAX_LAYERS = 8;
    const MAX_COLORS = 4;

    const VERTEX = `#version 300 es
in vec2 aPosition;
void main() {{
  gl_Position = vec4(aPosition, 0.0, 1.0);
}}`;

    const FRAGMENT = `#version 300 es
precision highp float;
precision highp int;
uniform float uTime;
uniform vec2 uResolution;
uniform vec2 uFocal;
uniform vec2 uRotation;
uniform float uGloss;
uniform float uDepth;
uniform float uDensity;
uniform float uHueShift;
uniform float uSpeed;
uniform vec2 uMouse;
uniform float uStarGlow;
uniform float uFlareGain;
uniform float uSquash;
uniform float uSaturation;
uniform float uMouseRepulsion;
uniform float uTwinkleIntensity;
uniform float uRotationAngle;
uniform float uRepulsionStrength;
uniform float uMouseActiveFactor;
uniform float uAutoCenterRepulsion;
uniform int uLayers;
uniform vec3 uColors[4];
uniform int uColorCount;
uniform float uWarp;
uniform float uReveal;
uniform float uMode;
uniform vec3 uBackground;
uniform float uOpacity;
out vec4 outColor;

#define STAR_COLOR_CUTOFF 0.2
#define MAT45 mat2(0.7071, -0.7071, 0.7071, 0.7071)
#define PERIOD 3.0

float Hash21(vec2 p) {{
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}}

float tri(float x) {{
  return abs(fract(x) * 2.0 - 1.0);
}}

float tris(float x) {{
  float t = fract(x);
  return 1.0 - smoothstep(0.0, 1.0, abs(2.0 * t - 1.0));
}}

float trisn(float x) {{
  float t = fract(x);
  return 2.0 * (1.0 - smoothstep(0.0, 1.0, abs(2.0 * t - 1.0))) - 1.0;
}}

float Star(vec2 uv, float flare, vec2 radial, float invReach) {{
  float d = length(uv);
  float m = uStarGlow / max(d, 0.0005);
  float rays = smoothstep(0.0, 1.0, 1.0 - abs(uv.x * uv.y * 1000.0));
  m += rays * flare * uFlareGain;
  uv *= MAT45;
  rays = smoothstep(0.0, 1.0, 1.0 - abs(uv.x * uv.y * 1000.0));
  m += rays * 0.3 * flare * uFlareGain;
  m *= smoothstep(1.0, 0.2, d * invReach);
  return m;
}}

vec3 StarLayer(vec2 uv, vec2 radial, vec2 repelAt, float pushCells, float spread) {{
  vec3 col = vec3(0.0);
  vec2 gv = fract(uv) - 0.5;
  vec2 id = floor(uv);
  for (int y = -1; y <= 1; y++) {{
    for (int x = -1; x <= 1; x++) {{
      vec2 offset = vec2(float(x), float(y));
      vec2 si = id + offset;
      float seed = Hash21(si);
      float size = fract(seed * 345.32);
      float glossLocal = tri(uGloss / (PERIOD * seed + 1.0));
      float flareSize = smoothstep(0.9, 1.0, size) * glossLocal;

      float pick = Hash21(si + 7.0) * float(uColorCount);
      vec3 base = uColors[int(min(floor(pick), float(uColorCount - 1)))];

      vec2 pad = vec2(tris(seed * 34.0 + uTime * uSpeed / 10.0), tris(seed * 38.0 + uTime * uSpeed / 30.0)) - 0.5;
      vec2 shift = vec2(0.0);
      float invReach = 1.0;
#ifdef REPEL
      vec2 away = si + 0.5 + pad - repelAt;
      float dist = length(away);
      float q = dist * spread;
      float cells = pushCells * exp(-q * q);
      float moved = cells * inversesqrt(1.0 + cells * cells * 2.78);
      shift = away * (moved / max(dist, 0.0001));
      invReach = 1.0 / (1.0 - moved);
#endif
      float star = Star(gv - offset - pad - shift, flareSize, radial, invReach);
      float twinkle = trisn(uTime * uSpeed + seed * 6.2831) * 0.5 + 1.0;
      twinkle = mix(1.0, twinkle, uTwinkleIntensity);
      col += star * twinkle * size * base;
    }}
  }}
  return col;
}}

void main() {{
  vec2 focalPx = uFocal * uResolution;
  vec2 uv = (gl_FragCoord.xy - focalPx) / uResolution.y;
  vec2 mouseNorm = uMouse - vec2(0.5);

  vec2 repelAt = vec2(0.0);
  float strength = 0.0;
  float push = 0.0;
  if (uMouseRepulsion > 0.5) {{
    repelAt = (uMouse * uResolution - focalPx) / uResolution.y;
    strength = max(uRepulsionStrength, 0.0);
    push = strength * 0.05 * uMouseActiveFactor;
  }} else {{
    uv += mouseNorm * 0.1 * uMouseActiveFactor;
  }}
  float radius = 0.16 + 0.04 * strength;

  vec2 radial = length(uv) > 0.0001 ? normalize(uv) : vec2(1.0, 0.0);
  float angle = uRotationAngle;
  uv = mat2(cos(angle), -sin(angle), sin(angle), cos(angle)) * uv;
  uv = mat2(uRotation.x, -uRotation.y, uRotation.y, uRotation.x) * uv;
  radial = mat2(cos(angle), -sin(angle), sin(angle), cos(angle)) * radial;
  radial = mat2(uRotation.x, -uRotation.y, uRotation.y, uRotation.x) * radial;
  repelAt = mat2(cos(angle), -sin(angle), sin(angle), cos(angle)) * repelAt;
  repelAt = mat2(uRotation.x, -uRotation.y, uRotation.y, uRotation.x) * repelAt;

  vec3 col = vec3(0.0);
  float layers = float(uLayers);
  for (int k = 0; k < 8; k++) {{
    if (k >= uLayers) break;
    float i = float(k) / layers;
    float depth = fract(i + uDepth);
    float scale = mix(20.0 * uDensity, 0.5 * uDensity, depth);
    float fade = depth * smoothstep(1.0, 0.9, depth);
    vec2 offset = vec2(i * 453.32);
    col += StarLayer(uv * scale + offset, radial, repelAt * scale + offset, push * scale, 1.0 / (scale * radius)) * fade;
  }}
  col *= uReveal;

  float alpha = min(smoothstep(0.0, 0.3, length(col)), 1.0) * uOpacity;
  outColor = vec4(col * alpha, alpha);
}}`;

    const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

    const s = {{
      focal: [0.5, 0.5],
      rotation: [1.0, 0.0],
      starSpeed: 0.22,
      density: 0.85,
      hueShift: 140,
      disableAnimation: false,
      speed: 0.55,
      mouseInteraction: true,
      glowIntensity: 0.22,
      saturation: 0.0,
      mouseRepulsion: true,
      repulsionStrength: 1.4,
      twinkleIntensity: 0.22,
      rotationSpeed: 0.025,
      autoCenterRepulsion: 0,
      transparent: true,
      lightMode: false,
      palette: ['#527DFF', '#55D6E8', '#A8C7FF', '#E1E9FF'],
      starSize: 0.95,
      flareIntensity: 0.35,
      layers: 4,
      reverse: false,
      clickWarp: false,
      intro: false,
      backgroundColor: '#0A1020',
      opacity: 0.68,
      dpr: 1.75
    }};

    const parseHex = hex => {{
      const h = hex.replace('#', '');
      const n = parseInt(h, 16);
      return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
    }};

    const colors = new Float32Array(MAX_COLORS * 3);
    s.palette.forEach((c, idx) => colors.set(parseHex(c), idx * 3));
    const bgRgb = parseHex(s.backgroundColor);

    let gl = null;
    let baseProg = null;
    let repelProg = null;
    let vao = null;
    let buffer = null;
    let lost = false;

    const buildProgram = (glCtx, repel) => {{
      const defines = repel ? '#define REPEL\\n' : '';
      const prog = glCtx.createProgram();
      const vs = glCtx.createShader(glCtx.VERTEX_SHADER);
      const fs = glCtx.createShader(glCtx.FRAGMENT_SHADER);
      if (!prog || !vs || !fs) return null;
      glCtx.shaderSource(vs, VERTEX);
      glCtx.shaderSource(fs, FRAGMENT.replace('\\n', '\\n' + defines));
      glCtx.compileShader(vs);
      glCtx.compileShader(fs);
      glCtx.attachShader(prog, vs);
      glCtx.attachShader(prog, fs);
      glCtx.bindAttribLocation(prog, 0, 'aPosition');
      glCtx.linkProgram(prog);
      glCtx.deleteShader(vs);
      glCtx.deleteShader(fs);
      if (!glCtx.getProgramParameter(prog, glCtx.LINK_STATUS)) return null;
      const uniforms = {{}};
      const count = glCtx.getProgramParameter(prog, glCtx.ACTIVE_UNIFORMS);
      for (let i = 0; i < count; i++) {{
        const info = glCtx.getActiveUniform(prog, i);
        if (info) uniforms[info.name.replace('[0]', '')] = glCtx.getUniformLocation(prog, info.name);
      }}
      return {{ program: prog, uniforms }};
    }};

    const initGL = () => {{
      gl = canvas.getContext('webgl2', {{
        alpha: true,
        premultipliedAlpha: true,
        antialias: false,
        depth: false,
        stencil: false
      }});
      if (!gl) return false;
      baseProg = buildProgram(gl, false);
      repelProg = buildProgram(gl, true);
      if (!baseProg) return false;
      buffer = gl.createBuffer();
      vao = gl.createVertexArray();
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0);
      gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
      return true;
    }};

    if (!initGL()) return;

    const pointer = {{ x: 0.5, y: 0.5, inside: false }};
    const state = {{
      time: 0, gloss: 0, depth: 0, angle: 0,
      mx: 0.5, my: 0.5, active: 0, boost: 0, reveal: 1
    }};
    let raf = 0;
    let last = 0;

    const render = () => {{
      if (!gl || lost) return;
      const repel = s.mouseRepulsion && state.active > 0.005;
      const prog = (repel && repelProg) ? repelProg : baseProg;
      if (!prog) return;
      const u = prog.uniforms;
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.useProgram(prog.program);
      gl.bindVertexArray(vao);
      gl.uniform1f(u.uTime, state.time);
      gl.uniform2f(u.uResolution, canvas.width, canvas.height);
      gl.uniform2f(u.uFocal, s.focal[0], s.focal[1]);
      gl.uniform2f(u.uRotation, s.rotation[0], s.rotation[1]);
      gl.uniform1f(u.uGloss, state.gloss);
      gl.uniform1f(u.uDepth, state.depth);
      gl.uniform1f(u.uDensity, s.density);
      gl.uniform1f(u.uHueShift, s.hueShift);
      gl.uniform1f(u.uSpeed, s.speed);
      gl.uniform2f(u.uMouse, state.mx, state.my);
      gl.uniform1f(u.uStarGlow, 0.05 * s.glowIntensity * s.starSize);
      gl.uniform1f(u.uFlareGain, s.glowIntensity * s.flareIntensity);
      gl.uniform1f(u.uSquash, 0.0);
      gl.uniform1f(u.uSaturation, s.saturation);
      gl.uniform1f(u.uMouseRepulsion, s.mouseRepulsion ? 1 : 0);
      gl.uniform1f(u.uTwinkleIntensity, s.twinkleIntensity);
      gl.uniform1f(u.uRotationAngle, state.angle);
      gl.uniform1f(u.uRepulsionStrength, s.repulsionStrength);
      gl.uniform1f(u.uMouseActiveFactor, state.active);
      gl.uniform1f(u.uAutoCenterRepulsion, s.autoCenterRepulsion);
      gl.uniform1i(u.uLayers, s.layers);
      gl.uniform3fv(u.uColors, colors);
      gl.uniform1i(u.uColorCount, s.palette.length);
      gl.uniform1f(u.uWarp, 0.0);
      gl.uniform1f(u.uReveal, 1.0);
      gl.uniform1f(u.uMode, 1.0);
      gl.uniform3fv(u.uBackground, bgRgb);
      gl.uniform1f(u.uOpacity, s.opacity);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }};

    const frame = now => {{
      raf = 0;
      if (doc.hidden || lost) return;
      const dt = last ? clamp((now - last) / 1000, 0.0005, 0.05) : 1 / 60;
      last = now;
      const motion = (s.disableAnimation || reducedMotion) ? 0 : 1;
      const flight = (s.starSpeed / 10);
      state.time += dt * motion;
      state.gloss += dt * flight * motion;
      state.depth += dt * flight * s.speed * motion;
      state.angle += dt * s.rotationSpeed * motion;

      const follow = 1 - Math.exp(-dt / 0.325);
      const engaged = s.mouseInteraction && pointer.inside && !reducedMotion;
      if (engaged) {{
        state.mx += (pointer.x - state.mx) * follow;
        state.my += (pointer.y - state.my) * follow;
      }}
      const target = engaged ? 1 : 0;
      state.active += (target - state.active) * follow;
      if (Math.abs(target - state.active) < 0.001) state.active = target;

      render();
      if (motion > 0 || state.active !== target) {{
        raf = win.requestAnimationFrame(frame);
      }} else {{
        last = 0;
      }}
    }};

    const wake = () => {{
      if (!raf && !doc.hidden && !lost) raf = win.requestAnimationFrame(frame);
    }};

    const resize = () => {{
      const w = Math.max(1, win.innerWidth);
      const h = Math.max(1, win.innerHeight);
      const ratio = Math.min(s.dpr, win.devicePixelRatio || 1, 2);
      const cw = Math.max(1, Math.round(w * ratio));
      const ch = Math.max(1, Math.round(h * ratio));
      if (canvas.width !== cw || canvas.height !== ch) {{
        canvas.width = cw;
        canvas.height = ch;
      }}
      render();
      wake();
    }};

    win.addEventListener('pointermove', ev => {{
      pointer.inside = true;
      pointer.x = ev.clientX / Math.max(1, win.innerWidth);
      pointer.y = 1 - ev.clientY / Math.max(1, win.innerHeight);
      wake();
    }}, {{ passive: true }});

    doc.documentElement.addEventListener('pointerleave', () => {{
      pointer.inside = false;
    }});

    doc.addEventListener('visibilitychange', () => {{
      last = 0;
      wake();
    }});

    canvas.addEventListener('webglcontextlost', ev => {{
      ev.preventDefault();
      lost = true;
      if (raf) win.cancelAnimationFrame(raf);
      raf = 0;
    }});

    canvas.addEventListener('webglcontextrestored', () => {{
      lost = false;
      if (initGL()) {{
        resize();
        wake();
      }}
    }});

    win.addEventListener('resize', resize, {{ passive: true }});
    resize();
  }})();


  /* ========================================================================
     СЛОЙ 2: <SplashCursor /> — React Bits Fluid Simulation (z-index: 1)
     Параметры: rainbow=false, colors=['#527DFF','#55D6E8','#A8C7FF'],
     colorSpeed=0.12, intensity=0.55, size=0.75, force=0.65, swirl=2,
     trail=0.8, momentum=0.75, shading=0.55, glow=0.12, quality='medium',
     clickSplash=false, intro=false, theme='dark'.
     ======================================================================== */
  (function startPersistentSplashCursor() {{
    if (reducedMotion) return;

    let splashWrap = doc.getElementById('ps-splash-layer');
    if (!splashWrap) {{
      splashWrap = doc.createElement('div');
      splashWrap.id = 'ps-splash-layer';
      splashWrap.setAttribute('aria-hidden', 'true');
      const sCanvas = doc.createElement('canvas');
      sCanvas.id = 'ps-splash-canvas';
      splashWrap.appendChild(sCanvas);
      const gLayer = doc.getElementById('ps-galaxy-layer');
      if (gLayer && gLayer.nextSibling) {{
        doc.body.insertBefore(splashWrap, gLayer.nextSibling);
      }} else {{
        doc.body.prepend(splashWrap);
      }}
    }}
    const canvas = doc.getElementById('ps-splash-canvas');
    if (!canvas) return;

    const QUALITY = {{
      low: {{ sim: 64, dye: 512, iterations: 10 }},
      medium: {{ sim: 96, dye: 768, iterations: 14 }},
      high: {{ sim: 128, dye: 1440, iterations: 20 }}
    }};
    const BLOOM_RESOLUTION = 192;
    const BLOOM_ITERATIONS = 3;
    const BLOOM_THRESHOLD = 0.35;
    const BLOOM_KNEE = 0.7;

    const VERTEX = `#version 300 es
precision highp float;
in vec2 aPosition;
uniform vec2 texelSize;
out vec2 vUv;
out vec2 vL;
out vec2 vR;
out vec2 vT;
out vec2 vB;
void main() {{
  vUv = aPosition * 0.5 + 0.5;
  vL = vUv - vec2(texelSize.x, 0.0);
  vR = vUv + vec2(texelSize.x, 0.0);
  vT = vUv + vec2(0.0, texelSize.y);
  vB = vUv - vec2(0.0, texelSize.y);
  gl_Position = vec4(aPosition, 0.0, 1.0);
}}`;

    const HEADER = `#version 300 es
precision highp float;
precision highp sampler2D;
in vec2 vUv;
in vec2 vL;
in vec2 vR;
in vec2 vT;
in vec2 vB;
out vec4 outColor;
`;

    const SHADERS = {{
      copy: `uniform sampler2D uTexture;
void main() {{
  outColor = texture(uTexture, vUv);
}}`,
      clear: `uniform sampler2D uTexture;
uniform float value;
void main() {{
  outColor = value * texture(uTexture, vUv);
}}`,
      splat: `uniform sampler2D uTarget;
uniform float aspectRatio;
uniform vec3 color;
uniform vec2 pointA;
uniform vec2 pointB;
uniform float radius;
void main() {{
  vec2 scale = vec2(aspectRatio, 1.0);
  vec2 pa = (vUv - pointA) * scale;
  vec2 ba = (pointB - pointA) * scale;
  float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-9), 0.0, 1.0);
  vec2 d = pa - ba * h;
  vec3 base = texture(uTarget, vUv).xyz;
  outColor = vec4(base + exp(-dot(d, d) / radius) * color, 1.0);
}}`,
      advection: `uniform sampler2D uVelocity;
uniform sampler2D uSource;
uniform vec2 texelSize;
uniform float dt;
uniform float dissipation;
void main() {{
  vec2 coord = vUv - dt * texture(uVelocity, vUv).xy * texelSize;
  outColor = texture(uSource, coord) / (1.0 + dissipation * dt);
}}`,
      divergence: `uniform sampler2D uVelocity;
void main() {{
  float L = texture(uVelocity, vL).x;
  float R = texture(uVelocity, vR).x;
  float T = texture(uVelocity, vT).y;
  float B = texture(uVelocity, vB).y;
  vec2 C = texture(uVelocity, vUv).xy;
  if (vL.x < 0.0) L = -C.x;
  if (vR.x > 1.0) R = -C.x;
  if (vT.y > 1.0) T = -C.y;
  if (vB.y < 0.0) B = -C.y;
  outColor = vec4(0.5 * (R - L + T - B), 0.0, 0.0, 1.0);
}}`,
      curl: `uniform sampler2D uVelocity;
void main() {{
  float L = texture(uVelocity, vL).y;
  float R = texture(uVelocity, vR).y;
  float T = texture(uVelocity, vT).x;
  float B = texture(uVelocity, vB).x;
  outColor = vec4(0.5 * (R - L - T + B), 0.0, 0.0, 1.0);
}}`,
      vorticity: `uniform sampler2D uVelocity;
uniform sampler2D uCurl;
uniform float curl;
uniform float dt;
void main() {{
  float L = texture(uCurl, vL).x;
  float R = texture(uCurl, vR).x;
  float T = texture(uCurl, vT).x;
  float B = texture(uCurl, vB).x;
  float C = texture(uCurl, vUv).x;
  vec2 force = 0.5 * vec2(abs(T) - abs(B), abs(R) - abs(L));
  force /= length(force) + 0.0001;
  force *= curl * C;
  force.y *= -1.0;
  vec2 velocity = texture(uVelocity, vUv).xy + force * dt;
  outColor = vec4(clamp(velocity, -1000.0, 1000.0), 0.0, 1.0);
}}`,
      pressure: `uniform sampler2D uPressure;
uniform sampler2D uDivergence;
void main() {{
  float L = texture(uPressure, vL).x;
  float R = texture(uPressure, vR).x;
  float T = texture(uPressure, vT).x;
  float B = texture(uPressure, vB).x;
  float divergence = texture(uDivergence, vUv).x;
  outColor = vec4((L + R + B + T - divergence) * 0.25, 0.0, 0.0, 1.0);
}}`,
      gradient: `uniform sampler2D uPressure;
uniform sampler2D uVelocity;
void main() {{
  float L = texture(uPressure, vL).x;
  float R = texture(uPressure, vR).x;
  float T = texture(uPressure, vT).x;
  float B = texture(uPressure, vB).x;
  vec2 velocity = texture(uVelocity, vUv).xy - vec2(R - L, T - B);
  outColor = vec4(velocity, 0.0, 1.0);
}}`,
      prefilter: `uniform sampler2D uTexture;
uniform vec3 curve;
uniform float threshold;
void main() {{
  vec3 c = texture(uTexture, vUv).rgb;
  float br = max(c.r, max(c.g, c.b));
  float rq = clamp(br - curve.x, 0.0, curve.y);
  rq = curve.z * rq * rq;
  c *= max(rq, br - threshold) / max(br, 0.0001);
  outColor = vec4(c, 0.0);
}}`,
      blur: `uniform sampler2D uTexture;
uniform float intensity;
void main() {{
  vec4 sum = texture(uTexture, vL) + texture(uTexture, vR) + texture(uTexture, vT) + texture(uTexture, vB);
  outColor = sum * 0.25 * intensity;
}}`,
      display: `uniform sampler2D uTexture;
uniform sampler2D uBloom;
uniform vec2 texelSize;
uniform float shading;
uniform float bloom;
uniform float light;
float hash(vec2 p) {{
  vec3 q = fract(vec3(p.xyx) * 0.1031);
  q += dot(q, q.yzx + 33.33);
  return fract((q.x + q.y) * q.z);
}}
void main() {{
  vec3 c = texture(uTexture, vUv).rgb;
  if (shading > 0.0) {{
    float dx = length(texture(uTexture, vR).rgb) - length(texture(uTexture, vL).rgb);
    float dy = length(texture(uTexture, vT).rgb) - length(texture(uTexture, vB).rgb);
    vec3 n = normalize(vec3(dx, dy, length(texelSize)));
    c *= mix(1.0, clamp(n.z + 0.7, 0.7, 1.0), shading);
  }}
  if (bloom > 0.0) {{
    c += max(texture(uBloom, vUv).rgb, 0.0) * bloom;
  }}
  c = max(c, 0.0);
  float peak = max(c.r, max(c.g, c.b));
  float grain = (hash(gl_FragCoord.xy) - 0.5) / 255.0 * smoothstep(0.0, 0.03, peak);
  c = max(c + grain, 0.0);
  float alpha = clamp(max(c.r, max(c.g, c.b)), 0.0, 1.0);
  outColor = vec4(min(c, vec3(alpha)), alpha);
}}`
    }};

    const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
    const parseColor = value => {{
      const hex = String(value).replace('#', '').trim();
      const number = parseInt(hex.slice(0, 6), 16);
      if (Number.isNaN(number)) return [1, 1, 1];
      return [((number >> 16) & 255) / 255, ((number >> 8) & 255) / 255, (number & 255) / 255];
    }};

    const s = {{
      palette: ['#527DFF', '#55D6E8', '#A8C7FF'].map(parseColor),
      rainbow: false,
      colorSpeed: 0.12,
      intensity: 0.55,
      size: 0.75,
      force: 0.65,
      swirl: 2.0,
      trail: 0.8,
      momentum: 0.75,
      shading: 0.55,
      glow: 0.12,
      quality: 'medium',
      clickSplash: false,
      contained: false,
      light: false
    }};

    const gl = canvas.getContext('webgl2', {{
      alpha: true,
      premultipliedAlpha: true,
      antialias: false,
      depth: false,
      stencil: false,
      preserveDrawingBuffer: false
    }});
    if (!gl) return;
    gl.getExtension('EXT_color_buffer_float');
    gl.getExtension('EXT_color_buffer_half_float');

    const renderable = (internal, format) => {{
      const texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texImage2D(gl.TEXTURE_2D, 0, internal, 4, 4, 0, format, gl.HALF_FLOAT, null);
      const fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
      const complete = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.deleteFramebuffer(fbo);
      gl.deleteTexture(texture);
      return complete;
    }};
    const rgba = {{ internal: gl.RGBA16F, format: gl.RGBA }};
    if (!renderable(rgba.internal, rgba.format)) return;
    const rg = renderable(gl.RG16F, gl.RG) ? {{ internal: gl.RG16F, format: gl.RG }} : rgba;
    const r = renderable(gl.R16F, gl.RED) ? {{ internal: gl.R16F, format: gl.RED }} : rg;

    const compile = (type, source) => {{
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      return shader;
    }};
    const vertex = compile(gl.VERTEX_SHADER, VERTEX);
    const programs = {{}};
    let broken = false;
    Object.entries(SHADERS).forEach(([name, body]) => {{
      const fragment = compile(gl.FRAGMENT_SHADER, HEADER + body);
      const program = gl.createProgram();
      gl.attachShader(program, vertex);
      gl.attachShader(program, fragment);
      gl.bindAttribLocation(program, 0, 'aPosition');
      gl.linkProgram(program);
      gl.deleteShader(fragment);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) broken = true;
      const uniforms = {{}};
      const count = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
      for (let i = 0; i < count; i++) {{
        const info = gl.getActiveUniform(program, i);
        if (info) uniforms[info.name] = gl.getUniformLocation(program, info.name);
      }}
      programs[name] = {{ program, uniforms }};
    }});
    gl.deleteShader(vertex);
    if (broken) return;

    const buffer = gl.createBuffer();
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    const targets = new Set();
    let lost = false;

    const use = name => {{
      const item = programs[name];
      gl.useProgram(item.program);
      return item.uniforms;
    }};

    const blit = target => {{
      if (target) {{
        gl.viewport(0, 0, target.width, target.height);
        gl.bindFramebuffer(gl.FRAMEBUFFER, target.fbo);
      }} else {{
        gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      }}
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }};

    const createTarget = (width, height, format, filter) => {{
      gl.activeTexture(gl.TEXTURE0);
      const texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, format.internal, width, height, 0, format.format, gl.HALF_FLOAT, null);
      const fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
      gl.viewport(0, 0, width, height);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      const target = {{
        texture, fbo, width, height,
        texelX: 1 / width, texelY: 1 / height,
        attach: unit => {{
          gl.activeTexture(gl.TEXTURE0 + unit);
          gl.bindTexture(gl.TEXTURE_2D, texture);
          return unit;
        }}
      }};
      targets.add(target);
      return target;
    }};

    const destroyTarget = target => {{
      if (!target) return;
      gl.deleteFramebuffer(target.fbo);
      gl.deleteTexture(target.texture);
      targets.delete(target);
    }};

    const reshape = (target, width, height, format) => {{
      gl.bindTexture(gl.TEXTURE_2D, target.texture);
      gl.texImage2D(gl.TEXTURE_2D, 0, format.internal, width, height, 0, format.format, gl.HALF_FLOAT, null);
      target.width = width;
      target.height = height;
      target.texelX = 1 / width;
      target.texelY = 1 / height;
    }};

    const createDouble = (width, height, format, filter) => {{
      const pair = {{
        read: createTarget(width, height, format, filter),
        write: createTarget(width, height, format, filter),
        width, height,
        texelX: 1 / width, texelY: 1 / height,
        swap: () => {{
          const current = pair.read;
          pair.read = pair.write;
          pair.write = current;
        }}
      }};
      return pair;
    }};

    const resizeDouble = (pair, width, height, format, filter, keep) => {{
      if (keep) {{
        const next = createTarget(width, height, format, filter);
        const u = use('copy');
        gl.uniform1i(u.uTexture, pair.read.attach(0));
        blit(next);
        destroyTarget(pair.read);
        pair.read = next;
      }} else {{
        reshape(pair.read, width, height, format);
      }}
      reshape(pair.write, width, height, format);
      pair.width = width;
      pair.height = height;
      pair.texelX = 1 / width;
      pair.texelY = 1 / height;
    }};

    const resolution = base => {{
      const width = gl.drawingBufferWidth;
      const height = gl.drawingBufferHeight;
      const aspect = Math.max(width, height) / Math.max(1, Math.min(width, height));
      const shortSide = Math.round(base);
      const longSide = Math.round(base * aspect);
      return width > height ? {{ width: longSide, height: shortSide }} : {{ width: shortSide, height: longSide }};
    }};

    const fit = () => {{
      const ratio = Math.min(win.devicePixelRatio || 1, 1.5);
      const width = Math.max(1, Math.floor(win.innerWidth * ratio));
      const height = Math.max(1, Math.floor(win.innerHeight * ratio));
      if (canvas.width === width && canvas.height === height) return;
      canvas.width = width;
      canvas.height = height;
    }};

    const sizes = () => {{
      const q = QUALITY[s.quality];
      const shortSide = Math.min(gl.drawingBufferWidth, gl.drawingBufferHeight);
      return {{ sim: resolution(q.sim), ink: resolution(Math.max(q.sim, Math.min(q.dye, shortSide))) }};
    }};

    fit();
    const initial = sizes();
    const dye = createDouble(initial.ink.width, initial.ink.height, rgba, gl.LINEAR);
    const velocity = createDouble(initial.sim.width, initial.sim.height, rg, gl.LINEAR);
    const pressure = createDouble(initial.sim.width, initial.sim.height, r, gl.NEAREST);
    const divergence = createTarget(initial.sim.width, initial.sim.height, r, gl.NEAREST);
    const curl = createTarget(initial.sim.width, initial.sim.height, r, gl.NEAREST);
    let bloom = null;
    let bloomChain = [];

    const dropBloom = () => {{
      destroyTarget(bloom);
      bloomChain.forEach(destroyTarget);
      bloom = null;
      bloomChain = [];
    }};

    const ensureBloom = () => {{
      if (bloom) return bloom;
      const size = resolution(BLOOM_RESOLUTION);
      const created = createTarget(size.width, size.height, rgba, gl.LINEAR);
      for (let i = 0; i < BLOOM_ITERATIONS; i++) {{
        const width = size.width >> (i + 1);
        const height = size.height >> (i + 1);
        if (width < 2 || height < 2) break;
        bloomChain.push(createTarget(width, height, rgba, gl.LINEAR));
      }}
      bloom = created;
      return created;
    }};

    const resize = () => {{
      fit();
      const next = sizes();
      if (dye.width !== next.ink.width || dye.height !== next.ink.height) {{
        resizeDouble(dye, next.ink.width, next.ink.height, rgba, gl.LINEAR, true);
      }}
      if (velocity.width !== next.sim.width || velocity.height !== next.sim.height) {{
        resizeDouble(velocity, next.sim.width, next.sim.height, rg, gl.LINEAR, true);
        resizeDouble(pressure, next.sim.width, next.sim.height, r, gl.NEAREST, false);
        reshape(divergence, next.sim.width, next.sim.height, r);
        reshape(curl, next.sim.width, next.sim.height, r);
      }}
      const glowSize = resolution(BLOOM_RESOLUTION);
      if (bloom && (bloom.width !== glowSize.width || bloom.height !== glowSize.height)) dropBloom();
    }};

    const radiusFor = scale => {{
      const aspect = canvas.width / canvas.height;
      return ((0.2 * s.size * scale) / 100) * (aspect > 1 ? aspect : 1);
    }};

    const splat = (ax, ay, bx, by, vx, vy, color, radius) => {{
      const u = use('splat');
      gl.uniform1i(u.uTarget, velocity.read.attach(0));
      gl.uniform1f(u.aspectRatio, canvas.width / canvas.height);
      gl.uniform2f(u.pointA, ax, ay);
      gl.uniform2f(u.pointB, bx, by);
      gl.uniform3f(u.color, vx, vy, 0);
      gl.uniform1f(u.radius, radius);
      blit(velocity.write);
      velocity.swap();
      gl.uniform1i(u.uTarget, dye.read.attach(0));
      gl.uniform3f(u.color, color[0], color[1], color[2]);
      blit(dye.write);
      dye.swap();
    }};

    const colorAt = (offset, now) => {{
      const phase = (((offset + (now / 1000) * s.colorSpeed * 0.6) % 1) + 1) % 1;
      const palette = s.palette;
      const position = phase * palette.length;
      const from = palette[Math.floor(position) % palette.length];
      const to = palette[(Math.floor(position) + 1) % palette.length];
      const t = position - Math.floor(position);
      const blend = t * t * (3 - 2 * t);
      return [
        from[0] + (to[0] - from[0]) * blend,
        from[1] + (to[1] - from[1]) * blend,
        from[2] + (to[2] - from[2]) * blend
      ];
    }};

    const flush = (pointer, dt, now) => {{
      const aspect = canvas.width / canvas.height;
      const length = Math.hypot((pointer.x - pointer.px) * aspect, pointer.y - pointer.py);
      if (length > 0.35) {{
        pointer.px = pointer.x;
        pointer.py = pointer.y;
        return;
      }}
      let dx = pointer.x - pointer.px;
      let dy = pointer.y - pointer.py;
      if (aspect < 1) dx *= aspect;
      else dy /= aspect;
      const radius = radiusFor(1);
      const spread = 1 + length / (1.77 * Math.sqrt(radius));
      const push = (6000 * s.force) / Math.sqrt(spread);
      const amount = (0.15 * s.intensity * Math.min(dt * 60, 1)) / Math.sqrt(spread);
      const color = colorAt(pointer.offset, now).map(c => c * amount);
      splat(pointer.px, pointer.py, pointer.x, pointer.y, dx * push, dy * push, color, radius);
      pointer.px = pointer.x;
      pointer.py = pointer.y;
    }};

    const step = dt => {{
      const iterations = QUALITY[s.quality].iterations;
      gl.disable(gl.BLEND);

      let u = use('curl');
      gl.uniform2f(u.texelSize, velocity.texelX, velocity.texelY);
      gl.uniform1i(u.uVelocity, velocity.read.attach(0));
      blit(curl);

      u = use('vorticity');
      gl.uniform2f(u.texelSize, velocity.texelX, velocity.texelY);
      gl.uniform1i(u.uVelocity, velocity.read.attach(0));
      gl.uniform1i(u.uCurl, curl.attach(1));
      gl.uniform1f(u.curl, s.swirl);
      gl.uniform1f(u.dt, dt);
      blit(velocity.write);
      velocity.swap();

      u = use('divergence');
      gl.uniform2f(u.texelSize, velocity.texelX, velocity.texelY);
      gl.uniform1i(u.uVelocity, velocity.read.attach(0));
      blit(divergence);

      u = use('clear');
      gl.uniform1i(u.uTexture, pressure.read.attach(0));
      gl.uniform1f(u.value, 0.1);
      blit(pressure.write);
      pressure.swap();

      u = use('pressure');
      gl.uniform2f(u.texelSize, velocity.texelX, velocity.texelY);
      gl.uniform1i(u.uDivergence, divergence.attach(0));
      for (let i = 0; i < iterations; i++) {{
        gl.uniform1i(u.uPressure, pressure.read.attach(1));
        blit(pressure.write);
        pressure.swap();
      }}

      u = use('gradient');
      gl.uniform2f(u.texelSize, velocity.texelX, velocity.texelY);
      gl.uniform1i(u.uPressure, pressure.read.attach(0));
      gl.uniform1i(u.uVelocity, velocity.read.attach(1));
      blit(velocity.write);
      velocity.swap();

      u = use('advection');
      gl.uniform2f(u.texelSize, velocity.texelX, velocity.texelY);
      gl.uniform1i(u.uVelocity, velocity.read.attach(0));
      gl.uniform1i(u.uSource, velocity.read.attach(0));
      gl.uniform1f(u.dt, dt);
      gl.uniform1f(u.dissipation, 2 / s.momentum);
      blit(velocity.write);
      velocity.swap();

      gl.uniform1i(u.uVelocity, velocity.read.attach(0));
      gl.uniform1i(u.uSource, dye.read.attach(1));
      gl.uniform1f(u.dissipation, 3.5 / s.trail);
      blit(dye.write);
      dye.swap();
    }};

    const applyBloom = amount => {{
      const base = ensureBloom();
      if (!bloomChain.length) return;
      gl.disable(gl.BLEND);
      let u = use('prefilter');
      const knee = BLOOM_THRESHOLD * BLOOM_KNEE + 0.0001;
      gl.uniform3f(u.curve, BLOOM_THRESHOLD - knee, knee * 2, 0.25 / knee);
      gl.uniform1f(u.threshold, BLOOM_THRESHOLD);
      gl.uniform1i(u.uTexture, dye.read.attach(0));
      blit(base);
      u = use('blur');
      gl.uniform1f(u.intensity, 1);
      let lastT = base;
      bloomChain.forEach(target => {{
        gl.uniform2f(u.texelSize, lastT.texelX, lastT.texelY);
        gl.uniform1i(u.uTexture, lastT.attach(0));
        blit(target);
        lastT = target;
      }});
      gl.blendFunc(gl.ONE, gl.ONE);
      gl.enable(gl.BLEND);
      for (let i = bloomChain.length - 2; i >= 0; i--) {{
        const target = bloomChain[i];
        gl.uniform2f(u.texelSize, lastT.texelX, lastT.texelY);
        gl.uniform1i(u.uTexture, lastT.attach(0));
        blit(target);
        lastT = target;
      }}
      gl.disable(gl.BLEND);
      gl.uniform1f(u.intensity, amount);
      gl.uniform2f(u.texelSize, lastT.texelX, lastT.texelY);
      gl.uniform1i(u.uTexture, lastT.attach(0));
      blit(base);
    }};

    const render = () => {{
      if (s.glow > 0) applyBloom(2 * s.glow);
      gl.disable(gl.BLEND);
      const u = use('display');
      gl.uniform2f(u.texelSize, 1 / gl.drawingBufferWidth, 1 / gl.drawingBufferHeight);
      gl.uniform1i(u.uTexture, dye.read.attach(0));
      gl.uniform1i(u.uBloom, (bloom ?? dye.read).attach(1));
      gl.uniform1f(u.shading, s.shading);
      gl.uniform1f(u.bloom, s.glow > 0 ? 1 : 0);
      gl.uniform1f(u.light, 0);
      blit(null);
    }};

    const clearScreen = () => {{
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
    }};

    const pointers = new Map();
    let raf = 0;
    let last = 0;
    let lastActivity = performance.now();

    const frame = now => {{
      raf = 0;
      if (lost || doc.hidden) return;
      const dt = clamp((now - last) / 1000, 0, 1 / 60);
      last = now;
      resize();
      pointers.forEach(pointer => {{
        if (!pointer.moved) return;
        pointer.moved = false;
        flush(pointer, dt, now);
      }});
      step(dt);
      render();
      const quiet = (2.2 * s.trail + 0.4) * 1000;
      if (now - lastActivity < quiet) raf = win.requestAnimationFrame(frame);
      else clearScreen();
    }};

    const wake = () => {{
      lastActivity = performance.now();
      if (raf || lost || doc.hidden) return;
      last = performance.now();
      raf = win.requestAnimationFrame(frame);
    }};

    const track = (id, clientX, clientY) => {{
      const w = win.innerWidth;
      const h = win.innerHeight;
      if (!w || !h) return;
      const x = clientX / w;
      const y = 1 - clientY / h;
      let pointer = pointers.get(id);
      if (!pointer) {{
        pointer = {{ x: 0, y: 0, px: 0, py: 0, ready: false, moved: false, offset: Math.random() }};
        pointers.set(id, pointer);
      }}
      if (!pointer.ready) {{
        pointer.x = pointer.px = x;
        pointer.y = pointer.py = y;
        pointer.ready = true;
        return;
      }}
      pointer.x = x;
      pointer.y = y;
      pointer.moved = true;
      wake();
    }};

    win.addEventListener('pointermove', ev => {{
      if (ev.pointerType !== 'touch') track('p' + ev.pointerId, ev.clientX, ev.clientY);
    }}, {{ passive: true }});

    doc.documentElement.addEventListener('pointerleave', () => {{
      pointers.forEach(p => {{ p.ready = false; }});
    }});

    canvas.addEventListener('webglcontextlost', ev => {{
      ev.preventDefault();
      lost = true;
      if (raf) win.cancelAnimationFrame(raf);
      raf = 0;
    }});
  }})();


  /* ========================================================================
     СЛОЙ 3: <AnimatedContent /> — Наблюдатель за переходами страниц
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
      const delay = Math.min(idx * 55, 420);
      el.style.opacity = '0';
      el.style.transform = 'translate3d(0, 28px, 0) scale(0.99)';
      el.style.transition = 'none';
      setTimeout(() => {{
        win.requestAnimationFrame(() => {{
          el.style.transition = 'opacity 560ms cubic-bezier(0.215, 0.61, 0.355, 1), transform 560ms cubic-bezier(0.215, 0.61, 0.355, 1)';
          el.style.opacity = '1';
          el.style.transform = 'translate3d(0, 0, 0) scale(1)';
        }});
      }}, 16 + delay);
    }});
  }};

  win.__PS_TRIGGER_ANIMATED_CONTENT__ = runAnimatedContent;
  runAnimatedContent();

  // MutationObserver в родительском окне автоматически подхватывает смену страниц в Streamlit!
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

  const legacyBg = parentDoc.getElementById('ps-galaxy-bg-container');
  if (legacyBg) legacyBg.remove();
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
