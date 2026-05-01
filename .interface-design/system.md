# Interface Design System

## Product

This is the Sandpad audio lab — a collection of whistle pitch detection and scale training tools. The visual language should feel like a quiet, personal audio analyzer: warm dark, precise, and compact. Color is reserved for state (recording, playing) and musical function. Navigation pages follow the same system as the tools; nothing shifts palette between the hub and the tools.

### Scale Ear Trainer

Single-screen practice instrument for whistle pitch work: precise, compact, adult.

## Typography

- UI face: Manrope.
- Data/readout face: JetBrains Mono.
- Base UI size: 13px with 1.65 line height.
- Page title: 24-30px, 600 weight, no hero treatment.
- Labels: 10px JetBrains Mono, uppercase, 0.1em tracking.
- Canvas titles: 13px JetBrains Mono, 600 weight.
- Metrics and current exercise: 18px JetBrains Mono, 600 weight.

## Palette

- Page: `#090807`.
- Panels: `#11100f`.
- Raised controls: `#171513`.
- Inset controls and readouts: `#0c0b0a` / `#0b0b0a`.
- Primary text: `#ebe5dc`.
- Secondary text: `#a49c91`.
- Muted text: `#6f675f`.
- Action/accent lime: `#cce600`, used sparingly.
- Warm detector/action orange: `#ea6f16`.
- Scale-degree colors may remain vivid because they encode musical function.

## Depth And Borders

- Use borders-first depth, not soft shadows.
- Standard border: `rgba(220, 214, 204, 0.14)`.
- Soft separation: `rgba(220, 214, 204, 0.08)`.
- Strong/focus border: `rgba(220, 214, 204, 0.28)`.
- Focus ring: `rgba(234, 111, 22, 0.32)`.
- Shadow should be barely present: `0 1px 0 rgba(255, 255, 255, 0.025)`.
- Panel radius: 4px.
- Control radius: 3px.
- Canvas radius: 4px.

## Spacing

- Use a 4px base grid.
- Common internal gaps: 6px, 8px, 10px, 12px, 14px, 16px.
- Controls should feel dense but not cramped.
- Header is compact; avoid subtitles or marketing copy in the main screen.

## Component Patterns

- Buttons: 38px minimum height, 13px horizontal padding, 500 weight.
- Primary actions are outlined/tinted, not solid neon blocks.
- Selects: 38px height, inset dark background, 1px low-contrast border.
- Sliders: thin 4px track with a small rectangular thumb.
- Panels and canvases use the same sharp, low-contrast border language.
- Musical data colors belong inside piano roll, histogram, degree chips, and spectrogram guides.

## Navigation / Hub Patterns (index.html)

### Header
- Orange pip dot eyebrow: `5px` circle at `#ea6f16`, followed by `10px` JetBrains Mono uppercase label in `--faint`.
- H1: Manrope 800, `clamp(40px, 5.5vw, 62px)`, `letter-spacing: -0.035em`.
- Lede: 15px Manrope, `--muted`, `max-width: 58ch`, `line-height: 1.72`.
- Subtle orange bloom: `linear-gradient(180deg, rgba(234, 111, 22, 0.04) 0%, transparent 260px)`.

### Tool Cards
- Grid: `repeat(auto-fill, minmax(280px, 1fr))`, `gap: 6px`.
- Base card: `var(--panel)` background, `1px solid var(--line)`, `border-radius: 4px`.
- `is-main` cards: orange accent border `rgba(234, 111, 22, 0.26)` / hover `0.5`.
- `is-new` cards: lime accent border `rgba(204, 230, 0, 0.24)` / hover `0.48`.
- Card name: 14px Manrope 700, `letter-spacing: -0.015em`.
- Card desc: 12.5px Manrope, `--muted`, `line-height: 1.58`.

### Badges
- `9px` JetBrains Mono, 700, uppercase, `letter-spacing: 0.1em`, `border-radius: 2px`, `padding: 2px 6px`.
- Main: orange text + border + tinted background.
- New: lime text + border + tinted background.
- Tool: `--faint` text, `var(--line)` border, transparent background.

### Compact List Rows (piano variants, any long collection)
- `display: flex; justify-content: space-between`, `padding: 8px 11px`.
- Transparent border by default, `var(--panel)` + `var(--line)` border on hover.
- Name: 12px JetBrains Mono 600. Tag: 9px JetBrains Mono 600 `--faint`.
- Index/root rows use `--orange` for the name.
- Gap between rows: `2px`.

### Version Timeline
- Flex row of `ver-link` nodes with `ver-sep` dividers (`16px × 1px`, `var(--line)`).
- Each node: flex-column, `align-items: center`, `gap: 5px`, `padding: 7px 10px 9px`.
- Dot: `8px` circle, `1.5px solid var(--faint)`. Best node: filled `var(--lime)` with glow `box-shadow: 0 0 6px rgba(204, 230, 0, 0.35)`.
- Version label: 10px JetBrains Mono 700. Sub-label: 9px JetBrains Mono `--faint`.
- Best node: lime color throughout; use `✦` suffix on the version label.
- Full descriptions as `title` attributes for accessibility without visual clutter.

### Section Headers
- `10px` JetBrains Mono 700, uppercase, `letter-spacing: 0.12em`, `--muted`.
- Count/meta: same size, `--faint`, no uppercase.
- `margin-bottom: 12px`.

### Footer
- `10px` JetBrains Mono, `--faint`, `border-top: 1px solid var(--line-soft)`, `padding-top: 20px`.
