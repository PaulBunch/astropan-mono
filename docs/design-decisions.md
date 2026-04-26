# Design Decisions: AstroPan Font

[Читать на русском](design-decisions.ru.md)

This document records the key architectural and aesthetic decisions of the project. The main goal is to create a set of astrological symbols optimized for legibility at ultra-small sizes (**10px**) in developer environments.

## 1. Fundamental Principles
* **Decisive shapes over detail:** At 10px, any detail smaller than 1px (100 UPM) becomes noise. Priority is given to preserving internal counter-space
* **Optical consistency:** The font is designed as a visual companion to **JetBrains Mono**, inheriting its “technical” character and vertical metrics
* **Clarity over systematism:** The choice of glyph width is dictated not by mathematical multiples of the terminal grid, but by the physical legibility of the sign

---

## 2. Geometric Metrics

| Parameter          | Value       | Rationale                                                                                               |
| :----------------- | :---------- | :------------------------------------------------------------------------------------------------------ |
| **UPM**            | 1000        | Industry standard for precise coordinate control.                                                       |
| **Advance Width**  | **800 UPM** | **Final decision.** Provides 8px width at 10px size. Balance between density and legibility.            |
| **Cap Height**     | 730 UPM     | Aligned with JetBrains Mono uppercase height.                                                           |
| **x-Height**       | 550 UPM     | Aligned with JetBrains Mono lowercase height.                                                           |
| **Sidebearings**   | 50–100 UPM  | Minimum “safety gap” to prevent glyphs from merging.                                                    |

---

## 3. Design Language and Stroke

The font is divided into two functional groups with different drawing approaches:

### 3.1. Planets and Aspects (Geometric Group)
* **Stroke type:** Monoline (Constant weight)
* **Thickness:** Main stroke — **80 UPM**, additional elements — **50 UPM**
* **Concept:** Use of the circle as the base element for all planetary glyphs
* **Spacing rule:** Minimum distance between parallel strokes — **100 UPM** (1px)

### 3.2. Zodiac Signs (Calligraphic Group)
* **Stroke type:** Dynamic stroke with manual thickness compensation
* **Goal:** Preserve traditional recognizability of signs at high element density (especially Virgo ♍ and Scorpio ♏)
* **Rounding:** Aggressive radii (**20+ UPM**) to prevent “blobs” at rasterized corners

---

## 4. Rasterization Rules (Grid-Fitting)
* **Grid alignment:** All nodes and stroke boundaries should gravitate toward the major grid step of **100 UPM**
* **Optical overshoots:** Rounded elements (planet circles, Aries arcs) extend beyond the baseline and Cap Height by **10–20 UPM** to compensate for the optical illusion of shrinking circles
* **Centering:** All glyphs are strictly geometrically centered within the 800 UPM width

---

## 5. Rejected Alternatives
* **Advance Width 600 UPM:** Rejected due to the inability to preserve the structure of complex signs (Pluto, Virgo) without reducing stroke thickness below the critical 50 UPM
* **Advance Width 900 UPM (1.5x of 600):** Despite being a standard multiple, this option was rejected after 10px (144 DPI) tests. Vertically symmetrical glyphs with delicate elements (e.g., Pluto) lose clarity
* **Double-width (1200 UPM):** Rejected as excessively wide, creating overly large visual gaps in text
