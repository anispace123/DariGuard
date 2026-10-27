---
name: review-animations
description: Review animation and motion code against strict senior design engineering standards. Evaluates duration, easing curves, GPU properties, reduced-motion compliance, and spatial origin.
metadata:
  author: emilkowalski
  version: "1.0.0"
---

# Review Animations (Emil Kowalski)

Audit motion code for craft regressions and poor feel. Defaults to flagging issues until proven snappy and justified.

## 10 Non-Negotiable Standards

1. **Justified Motion:** Does the motion convey state, spatial continuity, or immediate tactile feedback?
2. **Frequency Appropriateness:** Is this action repeated 100 times an hour? If yes, eliminate delay.
3. **Responsive Easing:** Check for sluggish `ease-in` curves on entering elements; reject them in favor of fast deceleration (`cubic-bezier(0.16, 1, 0.3, 1)`).
4. **Sub-300ms Rule:** Any transition taking $>300\text{ms}$ is flagged unless it is an explicit cinematic intro.
5. **GPU-Only Transforms:** Flag any CSS transitions on `width`, `height`, `left`, `right`, `top`, `bottom`, `margin`, `padding`.
6. **Accessible Reduced-Motion:** Ensure `@media (prefers-reduced-motion: reduce)` disables or minimizes motion.
7. **No `scale(0)`:** Initial scaling must start from $\ge 0.95$.
8. **Spatial Anchoring:** Dropdowns and modals must visually connect to their trigger element.
9. **No Floating Delay:** Stagger delays must not exceed $30\text{ms}$ per item, with maximum cumulative stagger $\le 150\text{ms}$.
10. **Zero Layout Thrashing:** Motion must not cause sibling elements to re-flow unexpectedly.
