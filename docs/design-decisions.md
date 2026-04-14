# Design Decisions

Key architectural choices made in Pitch Detective, with reasoning.

---

## Single-File Architecture

**Choice:** All HTML, CSS, and JavaScript live in one file (`pitch-detective.html`).

**Why:** The primary deployment target is a GitHub Gist rendered via `htmlpreview.github.io`, or a URL shared from a phone. A single file can be deployed via `bash deploy-gist.sh`, shared as a URL, or opened directly from a filesystem. No build step, no CDN, no dependencies beyond Google Fonts. This makes iteration fast and deployment zero-friction.

**Trade-off:** The file is large (~3300+ lines). When adding features, be disciplined about section comments (`// ─── SECTION ───`).

---

## Pitch Detection: Dual-Mode (Autocorr + Spectral)

**Choice:** Blend autocorrelation (YIN-style) with spectral peak analysis; prefer spectral when they agree within 0.8 semitones.

**Why:** Autocorrelation is robust for clean sine-like whistles but can octave-jump on breathy tones. Spectral analysis catches the fundamental bin well for harmonic-rich input but can track upper partials. Neither alone is reliable across all input types. Blending (70% spectral, 30% autocorr when they agree) outperforms either alone in informal testing.

**Current limits:** The frequency range is fixed at 350–3200 Hz (optimised for whistling and voice; instruments like guitar lower strings won't work well).

---

## Note Stabilisation via Pitch Clusters

**Choice:** Rather than a simple fixed-threshold note-change detector, use a sliding window of `voicedMidiFrames` → cluster them by proximity (±0.9 semitone tolerance) → snap the current pitch to the nearest cluster centre.

**Why:** Whistlers wobble. A raw pitch detector produces a jagged MIDI trace that flickers several semitones around the true note. Clustering over a 2.6s window finds the "intended" pitches — the ones that appear repeatedly — and snaps to them. This dramatically reduces spurious note events.

**Parameters to tune:**
- `MIDI_CLUSTER_WINDOW_MS = 2600` — how far back to look for clusters
- `MIDI_CLUSTER_TOLERANCE = 0.9` — semitone radius of a single cluster
- `MIDI_CLUSTER_MIN_FRAMES = 4` — a cluster must appear in at least 4 frames

---

## Phrase Boundaries

**Choice:** A silence gap ≥ 900ms (`PHRASE_GAP_MS`) closes the current phrase. Start/Stop listening also closes a phrase.

**Why:** Phrases are the unit for scale inference. Breaking too eagerly (small gap) produces too-short phrases for meaningful scale detection. Breaking too rarely means a single long session never segments. 900ms is roughly "take a breath between phrases." This is tunable.

---

## Scale Inference: Phrase-First, Whole-Idea Fallback

**Choice:** Scale inference prefers the currently-active phrase's notes. If the active phrase has fewer than 3 notes, it falls back to the most recent phrase with ≥3 notes, then the whole session.

**Why:** A scale fits better when inferred from a single coherent phrase. If the user switches keys between phrases (modulation, different song segments), phrase-first detection will follow. The fallback to session-level prevents showing nothing while the first phrase builds up.

---

## Scale Confidence Formula

**The problem (as seen in practice):** Early versions reported 97%+ confidence after only 2–3 notes. When you whistle just C and G, ten different scales all contain both notes — C Major, G Major, A minor, E Phrygian, G Mixolydian, C Pentatonic, etc. Showing "97% C Major" is misleading.

**Current approach (as of April 2026):**

```js
const distinctPC = new Set(context.notes.map(n => n.pitchClass)).size;
const breadth = Math.min(1, distinctPC / Math.max(5, best.intervals.length * 0.7));
const uniqueness = secondBest
  ? (best.score - secondBest.score) / (Math.abs(best.score) * 0.2 + 1)
  : 0.8;
const clampedUniqueness = Math.min(1, Math.max(0, uniqueness));
const confidence = Math.min(95, Math.round(best.coverage * 50 + clampedUniqueness * 30 + breadth * 20));
```

Three components:
1. **Coverage (50 pts max):** What fraction of the heard notes are in-scale? Still the primary signal.
2. **Uniqueness (30 pts max):** How much better is the winner than second place? Near-ties suppress confidence.
3. **Breadth (20 pts max):** Have we heard enough *distinct* pitch classes to meaningfully distinguish scales? Two notes can't distinguish C major from A minor.

Max is 95 (not 100/99) — the heuristic nature of the whole system means we should never claim certainty.

**UI:** The top 3 candidates are shown as a muted "Also fits: …" line, so the user can see the ambiguity directly.

---

## Scale Hysteresis (Lock Behaviour)

**Choice:** `updateScaleTracking()` requires a candidate to appear consistently for N frames before becoming the "committed" scale. During transitions, the old scale is held.

**Why:** Without hysteresis, the displayed scale flickers every few frames as the user changes notes. A musician needs to see a stable tonic, not one that changes with each note. Hysteresis trades latency for stability — acceptable for a sketch tool.

**Parameters:**
- `SCALE_LOCK_FRAMES_ACTIVE = 10` — frames needed to commit during active phrase
- `SCALE_LOCK_FRAMES_IDLE = 4` — frames needed when between phrases

---

## Pitch Contour Canvas

**Choice:** Store all raw pitch data in `contourPoints` and render a scrollable canvas that grows with the session.

**Why:** A fixed "last N seconds" window (as in some earlier versions) loses history. For a sketching tool, being able to scroll back and see what you played — and how the pitch wobbled — is valuable. The canvas matches the piano-roll's px/ms rate so both views stay in sync.

**During playback:** The contour also shows semi-transparent note blocks (the quantized melody) overlaid, creating a "piano roll on top of contour" view. This makes it easy to see how well the detected melody matches the raw pitch.

---

## Playback Engine

**Choice:** Pre-schedule all oscillators at once via `audioCtx.currentTime + offsetSeconds`, using a separate `AudioContext` from the mic capture context.

**Why:** Mixing playback and capture in the same context can cause feedback loops on devices without hardware monitoring separation. More importantly, pre-scheduling to the audio clock gives jitter-free timing — JavaScript's `setTimeout` is not sample-accurate.

**Tone design:** Sawtooth oscillator → lowpass filter (cutoff ~1200 Hz, Q ~1.2) → gain node with 8ms attack / 40ms release envelope. This gives a warm, buzzy tone that is clearly distinct from a raw whistle, so you can tell playback from live input.

---

## Export Formats

**ABC Notation:** Used because it is human-readable, copy-pasteable into many notation tools, and compact for short melodies. Duration quantisation is at 240ms units (one "beat" at 120 BPM).

**MIDI:** Standard type-0 MIDI file generated in pure JavaScript (no library). Rough timing only — not meant to be DAW-perfect, meant for "here is the rough idea" capture.

**Local Storage:** Saved ideas live in `localStorage` under `pitch-detective-ideas-v2`. This is intentionally browser-local with no server dependency. The capture server (`dev_server.py`) only saves recordings and JSON traces; it does not store the saved-idea list.

---

## Dev Server vs. Static

The `dev_server.py` capture server is a debugging aid only. It auto-saves `captures/` uploads so you can compare the browser's pitch trace to an offline analysis. It is not required for the app to function; all features work from `file://` or any static server.

The offline analysis script (`scripts/analyze_capture.py`) runs a separate pitch pass using `ffmpeg` + Python and compares it to the saved trace JSON — useful for tuning detector parameters.
