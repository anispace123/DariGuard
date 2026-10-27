---
name: web-design-guidelines
description: Review and enforce Web Interface Guidelines compliance covering accessibility (WCAG), focus states, form usability, responsive design, typography scales, touch targets, and interaction states. Use when designing, reviewing, or implementing web interfaces.
metadata:
  author: vercel-labs
  version: "1.0.0"
---

# Web Interface Guidelines (Vercel Labs)

Enforces high-craft, production-grade web interface design standards based on the official Vercel Web Interface Guidelines.

## Core Rules & Verification Checklist

### 1. Typography & Hierarchy
- Hierarchy must be strictly established through font weight, size, and semantic color contrast (not through decorative elements).
- Use a clear modular type scale (e.g., 12px, 14px, 16px, 20px, 24px, 32px, 48px).
- Line heights: tightly coupled for headings (`leading-tight` ~1.1-1.2), comfortable for body prose (`leading-relaxed` ~1.5-1.6).
- High contrast for primary text ($\ge 7:1$), readable muted secondary text ($\ge 4.5:1$).

### 2. Buttons & Actions
- Loading states: Keep original button label while indicating loading (do not cause layout shift).
- Prevent loading flicker: Show spinners with a small delay (~150ms) and enforce minimum visibility (~300ms).
- Ellipsis convention: Actions opening a dialog or triggering an ongoing asynchronous task must end with an ellipsis (`…`).
- Icon-only buttons: Must always have explicit `aria-label` or visually hidden screen reader text.
- Destructive actions: Always require confirmation or provide an explicit Undo window.

### 3. Forms & Inputs
- Mobile input sizing: Font size inside `<input>` and `<select>` must be $\ge 16\text{px}$ on mobile viewports to prevent iOS Safari auto-zoom.
- Never block paste: Do not disable clipboard paste into inputs or textareas.
- Focus rings: All interactive elements must have visible, unobscured focus rings using `:focus-visible` (never remove outline without providing an accessible replacement).
- Input touch targets: Minimum 44x44px hit area on mobile, $\ge 24\text{px}$ on desktop.

### 4. Layout, Spacing & Color
- 8pt / 4pt grid system: All margins, paddings, and component sizes align with multiples of 4px/8px.
- Subtle borders & elevation: Prefer 1px crisp borders (`border-slate-800` / `border-slate-200`) over heavy drop shadows.
- No random gradients or excessive glassmorphism that obscures text contrast.
