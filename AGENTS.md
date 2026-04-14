# AGENTS.md — Agent Guide for Sandpad / Pitch Detective

This file is the primary reference for AI agents (Claude Code, sub-agents, or any LLM tool) working on this repo.

---

## Project at a Glance

**Pitch Detective** is a single-file, mobile-friendly browser app (`pitch-detective.html`) that:
1. Listens through the microphone via `getUserMedia`
2. Detects the fundamental frequency of whistled (or sung) notes using autocorrelation + spectral analysis
3. Groups notes into phrases separated by silence gaps
4. Infers the most likely musical scale from those phrases
5. Renders a scrollable piano-roll timeline and pitch contour
6. Exports rough ABC notation and MIDI

The best-crafted iterations live in `claude-opus/whistle-reader_*.html` — **consult these files first** for prior art on any feature you are about to build.

---

## Agent Hierarchy & Recommended Models

| Task Type                              | Recommended Agent          |
|----------------------------------------|----------------------------|
| Complex JS features, nuanced audio DSP | `opus` sub-agent (claude-opus-4-6 or later) |
| Documentation, small edits, configs   | Any model (sonnet or haiku fine) |
| Broad codebase exploration             | `Explore` sub-agent         |
| Architecture / planning                | `Plan` sub-agent            |

**Rule of thumb:** Anything touching the pitch detection pipeline, scale inference scoring, canvas rendering, or Web Audio scheduling should go to an **opus** model. These algorithms are subtle and small mistakes compound.

---

## File Map

```
pitch-detective.html          ← The app. HTML + CSS + JS in one file.
claude-opus/
  whistle-reader.html         ← v0 from opus: basic pitch display
  whistle-reader_1.html       ← v1: scale degree detection added
  whistle-reader_2.html       ← v2: contour canvas, chroma grid
  whistle-reader_3.html       ← v3: clustering refinements
  whistle-reader_4.html       ← v4: mode naming improvements
  whistle-reader_5.html       ← v5: confidence tuning
  whistle-reader_6.html       ← v6: tonic heuristics
  whistle-reader_7.html       ← v7: BEST — pitch contour w/ scale lines, download audio
dev_server.py                 ← Local capture server (saves .webm + analysis JSON)
scripts/analyze_capture.py    ← Offline pitch analysis using ffmpeg
captures/                     ← Auto-uploaded takes (webm + analysis JSON pairs)
docs/
  design-decisions.md         ← Key architectural choices and reasoning
  backlog.md                  ← Prioritized future work
README.md                     ← User-facing overview
AGENTS.md                     ← This file
CLAUDE.md                     ← Claude Code project settings (links here)
```

---

## Key Invariants — Do Not Break These

1. **Single-file**: `pitch-detective.html` must remain a standalone file. No npm, no bundler, no external scripts beyond Google Fonts.
2. **No microphone state leaks**: Always disconnect nodes and call `audioCtx.close()` in `stopListening()`.
3. **`captureOriginMs`** is the `performance.now()` timestamp at which the current take began. All note `startTime` / `endTime` values are in the same `performance.now()` epoch.
4. **`normalizeCapturedNotes()`** is the canonical source of cleaned notes for all exports, piano roll rendering, and scale inference. Do not bypass it.
5. **Scale confidence must reflect ambiguity.** If multiple scales score similarly, confidence must be low, not high. See `docs/design-decisions.md` for the confidence formula rationale.

---

## Adding Features — Checklist

Before submitting any feature change to `pitch-detective.html`:

- [ ] Does it work in Chrome on iOS (Safari WebKit)? (primary target device)
- [ ] Does `clearHistory()` / `resetCaptureState()` also reset any new state you introduced?
- [ ] Does `stopListening()` cleanly tear down any new AudioNodes?
- [ ] Is any new `requestAnimationFrame` loop cancelled on stop?
- [ ] Is new canvas rendering HiDPI-safe (multiply by `devicePixelRatio`)?
- [ ] Does playback use a **separate** `AudioContext` from the mic capture context?
- [ ] Is the confidence change tested with both a 2-note melody and a full 8-note melody?

---

## The Pitch Detection Pipeline (brief)

```
Microphone → highpass (420 Hz) → lowpass (2600 Hz) → AnalyserNode
                                                          ↓
                               detectPitchFromSpectrum()  +  detectPitchFromAutocorr()
                                        ↓ blend (spectral primary)
                               recordVoicedMidiFrame(freq, now)   ← raw pitch history
                               stabilizeNoteToClusters(freq, now) ← cluster-snap
                               handleStableDetectedNote(note, now) ← note events
```

`voicedMidiFrames` holds `{time, midi}` for every voiced frame (useful for contour drawing).  
`recordedNotes` holds `{midi, startTime, endTime, durationMs, phraseId, ...}` for committed notes.

---

## Scale Inference Pipeline (brief)

```
recordedNotes → getScaleContext() → evaluateScaleCandidate(root, scaleName)
                                         ↓  score each of 12 roots × 9 scales
                                    detectScale() → top candidate + confidence
                                         ↓
                                    updateScaleTracking() → hysteresis / lock
                                         ↓
                                    updateScaleDisplay()  ← UI
```

**Key weakness**: With only 2–3 unique pitch classes, almost every scale fits at high coverage. Confidence must penalise this. See `docs/design-decisions.md §Scale Confidence`.

---

## Playback Notes

- Playback uses a **separate** `AudioContext` — never share with the mic context.
- Schedule all oscillators upfront using `audioCtx.currentTime + offsetSeconds`.
- Oscillator teardown on Stop: `oscillator.stop(audioCtx.currentTime)` + `audioCtx.close()`.
- Playback position is tracked via `performance.now()` diff from the playback start timestamp.

---

## Contour Canvas Notes

- `contourPoints` array: `{time: performance.now(), midi: float, degree: int|null}`
- Silence frames should push `{time, midi: 0, degree: null}` to break the line.
- Canvas is rendered at `devicePixelRatio` for crispness.
- Pixel-per-ms ratio: `ROLL_PX_PER_MS` (currently 0.11) — keep contour and piano roll in sync.
- Scale degree reference lines: solid + thicker for tonic (degree 0 interval), dashed for others.
- Left margin (~40px) reserved for degree number labels.

---

## Commit Style

- Co-author every commit:
  ```
  Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
  ```
  (or the appropriate model slug)
- Commit messages: imperative, present-tense, one sentence.
- Commit per logical feature, not per file change.

---

## What NOT To Do

- Do not use `eval()`, inline event handlers added via `innerHTML` with sensitive data, or fetch from third-party origins.
- Do not add a build step, package.json, or node_modules.
- Do not store audio blobs in localStorage (they are too large; use download buttons or the capture server).
- Do not show raw score numbers in the UI — only confidence percentages and human-readable labels.
- Do not make the scale lock snap instantly; the hysteresis in `updateScaleTracking()` is intentional.
