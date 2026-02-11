# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Threads Automation  
**Generated:** 2024  
**Category:** SaaS Dashboard / Analytics Dashboard

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#2563EB` | `--color-primary` |
| Secondary | `#3B82F6` | `--color-secondary` |
| CTA/Accent | `#F97316` | `--color-cta` |
| Background | `#F8FAFC` | `--color-background` |
| Text | `#1E293B` | `--color-text` |
| Border | `#E2E8F0` | `--color-border` |

**Color Notes:** Trust blue + orange CTA contrast. High contrast for accessibility (WCAG AA minimum).

### Typography

- **Heading Font:** Inter (system sans-serif fallback)
- **Body Font:** Inter (system sans-serif fallback)
- **Mood:** Clean, professional, readable
- **Google Fonts:** [Inter](https://fonts.google.com/specimen/Inter)

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
```

### Spacing Variables

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Hero images, featured cards |

---

## Component Specs

### Buttons

```css
/* Primary Button */
.btn-primary {
  background: #2563EB;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
  min-height: 44px; /* Touch target */
}

.btn-primary:hover {
  background: #1D4ED8;
  transform: translateY(-1px);
}

.btn-primary:focus {
  outline: none;
  ring: 2px;
  ring-color: #2563EB;
  ring-offset: 2px;
}

.btn-primary:active {
  transform: scale(0.98);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: #2563EB;
  border: 2px solid #2563EB;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
  min-height: 44px;
}
```

### Cards

```css
.card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px; /* Prevent zoom on iOS */
  transition: border-color 200ms ease;
  min-height: 44px; /* Touch target */
}

.input:focus {
  border-color: #2563EB;
  outline: none;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #F3F4F6;
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Data-Dense + Minimalism

**Keywords:** Clean, simple, spacious, functional, white space, high contrast, geometric, sans-serif, grid-based, essential

**Best For:** Enterprise apps, dashboards, documentation sites, SaaS platforms, professional tools

**Key Effects:** Subtle hover (200-250ms), smooth transitions, clear type hierarchy, fast loading

### Page Pattern

**Pattern Name:** Data-Dense Dashboard

- **Conversion Strategy:** Real-time data visibility, clear metrics hierarchy
- **CTA Placement:** Action buttons in header, inline with data
- **Section Order:** Header > Filters > Stats Cards > Charts > Recent Activity

---

## Anti-Patterns (Do NOT Use)

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y
- ❌ **Touch targets < 44px** — Minimum 44x44px on mobile
- ❌ **No ARIA labels** — Icon-only buttons need aria-label
- ❌ **No reduced motion support** — Respect prefers-reduced-motion

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile
- [ ] Touch targets minimum 44x44px
- [ ] ARIA labels on icon-only buttons
- [ ] Semantic HTML (button, nav, main, etc.)

---

## Accessibility Requirements

### WCAG Compliance
- **Minimum:** WCAG AA (4.5:1 contrast ratio)
- **Target:** WCAG AAA (7:1 contrast ratio) for critical text

### Keyboard Navigation
- All interactive elements accessible via Tab
- Focus order matches visual order
- Visible focus indicators (2-4px ring)
- Skip links for navigation-heavy pages

### Screen Readers
- Semantic HTML elements
- ARIA labels for icon-only buttons
- ARIA live regions for dynamic content
- Proper heading hierarchy (h1 → h2 → h3)

### Motion
- Respect `prefers-reduced-motion: reduce`
- Disable animations when reduced motion preferred
- Use `motion-reduce:` Tailwind variant

---

## Performance Guidelines

- **Image Optimization:** Use WebP format, appropriate sizes
- **Lazy Loading:** Below-fold images lazy load
- **Code Splitting:** Route-based code splitting
- **Font Loading:** `font-display: swap` for web fonts
- **Animation Performance:** Use `transform` and `opacity` only

---

**Last Updated:** 2024  
**Version:** 1.0.0
