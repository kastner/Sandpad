# Pitch Detection Findings — 2026-04-14

Analysis session using saved feedback bundles (recording WAV + playback WAV +
verbose JSON). All bugs were found by diffing `rawNotes` vs `normalizedNotes`
against the voiced-frame trace and the raw audio spectrum.

---

## Bug 1 — Systematic octave-halving on pure whistle tones

**Symptom:** Every detected note was one octave below the whistled pitch
(C#6→C#5, B5→B4, D6→D5). Scale detector downstream identified the wrong key
(B Harmonic Minor instead of D Major on "Mary Had a Little Lamb").

**Root cause:** `detectPitchFromAutocorr` corrected for upper-partial peaks
using a `while` loop:

```js
while (correctedPos * 2 <= maxLag) {
  if (c[lowerLag] >= c[correctedPos] * 0.95) correctedPos = lowerLag;
  else break;
}
```

For near-pure whistle tones the autocorrelation function is nearly periodic, so
`c[lag×2] / c[lag] ≈ 1.0`. The loop **always fired** and unconditionally halved
the detected frequency.

**Fix:** Replace the while-loop with a single-step guard that only fires when
the detected frequency is above `DETECT_MAX_FREQ / 2` (~1600 Hz). Below that
threshold the detection is already plausible as a fundamental.

```js
const candidateHz = sampleRate / maxPos;
if (candidateHz > DETECT_MAX_FREQ / 2 && maxPos * 2 <= maxLag) {
  if (c[maxPos * 2] >= c[maxPos] * 0.88) maxPos = maxPos * 2;
}
```

---

## Bug 2 — Ghost "transition" notes between short inter-note silences

**Symptom:** A 150 ms silence between e.g. B5 and E6 produced a spurious C#6
(≈ 62%×B5 + 38%×E6) as the first note of the second phrase. The last phrase of
a song always sounded fine because its preceding silence was >300 ms.

**Root cause:** `smoothedFreq` was only reset by a `setTimeout(UI_FADE_MS=300ms)`
that never fired on short gaps. When E6 started, the first frame blended the
stale B5 frequency:

```
smoothedFreq = 0.62 × 987Hz + 0.38 × 1319Hz = 1113Hz = C#6
```

That C#6 became a real 120 ms note event before the pitch stabilised.

**Fix:** Reset `smoothedFreq = -1` immediately in `handleSilence()` (the first
silent RAF frame), not via a delayed timer.

---

## Bug 3 — Whistle attack glide captured as separate short notes

**Symptom:** Every phrase started with 1–3 spurious 120 ms notes at pitches
below the intended first note (G#5 → A5 → A#5 before the intended B5 onset).

**Root cause:** Whistles always glide up to pitch over ~150 ms during the
attack. `handleStableDetectedNote` committed a note event on the very first
voiced frame from silence, so each pitch class in the glide got its own event.

**Fix:** Phrase onset guard in `handleStableDetectedNote`. When
`currentNoteEvent === null`, require `NOTE_SWITCH_FRAMES` (3) consecutive frames
of the same pitch class before committing. The attack glide changes pitch class
every 1–2 frames so it never accumulates 3; the sustained note does within
~50 ms. `pendingOnsetStartTime` backdates the note's start so duration is
correct.

---

## Bug 4 — Cluster chain-merge spanning many semitones

**Symptom:** `midiClusters` showed a single cluster with `spread=5.48` semitones
(centerMidi 73.78, covering D–G#). Every note snapped to this one mega-cluster,
destroying pitch resolution.

**Root cause:** `computeMidiClusters` had two join conditions:

```js
if (Math.abs(frame.midi - center) <= tolerance
 || Math.abs(frame.midi - cluster.max) <= tolerance * 0.75)
```

The second condition (distance to `cluster.max`) allowed unbounded walking:
frames 0.4 st apart would all merge even if the cluster spanned 5+ semitones.

**Fix:** Remove the `cluster.max` condition. Only merge if within `tolerance`
of the cluster **center**. This bounds clusters to ±`MIDI_CLUSTER_TOLERANCE`
(0.55 st) around their mean.

---

## Bug 5 — Same-MIDI gap merge too aggressive (120 ms threshold)

**Symptom:** Two intentionally re-articulated D#6 notes (gap=112 ms) were
merged into one 1206 ms blob in `normalizeCapturedNotes`. The transition filter
then absorbed B5+D6 after it because D#6 and D6 differ by 1 semitone.

**Root cause:** The first step in `normalizeCapturedNotes` hardcoded:

```js
if (prev.midi === note.midi && gap <= 120) { /* merge */ }
```

120 ms is ~7 RAF frames — easily a real deliberate gap between repeated notes.

**Fix:** Dropped to **35 ms** (sub-2-frame glitch only). Also tightened:
- `prevNextDistance <= 1` → `=== 0` in the transition bridge filter
- `bridgeDistance <= 2` → `prev.pitchClass === next.pitchClass` in
  `applyTonalCleanup`

---

## Bug 6 — `applyTonalCleanup` rewrites intentional notes

**Symptom:** G#5 (intentional) was snapped to G5 (nearest in G Harmonic Minor),
then `applyDegreeMelodyCleanup` treated the resulting G5 as a short bridge
between F#5(deg7) and C6(deg4) and teleported it 5 semitones to C6. B5 became
A#5. G5s at end became F#5s. The whole melody was re-composed.

**Root cause:** `applyTonalCleanup` first snaps out-of-scale notes to the
nearest scale degree (within 1–2 semitones), then `applyDegreeMelodyCleanup`
treats the newly-snapped notes as "bridge" artifacts and absorbs or
repositions them. A cascading rewrite of intentional pitches.

The scale fit was also imperfect (5/8 pitch classes matched), so even the snap
step was unreliable.

**Fix:** Bypass `applyTonalCleanup` entirely — `normalizeCapturedNotes` now
returns the pitch-class-merged notes directly. Cluster stabilisation at
detection time already handles pitch accuracy; post-hoc scale-based rewriting
only hurts when the detected scale is imprecise or when the melody deliberately
uses chromatic / modal colour notes.

---

## Parameters changed from session defaults

| Parameter | Old | New | Reason |
|---|---|---|---|
| `PITCH_CLASS_MERGE_GAP_MS` | 220 ms | 80 ms | "E E E" triplets were merged |
| `MIDI_CLUSTER_TOLERANCE` | 0.9 st | 0.55 st | Mega-cluster issue |
| Same-MIDI merge threshold (inline) | 120 ms | 35 ms | Re-articulated notes merged |

---

## What works well now

- Pitch detection is octave-correct across the full whistle range (~950–2400 Hz)
- Inter-note gaps >35 ms are preserved as distinct note events
- Phrase onset attack glides are suppressed (first 3 frames required to be stable)
- Short silences between notes don't inject ghost transition notes
- Intentional chromatic and out-of-scale notes survive normalization unchanged

## Still rough / future work

- Notes detected during the onset guard window (first ~50 ms of a phrase) are
  silently discarded — their startTime is backdated but the detector may still
  start slightly late on very short notes
- `applyDegreeMelodyCleanup` in `applyTonalCleanup` still exists but is no
  longer called — could be removed or repurposed for an opt-in "snap to scale"
  mode
- Vibrato / wide pitch wobble (e.g. A#5/B5 oscillation at 82.0–82.9) causes
  the note to flip pitch class every few frames; with cluster tolerance at
  0.55 st these sometimes form two clusters (A#5 and B5) and the note switches
  during a sustained tone. See backlog: "Vibrato / ornament detection"
