"""Интеграция компонентов React Bits (Galaxy, TechText, AnimatedContent) для Pharma Sentinel.

Реализует три компонента из библиотеки React Bits:
1. <Galaxy /> — полноэкранный WebGL2 шейдерный фон (#version 300 es) с параметрами:
   density=1, glowIntensity=0.42, flareIntensity=1, starSpeed=0.5, mouseRepulsion=true, clickWarp=true.
2. <TechText /> — интерактивный 2D Canvas заголовок с посимвольной векторной обводкой (reveal="letter"),
   dashLength=4, dashGap=2, specks=15, clickKick=true, guides=false.
3. <AnimatedContent /> — каскадная анимация появления контента и переходов между страницами
   (distance=60, direction="vertical", duration=0.75, ease="power3.out", stagger=0.08, threshold=0.1).
"""


def render_tech_text_and_effects_html(
    text: str = "PHARMA SENTINEL",
    subtitle: str = "КЛИНИЧЕСКАЯ ФАРМАКОЛОГИЯ · DDINTER v2024.11",
    page_key: str = "workspace",
    height: int = 74,
) -> str:
    """Рендерит <TechText /> в шапке и монтирует <Galaxy /> + <AnimatedContent /> в родительский документ."""
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
    height: 52px;
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
    color: #526071;
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
    <div class="header-sub">{subtitle}</div>
  </div>

<script>
/* ==========================================================================
   1. <TechText /> — React Bits Interactive Wordmark
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
    fontSize: 34,
    letterSpacing: -0.04,
    color: '#0F172A',
    accentColor: '#1A56A0',
    align: 'left',
    reach: 200,
    softness: 0.7,
    dashLength: 4,
    dashGap: 2,
    strokeWidth: 1.5,
    lineStyle: 'dashed',
    reveal: 'letter',
    specks: 15,
    selection: true,
    labels: true,
    draggable: true,
    bounce: 0.4,
    sweep: true,
    speed: 1.0,
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
    const current = getComputedStyle(container).color || '#0F172A';
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
    const inkWidth = m.actualBoundingBoxLeft + m.actualBoundingBoxRight;
    const inkHeight = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
    const start = 2;
    const x = start + m.actualBoundingBoxLeft;
    const baseline = (height - inkHeight) / 2 + m.actualBoundingBoxAscent + 4;
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
      const size = pick < 0.46 ? 2 : pick < 0.7 ? 3 : pick < 0.84 ? 4 : 6;
      const large = size >= 6;
      const out = (large ? 6 : 3) + Math.floor(noise(seed, k, cycle, 1) * 3) * grid;
      const x = frame.x1 + Math.round((px + nx * out - frame.x1) / grid) * grid;
      const y = frame.y1 + Math.round((py + ny * out - frame.y1) / grid) * grid;
      const tone = noise(seed, k, cycle, 3);
      const blink = life < 0.06 || (life > 0.32 && life < 0.36) ? 0.35 : 1;
      const alpha = a * (large ? 0.3 + 0.4 * tone : 0.3 + 0.6 * tone) * blink;
      const left = Math.round(x - size / 2);
      const top = Math.round(y - size / 2);
      ctx.globalAlpha = alpha;
      if (tone < 0.26 || (large && tone < 0.78)) {{
        ctx.strokeRect(left + 0.5, top + 0.5, size, size);
      }} else {{
        ctx.fillRect(left, top, size, size);
      }}
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
    ctx.globalAlpha = 0.5 * a;
    ctx.stroke();

    ctx.beginPath();
    for (const [cx, cy] of [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]) {{
      ctx.rect(Math.round(cx) - 2, Math.round(cy) - 2, 4, 4);
    }}
    ctx.globalAlpha = 0.95 * a;
    ctx.fill();
    ctx.globalAlpha = 1;

    if (s.specks > 0) drawSpecks(s, a, accent);

    if (!s.labels) return;
    ctx.font = LABEL_FONT;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillStyle = accent;
    ctx.globalAlpha = 0.78 * a;
    const label = moved > 1
      ? `${{signed(Math.round(glyph.offset.x))}}, ${{signed(Math.round(-glyph.offset.y))}}`
      : `${{glyph.char}} ${{Math.round(glyph.box.x2 - glyph.box.x1)}}×${{Math.round(glyph.box.y2 - glyph.box.y1)}}`;
    ctx.fillText(label, Math.round(frame.x2) + 6, Math.round(frame.y1));
    ctx.globalAlpha = 1;
  }};

  const kick = index => {{
    const strength = (word ? word.size : 40) * 9.5;
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
   2. <Galaxy /> + <AnimatedContent /> — Монтирование в родительское окно
   ========================================================================== */
