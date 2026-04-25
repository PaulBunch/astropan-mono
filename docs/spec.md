# AstroPan Mono — Font Technical Specification

> [Читать на русском](spec.ru.md)

## 1. Project Overview
**Name:** AstroPan Mono  
**Type:** Monospaced Icon Font  
**Purpose:** Display of astrological symbols in the AstroPan app interface and other compatible projects  
**License:** SIL Open Font License 1.1 (OFL)  
**Distribution format:** `.woff2` (primary), `.ttf` (archive)

---

## 2. Goals and Constraints
* **Main goal:** Create a consistent set of symbols that remain clearly identifiable at small sizes (**10px**). Priority is given to preserving counter-space and optical compensation of shapes.
* **Unified style:** Uniform stroke thickness, corner radii, and optical density for all glyphs ([details](design-decisions.md)).
* **Compatibility:** Proportions must allow seamless use alongside **JetBrains Mono**.

---

## 3. Technical Specifications

### 3.1. Font Metrics

**Glyph**
| Parameter          | Value                | Rationale                                 |
| :----------------- | :------------------- | :---------------------------------------- |
| Units Per Em (UPM) | 1000                 |                                           |
| Ascender           | 800                  |                                           |
| Descender          | -200                 |                                           |
| Cap height         | 730                  | Aligned with JetBrains Mono               |
| x-height           | 550                  | Aligned with JetBrains Mono               |
| Baseline           | 0                    |                                           |
| Advance width      | 800                  | Ensures clear symmetry (8px at 10px size) |
| Sidebearings       | 60–100 UPM each side | Ensures >1px spacing at 10px              |

**Stroke**
| Parameter                 | Value   | Rationale                                     |
| :------------------------ | :------ | :-------------------------------------------- |
| Main stroke width         | 80 UPM  | [Main stroke width selection](main_stroke.md) |
| Thin stroke width         | 50 UPM  |                                               |
| Min. gap between strokes  | 100 UPM | ≥1px to prevent merging                       |
| Corner rounding           | 20 UPM  | Softens “blobs” during rasterization          |

**Grid**
- All nodes are aligned to a minor grid step: 10 UPM
- Key outline boundaries are aligned to a major grid step: 100 UPM (for pixel-perfect rendering at 10px)

### 3.2. Geometry and Pixel Symmetry
Instead of adaptive width multiples (600/900/1200), the project uses a unified **800 UPM** standard for “Pixel Perfect” rendering:

1. **Even symmetry principle:** With 800 UPM width, the geometric center is at 400 UPM, matching the boundary between the 4th and 5th pixel on a 10-pixel grid.
2. **Optical overshoot:** Rounded elements may overshoot up to 10 UPM.
3. **Whitespace rule:** The glyph must occupy the central area so that the total “air” (LSB + RSB) is at least **100 UPM**.

**Density references**
- For signs: Virgo
- For planets: Pluto

---

## 4. Glyph Set (41 symbols)

### 4.1. Zodiac Signs (12)
| Symbol | Unicode | Name      |
| :----- | :------ | :-------- |
| ♈      | U+2648  | Aries     |
| ♉      | U+2649  | Taurus    |
| ♊      | U+264A  | Gemini    |
| ♋      | U+264B  | Cancer    |
| ♌      | U+264C  | Leo       |
| ♍      | U+264D  | Virgo     |
| ♎      | U+264E  | Libra     |
| ♏      | U+264F  | Scorpio   |
| ♐      | U+2650  | Sagittarius |
| ♑      | U+2651  | Capricorn |
| ♒      | U+2652  | Aquarius  |
| ♓      | U+2653  | Pisces    |

### 4.2. Planets (10)
| Symbol | Unicode | Name      |
| :----- | :------ | :-------- |
| ☉      | U+2609  | Sun       |
| ☽      | U+263D  | Moon      |
| ☿      | U+263F  | Mercury   |
| ♀      | U+2640  | Venus     |
| ♂      | U+2642  | Mars      |
| ♃      | U+2643  | Jupiter   |
| ♄      | U+2644  | Saturn    |
| ♅      | U+2645  | Uranus    |
| ♆      | U+2646  | Neptune   |
| ⯓      | U+2BD3  | Pluto     |

### 4.3. Major Aspects (5)
| Symbol | Unicode | Name        | Angle |
| :----- | :------ | :---------- | :---- |
| ☌      | U+260C  | Conjunction | 0°    |
| ⚹      | U+26B9  | Sextile     | 60°   |
| □      | U+25A1  | Square      | 90°   |
| △      | U+25B3  | Trine       | 120°  |
| ☍      | U+260D  | Opposition  | 180°  |

### 4.4. Minor Aspects (2)
| Symbol | Unicode | Name        | Angle |
| :----- | :------ | :---------- | :---- |
| ⚺      | U+26BA  | Semisextile | 30°   |
| ⚻      | U+26BB  | Quincunx    | 150°  |

### 4.5. House Signs (12)
There are no standard Unicode points for houses.  
Use Private Use Area (PUA): U+E001–U+E00C.

| Code   | Name     |
| :----- | :------- |
| U+E001 | House I  |
| U+E002 | House II |
| ...    | ...      |
| U+E00C | House XII|

For web use, create a CSS class map (`.icon-house-1`).

---

## 5. Workflow

