# EduMetrics UI Design System & Guidelines

This document outlines the visual language, design tokens, layout hierarchy, and reusable components for the EduMetrics teacher website. All future pages, components, modals, and tables **must** strictly adhere to this system to maintain visual cohesion, elegance, and consistency.

---

## 1. Color Palette (Strict)

The interface strictly uses the following curated palette and their accessible contrast tints/shades:

| Token Name | Hex Code | Purpose |
| :--- | :--- | :--- |
| `--color-cream` | `#F3EFDF` | Main canvas background, primary warm tone |
| `--color-cream-surface` | `#FAF8F2` | Inner elevated panels, table row highlights |
| `--color-cream-white` | `#FFFFFF` | Crisp contrast card backgrounds |
| `--color-sage` | `#BDCFAA` | Highlights, active pill tags, hover states |
| `--color-sage-light` | `#DCE7D0` | Subtle background badges, pass statuses |
| `--color-olive` | `#8E9E83` | Primary action buttons, badges, accents |
| `--color-olive-dark` | `#77876D` | Button hover states, prominent numbers |
| `--color-slate` | `#5E7892` | Primary accent, secondary text, chart series |
| `--color-light-slate` | `#A7B7C6` | Borders, outlines, secondary surfaces |
| `--color-dark-band` | `#1B2620` | Deep forest slate for feature bands & dark sections |
| `--color-dark-surface` | `#24322B` | Rounded icon tiles background |
| `--color-text-dark` | `#19241D` | High-contrast body text on cream surfaces |
| `--color-text-light` | `#F3EFDF` | High-contrast text on dark panels |

> **Rule:** Never use generic pure blacks (`#000000`), saturated primary blues, or random hex colors. Use the defined CSS variables.

---

## 2. Typography Rules (Strict)

| Hierarchy | Typeface | Usage |
| :--- | :--- | :--- |
| **Headings & Titles** | `Playfair Display` (Serif) | `h1`, `h2`, `h3`, `h4`, hero titles, card titles, table headers, large KPI numbers |
| **Body & UI Elements** | `Clarity City` (Sans-Serif) | Paragraphs, navigation items, buttons, form inputs, table data cells, badge text |

### CSS Variables:
```css
--font-title: 'Playfair Display', Georgia, serif;
--font-body: 'Clarity City', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

---

## 3. Layout Language & Generous Radii

The interface spans **full-screen edge-to-edge** without artificial outer frame boxes, utilizing balanced fluid horizontal padding (`clamp(1.5rem, 4vw, 4rem)`). The signature aesthetic is based on soft, generous curves, pill controls, floating action bars, and interlocking panels:

### Radius Tokens:
```css
--radius-panel: 32px;   /* Large nested sections & dark feature band */
--radius-card: 24px;    /* Cards, dropzones, KPI containers */
--radius-tile: 18px;    /* Icon tiles & nested list items */
--radius-pill: 9999px;  /* Nav items, buttons, search bars, chips */
--radius-circle: 50%;   /* Icon circles, medals, avatar containers */
```

---

## 4. Reusable UI Components

### 1. Connected Dual-Pill Button (`.dual-pill-btn`)
Used for primary actions with a connected circular action icon capsule:
```html
<a href="#" class="dual-pill-btn">
    <span>Action Title</span>
    <div class="dual-pill-circle">
        <!-- Inline SVG Icon -->
    </div>
</a>
```

### 2. Standalone Pill Buttons (`.pill-btn`)
Variants:
* `.pill-btn-olive`: Solid muted olive background with cream text.
* `.pill-btn-slate`: Solid slate blue background with cream text.
* `.pill-btn-outline`: Semi-transparent cream background with light-slate border.
* `.pill-btn-sm`: Compact button for tables and cards.

### 3. Floating Action Bar (`.floating-action-bar`)
A pill-shaped bar with nested chips, search input, and a circular action button:
```html
<div class="floating-action-bar">
    <span class="action-bar-chip">Active Filter</span>
    <input type="text" class="action-bar-input" placeholder="Search...">
    <button class="action-bar-circle-btn">
        <!-- SVG Icon -->
    </button>
</div>
```

### 4. Rounded Icon Tiles (`.quick-tile`)
Used in the dark feature band for quick links and module navigation:
```html
<div class="quick-tiles-grid">
    <a href="#" class="quick-tile">
        <div class="quick-tile-icon"><!-- SVG --></div>
        <span class="quick-tile-label">Module Name</span>
    </a>
</div>
```

### 5. Chic Card & Header (`.chic-card`, `.chic-card-header`)
Generously rounded white/cream containers with subtle slate borders:
```html
<div class="chic-card">
    <div class="chic-card-header">
        <span class="chic-card-title">Section Title</span>
        <span class="chic-badge badge-sage">Tag</span>
    </div>
    <!-- Card Content -->
</div>
```

### 6. Badges & Chips (`.chic-badge`)
* `.badge-sage`: Soft sage highlight.
* `.badge-olive`: Olive background highlight.
* `.badge-slate`: Slate blue badge.
* `.badge-alert`: Muted reddish tone for failures / risks.
* `.badge-pass`: Subtle green tint for passing status.

### 7. Form Controls & Sliders (`.chic-input`, `input[type="range"]`)
Inputs use rounded corners (`--radius-tile`), cream surface backgrounds, and slate focus rings. Sliders use custom olive thumbs with smooth hover scaling.

---

## 5. Iconography Policy

* **Zero Emojis:** Never use unicode emojis (e.g., no smiley, book, chart, graduation emojis).
* **Pure SVGs:** Use clean, minimalist inline SVG vector icons with `stroke-width="1.8"` to `2.5`, colored using CSS variables (`var(--color-olive)`, `var(--color-slate)`, or `currentColor`).
