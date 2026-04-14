# Backlog

Future work items for Pitch Detective, loosely prioritised.

Legend: 🔴 High · 🟡 Medium · 🟢 Low · 🔬 Research needed

---

## Active / In Progress

- [x] Melody playback — notes play with correct sustained durations
- [x] Whistle workbench checkpoint — new `whistle-workbench.html` for whistle-only iteration with waveform, large contour, playback, and feedback bundles
- [x] Playback timbre pivot — moved away from the old bright synthetic tone toward a darker piano-ish additive voice with stronger fundamental and faster overtone decay
- [x] Scrollable pitch contour canvas — full-session history, auto-scroll live
- [x] Piano roll overlay on contour — semi-transparent quantized notes over raw trace
- [x] Scale confidence fix — less eager, shows top-3 alternatives
- [x] AGENTS.md + CLAUDE.md + docs/ — project documentation
- [x] Feedback bundle (Save Feedback button) — saves recording WAV + playback WAV + verbose JSON for offline analysis
- [x] Pitch detection overhaul — fixed systematic octave-halving on pure whistles (see `docs/pitch-detection-findings-2026-04-14.md`)
- [x] Ghost note fix — `smoothedFreq` reset on first silent frame, not after 300ms timer
- [x] Onset attack guard — 3-frame stability required before committing first note of a phrase
- [x] Cluster chain-merge fix — removed `cluster.max` proximity condition that allowed unbounded spread
- [x] Same-MIDI merge threshold — 120ms → 35ms to preserve re-articulated notes
- [x] Removed `applyTonalCleanup` — was re-composing melodies through an imperfect scale lens

---

## Pitch Detection

