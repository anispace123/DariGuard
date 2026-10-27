---
name: animate
description: Build web animations and micro-interactions from scratch with high craft standards — purposeful motion, sub-300ms durations, responsive ease-out curves, GPU-accelerated properties only.
metadata:
  author: emilkowalski
  version: "1.0.0"
---

# Animate Skill (Emil Kowalski)

Guidelines for building purposeful, responsive micro-interactions and transitions.

## Core Rules

1. **Answer "Why does it move?":**
   - Provide spatial continuity (where did this item come from?).
   - Feedback for user action (confirm click or selection).
   - Draw attention to high-priority changes (e.g., alert appearance).
   - If an element doesn't need to move, **do not animate it**.

2. **Properties:**
   - ONLY animate GPU-composited properties: `transform` (`translate`, `scale`, `rotate`) and `opacity`.
   - NEVER animate layout geometry: `width`, `height`, `top`, `left`, `margin`, `padding`.

3. **Curves & Timings:**
   - **Sub-300ms Rule:** UI animations should complete within 150ms – 250ms.
   - **No `ease-in` on UI entry:** Entering UI elements must start fast and decelerate gracefully using `ease-out` or custom cubic-beziers:
     `cubic-bezier(0.16, 1, 0.3, 1)` (snappy spring feel) or `cubic-bezier(0, 0, 0.2, 1)`.
   - High-frequency actions (like keyboard navigation, typing) must have zero or near-instant animation (<80ms).

4. **Origins & Natural Scaling:**
   - Popovers, modals, and tooltips should animate from their trigger or natural center.
   - Initial scale should be subtle (e.g. `scale(0.96) -> scale(1)`), NEVER scale from raw zero (`scale(0)`).

5. **Accessibility:**
   - Always wrap CSS transitions and keyframes in `@media (prefers-reduced-motion: reduce)`.