(function mountParentEffects() {{
  let parentWin, parentDoc;
  try {{
    parentWin = window.parent;
    parentDoc = window.parent.document;
    if (!parentDoc || !parentDoc.body) return;
  }} catch (e) {{
    return;
  }}

  /* --- Прозрачность контейнеров Streamlit поверх <Galaxy /> --- */
  if (!parentDoc.getElementById('ps-galaxy-parent-styles')) {{
    const styleEl = parentDoc.createElement('style');
    styleEl.id = 'ps-galaxy-parent-styles';
    styleEl.textContent = `
      .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{
        background: transparent !important;
      }}
      [data-testid="stMainBlockContainer"], .block-container {{
        position: relative;
        z-index: 2;
      }}
    `;
    parentDoc.head.appendChild(styleEl);
  }}

  /* --- A. <Galaxy /> WebGL2 Shader Background --- */
  if (!parentDoc.getElementById('ps-galaxy-bg-container')) {{
    const bgWrap = parentDoc.createElement('div');
    bgWrap.id = 'ps-galaxy-bg-container';
    bgWrap.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:0;pointer-events:none;overflow:hidden;';
    const canvas = parentDoc.createElement('canvas');
    canvas.id = 'ps-galaxy-bg-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    canvas.style.cssText = 'position:absolute;inset:0;display:block;width:100%;height:100%;';
    bgWrap.appendChild(canvas);
    parentDoc.body.prepend(bgWrap);

    const gl = canvas.getContext('webgl2', {{
      alpha: true,
      premultipliedAlpha: true,
      antialias: false,
      depth: false,
      stencil: false
    }});

    if (gl) {{
      const MAX_LAYERS = 8;
      const MAX_COLORS = 4;
      const INTRO_SECONDS = 2.2;

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
uniform vec3 uColors[${{MAX_COLORS}}];
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

vec3 hsv2rgb(vec3 c) {{
  vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}}

float Star(vec2 uv, float flare, vec2 radial, float invReach) {{
#ifdef WARP
  float along = dot(uv, radial);
  float d = sqrt(max(dot(uv, uv) - uSquash * along * along, 0.0));
#else
  float d = length(uv);
#endif
  float m = uStarGlow / d;
  float rays = smoothstep(0.0, 1.0, 1.0 - abs(uv.x * uv.y * 1000.0));
  m += rays * flare * uFlareGain;
  uv *= MAT45;
  rays = smoothstep(0.0, 1.0, 1.0 - abs(uv.x * uv.y * 1000.0));
  m += rays * 0.3 * flare * uFlareGain;
  m *= smoothstep(1.0, 0.2, d * invReach);
#ifdef WARP
  m *= mix(1.0, smoothstep(1.0, 0.55, length(uv) * invReach), min(uWarp * 4.0, 1.0));
#endif
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

#ifdef PALETTE
      float pick = Hash21(si + 7.0) * float(uColorCount);
      vec3 base = uColors[int(min(floor(pick), float(uColorCount - 1)))];
#else
      float red = smoothstep(STAR_COLOR_CUTOFF, 1.0, Hash21(si + 1.0)) + STAR_COLOR_CUTOFF;
      float blu = smoothstep(STAR_COLOR_CUTOFF, 1.0, Hash21(si + 3.0)) + STAR_COLOR_CUTOFF;
      float grn = min(red, blu) * seed;
      vec3 base = vec3(red, grn, blu);
      float hue = atan(base.g - base.r, base.b - base.r) / (2.0 * 3.14159) + 0.5;
      hue = fract(hue + uHueShift / 360.0);
      float sat = length(base - vec3(dot(base, vec3(0.299, 0.587, 0.114)))) * uSaturation;
      float val = max(max(base.r, base.g), base.b);
      base = hsv2rgb(vec3(hue, sat, val));
#endif

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
  if (uAutoCenterRepulsion > 0.0) {{
    strength = uAutoCenterRepulsion;
    push = strength * 0.05;
  }} else if (uMouseRepulsion > 0.5) {{
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
  for (int k = 0; k < ${{MAX_LAYERS}}; k++) {{
    if (k >= uLayers) break;
    float i = float(k) / layers;
    float depth = fract(i + uDepth);
    float scale = mix(20.0 * uDensity, 0.5 * uDensity, depth);
    float fade = depth * smoothstep(1.0, 0.9, depth);
    vec2 offset = vec2(i * 453.32);
    col += StarLayer(uv * scale + offset, radial, repelAt * scale + offset, push * scale, 1.0 / (scale * radius)) * fade;
  }}
  col *= uReveal;

  if (uMode > 1.5) {{
    vec3 lit = col * smoothstep(0.0, 0.3, length(col));
    float energy = max(max(lit.r, lit.g), lit.b);
    vec3 tint = lit / max(energy, 0.0001);
    vec3 ink = tint * (0.16 / max(dot(tint, vec3(0.2126, 0.7152, 0.0722)), 0.16));
    float coverage = pow(min(energy * 1.3, 1.0), 1.3) * 0.92 * uOpacity;
    outColor = uMode > 2.5 ? vec4(ink * coverage, coverage) : vec4(mix(uBackground, ink, coverage), 1.0);
  }} else if (uMode > 0.5) {{
    float alpha = min(smoothstep(0.0, 0.3, length(col)), 1.0) * uOpacity;
    outColor = vec4(col * alpha, alpha);
  }} else {{
    outColor = vec4(mix(uBackground, col, uOpacity), 1.0);
  }}
}}`;

      const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
      const keyOf = (palette, repel, warp) => (palette ? 4 : 0) + (repel ? 2 : 0) + (warp ? 1 : 0);

      const start = (gl, palette, repel, warp) => {{
        const defines = `${{palette ? '#define PALETTE\\n' : ''}}${{repel ? '#define REPEL\\n' : ''}}${{warp ? '#define WARP\\n' : ''}}`;
        const program = gl.createProgram();
        const vertex = gl.createShader(gl.VERTEX_SHADER);
        const fragment = gl.createShader(gl.FRAGMENT_SHADER);
        if (!program || !vertex || !fragment) return null;
        gl.shaderSource(vertex, VERTEX);
        gl.shaderSource(fragment, FRAGMENT.replace('\\n', `\\n${{defines}}`));
        gl.compileShader(vertex);
        gl.compileShader(fragment);
        gl.attachShader(program, vertex);
        gl.attachShader(program, fragment);
        gl.bindAttribLocation(program, 0, 'aPosition');
        gl.linkProgram(program);
        gl.deleteShader(vertex);
        gl.deleteShader(fragment);
        return program;
      }};

      const finish = (gl, program) => {{
        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return null;
        const uniforms = {{}};
        const count = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
        for (let i = 0; i < count; i++) {{
          const info = gl.getActiveUniform(program, i);
          if (info) uniforms[info.name.replace('[0]', '')] = gl.getUniformLocation(program, info.name);
        }}
        return {{ program, uniforms }};
      }};

      const s = {{
        focal: [0.5, 0.5],
        rotation: [1.0, 0.0],
        starSpeed: 0.5,
        density: 1.0,
        hueShift: 140,
        disableAnimation: false,
        speed: 1.0,
        mouseInteraction: true,
        glowIntensity: 0.38,
        saturation: 0.35,
        mouseRepulsion: true,
        repulsionStrength: 2.0,
        twinkleIntensity: 0.3,
        rotationSpeed: 0.1,
        autoCenterRepulsion: 0,
        transparent: false,
        lightMode: true,
        palette: ['#1A56A0', '#0D7A75', '#1E3A5F', '#2563EB'],
        starSize: 1.2,
        flareIntensity: 1.0,
        layers: 4,
        reverse: false,
        clickWarp: true,
        intro: true,
        backgroundColor: '#FAF9F6',
        opacity: 0.85,
        dpr: 2
      }};

      const programs = new Map();
      const entry = (palette, repel, warp) => {{
        const key = keyOf(palette, repel, warp);
        let found = programs.get(key);
        if (!found) {{
          found = {{ program: start(gl, palette, repel, warp), linked: null, done: false }};
          programs.set(key, found);
        }}
        return found;
      }};
      const variant = (palette, repel, warp) => {{
        const found = entry(palette, repel, warp);
        if (!found.done && found.program) {{
          found.linked = finish(gl, found.program);
          found.done = true;
        }}
        return found.linked;
      }};

      if (variant(true, false, false)) {{
        const buffer = gl.createBuffer();
        const vao = gl.createVertexArray();
        gl.bindVertexArray(vao);
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
        gl.enableVertexAttribArray(0);
        gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

        const probe = parentDoc.createElement('canvas').getContext('2d', {{ willReadFrequently: true }});
        const reduce = parentWin.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
        const parse = (value, fallback) => {{
          if (!value || !probe) return fallback;
          probe.clearRect(0, 0, 1, 1);
          probe.fillStyle = value;
          probe.fillRect(0, 0, 1, 1);
          const [r, g, b] = probe.getImageData(0, 0, 1, 1).data;
          return [r / 255, g / 255, b / 255];
        }};

        const colors = new Float32Array(MAX_COLORS * 3);
        s.palette.forEach((val, idx) => colors.set(parse(val, [0.1, 0.3, 0.6]), idx * 3));
        const bgRgb = parse(s.backgroundColor, [0.98, 0.976, 0.965]);

        const pointer = {{ x: 0.5, y: 0.5, inside: false }};
        const state = {{
          time: 0, gloss: 0, depth: 0, angle: 0,
          mx: 0.5, my: 0.5, active: 0, boost: 0,
          reveal: s.intro && !reduce ? 0 : 1
        }};
        let raf = 0;
        let last = 0;

        const render = () => {{
          const mode = s.lightMode ? (s.transparent ? 3 : 2) : s.transparent ? 1 : 0;
          const repel = s.mouseRepulsion && state.active > 0;
          const warp = state.boost > 0;
          const base = variant(true, false, false);
          if (!base) return;
          const program = (repel || warp ? variant(true, repel, warp) : null) ?? base;
          const u = program.uniforms;
          gl.viewport(0, 0, canvas.width, canvas.height);
          gl.useProgram(program.program);
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
          const stretch = 1 + state.boost * 5;
          gl.uniform1f(u.uStarGlow, (0.05 * s.glowIntensity * s.starSize) / Math.pow(stretch, 0.6));
          gl.uniform1f(u.uFlareGain, s.glowIntensity * s.flareIntensity);
          gl.uniform1f(u.uSquash, 1 - 1 / (stretch * stretch));
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
          gl.uniform1f(u.uWarp, state.boost);
          const fade = Math.min(1, state.reveal / 0.35);
          gl.uniform1f(u.uReveal, fade * fade * (3 - 2 * fade));
          gl.uniform1f(u.uMode, mode);
          gl.uniform3fv(u.uBackground, bgRgb);
          gl.uniform1f(u.uOpacity, s.opacity);
          gl.drawArrays(gl.TRIANGLES, 0, 3);
        }};

        const frame = now => {{
          raf = 0;
          if (parentDoc.hidden) return;
          const dt = last ? clamp((now - last) / 1000, 0.0005, 0.05) : 1 / 60;
          last = now;
          const motion = s.disableAnimation || reduce ? 0 : 1;
          if (s.intro && !reduce && state.reveal < 1) {{
            state.reveal = Math.min(1, state.reveal + dt / INTRO_SECONDS);
            state.boost = Math.max(state.boost, Math.pow(1 - state.reveal, 2) * 1.4);
          }} else {{
            state.reveal = 1;
          }}
          const flight = (s.starSpeed / 10) * (s.reverse ? -1 : 1);
          state.time += dt * motion;
          state.gloss += dt * flight * motion;
          state.depth += dt * flight * s.speed * motion * (1 + state.boost * 14);
          state.angle += dt * s.rotationSpeed * motion;
          state.boost *= Math.exp(-dt * 1.3);
          if (state.boost < 0.001) state.boost = 0;

          const follow = 1 - Math.exp(-dt / 0.325);
          const engaged = s.mouseInteraction && pointer.inside && !reduce;
          if (engaged) {{
            state.mx += (pointer.x - state.mx) * follow;
            state.my += (pointer.y - state.my) * follow;
          }}
          const target = engaged ? 1 : 0;
          state.active += (target - state.active) * follow;
          if (Math.abs(target - state.active) < 0.001) state.active = target;

          render();
          if (motion > 0 || state.boost > 0 || state.active !== target || state.reveal < 1) {{
            raf = parentWin.requestAnimationFrame(frame);
          }} else {{
            last = 0;
          }}
        }};

        const wake = () => {{
          if (!raf && !parentDoc.hidden) raf = parentWin.requestAnimationFrame(frame);
        }};

        const resize = () => {{
          const w = Math.max(1, parentWin.innerWidth);
          const h = Math.max(1, parentWin.innerHeight);
          const ratio = Math.min(s.dpr || parentWin.devicePixelRatio || 1, 2);
          canvas.width = Math.max(1, Math.round(w * ratio));
          canvas.height = Math.max(1, Math.round(h * ratio));
          render();
          wake();
        }};

        parentWin.addEventListener('pointermove', ev => {{
          const w = Math.max(1, parentWin.innerWidth);
          const h = Math.max(1, parentWin.innerHeight);
          pointer.inside = true;
          pointer.x = ev.clientX / w;
          pointer.y = 1 - ev.clientY / h;
          wake();
        }}, {{ passive: true }});

        parentWin.addEventListener('pointerdown', () => {{
          if (!s.clickWarp || reduce) return;
          state.boost = Math.min(1.6, state.boost + 0.9);
          wake();
        }}, {{ passive: true }});

        parentWin.addEventListener('resize', resize, {{ passive: true }});
        resize();
      }}
    }}
  }}

  /* ==========================================================================
     3. <AnimatedContent /> — React Bits GSAP + ScrollTrigger Page Transitions
     ========================================================================== */
  const currentPage = {page_key!r};
  const reduce = parentWin.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  if (reduce) return;

  const runAnimatedContent = () => {{
    const mainBlock = parentDoc.querySelector('[data-testid="stMainBlockContainer"], .block-container');
    if (!mainBlock) return;

    const wrapper = mainBlock.querySelector('.ps-animated-page-root');
    const targets = Array.from(
      (wrapper || mainBlock).querySelectorAll(
        '.ps-anim-item, .ps-stat-box, .ps-card-finding, .ps-supp-row, [data-testid="stDataFrame"], [data-testid="stPlot"]'
      )
    );

    const stamp = currentPage + '_' + targets.length;
    if (mainBlock.dataset.psLastAnimated === stamp) return;
    mainBlock.dataset.psLastAnimated = stamp;

    const gsapInstance = parentWin.gsap;
    if (gsapInstance) {{
      gsapInstance.killTweensOf(targets);
      gsapInstance.fromTo(
        targets,
        {{ y: 55, opacity: 0, scale: 0.985 }},
        {{
          y: 0,
          opacity: 1,
          scale: 1,
          duration: 0.72,
          ease: 'power3.out',
          stagger: 0.07,
          clearProps: 'transform'
        }}
      );
    }} else {{
      // Мгновенный аппаратный фоллбэк (power3.out = cubic-bezier(0.215, 0.61, 0.355, 1))
      targets.forEach((el, idx) => {{
        const delay = Math.min(idx * 65, 520);
        el.style.opacity = '0';
        el.style.transform = 'translate3d(0, 52px, 0) scale(0.985)';
        el.style.transition = 'none';
        setTimeout(() => {{
          parentWin.requestAnimationFrame(() => {{
            el.style.transition = 'opacity 720ms cubic-bezier(0.215, 0.61, 0.355, 1), transform 720ms cubic-bezier(0.215, 0.61, 0.355, 1)';
            el.style.opacity = '1';
            el.style.transform = 'translate3d(0, 0, 0) scale(1)';
          }});
        }}, 16 + delay);
      }});
    }}
  }};

  // Подгружаем GSAP + ScrollTrigger в родительское окно, если еще не загружен
  if (!parentWin.gsap && !parentDoc.getElementById('ps-gsap-script')) {{
    const s1 = parentDoc.createElement('script');
    s1.id = 'ps-gsap-script';
    s1.src = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js';
    s1.onload = () => {{
      const s2 = parentDoc.createElement('script');
      s2.src = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js';
      s2.onload = () => {{
        if (parentWin.gsap && parentWin.ScrollTrigger) {{
          parentWin.gsap.registerPlugin(parentWin.ScrollTrigger);
        }}
      }};
      parentDoc.head.appendChild(s2);
    }};
    parentDoc.head.appendChild(s1);
  }}

  runAnimatedContent();
  setTimeout(runAnimatedContent, 80);
  setTimeout(runAnimatedContent, 220);
}})();
</script>
</body>
</html>"""
