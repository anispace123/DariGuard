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
    height: int = 8,
    sound_enabled: bool = False,
) -> str:
    """Инжектирует глобальный движок сайта: интерактивный молекулярный фон, React Bits <BubbleMenu /> в правом верхнем углу и WebAudio."""
    sound_flag_js = "true" if sound_enabled else "false"
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 100%;
    height: {height}px;
    overflow: hidden;
    background: transparent;
  }}
</style>
</head>
<body>
<script>
/* ==========================================================================
   1. Глобальный движок сайта PHARMA SENTINEL V6:
      - Интерактивный молекулярный фон со сборкой молекул вокруг курсора (#ps-molecular-canvas)
      - Навигационное <BubbleMenu /> (React Bits + GSAP) в правом верхнем углу (#ps-reactbits-bubble-dock)
      - Полное скрытие старой горизонтальной радио-полосы навигации
      - Тактильное WebAudio-сопровождение ховеров, карточек и кликов BubbleMenu
   ========================================================================== */
function initPharmaSentinelPersistentEngine() {{
  if (window.__PS_PERSISTENT_ENGINE_V7__) return;
  window.__PS_PERSISTENT_ENGINE_V7__ = true;
  window.__PS_PERSISTENT_ENGINE_V6__ = true;
  window.__PS_PERSISTENT_ENGINE_ACTIVE__ = true;

  const doc = document;
  const win = window;
  const reducedMotion = win.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

  /* ------------------------------------------------------------------------
     Базовые стили сайта + полное скрытие горизонтальной радио-навигации +
     React Bits <BubbleMenu /> в правом верхнем углу + универсальные ховеры карточек
     ------------------------------------------------------------------------ */
  let styleTag = doc.getElementById('ps-persistent-layer-styles');
  if (!styleTag) {{
    styleTag = doc.createElement('style');
    styleTag.id = 'ps-persistent-layer-styles';
  }}
  styleTag.textContent = `
    html, body {{
      background-color: #070E12 !important;
      color: #EAF2F2 !important;
    }}
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{
      background: transparent !important;
    }}
    [data-testid="stMainBlockContainer"], .block-container {{
      position: relative !important;
      z-index: 2 !important;
      padding-top: 2.2rem !important;
    }}

    /* ПОЛНОЕ СКРЫТИЕ старой горизонтальной радио-строки переключения страниц */
    .st-key-main_nav_radio,
    div[data-testid="stElementContainer"]:has(.st-key-main_nav_radio),
    div[data-testid="stElementContainer"]:has(div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5)),
    div[data-testid="stRadio"]:has(div[role="radiogroup"] > label:nth-child(5)) {{
      position: fixed !important;
      top: -9999px !important;
      left: -9999px !important;
      width: 1px !important;
      height: 1px !important;
      opacity: 0 !important;
      pointer-events: none !important;
      overflow: hidden !important;
      margin: 0 !important;
      padding: 0 !important;
      border: 0 !important;
      clip: rect(0, 0, 0, 0) !important;
      z-index: -9999 !important;
    }}

    /* Молекулярный интерактивный фон */
    #ps-molecular-layer {{
      position: fixed !important;
      inset: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      z-index: 0 !important;
      pointer-events: none !important;
      overflow: hidden !important;
      background:
        radial-gradient(circle at 78% 24%, rgba(54, 214, 176, 0.14) 0%, rgba(103, 183, 209, 0.08) 32%, rgba(7, 14, 18, 0) 68%),
        radial-gradient(circle at 18% 76%, rgba(103, 183, 209, 0.13) 0%, rgba(54, 214, 176, 0.05) 36%, rgba(7, 14, 18, 0) 70%),
        linear-gradient(160deg, #060C10 0%, #0A171F 52%, #071E28 100%) !important;
    }}
    #ps-molecular-canvas {{
      position: absolute !important;
      inset: 0 !important;
      display: block !important;
      width: 100% !important;
      height: 100% !important;
      pointer-events: none !important;
    }}

    /* ======================================================================
       REACT BITS <BubbleMenu /> — СВОРАЧИВАЕМОЕ МЕНЮ В ПРАВОМ ВЕРХНЕМ УГЛУ
       ====================================================================== */
    #ps-reactbits-bubble-dock.bubble-menu {{
      position: fixed !important;
      top: 14px !important;
      right: 20px !important;
      left: auto !important;
      transform: none !important;
      display: flex !important;
      align-items: center !important;
      justify-content: flex-end !important;
      gap: 8px !important;
      padding: 0 !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      backdrop-filter: none !important;
      pointer-events: none !important;
      z-index: 999995 !important;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    #ps-reactbits-bubble-dock .bubble {{
      --bubble-size: 38px;
      width: var(--bubble-size);
      height: var(--bubble-size);
      border-radius: 9999px;
      background: rgba(11, 18, 22, 0.94);
      border: 1px solid rgba(54, 214, 176, 0.48);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.60), 0 0 16px rgba(54, 214, 176, 0.20);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      pointer-events: auto;
      cursor: pointer;
      user-select: none;
      transition:
        transform 220ms cubic-bezier(0.34, 1.56, 0.64, 1),
        border-color 180ms ease,
        box-shadow 180ms ease,
        background 180ms ease;
    }}

    #ps-reactbits-bubble-dock .bubble:hover {{
      transform: translateY(-2px) scale(1.04);
      border-color: #36D6B0;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.70), 0 0 24px rgba(54, 214, 176, 0.42);
      background: rgba(17, 30, 36, 0.96);
    }}

    #ps-reactbits-bubble-dock .logo-bubble {{
      width: auto !important;
      min-height: 38px;
      height: 38px;
      padding: 0 13px;
      gap: 8px;
      color: #EAF2F2;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.03em;
      white-space: nowrap;
    }}

    #ps-reactbits-bubble-dock .ps-rb-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #36D6B0;
      box-shadow: 0 0 10px #36D6B0;
      flex-shrink: 0;
    }}

    #ps-reactbits-bubble-dock .toggle-bubble.menu-btn {{
      width: 38px;
      height: 38px;
      flex-direction: column;
      gap: 0;
      padding: 0;
      background: linear-gradient(135deg, rgba(54, 214, 176, 0.22), rgba(17, 27, 32, 0.95));
      border: 1px solid #36D6B0;
    }}

    #ps-reactbits-bubble-dock .menu-line {{
      width: 17px;
      height: 2px;
      background: #EAF2F2;
      border-radius: 2px;
      display: block;
      margin: 0 auto;
      transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.2s ease;
      transform-origin: center;
    }}

    #ps-reactbits-bubble-dock .menu-line + .menu-line {{
      margin-top: 5px;
    }}

    #ps-reactbits-bubble-dock .toggle-bubble.menu-btn.open {{
      background: linear-gradient(135deg, #36D6B0 0%, #24A98B 100%);
      box-shadow: 0 0 24px rgba(54, 214, 176, 0.55);
    }}

    #ps-reactbits-bubble-dock .toggle-bubble.menu-btn.open .menu-line {{
      background: #041410;
    }}

    #ps-reactbits-bubble-dock .toggle-bubble.menu-btn.open .menu-line.first {{
      transform: translateY(3.5px) rotate(45deg);
    }}

    #ps-reactbits-bubble-dock .toggle-bubble.menu-btn.open .menu-line.second {{
      transform: translateY(-3.5px) rotate(-45deg);
    }}

    /* Панель раскрывающихся пилюль React Bits <BubbleMenu /> в правом верхнем углу */
    #ps-rb-overlay.bubble-menu-items {{
      position: fixed;
      top: 58px;
      right: 20px;
      width: min(340px, calc(100vw - 28px));
      padding: 12px;
      border-radius: 20px;
      background: rgba(9, 16, 20, 0.96);
      border: 1px solid rgba(54, 214, 176, 0.42);
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.85), 0 0 32px rgba(54, 214, 176, 0.22);
      backdrop-filter: blur(22px);
      -webkit-backdrop-filter: blur(22px);
      display: none;
      pointer-events: none;
      z-index: 999994;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    #ps-rb-overlay.bubble-menu-items.open {{
      pointer-events: auto;
    }}

    #ps-rb-overlay .pill-list {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 7px;
      width: 100%;
    }}

    #ps-rb-overlay .pill-list .pill-col {{
      display: flex;
      width: 100%;
      box-sizing: border-box;
    }}

    #ps-rb-overlay .pill-link {{
      --pill-bg: #111B20;
      --pill-color: #EAF2F2;
      --pill-border: rgba(103, 183, 209, 0.25);
      --item-rot: 0deg;
      --hover-bg: #36D6B0;
      --hover-color: #041410;
      width: 100%;
      min-height: 40px;
      height: 40px;
      padding: 0 14px;
      font-size: 0.82rem;
      font-weight: 600;
      line-height: 1.2;
      border-radius: 999px;
      background: var(--pill-bg);
      color: var(--pill-color);
      border: 1px solid var(--pill-border);
      text-decoration: none;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: 9px;
      position: relative;
      transition:
        background 0.22s ease,
        color 0.22s ease,
        border-color 0.22s ease,
        box-shadow 0.22s ease,
        transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
      will-change: transform;
      cursor: pointer;
      white-space: nowrap;
      overflow: hidden;
    }}

    @media (min-width: 769px) {{
      #ps-rb-overlay .pill-link {{
        transform: rotate(var(--item-rot));
      }}
      #ps-rb-overlay .pill-link:hover {{
        transform: rotate(var(--item-rot)) scale(1.05) translateY(-2px) !important;
        background: var(--hover-bg) !important;
        color: var(--hover-color) !important;
        border-color: var(--hover-bg) !important;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.55), 0 0 20px var(--hover-bg) !important;
      }}
      #ps-rb-overlay .pill-link:active {{
        transform: rotate(var(--item-rot)) scale(0.96) !important;
      }}
    }}

    #ps-rb-overlay .pill-link.active {{
      background: linear-gradient(135deg, #36D6B0 0%, #24A98B 100%) !important;
      color: #041410 !important;
      border-color: #36D6B0 !important;
      font-weight: 700 !important;
      box-shadow: 0 0 22px rgba(54, 214, 176, 0.48) !important;
    }}

    #ps-rb-overlay .pill-link .pill-num {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 999px;
      background: rgba(54, 214, 176, 0.14);
      color: #36D6B0;
      border: 1px solid rgba(54, 214, 176, 0.35);
      transition: all 0.2s ease;
    }}

    #ps-rb-overlay .pill-link:hover .pill-num,
    #ps-rb-overlay .pill-link.active .pill-num {{
      background: rgba(4, 20, 16, 0.22);
      color: inherit;
      border-color: rgba(4, 20, 16, 0.35);
    }}

    #ps-rb-overlay .pill-link .pill-label {{
      display: inline-block;
      will-change: transform, opacity;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    @media (max-width: 768px) {{
      #ps-reactbits-bubble-dock.bubble-menu {{
        top: 10px !important;
        right: 12px !important;
        gap: 6px !important;
      }}
      #ps-reactbits-bubble-dock .logo-bubble {{
        height: 36px;
        min-height: 36px;
        padding: 0 10px;
        font-size: 10px;
        max-width: 58vw;
        overflow: hidden;
        text-overflow: ellipsis;
      }}
      #ps-reactbits-bubble-dock .toggle-bubble.menu-btn {{
        width: 36px;
        height: 36px;
      }}
      #ps-rb-overlay.bubble-menu-items {{
        top: 52px;
        right: 10px;
        width: calc(100vw - 20px);
        padding: 10px;
      }}
      #ps-rb-overlay .pill-link {{
        min-height: 38px;
        height: 38px;
        font-size: 0.78rem;
        padding: 0 12px;
      }}
      #ps-rb-overlay .pill-link:hover {{
        transform: scale(1.03) !important;
        background: var(--hover-bg) !important;
        color: var(--hover-color) !important;
      }}
    }}

    /* ======================================================================
       УНИВЕРСАЛЬНЫЕ ХОВЕР-ЭФФЕКТЫ НА ВСЕ КАРТОЧКИ И ИНТЕРАКТИВНЫЕ БЛОКИ
       ====================================================================== */
    .ps-stat-box,
    .ps-card-finding,
    .ps-supp-row,
    .ps-overview-card,
    .ps-qgen-card,
    .ps-token-bar,
    .ps-disclaimer,
    .ps-rec-box,
    [data-testid="stDataFrame"],
    [data-testid="stExpander"],
    div[data-testid="stMarkdownContainer"] > div[style*="border"] {{
      transition:
        transform 220ms cubic-bezier(0.34, 1.56, 0.64, 1) !important,
        border-color 200ms ease !important,
        box-shadow 220ms ease !important,
        background 220ms ease !important;
    }}

    .ps-stat-box:hover,
    .ps-card-finding:hover,
    .ps-supp-row:hover,
    .ps-overview-card:hover,
    .ps-qgen-card:hover,
    .ps-token-bar:hover,
    .ps-disclaimer:hover,
    .ps-rec-box:hover,
    [data-testid="stDataFrame"]:hover,
    [data-testid="stExpander"]:hover,
    div[data-testid="stMarkdownContainer"] > div[style*="border"]:hover {{
      transform: translateY(-5px) scale(1.01) !important;
      border-color: #36D6B0 !important;
      box-shadow: 0 14px 34px rgba(0, 0, 0, 0.58), 0 0 24px rgba(54, 214, 176, 0.24) !important;
    }}
  `;
  if (!styleTag.parentNode) {{
    doc.head.appendChild(styleTag);
  }}

  const oldLayers = ['ps-galaxy-layer', 'ps-splash-layer', 'ps-galaxy-bg-container'];
  oldLayers.forEach(id => {{
    const el = doc.getElementById(id);
    if (el) el.remove();
  }});

  /* ------------------------------------------------------------------------
     Web Audio API: звуковое сопровождение на BubbleMenu, карточках и кнопках
     ------------------------------------------------------------------------ */
  let audioCtx = null;
  let lastHoverSoundAt = 0;

  function ensureAudioContext() {{
    const AudioContextClass = win.AudioContext || win.webkitAudioContext;
    if (!AudioContextClass) return null;
    if (!audioCtx) audioCtx = new AudioContextClass();
    if (audioCtx.state === 'suspended') {{
      audioCtx.resume().catch(() => {{}});
    }}
    return audioCtx;
  }}

  // Принудительная активация звука по первому клику/касанию (требование современных браузеров)
  const unlockAudioContext = () => {{
    const ctx = ensureAudioContext();
    if (ctx && ctx.state === 'suspended') {{
      ctx.resume().catch(() => {{}});
    }}
    win.removeEventListener('pointerdown', unlockAudioContext);
    win.removeEventListener('click', unlockAudioContext);
    doc.removeEventListener('pointerdown', unlockAudioContext);
  }};
  win.addEventListener('pointerdown', unlockAudioContext, {{ passive: true }});
  win.addEventListener('click', unlockAudioContext, {{ passive: true }});
  doc.addEventListener('pointerdown', unlockAudioContext, {{ passive: true }});

  function playScientificCue(freqStart = 528, freqEnd = 784) {{
    if (win.__PS_SOUND_ENABLED__ === false || reducedMotion) return;
    try {{
      const ctxAudio = ensureAudioContext();
      if (!ctxAudio) return;
      const now = ctxAudio.currentTime;
      const osc = ctxAudio.createOscillator();
      const gain = ctxAudio.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freqStart, now);
      osc.frequency.exponentialRampToValueAtTime(freqEnd, now + 0.085);
      gain.gain.setValueAtTime(0.065, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.11);
      osc.connect(gain);
      gain.connect(ctxAudio.destination);
      osc.start(now);
      osc.stop(now + 0.11);
    }} catch (e) {{}}
  }}

  function playBubbleToggleCue(opening = true) {{
    if (win.__PS_SOUND_ENABLED__ === false || reducedMotion) return;
    try {{
      const ctxAudio = ensureAudioContext();
      if (!ctxAudio) return;
      const now = ctxAudio.currentTime;
      const notes = opening ? [523.25, 659.25, 783.99] : [783.99, 659.25, 523.25];
      notes.forEach((freq, idx) => {{
        const osc = ctxAudio.createOscillator();
        const gain = ctxAudio.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + idx * 0.028);
        gain.gain.setValueAtTime(0.055, now + idx * 0.028);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.028 + 0.095);
        osc.connect(gain);
        gain.connect(ctxAudio.destination);
        osc.start(now + idx * 0.028);
        osc.stop(now + idx * 0.028 + 0.095);
      }});
    }} catch (e) {{}}
  }}

  function playHoverCue() {{
    if (win.__PS_SOUND_ENABLED__ === false || reducedMotion) return;
    const nowPerf = performance.now();
    if (nowPerf - lastHoverSoundAt < 55) return;
    lastHoverSoundAt = nowPerf;
    try {{
      const ctxAudio = ensureAudioContext();
      if (!ctxAudio) return;
      const now = ctxAudio.currentTime;
      const osc = ctxAudio.createOscillator();
      const gain = ctxAudio.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.exponentialRampToValueAtTime(1174.66, now + 0.035);
      gain.gain.setValueAtTime(0.045, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.045);
      osc.connect(gain);
      gain.connect(ctxAudio.destination);
      osc.start(now);
      osc.stop(now + 0.045);
    }} catch (e) {{}}
  }}

  win.__PS_PLAY_CUE__ = playScientificCue;
  win.__PS_PLAY_HOVER__ = playHoverCue;

  /* ------------------------------------------------------------------------
     Интерактивная молекулярная сеть: при наведении и клике курсора
     точки притягиваются, соприкасаются и собираются в светящуюся молекулу!
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

  const NODE_COUNT = 64;
  const MAX_DISTANCE = 148;
  const ATOMS = ['C', 'N', 'O', 'C', 'C', 'N', 'O', 'S', 'P', 'F'];
  const nodes = [];
  const ripples = [];

  const mouse = {{ x: -9999, y: -9999, active: false, pressed: false, clickTime: 0 }};
  let width = win.innerWidth;
  let height = win.innerHeight;
  let dpr = Math.min(win.devicePixelRatio || 1, 2);
  let rafId = 0;

  const ATOM_PALETTE = [
    {{ fill: 'rgba(54, 214, 176, 0.72)', glow: 'rgba(54, 214, 176, 0.24)' }},
    {{ fill: 'rgba(103, 183, 209, 0.72)', glow: 'rgba(103, 183, 209, 0.24)' }},
    {{ fill: 'rgba(245, 158, 11, 0.58)', glow: 'rgba(245, 158, 11, 0.18)' }},
    {{ fill: 'rgba(234, 242, 242, 0.62)', glow: 'rgba(234, 242, 242, 0.16)' }}
  ];

  const RING_SLOTS = [
    {{ dx: 0, dy: 0 }},
    {{ dx: 36, dy: 0 }},
    {{ dx: 18, dy: 31 }},
    {{ dx: -18, dy: 31 }},
    {{ dx: -36, dy: 0 }},
    {{ dx: -18, dy: -31 }},
    {{ dx: 18, dy: -31 }},
    {{ dx: 68, dy: 18 }},
    {{ dx: -68, dy: -18 }},
    {{ dx: 0, dy: 64 }},
    {{ dx: 0, dy: -64 }},
    {{ dx: 54, dy: -42 }},
    {{ dx: -54, dy: 42 }}
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
      const pal = ATOM_PALETTE[i % ATOM_PALETTE.length];
      nodes.push({{
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.48,
        vy: (Math.random() - 0.5) * 0.48,
        radius: 2.2 + (i % 3) * 0.9,
        fill: pal.fill,
        glow: pal.glow,
        atom: ATOMS[i % ATOMS.length],
        doubleBond: i % 4 === 0,
        assembled: false
      }});
    }}
  }}

  function updateAndDraw() {{
    rafId = 0;
    if (doc.hidden) return;

    ctx.clearRect(0, 0, width, height);
    const now = performance.now();
    const clickBoost = (now - mouse.clickTime) < 1600 ? 1.0 : 0.0;

    if (mouse.active && !reducedMotion) {{
      const candidates = [];
      for (let i = 0; i < nodes.length; i++) {{
        const n = nodes[i];
        n.assembled = false;
        const d = Math.hypot(n.x - mouse.x, n.y - mouse.y);
        const captureRadius = (mouse.pressed || clickBoost > 0) ? 290 : 210;
        if (d < captureRadius) {{
          candidates.push({{ node: n, dist: d }});
        }}
      }}
      candidates.sort((a, b) => a.dist - b.dist);
      const count = Math.min(candidates.length, RING_SLOTS.length);
      const angleOffset = now * 0.0008;
      const cosA = Math.cos(angleOffset);
      const sinA = Math.sin(angleOffset);

      for (let k = 0; k < count; k++) {{
        const c = candidates[k].node;
        const slot = RING_SLOTS[k];
        const rx = slot.dx * cosA - slot.dy * sinA;
        const ry = slot.dx * sinA + slot.dy * cosA;
        const tx = mouse.x + rx;
        const ty = mouse.y + ry;
        const pull = (mouse.pressed || clickBoost > 0) ? 0.14 : 0.065;
        c.x += (tx - c.x) * pull;
        c.y += (ty - c.y) * pull;
        c.assembled = true;
      }}
    }}

    for (let i = 0; i < nodes.length; i++) {{
      const a = nodes[i];
      for (let j = i + 1; j < nodes.length; j++) {{
        const b = nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.hypot(dx, dy);
        const bothAssembled = a.assembled && b.assembled;
        const limit = bothAssembled ? 95 : MAX_DISTANCE;

        if (dist < limit) {{
          const baseAlpha = (1 - dist / limit) * (bothAssembled ? 0.68 : 0.18);
          ctx.strokeStyle = bothAssembled
            ? `rgba(54, 214, 176, ${{baseAlpha.toFixed(3)}})`
            : `rgba(103, 183, 209, ${{baseAlpha.toFixed(3)}})`;
          ctx.lineWidth = bothAssembled ? 1.55 : 0.85;

          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();

          if (bothAssembled && a.doubleBond && dist > 12) {{
            const nx = -dy / dist * 3.0;
            const ny = dx / dist * 3.0;
            ctx.strokeStyle = `rgba(103, 183, 209, ${{(baseAlpha * 0.85).toFixed(3)}})`;
            ctx.lineWidth = 1.0;
            ctx.beginPath();
            ctx.moveTo(a.x + nx, a.y + ny);
            ctx.lineTo(b.x + nx, b.y + ny);
            ctx.stroke();
          }}
        }}
      }}
    }}

    for (let r = ripples.length - 1; r >= 0; r--) {{
      const rp = ripples[r];
      rp.radius += 3.2;
      rp.alpha *= 0.94;
      if (rp.alpha < 0.02) {{
        ripples.splice(r, 1);
        continue;
      }}
      ctx.strokeStyle = `rgba(54, 214, 176, ${{rp.alpha.toFixed(3)}})`;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(rp.x, rp.y, rp.radius, 0, Math.PI * 2);
      ctx.stroke();
    }}

    ctx.font = '600 8px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let i = 0; i < nodes.length; i++) {{
      const n = nodes[i];

      if (!reducedMotion && !n.assembled) {{
        n.x += n.vx;
        n.y += n.vy;

        if (n.x < 0) {{ n.x = 0; n.vx *= -1; }}
        else if (n.x > width) {{ n.x = width; n.vx *= -1; }}
        if (n.y < 0) {{ n.y = 0; n.vy *= -1; }}
        else if (n.y > height) {{ n.y = height; n.vy *= -1; }}
      }}

      const r = n.assembled ? n.radius * 1.65 : n.radius;

      ctx.fillStyle = n.assembled ? 'rgba(54, 214, 176, 0.28)' : n.glow;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r * 2.5, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = n.assembled ? '#36D6B0' : n.fill;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fill();

      if (n.assembled) {{
        ctx.fillStyle = '#041410';
        ctx.fillText(n.atom, n.x, n.y + 0.5);
      }}
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

  win.addEventListener('pointerdown', ev => {{
    ensureAudioContext();
    mouse.x = ev.clientX;
    mouse.y = ev.clientY;
    mouse.active = true;
    mouse.pressed = true;
    mouse.clickTime = performance.now();
    ripples.push({{ x: ev.clientX, y: ev.clientY, radius: 8, alpha: 0.65 }});
    startLoop();
  }}, {{ passive: true }});

  win.addEventListener('pointerup', () => {{
    mouse.pressed = false;
  }}, {{ passive: true }});

  doc.documentElement.addEventListener('pointerleave', () => {{
    mouse.active = false;
    mouse.pressed = false;
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

  /* ------------------------------------------------------------------------
     React Bits <BubbleMenu /> (JS + CSS + GSAP) в ПРАВОМ ВЕРХНЕМ УГЛУ
     Сворачивается и разворачивается с GSAP back.out(1.5) и звуковым откликом
     ------------------------------------------------------------------------ */
  const oldDock = doc.getElementById('ps-reactbits-bubble-dock');
  if (oldDock) oldDock.remove();
  const oldOverlay = doc.getElementById('ps-rb-overlay');
  if (oldOverlay) oldOverlay.remove();

  const bubbleDock = doc.createElement('nav');
  bubbleDock.id = 'ps-reactbits-bubble-dock';
  bubbleDock.className = 'bubble-menu fixed';
  bubbleDock.setAttribute('aria-label', 'Навигация по разделам PHARMA SENTINEL');
  bubbleDock.innerHTML = `
    <div class="bubble logo-bubble" id="ps-rb-logo-bubble" title="Активный раздел · Нажмите, чтобы открыть или свернуть меню">
      <span class="ps-rb-dot"></span>
      <span class="logo-content" id="ps-rb-active-label">PHARMA SENTINEL</span>
    </div>
    <button type="button" class="bubble toggle-bubble menu-btn" id="ps-rb-toggle-btn" aria-label="Открыть разделы сайта" aria-pressed="false">
      <span class="menu-line first"></span>
      <span class="menu-line second"></span>
    </button>
  `;
  doc.body.appendChild(bubbleDock);

  const overlayEl = doc.createElement('div');
  overlayEl.id = 'ps-rb-overlay';
  overlayEl.className = 'bubble-menu-items fixed';
  overlayEl.setAttribute('aria-hidden', 'true');
  overlayEl.innerHTML = `<ul class="pill-list" id="ps-rb-items-list" role="menu" aria-label="Разделы сайта"></ul>`;
  doc.body.appendChild(overlayEl);

  const toggleBtn = doc.getElementById('ps-rb-toggle-btn');
  const logoBubble = doc.getElementById('ps-rb-logo-bubble');
  const activeLabelEl = doc.getElementById('ps-rb-active-label');
  const itemsList = doc.getElementById('ps-rb-items-list');

  let isMenuOpen = false;
  let lastNavSignature = '';

  const ITEM_ROTATIONS = [-5, 5, -5, 5, -4, 4, -4];
  const ITEM_HOVER_STYLES = [
    {{ bgColor: '#36D6B0', textColor: '#041410' }},
    {{ bgColor: '#38BDF8', textColor: '#041410' }},
    {{ bgColor: '#10B981', textColor: '#041410' }},
    {{ bgColor: '#F59E0B', textColor: '#041410' }},
    {{ bgColor: '#A855F7', textColor: '#ffffff' }},
    {{ bgColor: '#06B6D4', textColor: '#041410' }},
    {{ bgColor: '#F43F5E', textColor: '#ffffff' }}
  ];

  const animateBubbleMenu = (openState) => {{
    const bubbles = Array.from(overlayEl.querySelectorAll('.pill-link'));
    const labels = Array.from(overlayEl.querySelectorAll('.pill-label'));
    const animationEase = 'back.out(1.5)';
    const animationDuration = 0.42;
    const staggerDelay = 0.065;

    if (openState) {{
      overlayEl.style.display = 'block';
      overlayEl.classList.add('open');
      overlayEl.setAttribute('aria-hidden', 'false');
      toggleBtn.classList.add('open');
      toggleBtn.setAttribute('aria-pressed', 'true');

      if (win.gsap && !reducedMotion && bubbles.length) {{
        win.gsap.killTweensOf([...bubbles, ...labels]);
        win.gsap.set(bubbles, {{ scale: 0, transformOrigin: '50% 50%' }});
        win.gsap.set(labels, {{ y: 20, autoAlpha: 0 }});
        bubbles.forEach((bubble, i) => {{
          const delay = i * staggerDelay;
          const tl = win.gsap.timeline({{ delay }});
          tl.to(bubble, {{
            scale: 1,
            duration: animationDuration,
            ease: animationEase
          }});
          if (labels[i]) {{
            tl.to(
              labels[i],
              {{
                y: 0,
                autoAlpha: 1,
                duration: animationDuration,
                ease: 'power3.out'
              }},
              `-=${{animationDuration * 0.85}}`
            );
          }}
        }});
      }} else {{
        bubbles.forEach(b => {{ b.style.transform = ''; b.style.opacity = '1'; }});
        labels.forEach(l => {{ l.style.transform = ''; l.style.opacity = '1'; }});
      }}
    }} else {{
      toggleBtn.classList.remove('open');
      toggleBtn.setAttribute('aria-pressed', 'false');
      overlayEl.classList.remove('open');
      overlayEl.setAttribute('aria-hidden', 'true');

      if (win.gsap && !reducedMotion && bubbles.length) {{
        win.gsap.killTweensOf([...bubbles, ...labels]);
        win.gsap.to(labels, {{
          y: 18,
          autoAlpha: 0,
          duration: 0.16,
          ease: 'power3.in'
        }});
        win.gsap.to(bubbles, {{
          scale: 0,
          duration: 0.18,
          ease: 'power3.in',
          onComplete: () => {{
            if (!isMenuOpen) overlayEl.style.display = 'none';
          }}
        }});
      }} else {{
        overlayEl.style.display = 'none';
      }}
    }}
  }};

  const setBubbleMenuOpen = (nextState) => {{
    isMenuOpen = Boolean(nextState);
    playBubbleToggleCue(isMenuOpen);
    animateBubbleMenu(isMenuOpen);
  }};

  const syncBubbleItems = (force = false) => {{
    let navGroup = null;
    const groups = doc.querySelectorAll('div[data-testid="stRadio"] > div[role="radiogroup"], div[role="radiogroup"][aria-label="Navigation"]');
    groups.forEach(g => {{
      if (g.getAttribute('aria-label') === 'Navigation' || g.children.length >= 6) navGroup = g;
    }});
    if (!navGroup || !itemsList) return;

    // Принудительно скрываем техническую радио-строку позади BubbleMenu
    const hideTargets = [
      navGroup,
      navGroup.closest('div[data-testid="stRadio"]'),
      navGroup.closest('div[data-testid="stElementContainer"]')
    ];
    hideTargets.forEach(el => {{
      if (el) {{
        el.style.cssText = 'position:fixed !important; top:-99999px !important; left:-99999px !important; width:0px !important; height:0px !important; opacity:0 !important; pointer-events:none !important; overflow:hidden !important; margin:0 !important; padding:0 !important; border:0 !important; display:none !important; z-index:-99999 !important;';
      }}
    }});

    const labels = Array.from(navGroup.querySelectorAll('label'));
    let activeIdx = 0;
    const texts = labels.map((lbl, idx) => {{
      const inp = lbl.querySelector('input[type="radio"]');
      const isChecked = (inp && inp.checked) || lbl.getAttribute('data-checked') === 'true';
      if (isChecked) activeIdx = idx;
      return (lbl.textContent || '').trim();
    }});

    const sig = texts.join('|') + '::' + activeIdx;
    if (!force && sig === lastNavSignature) return;
    lastNavSignature = sig;

    const activeText = texts[activeIdx] || texts[0] || 'Анализ';
    if (activeLabelEl) {{
      activeLabelEl.textContent = activeText;
    }}

    itemsList.innerHTML = '';
    labels.forEach((lbl, idx) => {{
      const text = texts[idx];
      const rot = ITEM_ROTATIONS[idx % ITEM_ROTATIONS.length];
      const hStyle = ITEM_HOVER_STYLES[idx % ITEM_HOVER_STYLES.length];

      const li = doc.createElement('li');
      li.className = 'pill-col';
      li.setAttribute('role', 'none');

      const btn = doc.createElement('button');
      btn.type = 'button';
      btn.setAttribute('role', 'menuitem');
      btn.className = 'pill-link' + (idx === activeIdx ? ' active' : '');
      btn.style.setProperty('--item-rot', `${{rot}}deg`);
      btn.style.setProperty('--hover-bg', hStyle.bgColor);
      btn.style.setProperty('--hover-color', hStyle.textColor);
      btn.innerHTML = `<span class="pill-num">0${{idx + 1}}</span><span class="pill-label">${{text}}</span>`;

      btn.addEventListener('pointerenter', () => {{
        playHoverCue();
      }});

      btn.addEventListener('click', (e) => {{
        e.preventDefault();
        e.stopPropagation();
        playScientificCue(587.33, 880.0);
        setBubbleMenuOpen(false);

        // Динамический поиск живого элемента в DOM Streamlit
        let targetGrp = null;
        const curGroups = doc.querySelectorAll('div[data-testid="stRadio"] > div[role="radiogroup"], div[role="radiogroup"][aria-label="Navigation"]');
        curGroups.forEach(g => {{
          if (g.getAttribute('aria-label') === 'Navigation' || g.children.length >= 6) {{
            targetGrp = g;
          }}
        }});
        if (targetGrp) {{
          const liveLabels = Array.from(targetGrp.querySelectorAll('label'));
          if (liveLabels[idx]) {{
            liveLabels[idx].click();
          }}
        }} else if (lbl && lbl.click) {{
          lbl.click();
        }}
      }});

      li.appendChild(btn);
      itemsList.appendChild(li);
    }});
  }};

  const handleToggleClick = (e) => {{
    e.preventDefault();
    e.stopPropagation();
    syncBubbleItems(true);
    setBubbleMenuOpen(!isMenuOpen);
  }};

  if (toggleBtn) {{
    toggleBtn.addEventListener('pointerenter', () => playHoverCue());
    toggleBtn.addEventListener('click', handleToggleClick);
  }}
  if (logoBubble) {{
    logoBubble.addEventListener('pointerenter', () => playHoverCue());
    logoBubble.addEventListener('click', handleToggleClick);
  }}

  doc.addEventListener('click', (e) => {{
    if (!isMenuOpen) return;
    if (bubbleDock.contains(e.target) || overlayEl.contains(e.target)) return;
    setBubbleMenuOpen(false);
  }});

  doc.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape' && isMenuOpen) {{
      setBubbleMenuOpen(false);
    }}
  }});

  syncBubbleItems(true);

  /* ========================================================================
     3. <AnimatedContent /> from React Bits (JavaScript + CSS + GSAP)
     ======================================================================== */
  const AnimatedContent = {{
    animate: function(elements, customProps = {{}}) {{
      if (reducedMotion || !elements || !elements.length) return;

      const targets = Array.from(elements).filter(el => !el.dataset.psAnimatedDone);
      if (!targets.length) return;

      targets.forEach(el => {{
        el.dataset.psAnimatedDone = '1';
      }});

      const distance = Number(customProps.distance ?? 40);
      const direction = customProps.direction ?? 'vertical';
      const reverse = Boolean(customProps.reverse ?? false);
      const duration = Number(customProps.duration ?? 0.5);
      const ease = customProps.ease ?? 'power3.out';
      const initialOpacity = Number(customProps.initialOpacity ?? 0);
      const animateOpacity = customProps.animateOpacity !== false;
      const scale = Number(customProps.scale ?? 0.98);
      const delay = Number(customProps.delay ?? 0);
      const blur = Number(customProps.blur ?? 0);
      const stagger = Number(customProps.stagger ?? 0.05);
      const wipe = Boolean(customProps.wipe ?? false);

      const xVal = direction === 'horizontal' ? (reverse ? -distance : distance) : 0;
      const yVal = direction === 'vertical' ? (reverse ? -distance : distance) : 0;

      if (win.gsap) {{
        const fromVars = {{
          x: xVal,
          y: yVal,
          scale: scale,
          overwrite: 'auto'
        }};
        if (animateOpacity) fromVars.opacity = initialOpacity;
        if (blur > 0) fromVars.filter = `blur(${{blur}}px)`;
        if (wipe) fromVars.clipPath = 'polygon(0 0, 100% 0, 100% 0, 0 0)';

        const toVars = {{
          x: 0,
          y: 0,
          scale: 1,
          duration: duration,
          ease: ease,
          delay: delay,
          stagger: stagger,
          overwrite: 'auto',
          clearProps: 'transform,filter,clipPath'
        }};
        if (animateOpacity) toVars.opacity = 1;
        if (blur > 0) toVars.filter = 'blur(0px)';
        if (wipe) toVars.clipPath = 'polygon(0 0, 100% 0, 100% 100%, 0% 100%)';

        win.gsap.fromTo(targets, fromVars, toVars);
      }} else {{
        targets.forEach((el, idx) => {{
          const delayMs = Math.round((delay + idx * stagger) * 1000);
          el.style.opacity = animateOpacity ? String(initialOpacity) : '1';
          el.style.transform = `translate3d(${{xVal}}px, ${{yVal}}px, 0) scale(${{scale}})`;
          if (blur > 0) el.style.filter = `blur(${{blur}}px)`;
          if (wipe) el.style.clipPath = 'polygon(0 0, 100% 0, 100% 0, 0 0)';
          el.style.transition = 'none';

          setTimeout(() => {{
            win.requestAnimationFrame(() => {{
              el.style.transition = `opacity ${{Math.round(duration * 1000)}}ms cubic-bezier(0.16, 1, 0.3, 1), transform ${{Math.round(duration * 1000)}}ms cubic-bezier(0.16, 1, 0.3, 1), filter ${{Math.round(duration * 1000)}}ms ease, clip-path ${{Math.round(duration * 1000)}}ms ease`;
              if (animateOpacity) el.style.opacity = '1';
              el.style.transform = 'translate3d(0, 0, 0) scale(1)';
              if (blur > 0) el.style.filter = 'blur(0px)';
              if (wipe) el.style.clipPath = 'polygon(0 0, 100% 0, 100% 100%, 0% 100%)';
            }});
          }}, 16 + delayMs);
        }});
      }}
    }}
  }};

  win.AnimatedContent = AnimatedContent;
  win.__PS_ANIMATED_CONTENT__ = AnimatedContent;

  const runAnimatedContent = () => {{
    syncBubbleItems(false);
    if (reducedMotion) return;
    const mainBlock = doc.querySelector('[data-testid="stMainBlockContainer"], .block-container');
    if (!mainBlock) return;

    const customWrappers = mainBlock.querySelectorAll('.ps-animated-content, [data-animated-content]');
    customWrappers.forEach(wrapper => {{
      const children = Array.from(wrapper.children);
      const props = {{
        distance: wrapper.dataset.distance,
        direction: wrapper.dataset.direction,
        reverse: wrapper.dataset.reverse === 'true',
        duration: wrapper.dataset.duration,
        ease: wrapper.dataset.ease,
        scale: wrapper.dataset.scale,
        stagger: wrapper.dataset.stagger,
        blur: wrapper.dataset.blur,
        wipe: wrapper.dataset.wipe === 'true'
      }};
      AnimatedContent.animate(children, props);
    }});

    const standardElements = mainBlock.querySelectorAll(
      '.ps-anim-item, .ps-stat-box, .ps-card-finding, .ps-supp-row, .ps-disclaimer, .ps-qgen-card, .ps-overview-card, .ps-token-bar, [data-testid="stDataFrame"], [data-testid="stPlot"]'
    );
    AnimatedContent.animate(standardElements, {{
      distance: 16,
      direction: 'vertical',
      duration: 0.20,
      ease: 'power3.out',
      scale: 0.99,
      stagger: 0.03
    }});
  }};

  win.__PS_TRIGGER_ANIMATED_CONTENT__ = runAnimatedContent;
  runAnimatedContent();

  doc.addEventListener('click', (ev) => {{
    if (win.__PS_SOUND_ENABLED__ === false) return;
    const btn = ev.target && ev.target.closest && ev.target.closest('button, [role="radio"], [role="tab"], .ps-overview-card, .ps-stat-box, .ps-card-finding');
    if (btn) playScientificCue();
  }}, {{ passive: true }});

  doc.addEventListener('pointerover', (ev) => {{
    if (win.__PS_SOUND_ENABLED__ === false) return;
    const btn = ev.target && ev.target.closest && ev.target.closest(
      'button, .pill-link, .bubble, .ps-overview-card, .ps-stat-box, .ps-card-finding, .ps-supp-row, .ps-qgen-card, .ps-token-bar'
    );
    if (btn && (!ev.relatedTarget || !btn.contains(ev.relatedTarget))) {{
      playHoverCue();
    }}
  }}, {{ passive: true }});

  const appContainer = doc.querySelector('[data-testid="stAppViewContainer"]') || doc.body;
  const domObserver = new MutationObserver(() => {{
    runAnimatedContent();
    syncBubbleItems(false);
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

  if (typeof parentWin.__PS_SOUND_ENABLED__ === 'undefined') {{
    parentWin.__PS_SOUND_ENABLED__ = true;
  }} else if ({sound_flag_js}) {{
    parentWin.__PS_SOUND_ENABLED__ = true;
  }}

  if (!parentWin.gsap && !parentDoc.getElementById('ps-gsap-cdn')) {{
    const gsapScript = parentDoc.createElement('script');
    gsapScript.id = 'ps-gsap-cdn';
    gsapScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js';
    gsapScript.async = true;
    parentDoc.head.appendChild(gsapScript);
  }}

  if (!parentWin.__PS_PERSISTENT_ENGINE_V7__) {{
    parentWin.__PS_PERSISTENT_ENGINE_ACTIVE__ = false;
  }}

  if (parentWin.__PS_PERSISTENT_ENGINE_V7__) {{
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


def render_animated_content(
    content_html: str,
    distance: int = 40,
    direction: str = "vertical",
    reverse: bool = False,
    duration: float = 0.5,
    ease: str = "power3.out",
    scale: float = 0.98,
    stagger: float = 0.05,
    blur: int = 0,
    wipe: bool = False,
    container_class: str = "",
) -> str:
    """Обертка React Bits <AnimatedContent /> (JavaScript + CSS + GSAP) для HTML-контента Streamlit."""
    data_attrs = (
        f'data-animated-content="true" '
        f'data-distance="{distance}" '
        f'data-direction="{direction}" '
        f'data-reverse="{str(reverse).lower()}" '
        f'data-duration="{duration}" '
        f'data-ease="{ease}" '
        f'data-scale="{scale}" '
        f'data-stagger="{stagger}" '
        f'data-blur="{blur}" '
        f'data-wipe="{str(wipe).lower()}"'
    )
    extra_class = f" {container_class}" if container_class else ""
    return f'<div class="ps-animated-content{extra_class}" {data_attrs}>{content_html}</div>'


def render_albus_fingent_hero_3d_html(
    lang: str = "ru",
    active_drug_a: str = "Warfarin",
    active_drug_b: str = "Aspirin",
    major_count: int = 1,
    mod_count: int = 0,
    total_pairs_checked: int = 1,
    height: int = 440,
) -> str:
    """Рендерит флагманский 3D-экран по референсам Albus Therapeutics + Fingent + DNA Helix.

    Включает:
    - Интерактивную 3D WebGL-сцену (Three.js + Canvas fallback) с тремя переключаемыми 3D-объектами:
      1) Открытая 3D-капсула с высыпающимися микрогранулами (Albus Therapeutics video ref)
      2) Wireframe-плексус флакон и две светящиеся 3D-капсулы из треугольных граней (Fingent photo ref)
      3) Биолюминесцентная 3D спираль ДНК/макромолекулы с частицами боке (DNA photo & video ref)
    - Выносные телеметрические HUD-линии (72% CYP450 SUBSTRATES, 160,230 DDINTER PAIRS, 1,939 INN DRUGS)
    - Обязательный клинический дисклеймер против самолечения (Первичная скрининговая модель).
    """
    lang_n = (lang or "ru").lower()
    disp_a = "ASPIRIN" if active_drug_a.strip().lower() == "acetylsalicylic acid" else active_drug_a.upper()
    disp_b = "ASPIRIN" if active_drug_b.strip().lower() == "acetylsalicylic acid" else active_drug_b.upper()

    if lang_n == "kk":
        eyebrow = "01 — БІЗДІҢ ҒЫЛЫМ · AI IS REDEFINING DRUG SAFETY"
        headline = "Деректерге негізделген ЖИ арқылы дәрілік қауіпсіздікті трансформациялау."
        subtext = (
            "PHARMA SENTINEL — өзін-өзі емдеудің (самолечение) және полипрагмазияның қауіпті салдарын алдын ала "
            "болдырмауға арналған бастапқы клиникалық-фармакологиялық скрининг моделі (DDInter + PubMed + ML). "
            "Емдеуші дәрігерді немесе клиникалық фармакологты алмастырмайды."
        )
        btn_cap = "01 · 3D Пилюля"
        btn_fin = "02 · 3D Препараттар"
        btn_dna = "03 · 3D Молекула"
        anti_self_badge = "ӨЗІН-ӨЗІ ЕМДЕУДІҢ АЛДЫН АЛУ · ДӘРІГЕРДІ АЛМАСТЫРМАЙДЫ"
        focus_lbl = "АКТИВТІ КЛИНИКАЛЫҚ ФОКУС"
        cta_lbl = "3D РЕЖИМДІ АУЫСТЫРУ"
    elif lang_n == "en":
        eyebrow = "01 — OUR SCIENCE · AI IS REDEFINING DRUG DISCOVERY & SAFETY"
        headline = "Transforming Drug Safety with Data-Driven AI."
        subtext = (
            "PHARMA SENTINEL is a primary clinical pharmacology screening model combining DDInter, PubMed clinical studies, "
            "and topological ML to prevent hazardous self-medication. It never replaces an attending physician or clinical pharmacist."
        )
        btn_cap = "01 · 3D Capsule"
        btn_fin = "02 · 3D Pharmaceuticals"
        btn_dna = "03 · 3D Molecule"
        anti_self_badge = "ANTI-SELF-MEDICATION SCREENING · DOES NOT REPLACE A PHYSICIAN"
        focus_lbl = "ACTIVE CLINICAL FOCUS"
        cta_lbl = "SWITCH 3D MODEL"
    else:
        eyebrow = "01 — НАУЧНАЯ АРХИТЕКТУРА · AI IS REDEFINING DRUG SAFETY"
        headline = "Интеллектуальный 3D-аудит лекарств и защита от самолечения."
        subtext = (
            "PHARMA SENTINEL объединяет верифицированную матрицу DDInter (160 230 пар), клинические исследования PubMed "
            "и графовый ML-анализ. Первичная скрининговая модель для предотвращения опасного самолечения — не заменяет врача или клинического фармаколога."
        )
        btn_cap = "01 · 3D Пилюля"
        btn_fin = "02 · 3D Препараты"
        btn_dna = "03 · 3D Молекула"
        anti_self_badge = "ПЕРВИЧНЫЙ СКРИНИНГ ПРОТИВ САМОЛЕЧЕНИЯ · НЕ ЗАМЕНЯЕТ ВРАЧА"
        focus_lbl = "АКТИВНЫЙ КЛИНИЧЕСКИЙ ФОКУС"
        cta_lbl = "СМЕНИТЬ 3D-МОДЕЛЬ"

    return f"""<!DOCTYPE html>
<html lang="{lang_n}">
<head>
<meta charset="utf-8" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 100%;
    min-height: {height}px;
    background: transparent;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #EAF2F2;
    overflow: hidden;
  }}

  .hero-frame {{
    position: relative;
    width: 100%;
    height: {height}px;
    border-radius: 18px;
    border: 1px solid #263940;
    background:
      radial-gradient(circle at 26% 45%, rgba(54, 214, 176, 0.16) 0%, rgba(103, 183, 209, 0.09) 34%, rgba(11, 17, 20, 0) 68%),
      radial-gradient(circle at 82% 72%, rgba(103, 183, 209, 0.15) 0%, rgba(7, 26, 36, 0.45) 45%, rgba(11, 17, 20, 0.95) 85%),
      linear-gradient(135deg, #091318 0%, #0E1D24 52%, #07222C 100%);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.06);
    display: grid;
    grid-template-columns: 1.05fr 0.95fr;
    overflow: hidden;
    transition: border-color 220ms ease, box-shadow 220ms ease;
  }}
  .hero-frame:hover {{
    border-color: rgba(54, 214, 176, 0.65);
    box-shadow: 0 22px 54px rgba(0, 0, 0, 0.62), 0 0 26px rgba(54, 214, 176, 0.18);
  }}

  /* Левая 3D сцена (Пилюля с гранулами / Препараты / Молекула) */
  .stage-col {{
    position: relative;
    width: 100%;
    height: 100%;
    min-width: 0;
    cursor: grab;
    user-select: none;
    border-right: 1px solid rgba(38, 57, 64, 0.65);
    overflow: hidden;
  }}
  .stage-col:active {{ cursor: grabbing; }}

  #hero-webgl-canvas {{
    width: 100%;
    height: 100%;
    display: block;
  }}

  /* Выносные телеметрические HUD-чипы (не накладываются на мобильных экранах) */
  .hero-telemetry-bar {{
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    z-index: 5;
    pointer-events: none;
    display: flex;
    align-items: center;
    gap: 7px;
    flex-wrap: wrap;
  }}
  .hud-chip {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(11, 18, 22, 0.88);
    border: 1px solid rgba(54, 214, 176, 0.32);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding: 4px 10px;
    border-radius: 999px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45);
  }}
  .hud-chip-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #36D6B0;
    box-shadow: 0 0 6px #36D6B0;
    flex-shrink: 0;
  }}
  .hud-chip-dot.cyan {{ background: #67B7D1; box-shadow: 0 0 6px #67B7D1; }}
  .hud-chip-dot.gold {{ background: #F59E0B; box-shadow: 0 0 6px #F59E0B; }}
  .hud-chip-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13.5px;
    font-weight: 700;
    color: #EAF2F2;
    letter-spacing: -0.02em;
  }}
  .hud-chip-lbl {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    font-weight: 600;
    letter-spacing: 0.05em;
    color: #91A5AA;
    text-transform: uppercase;
  }}

  /* Идеально ровная 3-колоночная панель переключения 3D-моделей */
  .mode-switcher {{
    position: absolute;
    bottom: 12px;
    left: 12px;
    right: 12px;
    z-index: 6;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 7px;
  }}
  .mode-pill {{
    height: 32px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(11, 18, 22, 0.90);
    border: 1px solid #263940;
    color: #91A5AA;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    padding: 0 8px;
    border-radius: 999px;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    backdrop-filter: blur(10px);
    transition: transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1), border-color 160ms ease, color 160ms ease, background 160ms ease, box-shadow 160ms ease;
  }}
  .mode-pill:hover {{
    color: #EAF2F2;
    border-color: #36D6B0;
    background: rgba(54, 214, 176, 0.16);
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(54, 214, 176, 0.28);
  }}
  .mode-pill.active {{
    background: #36D6B0 !important;
    color: #041410 !important;
    font-weight: 700 !important;
    border-color: #36D6B0 !important;
    box-shadow: 0 0 16px rgba(54, 214, 176, 0.65) !important;
  }}

  /* Правая колонка с редакционной типографикой и выровненным блоком Активного Фокуса */
  .copy-col {{
    position: relative;
    z-index: 5;
    min-width: 0;
    padding: 22px 24px 20px 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
    overflow: hidden;
  }}
  .copy-top {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-width: 0;
  }}
  .eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.11em;
    color: #36D6B0;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .eyebrow::before {{
    content: "";
    width: 20px;
    height: 2px;
    background: #36D6B0;
    display: inline-block;
    flex-shrink: 0;
  }}
  .headline {{
    font-size: clamp(19px, 2.0vw, 27px);
    font-weight: 800;
    line-height: 1.16;
    letter-spacing: -0.025em;
    color: #EAF2F2;
    overflow-wrap: break-word;
    word-break: break-word;
  }}
  .subtext {{
    font-size: 12px;
    line-height: 1.5;
    color: #91A5AA;
    overflow-wrap: break-word;
  }}

  /* Плашка защиты от самолечения */
  .safety-mandate {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    align-self: flex-start;
    max-width: 100%;
    background: rgba(244, 63, 94, 0.12);
    border: 1px solid rgba(244, 63, 94, 0.42);
    color: #FDA4AF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.2px;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 6px;
    letter-spacing: 0.03em;
    line-height: 1.3;
  }}
  .safety-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #F43F5E;
    box-shadow: 0 0 8px #F43F5E;
    flex-shrink: 0;
  }}

  /* Выровненная 2-колоночная карточка АКТИВНОГО ФОКУСА */
  .active-pair-strip {{
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 10px;
    background: rgba(17, 27, 32, 0.90);
    border: 1px solid #263940;
    border-left: 3px solid #36D6B0;
    padding: 9px 13px;
    border-radius: 10px;
    transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
  }}
  .active-pair-strip:hover {{
    border-color: #36D6B0;
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(54, 214, 176, 0.20);
  }}
  .focus-meta {{
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }}
  .focus-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.8px;
    font-weight: 700;
    letter-spacing: 0.07em;
    color: #91A5AA;
    text-transform: uppercase;
  }}
  .pair-telemetry-pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    font-weight: 700;
    color: #EAF2F2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .cta-explore {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 36px;
    padding: 0 14px;
    border-radius: 8px;
    background: linear-gradient(135deg, #36D6B0 0%, #24A98B 100%);
    color: #041410;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: none;
    cursor: pointer;
    white-space: nowrap;
    box-shadow: 0 6px 18px rgba(54, 214, 176, 0.30);
    transition: transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 180ms ease;
  }}
  .cta-explore:hover {{
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 10px 26px rgba(54, 214, 176, 0.52);
  }}

  /* АДАПТИВНАЯ МОБИЛЬНАЯ ВЕРСТКА (устраняет наложение телеметрии и обрезку текста) */
  @media (max-width: 860px) {{
    html, body {{
      height: 100% !important;
      overflow: hidden !important;
    }}
    .hero-frame {{
      grid-template-columns: 1fr !important;
      grid-template-rows: 190px 1fr !important;
      height: 100% !important;
    }}
    .stage-col {{
      height: 190px !important;
      min-height: 190px !important;
      border-right: none !important;
      border-bottom: 1px solid rgba(38, 57, 64, 0.65) !important;
    }}
    .hero-telemetry-bar {{
      top: 6px !important;
      left: 6px !important;
      right: 6px !important;
      gap: 5px !important;
    }}
    .hud-chip {{
      padding: 2px 7px !important;
    }}
    .hud-chip-num {{ font-size: 11px !important; }}
    .hud-chip-lbl {{ font-size: 7px !important; }}
    .hud-chip-hide-mobile {{ display: none !important; }}
    .mode-switcher {{
      bottom: 6px !important;
      left: 6px !important;
      right: 6px !important;
      gap: 5px !important;
    }}
    .mode-pill {{
      height: 26px !important;
      font-size: 8.5px !important;
      padding: 0 5px !important;
    }}
    .copy-col {{
      padding: 10px 12px 10px 12px !important;
      gap: 6px !important;
      overflow-y: auto !important;
    }}
    .copy-top {{
      gap: 5px !important;
    }}
    .eyebrow {{
      font-size: 8px !important;
    }}
    .headline {{
      font-size: 15px !important;
      line-height: 1.18 !important;
    }}
    .subtext {{
      font-size: 10px !important;
      line-height: 1.32 !important;
    }}
    .safety-mandate {{
      font-size: 7.8px !important;
      padding: 3px 6px !important;
    }}
    .active-pair-strip {{
      grid-template-columns: 1fr auto !important;
      gap: 6px !important;
      padding: 6px 8px !important;
    }}
    .cta-explore {{
      height: 28px !important;
      padding: 0 10px !important;
      font-size: 9px !important;
    }}
  }}
</style>
</head>
<body>
  <div class="hero-frame">
    <div class="stage-col" id="hero-stage-col" title="Поверните 3D-модель мышью или нажмите для импульса молекул">
      <div class="hero-telemetry-bar">
        <div class="hud-chip">
          <span class="hud-chip-dot emerald"></span>
          <span class="hud-chip-num">72%</span>
          <span class="hud-chip-lbl">CYP450 &amp; P-GP SUBSTRATES</span>
        </div>
        <div class="hud-chip">
          <span class="hud-chip-dot cyan"></span>
          <span class="hud-chip-num">160.2K</span>
          <span class="hud-chip-lbl">DDINTER PAIRS</span>
        </div>
        <div class="hud-chip hud-chip-hide-mobile">
          <span class="hud-chip-dot gold"></span>
          <span class="hud-chip-num">1,939</span>
          <span class="hud-chip-lbl">INN DRUGS</span>
        </div>
      </div>

      <canvas id="hero-webgl-canvas"></canvas>

      <div class="mode-switcher">
        <button type="button" class="mode-pill active" id="btn-scene-capsule">{btn_cap}</button>
        <button type="button" class="mode-pill" id="btn-scene-fingent">{btn_fin}</button>
        <button type="button" class="mode-pill" id="btn-scene-dna">{btn_dna}</button>
      </div>
    </div>

    <div class="copy-col">
      <div class="copy-top">
        <div class="eyebrow">{eyebrow}</div>
        <h1 class="headline">{headline}</h1>
        <p class="subtext">{subtext}</p>
        <div class="safety-mandate">
          <span class="safety-dot"></span>
          <span>{anti_self_badge}</span>
        </div>
      </div>
      <div class="active-pair-strip">
        <div class="focus-meta">
          <div class="focus-tag">{focus_lbl} · MAJOR: <span style="color:#F43F5E;">{major_count}</span></div>
          <div class="pair-telemetry-pill">
            <span style="color:#36D6B0;">{disp_a}</span>
            <span style="color:#91A5AA; margin:0 5px;">×</span>
            <span style="color:#67B7D1;">{disp_b}</span>
          </div>
        </div>
        <button type="button" class="cta-explore" id="btn-hero-cycle">
          <span>{cta_lbl}</span>
          <span>↻</span>
        </button>
      </div>
    </div>
  </div>

<script>
(function initHero3DShowcase() {{
  const heroFrame = document.querySelector('.hero-frame');
  const container = document.getElementById('hero-stage-col');
  const canvas = document.getElementById('hero-webgl-canvas');
  if (!container || !canvas || typeof THREE === 'undefined') return;

  let width = Math.max(240, container.clientWidth);
  let height = Math.max(200, container.clientHeight);

  const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
  camera.position.set(0, 0.2, 11.4);

  // Освещение в тонах изумруда (#36D6B0), циана (#67B7D1) и студийного блика
  scene.add(new THREE.AmbientLight(0xd8f3f0, 0.65));
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.05);
  keyLight.position.set(6, 9, 8);
  scene.add(keyLight);

  const emeraldLight = new THREE.PointLight(0x36d6b0, 1.8, 22);
  emeraldLight.position.set(-5, 3, 5);
  scene.add(emeraldLight);

  const cyanLight = new THREE.PointLight(0x67b7d1, 1.6, 22);
  cyanLight.position.set(5, -3, 5);
  scene.add(cyanLight);

  const rootGroup = new THREE.Group();
  scene.add(rootGroup);

  function updateViewportCameraAndIframe() {{
    width = Math.max(240, container.clientWidth);
    height = Math.max(200, container.clientHeight);
    const isNarrow = window.innerWidth <= 780 || width < 420;
    camera.position.set(0, isNarrow ? 0.08 : 0.2, isNarrow ? 14.8 : 11.4);
    rootGroup.scale.setScalar(isNarrow ? 0.80 : 1.0);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);

    try {{
      if (window.frameElement && heroFrame) {{
        const neededH = Math.max(410, heroFrame.offsetHeight + 4);
        window.frameElement.style.height = neededH + 'px';
      }}
    }} catch (e) {{}}
  }}

  /* ==========================================================================
     СЦЕНА 1: ALBUS THERAPEUTICS — 3D открытая капсула + поток микрогранул
     ========================================================================== */
  const groupCapsule = new THREE.Group();
  rootGroup.add(groupCapsule);

  // Нижняя половина капсулы (матовый перламутрово-обсидиановый корпус)
  const capRadius = 1.25;
  const capLen = 1.65;
  const matShellDark = new THREE.MeshPhysicalMaterial({{
    color: 0x162830,
    roughness: 0.22,
    metalness: 0.15,
    clearcoat: 0.8,
    transparent: true,
    opacity: 0.94
  }});
  const matShellEmerald = new THREE.MeshPhysicalMaterial({{
    color: 0x36d6b0,
    emissive: 0x0d4a3b,
    emissiveIntensity: 0.35,
    roughness: 0.18,
    metalness: 0.12,
    clearcoat: 0.9,
    transparent: true,
    opacity: 0.88
  }});

  // Левая (нижняя) половина открытой капсулы
  const bottomHalf = new THREE.Group();
  const cyl1 = new THREE.Mesh(new THREE.CylinderGeometry(capRadius, capRadius, capLen, 36, 1, true), matShellDark);
  const dome1 = new THREE.Mesh(new THREE.SphereGeometry(capRadius, 36, 24, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), matShellDark);
  dome1.position.y = -capLen / 2;
  // Внутреннее светящееся кольцо среза капсулы
  const rim1 = new THREE.Mesh(
    new THREE.TorusGeometry(capRadius, 0.045, 16, 48),
    new THREE.MeshBasicMaterial({{ color: 0x36d6b0 }})
  );
  rim1.rotation.x = Math.PI / 2;
  rim1.position.y = capLen / 2;
  bottomHalf.add(cyl1, dome1, rim1);
  bottomHalf.position.set(-1.35, -0.75, 0);
  bottomHalf.rotation.z = -0.68;
  bottomHalf.rotation.x = 0.22;
  groupCapsule.add(bottomHalf);

  // Правая (верхняя) приоткрытая крышечка капсулы
  const topHalf = new THREE.Group();
  const cyl2 = new THREE.Mesh(new THREE.CylinderGeometry(capRadius * 1.03, capRadius * 1.03, capLen * 0.92, 36, 1, true), matShellEmerald);
  const dome2 = new THREE.Mesh(new THREE.SphereGeometry(capRadius * 1.03, 36, 24, 0, Math.PI * 2, 0, Math.PI / 2), matShellEmerald);
  dome2.position.y = (capLen * 0.92) / 2;
  const rim2 = new THREE.Mesh(
    new THREE.TorusGeometry(capRadius * 1.03, 0.045, 16, 48),
    new THREE.MeshBasicMaterial({{ color: 0x67b7d1 }})
  );
  rim2.rotation.x = Math.PI / 2;
  rim2.position.y = -(capLen * 0.92) / 2;
  topHalf.add(cyl2, dome2, rim2);
  topHalf.position.set(0.65, 1.28, -0.35);
  topHalf.rotation.z = -0.82;
  topHalf.rotation.y = 0.35;
  groupCapsule.add(topHalf);

  // 48 микрогранул (сфер), высыпающихся из открытой капсулы как в референсе Albus Therapeutics
  const pellets = [];
  const pelletGeo = new THREE.SphereGeometry(0.22, 24, 24);
  const pelletMats = [
    new THREE.MeshPhysicalMaterial({{ color: 0xeaf2f2, roughness: 0.18, metalness: 0.08, clearcoat: 0.7 }}),
    new THREE.MeshPhysicalMaterial({{ color: 0x36d6b0, emissive: 0x114d3e, emissiveIntensity: 0.3, roughness: 0.2, clearcoat: 0.8 }}),
    new THREE.MeshPhysicalMaterial({{ color: 0x67b7d1, emissive: 0x123e4d, emissiveIntensity: 0.25, roughness: 0.2, clearcoat: 0.8 }}),
    new THREE.MeshPhysicalMaterial({{ color: 0xf43f5e, emissive: 0x4d1020, emissiveIntensity: 0.25, roughness: 0.25, clearcoat: 0.7 }})
  ];

  for (let i = 0; i < 48; i++) {{
    const mat = pelletMats[i % 11 === 0 ? 3 : (i % 3)];
    const mesh = new THREE.Mesh(pelletGeo, mat);
    const t = i / 48;
    const spread = 0.35 + t * 1.65;
    const angle = i * 1.15;
    const bx = -0.95 + (t - 0.3) * 3.4 + Math.cos(angle) * spread * 0.65;
    const by = -0.35 + Math.sin(angle * 0.7) * spread * 0.95 + (t - 0.5) * 1.5;
    const bz = Math.sin(angle) * spread * 0.85;
    const scale = 0.68 + (i % 5) * 0.14;
    mesh.scale.setScalar(scale);
    mesh.position.set(bx, by, bz);
    groupCapsule.add(mesh);
    pellets.push({{ mesh, bx, by, bz, phase: i * 0.42, speed: 0.9 + (i % 4) * 0.25 }});
  }}

  /* ==========================================================================
     СЦЕНА 2: FINGENT REF — Светящийся 3D Wireframe-флакон + две 3D-капсулы
     ========================================================================== */
  const groupFingent = new THREE.Group();
  groupFingent.visible = false;
  rootGroup.add(groupFingent);

  const wireCyanMat = new THREE.MeshBasicMaterial({{ color: 0x67b7d1, wireframe: true, transparent: true, opacity: 0.52 }});
  const wireEmeraldMat = new THREE.MeshBasicMaterial({{ color: 0x36d6b0, wireframe: true, transparent: true, opacity: 0.68 }});
  const glassBottleMat = new THREE.MeshPhysicalMaterial({{
    color: 0x0e2a38,
    emissive: 0x0b3b49,
    emissiveIntensity: 0.4,
    roughness: 0.15,
    transmission: 0.6,
    transparent: true,
    opacity: 0.42
  }});

  // Корпус флакона Fingent
  const bottleGroup = new THREE.Group();
  const bodyGeo = new THREE.CylinderGeometry(1.45, 1.45, 2.9, 18, 6);
  const neckGeo = new THREE.CylinderGeometry(1.05, 1.45, 0.55, 18, 2);
  neckGeo.translate(0, 1.72, 0);
  const capGeo = new THREE.CylinderGeometry(1.18, 1.18, 0.65, 24, 2);
  capGeo.translate(0, 2.28, 0);

  bottleGroup.add(new THREE.Mesh(bodyGeo, glassBottleMat));
  bottleGroup.add(new THREE.Mesh(bodyGeo, wireCyanMat));
  bottleGroup.add(new THREE.Mesh(neckGeo, wireCyanMat));
  bottleGroup.add(new THREE.Mesh(capGeo, wireEmeraldMat));
  bottleGroup.position.set(1.25, -0.35, -0.5);
  groupFingent.add(bottleGroup);

  // Helper для создания светящейся плексус-капсулы Fingent на переднем плане
  function createPlexusPill(x, y, z, rz, rx) {{
    const pill = new THREE.Group();
    const pCyl = new THREE.CylinderGeometry(0.68, 0.68, 1.7, 16, 4);
    const pTop = new THREE.SphereGeometry(0.68, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2);
    pTop.translate(0, 0.85, 0);
    const pBot = new THREE.SphereGeometry(0.68, 16, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2);
    pBot.translate(0, -0.85, 0);

    pill.add(new THREE.Mesh(pCyl, glassBottleMat));
    pill.add(new THREE.Mesh(pCyl, wireEmeraldMat));
    pill.add(new THREE.Mesh(pTop, wireCyanMat));
    pill.add(new THREE.Mesh(pBot, wireEmeraldMat));

    // Внутренние биолюминесцентные точки внутри капсулы
    const ptsGeo = new THREE.BufferGeometry();
    const ptsArr = new Float32Array(45 * 3);
    for (let k = 0; k < 45; k++) {{
      const a = Math.random() * Math.PI * 2;
      const r = Math.random() * 0.52;
      ptsArr[k * 3] = Math.cos(a) * r;
      ptsArr[k * 3 + 1] = (Math.random() - 0.5) * 2.2;
      ptsArr[k * 3 + 2] = Math.sin(a) * r;
    }}
    ptsGeo.setAttribute('position', new THREE.BufferAttribute(ptsArr, 3));
    const ptsMat = new THREE.PointsMaterial({{ color: 0x36d6b0, size: 0.09, transparent: true, opacity: 0.9 }});
    pill.add(new THREE.Points(ptsGeo, ptsMat));

    pill.position.set(x, y, z);
    pill.rotation.z = rz;
    pill.rotation.x = rx;
    return pill;
  }}

  const fingentPill1 = createPlexusPill(-0.85, -0.75, 1.1, -0.78, 0.25);
  const fingentPill2 = createPlexusPill(0.45, -1.45, 1.5, 1.42, -0.18);
  groupFingent.add(fingentPill1, fingentPill2);

  /* ==========================================================================
     СЦЕНА 3: BIOLUMINESCENT 3D DNA HELIX (референс реф + доп реф фото.mp4)
     ========================================================================== */
  const groupDNA = new THREE.Group();
  groupDNA.visible = false;
  rootGroup.add(groupDNA);

  const rungCount = 26;
  const dnaSphereGeo = new THREE.SphereGeometry(0.16, 16, 16);
  const matStrandA = new THREE.MeshPhysicalMaterial({{ color: 0x36d6b0, emissive: 0x145e4c, emissiveIntensity: 0.55, roughness: 0.15 }});
  const matStrandB = new THREE.MeshPhysicalMaterial({{ color: 0x67b7d1, emissive: 0x16495c, emissiveIntensity: 0.55, roughness: 0.15 }});
  const matBokeh = new THREE.MeshBasicMaterial({{ color: 0xf59e0b, transparent: true, opacity: 0.75 }});

  for (let i = 0; i < rungCount; i++) {{
    const t = (i / (rungCount - 1) - 0.5) * 6.6;
    const ang = i * 0.46;
    const r = 1.35;
    const x1 = Math.cos(ang) * r;
    const z1 = Math.sin(ang) * r;
    const x2 = Math.cos(ang + Math.PI) * r;
    const z2 = Math.sin(ang + Math.PI) * r;

    const nodeA = new THREE.Mesh(dnaSphereGeo, matStrandA);
    nodeA.position.set(x1, t, z1);
    const nodeB = new THREE.Mesh(dnaSphereGeo, matStrandB);
    nodeB.position.set(x2, t, z2);
    groupDNA.add(nodeA, nodeB);

    // Перекладина (водородная связь пары оснований)
    const rungGeo = new THREE.CylinderGeometry(0.038, 0.038, r * 2, 10);
    const rungMesh = new THREE.Mesh(rungGeo, wireCyanMat);
    rungMesh.position.set(0, t, 0);
    rungMesh.rotation.z = Math.PI / 2;
    rungMesh.rotation.y = -ang;
    groupDNA.add(rungMesh);
  }}

  // Теплые золотисто-изумрудные частицы боке вокруг спирали ДНК (как на фото реф)
  const bokehGeo = new THREE.SphereGeometry(0.07, 10, 10);
  for (let b = 0; b < 32; b++) {{
    const bm = new THREE.Mesh(bokehGeo, b % 2 === 0 ? matBokeh : wireEmeraldMat);
    const ba = b * 1.7;
    bm.position.set(
      Math.cos(ba) * (1.8 + (b % 4) * 0.45),
      ((b / 32) - 0.5) * 6.0,
      Math.sin(ba) * (1.8 + (b % 3) * 0.45)
    );
    groupDNA.add(bm);
  }}
  groupDNA.rotation.z = -0.48;

  /* ==========================================================================
     Интерактивное вращение мышью, переключение сцен и импульс клика
     ========================================================================== */
  let currentMode = 0;
  let isDragging = false;
  let prevX = 0, prevY = 0;
  let targetRotY = 0, targetRotX = 0;
  let burstEnergy = 0;

  const btnCap = document.getElementById('btn-scene-capsule');
  const btnFin = document.getElementById('btn-scene-fingent');
  const btnDna = document.getElementById('btn-scene-dna');
  const btnCycle = document.getElementById('btn-hero-cycle');

  function triggerParentCue(isClick = false) {{
    try {{
      if (window.parent) {{
        if (isClick && typeof window.parent.__PS_PLAY_CUE__ === 'function') window.parent.__PS_PLAY_CUE__(554.37, 740);
        else if (!isClick && typeof window.parent.__PS_PLAY_HOVER__ === 'function') window.parent.__PS_PLAY_HOVER__();
      }}
    }} catch (e) {{}}
  }}

  function setSceneMode(modeIdx) {{
    currentMode = modeIdx;
    groupCapsule.visible = (modeIdx === 0);
    groupFingent.visible = (modeIdx === 1);
    groupDNA.visible = (modeIdx === 2);
    [btnCap, btnFin, btnDna].forEach((b, idx) => {{
      if (b) b.classList.toggle('active', idx === modeIdx);
    }});
    burstEnergy = 1.0;
    triggerParentCue(true);
  }}

  [btnCap, btnFin, btnDna, btnCycle].forEach(b => {{
    if (b) b.addEventListener('pointerenter', () => triggerParentCue(false));
  }});

  if (btnCap) btnCap.addEventListener('click', () => setSceneMode(0));
  if (btnFin) btnFin.addEventListener('click', () => setSceneMode(1));
  if (btnDna) btnDna.addEventListener('click', () => setSceneMode(2));
  if (btnCycle) btnCycle.addEventListener('click', () => setSceneMode((currentMode + 1) % 3));

  container.addEventListener('pointerdown', e => {{
    if (e.target.closest('button')) return;
    isDragging = true;
    prevX = e.clientX;
    prevY = e.clientY;
    burstEnergy = 1.0;
    triggerParentCue(true);
  }});
  window.addEventListener('pointermove', e => {{
    if (!isDragging) return;
    targetRotY += (e.clientX - prevX) * 0.008;
    targetRotX += (e.clientY - prevY) * 0.008;
    prevX = e.clientX;
    prevY = e.clientY;
  }});
  window.addEventListener('pointerup', () => {{ isDragging = false; }});

  updateViewportCameraAndIframe();

  let clock = 0;
  function animate() {{
    requestAnimationFrame(animate);
    clock += 0.016;
    burstEnergy *= 0.93;

    rootGroup.rotation.y += (targetRotY + Math.sin(clock * 0.55) * 0.22 - rootGroup.rotation.y) * 0.08;
    rootGroup.rotation.x += (targetRotX + Math.cos(clock * 0.4) * 0.08 - rootGroup.rotation.x) * 0.08;

    if (groupCapsule.visible) {{
      pellets.forEach(p => {{
        const wave = Math.sin(clock * p.speed + p.phase) * 0.14;
        const burst = burstEnergy * 0.55;
        p.mesh.position.x = p.bx * (1 + burst) + wave;
        p.mesh.position.y = p.by * (1 + burst) + Math.cos(clock * p.speed + p.phase) * 0.14;
        p.mesh.position.z = p.bz * (1 + burst);
      }});
    }}
    if (groupFingent.visible) {{
      bottleGroup.rotation.y = clock * 0.35;
      fingentPill1.position.y = -0.75 + Math.sin(clock * 1.4) * 0.12;
      fingentPill2.position.y = -1.45 + Math.cos(clock * 1.2) * 0.10;
    }}
    if (groupDNA.visible) {{
      groupDNA.rotation.y = clock * 0.55;
    }}

    renderer.render(scene, camera);
  }}
  animate();

  window.addEventListener('resize', updateViewportCameraAndIframe);
}})();
</script>
</body>
</html>"""


def render_albus_pipeline_and_hex_ring_html(
    lang: str = "ru",
    major_count: int = 1,
    mod_count: int = 1,
    minor_count: int = 0,
    supp_count: int = 2,
    inn_count: int = 3,
    pairs_count: int = 3,
) -> str:
    """Рендерит секции 'Our Pipeline' и '02 — HOW WE TREAT IT (3D Hexagonal Ring)' из видео-референса Albus Therapeutics в палитре проекта."""
    lang_n = (lang or "ru").lower()
    total = max(1, major_count + mod_count + minor_count + supp_count)
    p_maj = max(10, min(75, round(major_count / total * 100))) if major_count > 0 else 15
    p_mod = max(10, min(65, round(mod_count / total * 100))) if mod_count > 0 else 25
    p_supp = max(10, min(55, round(supp_count / total * 100))) if supp_count > 0 else 20
    p_safe = max(5, 100 - min(95, p_maj + p_mod + p_supp))

    if lang_n == "kk":
        pipe_title = "Клиникалық-фармакологиялық аудит конвейері (Clinical R&D Pipeline)"
        sec2_eyebrow = "02 — ҚАУІПТІ ҚАЛАЙ ТАЛДАЙМЫЗ"
        sec2_title = "Нысана-ағзалар және тәуекел деңгейлері"
    elif lang_n == "en":
        pipe_title = "Clinical Pharmacology Audit Pipeline"
        sec2_eyebrow = "02 — HOW WE ANALYZE IT"
        sec2_title = "Target Organ & Severity Areas"
    else:
        pipe_title = "Конвейер клинико-фармакологического аудита (Our Pipeline)"
        sec2_eyebrow = "02 — АРХИТЕКТУРА БЕЗОПАСНОСТИ"
        sec2_title = "Зоны органного риска и доказательности"

    raw_html = f"""
<div class="ps-albus-grid" style="margin: 1.15rem 0 1.35rem 0; display: grid; grid-template-columns: 1.18fr 0.82fr; gap: 16px;">
  <!-- СЕКЦИЯ A: OUR PIPELINE (по референсу Albus Therapeutics 00:03) -->
  <div style="background: #111B20; border: 1px solid #263940; border-radius: 14px; overflow: hidden; box-shadow: 0 10px 28px rgba(0,0,0,0.35);">
    <div style="background: linear-gradient(90deg, #0D3B33 0%, #144959 60%, #36D6B0 100%); padding: 12px 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
      <div style="font-size: 0.84rem; font-weight: 700; color: #EAF2F2; letter-spacing: 0.02em;">{pipe_title}</div>
      <div style="display: flex; gap: 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 600; color: #EAF2F2; text-transform: uppercase;">
        <span>01 INN NORMALIZE</span>
        <span>02 CYP450/P-gp</span>
        <span>03 DDINTER</span>
        <span>04 PUBMED BADS</span>
        <span>05 ML/AI AUDIT</span>
      </div>
    </div>
    <div style="padding: 16px 18px; display: flex; flex-direction: column; gap: 11px;">
      <div style="display: grid; grid-template-columns: 195px 1fr; align-items: center; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 7px; font-size: 0.78rem; font-weight: 600; color: #EAF2F2;">
          <span>Hemostasis &amp; GI</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#F43F5E; border:1px solid rgba(244,63,94,0.45); padding:1px 5px; border-radius:3px;">VKORC1/COX1</span>
        </div>
        <div style="height: 11px; background: #17252B; border-radius: 99px; overflow: hidden; display: flex;">
          <div style="width: 56%; background: #0D3B33;"></div>
          <div style="width: 28%; background: #F43F5E; box-shadow: 0 0 10px #F43F5E;"></div>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: 195px 1fr; align-items: center; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 7px; font-size: 0.78rem; font-weight: 600; color: #EAF2F2;">
          <span>Hepatic Clearance</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#36D6B0; border:1px solid rgba(54,214,176,0.45); padding:1px 5px; border-radius:3px;">CYP2C9/3A4</span>
        </div>
        <div style="height: 11px; background: #17252B; border-radius: 99px; overflow: hidden; display: flex;">
          <div style="width: 48%; background: #133540;"></div>
          <div style="width: 24%; background: #36D6B0; box-shadow: 0 0 10px #36D6B0;"></div>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: 195px 1fr; align-items: center; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 7px; font-size: 0.78rem; font-weight: 600; color: #EAF2F2;">
          <span>Renal Filtration</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#F59E0B; border:1px solid rgba(245,158,11,0.45); padding:1px 5px; border-radius:3px;">RAAS/PGI2</span>
        </div>
        <div style="height: 11px; background: #17252B; border-radius: 99px; overflow: hidden; display: flex;">
          <div style="width: 34%; background: #133540;"></div>
          <div style="width: 22%; background: #F59E0B;"></div>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: 195px 1fr; align-items: center; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 7px; font-size: 0.78rem; font-weight: 600; color: #EAF2F2;">
          <span>PubMed Supplements</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#67B7D1; border:1px solid rgba(103,183,209,0.45); padding:1px 5px; border-radius:3px;">PMIDs ({supp_count})</span>
        </div>
        <div style="height: 11px; background: #17252B; border-radius: 99px; overflow: hidden; display: flex;">
          <div style="width: 26%; background: #0D3B33;"></div>
          <div style="width: 19%; background: #67B7D1;"></div>
        </div>
      </div>
    </div>
  </div>
  <div style="background: #111B20; border: 1px solid #263940; border-radius: 14px; padding: 14px 18px; display: grid; grid-template-columns: 1.05fr 0.95fr; align-items: center; gap: 12px; box-shadow: 0 10px 28px rgba(0,0,0,0.35);">
    <div style="display: flex; justify-content: center; align-items: center;">
      <svg viewBox="0 0 230 190" style="width: 100%; max-width: 225px; height: auto; overflow: visible;">
        <defs>
          <linearGradient id="hexGradMaj" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#F43F5E"/>
            <stop offset="100%" stop-color="#BE123C"/>
          </linearGradient>
          <linearGradient id="hexGradEm" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#36D6B0"/>
            <stop offset="100%" stop-color="#0D9488"/>
          </linearGradient>
          <linearGradient id="hexGradCy" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#67B7D1"/>
            <stop offset="100%" stop-color="#0284C7"/>
          </linearGradient>
        </defs>
        <polygon points="68,38 148,26 184,84 156,112 132,68 82,76" fill="url(#hexGradEm)" stroke="#0B1114" stroke-width="2"/>
        <polygon points="184,84 152,154 98,162 110,128 140,122 156,112" fill="url(#hexGradMaj)" stroke="#0B1114" stroke-width="2"/>
        <polygon points="98,162 52,126 42,84 74,88 82,118 110,128" fill="url(#hexGradCy)" stroke="#0B1114" stroke-width="2"/>
        <polygon points="42,84 68,38 82,76 74,88" fill="#F59E0B" stroke="#0B1114" stroke-width="2"/>
        <polyline points="164,46 186,28 216,28" fill="none" stroke="#36D6B0" stroke-width="1.4"/>
        <text x="216" y="24" text-anchor="end" fill="#EAF2F2" font-family="JetBrains Mono, monospace" font-size="11" font-weight="700">{p_safe}%</text>
        <polyline points="162,138 184,158 216,158" fill="none" stroke="#F43F5E" stroke-width="1.4"/>
        <text x="216" y="153" text-anchor="end" fill="#F43F5E" font-family="JetBrains Mono, monospace" font-size="11" font-weight="700">{p_maj}%</text>
        <polyline points="56,134 34,154 6,154" fill="none" stroke="#67B7D1" stroke-width="1.4"/>
        <text x="6" y="149" text-anchor="start" fill="#67B7D1" font-family="JetBrains Mono, monospace" font-size="11" font-weight="700">{p_supp}%</text>
        <polyline points="50,62 28,44 6,44" fill="none" stroke="#F59E0B" stroke-width="1.4"/>
        <text x="6" y="39" text-anchor="start" fill="#F59E0B" font-family="JetBrains Mono, monospace" font-size="11" font-weight="700">{p_mod}%</text>
      </svg>
    </div>
    <div>
      <div style="font-family:'JetBrains Mono',monospace; font-size:0.62rem; font-weight:700; color:#36D6B0; letter-spacing:0.08em;">{sec2_eyebrow}</div>
      <div style="font-size:1.02rem; font-weight:700; color:#EAF2F2; margin:2px 0 8px 0;">{sec2_title}</div>
      <div style="background:rgba(54,214,176,0.08); border:1px solid rgba(54,214,176,0.28); border-radius:6px; padding:5px 9px; font-size:0.72rem; color:#EAF2F2; margin-bottom:6px;">
        <b style="color:#36D6B0;">1,939+</b> INN Substances · <b style="color:#67B7D1;">{inn_count}</b> Active
      </div>
      <div style="background:rgba(244,63,94,0.08); border:1px solid rgba(244,63,94,0.28); border-radius:6px; padding:5px 9px; font-size:0.72rem; color:#EAF2F2; margin-bottom:8px;">
        <b style="color:#F43F5E;">{major_count} Major</b> · <b style="color:#F59E0B;">{mod_count} Mod</b> · <b style="color:#67B7D1;">{supp_count} PubMed</b>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#91A5AA;">
        <div><span style="color:#F43F5E;">■</span> MAJOR RISK</div>
        <div><span style="color:#F59E0B;">■</span> MODERATE</div>
        <div><span style="color:#67B7D1;">■</span> PUBMED BADS</div>
        <div><span style="color:#36D6B0;">■</span> VERIFIED SAFE</div>
      </div>
    </div>
  </div>
</div>
"""
    return "".join(line.strip() for line in raw_html.splitlines() if line.strip())

