# Interface Design System

## Product

Scale Ear Trainer is a dark, single-screen practice instrument for whistle pitch work. The interface should feel like a quiet audio analyzer or small studio tool: precise, compact, and adult, with color reserved for pitch information and recording/playback state.

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
