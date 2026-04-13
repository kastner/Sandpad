# Sandpad

`Sandpad` currently hosts a small browser app called `Pitch Detective`: a single-file, mobile-friendly melodic sketchpad for whistled or otherwise clean monophonic melodies.

The app listens through the browser microphone, estimates the current fundamental frequency, groups notes into phrases, infers a likely scale from those phrases, and then emphasizes scale degrees over absolute note names so short melodic ideas are easier to reason about and save.

## What Is In This Repo

- `pitch-detective.html` is the full app: HTML, CSS, and JavaScript in one file.
- `deploy-gist.sh` publishes the HTML file as a public GitHub gist and opens an `htmlpreview.github.io` URL that is easy to test on a phone.
- `index.html` redirects to `pitch-detective.html` so the repo can also be served directly by GitHub Pages.

## How It Works

1. The app requests microphone access with `getUserMedia`.
2. It reads live audio samples through a Web Audio `AnalyserNode`.
3. It runs an autocorrelation-style pitch detector on the time-domain buffer.
4. It converts the detected frequency to MIDI, note name, octave, and cents deviation.
5. It turns stable pitch changes into note events with approximate durations.
6. It treats silence gaps and start/stop listening boundaries as phrase boundaries.
7. It scores candidate scales against the active phrase, recent phrase endings, and the broader captured idea.
8. It renders a scrollable piano-roll style timeline and exports rough ABC and MIDI from the captured note events.

The UI is deliberately self-contained:

- a waveform visualizer
- a large current-note display
- a cents tuner needle
- a scrollable piano-roll timeline
- phrase-aware scale detection with confidence and degree labels
- rough ABC/MIDI export plus local saved ideas

## Running It

Run a static file server and visit the page from `localhost` or GitHub Pages. On first use, allow microphone access.

For local testing:

```bash
python3 -m http.server 4173
```

Then open `http://127.0.0.1:4173/pitch-detective.html`.

If you want a quick phone-shareable URL from a machine that already has authenticated GitHub CLI access:

```bash
bash deploy-gist.sh
```

That script creates a public gist containing the app as `index.html`, builds an `htmlpreview.github.io` URL around the raw gist content, and tries to copy and open the result locally.

## Provenance

This repo was reconstructed from a local audit log of the original build session. The audit showed that the prototype was created as a single-file app in response to a request for a mobile-friendly whistle pitch detector, then lightly corrected after a sub-agent review found an inverted silence-clipping condition in the pitch detector.

The raw `audit.jsonl` is intentionally not committed. It includes the full agent transcript and sensitive execution metadata, and it is not required to understand, run, or modify the app.

## Current Limits

- Pitch detection is heuristic and works best for clean, monophonic input such as whistling.
- Scale detection is still heuristic. It is now phrase-aware, but it is not doing full tonal analysis or tempo detection.
- MIDI and ABC export are intentionally rough first passes, meant for sketch capture rather than notation-quality transcription.
- Saved ideas live in browser local storage for now.
- There is no backend, persistence layer, or build step.
