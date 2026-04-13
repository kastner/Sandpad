# Sandpad

`Sandpad` currently archives a small browser app called `Pitch Detective`: a single-file, mobile-friendly pitch detector for whistled or otherwise clean monophonic melodies.

The app listens through the browser microphone, estimates the current fundamental frequency, converts that frequency to a note name plus cents offset, and then builds a short rolling pitch-class history to guess the most likely scale and current scale degree.

## What Is In This Repo

- `pitch-detective.html` is the full app: HTML, CSS, and JavaScript in one file.
- `deploy-gist.sh` publishes the HTML file as a public GitHub gist and opens an `htmlpreview.github.io` URL that is easy to test on a phone.
- `index.html` redirects to `pitch-detective.html` so the repo can also be served directly by GitHub Pages.

## How It Works

1. The app requests microphone access with `getUserMedia`.
2. It reads live audio samples through a Web Audio `AnalyserNode`.
3. It runs an autocorrelation-style pitch detector on the time-domain buffer.
4. It converts the detected frequency to MIDI, note name, octave, and cents deviation.
5. It stores recent pitch classes in a roughly 5 second window.
6. It scores a set of candidate scales against that window and reports the best match, plus the current note's degree within that scale when possible.

The UI is deliberately self-contained:

- a waveform visualizer
- a large current-note display
- a cents tuner needle
- a rolling note history
- a scale detector with confidence and degree labels

## Running It

Open `pitch-detective.html` directly in a modern browser, or run a static file server and visit the page there. On first use, allow microphone access.

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
- Scale detection is approximate and based on a short rolling note histogram, not phrase-aware music analysis.
- There is no backend, persistence layer, or build step.
