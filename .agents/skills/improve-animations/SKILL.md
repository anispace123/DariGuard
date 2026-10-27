---
name: improve-animations
description: Survey an entire codebase's motion and animation code as a senior motion advisor, producing a prioritized audit and actionable implementation plan.
metadata:
  author: emilkowalski
  version: "1.0.0"
---

# Improve Animations (Emil Kowalski)

Global motion survey and prioritization for web interfaces.

## Workflow

1. **Map Motion Surface:** Identify all keyframes, transitions, and hover states across the application.
2. **Detect Bottlenecks:**
   - Sluggish dropdown or modal opens (>250ms or ease-in).
   - Layout thrashing caused by animating box dimensions.
   - Excessive animation on frequently clicked buttons.
3. **Produce Implementation Plan:**
   - Group fixes by priority (High: feel-breaking; Medium: polish; Low: minor enhancement).
   - Provide exact cubic-bezier timing functions, duration tokens, and property replacements.