- 🟡 **Vibrato / ornament detection** — A#5/B5 wobble (±50 cents) still forms two clusters at 0.55 st tolerance, causing note flips mid-sustain. Tag frames oscillating at > ±20 cents as "ornament" rather than note changes.
- 🟡 **Voiced/unvoiced confidence score** — return a confidence value from `detectPitch()` and use it to gate cluster updates (don't update clusters from low-confidence frames).
- 🟡 **Expand frequency range option** — a UI toggle for "instrument mode" (80–3200 Hz) vs "whistle mode" (350–3200 Hz) to support humming or guitar input.
- 🟢 **Onset latency** — the 3-frame onset guard (~50 ms) silently discards the attack; very short intended notes at phrase start may register late. Consider backdating note start to the first voiced frame of the winning pitch class.

---

## Scale / Mode Detection

- 🔴 **Tonic confidence separate from scale-type confidence** — currently the root and scale type are bundled. It would be more useful to say "tonic is almost certainly A, but it might be minor OR dorian."
- 🟡 **Multi-phrase tonal centre tracking** — detect when the user has modulated (started a new phrase in a different key) and show both the session key and the current phrase key.
- 🟡 **Melodic minor vs natural minor** — these differ only on 6̂ and 7̂; hard to distinguish from a short melody. Consider flagging them as "ambiguous minor."
- 🟢 **Show interval relationships** — when a note is detected, show it relative to the tonic as an arrow on the contour (e.g. "↑ P5 from tonic").
- 🔬 **Probabilistic key estimation** — replace the coverage-based scorer with a proper Bayesian model (prior = Krumhansl key profiles, likelihood = match to heard pitch classes). Likely needs testing against a labelled dataset.

---

## Contour Canvas

- 🟡 **Zoom control** — let the user pinch/scroll to change px/ms rate on the contour (currently fixed at ROLL_PX_PER_MS).
- 🟡 **Playhead scrubbing** — click/tap on the contour during playback to seek to that position.
- 🟢 **Colour by cents-from-scale** — shade the contour line by how far in cents the raw pitch is from the nearest scale degree (green = in tune, yellow = ±15¢, red = ±30¢+). Currently it's coloured by degree assignment.
- 🟢 **Export contour as SVG** — allow downloading the pitch contour as an SVG for use in music notation or presentations.

---

## Playback

- 🔴 **Keep tuning the workbench voice** — the new additive keyboard-ish tone is closer, but still needs work on brightness, attack noise, and long-note body.
- 🟡 **Instrument variety** — let the user choose the playback timbre: sine (pure), sawtooth (buzzy), triangle (flute-like), or a basic sampled piano/vibraphone via AudioBuffer.
- 🟡 **Tempo scaling** — a slider to play back the melody faster or slower (scale note durations proportionally).
- 🟡 **Loop** — loop the playback continuously until manually stopped.
- 🟢 **MIDI out** — send notes to a connected MIDI device via the Web MIDI API during playback.
- 🟢 **Harmonise playback** — optionally play back with a simple chord underneath (the tonic triad of the detected scale).

---

## Piano Roll

- 🟡 **Edit notes in the roll** — tap a note block to delete it, drag to move it, drag an edge to resize duration.
- 🟡 **Transpose** — a semitone up/down button that shifts all notes and updates the scale root.
- 🟢 **Colour by phrase** — different phrase bands get distinct background colours so they are visually separate.
- 🟢 **Click to play** — clicking a note in the piano roll plays that single note.

---

## Export / Sharing

- 🔴 **Better MIDI timing** — current MIDI export uses approximate durations. Improve by snapping to a calculated tempo grid derived from the phrase structure.
- 🟡 **Share URL** — encode the current idea (notes + scale) into a URL fragment so it can be shared without needing a server.
- 🟡 **MusicXML export** — more widely supported by notation software than ABC.
- 🟢 **WAV export of playback** — render the synthesized melody to a WAV file using OfflineAudioContext.
- 🟢 **Lilypond / MuseScore integration** — one-click export to an online engraver.

---

## UI / UX

- 🟡 **Dark/light mode toggle** — currently forced dark.
- 🟡 **Larger touch targets on mobile** — some buttons are too small for phone use; audit the mobile layout.
- 🟡 **Onboarding hint** — first-time users don't know what to do. A brief animated tooltip on "Start Listening" would help.
- 🟢 **Landscape layout on tablet** — the current single-column layout wastes space in landscape. Consider a two-column layout: contour + piano roll on the left, note display + scale card on the right.
- 🟢 **Accessibility** — ARIA labels, keyboard shortcuts, screen reader testing.

---

## Infrastructure

- 🟡 **Automated screenshot / regression test** — a Playwright or Puppeteer script that opens the page, feeds a pre-recorded audio clip via `AudioContext.createBuffer()`, and asserts the displayed scale matches the expected value.
- 🟡 **`dev_server.py` improvements** — add a simple `GET /api/captures` endpoint to list and replay saved takes from the browser UI.
- 🟢 **GitHub Pages auto-deploy** — a GitHub Actions workflow that updates `index.html` to the latest `pitch-detective.html` on push to main.
- 🟢 **Version stamp in UI** — show the git SHA or build date somewhere in the header badge.

---

## Known Bugs / Rough Edges

- `whistle-workbench.html` still over-segments whistle onsets on simple melodies like "Mary Had a Little Lamb"; the offline contour is usually simpler than the app's playable-note list.
- Scale detection with very short (< 3-note) phrases can show confident but wrong results.
- `applyTonalCleanup` and `applyDegreeMelodyCleanup` still exist in the code but are no longer called from `normalizeCapturedNotes`. They could be removed or repurposed for an opt-in "snap to scale" export mode.
- On some Android Chrome builds, `MediaRecorder` produces 0-byte chunks; the app falls back to trace-only silently but this is not surfaced to the user.
- The waveform visualizer sometimes goes black on resume from browser background tab; it recovers on the next frame but looks odd.
- Saved ideas in localStorage are not bounded; a user who saves hundreds of ideas will eventually hit the ~5MB limit without a clear error.
- A#5/B5 boundary wobble: cluster tolerance 0.55 st sometimes splits a slightly sharp A#5 into two clusters (A#5 and B5), causing note flips during a sustained tone.