### 5.1. File Structure
```
astropan-mono/
├── .github/                 # Infrastructure & CI/CD
│   └── workflows/
│       └── deploy.yml
├── src/
│   ├── config.toml          # Font parameters (name, version, metrics)
│   ├── glyphs/              # Source glyphs
│   │   ├── aries.svg
│   │   ├── taurus.svg
│   │   └── ...
│   ├── templates/ 
│   │   ├── guidelines.svg   # Master grid (non-editable layer)
│   │   └── glyph.svg        # New glyph template: guidelines + empty drawing layer
│   └── references/          # References (in .gitignore)
├── build/                   # Temporary files (.ufo) (in .gitignore)
├── dist/                    # Build output (in .gitignore)
│   ├── astropan-mono.woff2
│   └── astropan-mono.ttf
├── docs/
│   ├── spec.md              # Technical specification
│   ├── specimen.html        # Test page with all glyphs
│   └── design-decisions.md  # Design decisions log
├── scripts/
│   ├── build.py             # Font build script
│   ├── ff2ref.py            # Convert SVGs from FontForge to reference templates (scaling, cleaning, renaming)
│   └── svg_extractor.py     # Extract and normalize SVG icons from web sources into references (parsing, scaling, unique naming)
├── requirements.txt         # Dependency list
├── CONTRIBUTING.md          # Contributor guide: how to add glyphs, SVG requirements, naming conventions
├── README.md
└── LICENSE                  # OFL 1.1 license text
```

### 5.2. Tools
| Stage                | Tools                                |
| -------------------- | ------------------------------------ |
| Drawing              | Inkscape                             |
| Intermediate format  | UFO (Unified Font Object)            |
| Build (Compiler)     | `fontmake`, `ufoLib2`, `fonttools`   |
| Optimization         | `pyftsubset` (woff2 compression)     |
| Hinting              | FontForge                            |
| QA                   | Browser (10px test), Glyphr Studio   |

**Data flow:**  
`[SVG Sources]` → `[build.py]` → `[UFO Directory]` → `[fontmake]` → `[TTF/WOFF2]`

## 5.3. Data Management
The `src/config.toml` configures the build process:
* Maps file names (e.g., `pluto.svg`) to Unicode codepoints.
* Sets individual advance widths for wide glyphs.
* Stores global metrics (Ascender, Descender, UPM).

## 5.4. Coordinate Transformation (Inkscape → Font)
When importing vectors, the `build.py` script automatically converts coordinates from Inkscape’s screen system to font coordinates. The baseline in Inkscape is set at **800 px**.

**Y-axis inversion formula:**
$$y_{font} = 800 - y_{inkscape}$$

**Transformation examples (for UPM 1000):**
* Top boundary ($y_{ink} = 0$) $\Rightarrow$ $y_{font} = 800$ (Ascender)
* Baseline ($y_{ink} = 800$) $\Rightarrow$ $y_{font} = 0$ (Baseline)
* Bottom boundary ($y_{ink} = 1000$) $\Rightarrow$ $y_{font} = -200$ (Descender)

---

### 6. Development Phases

**Phase 0 — System (before drawing)**
- [x] Create `guidelines.svg`: em square 1000×1000, guides: baseline (0), cap height (730), x-height (550), geometric center (500), descender (-200)
- [x] Visually determine and fix the optical center value
- [x] Draw a test rectangle with a 100 UPM stroke width
- [x] Implement the initial font build script `build.py`
- [x] Implement the first version of `specimen.html`
- [x] Check test rectangle readability at 10px in browser
- [x] Finalize metric values in this document

**Phase 1 — Reference glyphs (6 symbols)**
Goal: test the system on edge cases.
- [x] ☍ Opposition — simplest
- [x] □ Square — angular
- [x] ⯓ Pluto — maximum density
- [x] ♍ Virgo — maximum density
- [x] ♈ Aries — average
- [x] ♄ Saturn — complex composite

Transition to Phase 2: all 6 symbols are unambiguously readable at `font-size: 10px` in Chrome and Firefox.

**Phase 2 — Full set (41 symbols)**
Order: aspects → planets → zodiac signs → houses.
Aspects first: geometrically simplest (circle, square, triangle), set the design language for the whole set.
Houses last: no Unicode reference, shape is defined freely after the design language is established.

**Phase 3 — Hinting and optimization**
- [ ] Hinting in FontForge if artifacts appear at 10px
- [x] `pyftsubset` → final `.woff2`
- [x] Check all glyphs at 10, 12, 14, 16px in `specimen.html`
- [ ] Run font through `fontbakery`

---

## 7. Quality Criteria
The font is ready for release if:

1. **Legibility:** 100% recognition of all glyphs at 10px in Chrome and Firefox on screens with 120–150 DPI. On low-DPI screens (96 DPI), readiness is defined by the absence of counter merging at 12px.
2. **Geometry:** Deviation of main vertical/horizontal stem thickness from the target 80 UPM does not exceed -10/+5 UPM. In areas of optical compensation (joins, traps), deviation up to -50/+15 UPM is allowed if visual uniformity is preserved.
3. **Counters:** Internal empty spaces (counters) ≥ 50 UPM (at least 0.5px)
4. **Centering:** All glyphs are optically balanced relative to the center
5. **File size:** `.woff2` file size is less than 20 KB
6. **Performance:** No FOUT (flash of unstyled text) artifacts with `font-display: block`

---

## 8. Inspiration
Technical solutions and visual rigor are based on the principles of **JetBrains Mono**.
