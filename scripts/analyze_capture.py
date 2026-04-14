#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEARCH_DIRS = [
    ROOT / "captures",
    ROOT,
    Path.home() / "Downloads",
]
SAMPLE_RATE = 16000
FRAME_SIZE = 4096
HOP_SIZE = 512
MIN_FREQ = 240.0
MAX_FREQ = 2200.0
MIN_NOTE_MS = 120.0
PITCH_CLASS_MERGE_GAP_MS = 240.0
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class FramePitch:
    time_s: float
    freq_hz: float
    midi: int
    pitch_class: int


def run(cmd: list[str], capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=capture_output)


def note_name(midi: int) -> str:
    pitch_class = midi % 12
    octave = math.floor(midi / 12) - 1
    return f"{NOTE_NAMES[pitch_class]}{octave}"


def midi_from_freq(freq_hz: float) -> int:
    return round(69 + 12 * math.log2(freq_hz / 440.0))


def frame_rms(frame: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(frame))))


def harmonic_score(spectrum: np.ndarray, freqs: np.ndarray, candidate_hz: float) -> float:
    score = 0.0
    for harmonic, weight in ((1, 1.0), (2, 0.85), (3, 0.65), (4, 0.45)):
        target = candidate_hz * harmonic
        if target < freqs[1] or target > freqs[-1]:
            continue
        index = int(np.argmin(np.abs(freqs - target)))
        lo = max(0, index - 1)
        hi = min(len(spectrum), index + 2)
        score += float(np.sum(spectrum[lo:hi])) * weight
    return score


def choose_candidate(frame: np.ndarray, sample_rate: int, prev_freq: float | None) -> float | None:
    windowed = frame * np.hanning(len(frame))
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(windowed), d=1.0 / sample_rate)
    min_bin = int(np.searchsorted(freqs, MIN_FREQ))
    max_bin = int(np.searchsorted(freqs, MAX_FREQ))
    band = spectrum[min_bin:max_bin]
    if len(band) < 8 or float(np.max(band)) < 0.01:
        return None

    spectral_idx = int(np.argmax(band)) + min_bin
    spectral_freq = float(freqs[spectral_idx])

    hps = band.copy()
    usable = len(hps)
    for factor in (2, 3, 4):
        downsampled = band[::factor]
        usable = min(usable, len(downsampled))
        hps[:usable] *= downsampled[:usable]
    hps_freq = float(freqs[int(np.argmax(hps[:usable])) + min_bin])

    autocorr = np.correlate(windowed, windowed, mode="full")[len(windowed) - 1 :]
    min_lag = max(2, int(sample_rate / MAX_FREQ))
    max_lag = min(len(autocorr) - 1, int(sample_rate / MIN_FREQ))
    corr_segment = autocorr[min_lag : max_lag + 1]
    if len(corr_segment) == 0:
        return None
    autocorr_freq = float(sample_rate / (int(np.argmax(corr_segment)) + min_lag))

    candidates = {
        spectral_freq,
        hps_freq,
        autocorr_freq,
        spectral_freq / 2.0,
        hps_freq / 2.0,
        autocorr_freq / 2.0,
        spectral_freq * 2.0,
        hps_freq * 2.0,
    }

    best_freq = None
    best_score = -1.0
    for candidate in candidates:
        if candidate < MIN_FREQ or candidate > MAX_FREQ:
            continue
        score = harmonic_score(spectrum, freqs, candidate)
        if prev_freq:
            semitone_distance = abs(12 * math.log2(candidate / prev_freq))
            score -= min(12.0, semitone_distance) * 0.35
        half = candidate / 2.0
        if MIN_FREQ <= half <= MAX_FREQ:
            half_score = harmonic_score(spectrum, freqs, half)
            if half_score >= score * 0.93:
                score = half_score + 0.1
                candidate = half
        if score > best_score:
            best_score = score
            best_freq = candidate

    return best_freq


def decode_audio(audio_path: Path) -> np.ndarray:
    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-i",
            str(audio_path),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-f",
            "f32le",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    return np.frombuffer(result.stdout, dtype=np.float32)


def ffprobe_metadata(audio_path: Path) -> dict:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            str(audio_path),
        ]
    )
    return json.loads(result.stdout)


def measure_volume(audio_path: Path) -> tuple[str | None, str | None]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "info",
            "-nostdin",
            "-i",
            str(audio_path),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    mean = None
    peak = None
    for line in result.stderr.splitlines():
        if "mean_volume:" in line:
            mean = line.rsplit("mean_volume:", 1)[1].strip()
        if "max_volume:" in line:
            peak = line.rsplit("max_volume:", 1)[1].strip()
    return mean, peak


def analyze_frames(samples: np.ndarray) -> list[FramePitch]:
    if len(samples) < FRAME_SIZE:
        return []

    global_rms = float(np.sqrt(np.mean(np.square(samples))))
    silence_floor = max(0.0025, global_rms * 0.45)
    frames: list[FramePitch] = []
    prev_freq: float | None = None
    for start in range(0, len(samples) - FRAME_SIZE + 1, HOP_SIZE):
        frame = samples[start : start + FRAME_SIZE]
        rms = frame_rms(frame)
        if rms < silence_floor:
            continue
        freq = choose_candidate(frame, SAMPLE_RATE, prev_freq)
        if not freq:
            continue
        midi = midi_from_freq(freq)
        frames.append(
            FramePitch(
                time_s=start / SAMPLE_RATE,
                freq_hz=freq,
                midi=midi,
                pitch_class=midi % 12,
            )
        )
        prev_freq = freq
    return frames


def merge_frames(frames: list[FramePitch]) -> list[dict]:
    notes: list[dict] = []
    current: dict | None = None
    for frame in frames:
        if current is None:
            current = {
                "start_s": frame.time_s,
                "end_s": frame.time_s + (HOP_SIZE / SAMPLE_RATE),
                "midi": frame.midi,
                "pitch_class": frame.pitch_class,
                "freq_samples": [frame.freq_hz],
            }
            continue

        gap_ms = (frame.time_s - current["end_s"]) * 1000.0
        same_pitch_class = frame.pitch_class == current["pitch_class"]
        adjacent_semitone = abs(frame.midi - current["midi"]) <= 1
        if gap_ms <= PITCH_CLASS_MERGE_GAP_MS and (same_pitch_class or adjacent_semitone):
            current["end_s"] = frame.time_s + (HOP_SIZE / SAMPLE_RATE)
            current["pitch_class"] = frame.pitch_class if same_pitch_class else current["pitch_class"]
            current["midi"] = frame.midi if same_pitch_class else current["midi"]
            current["freq_samples"].append(frame.freq_hz)
            continue

        duration_ms = (current["end_s"] - current["start_s"]) * 1000.0
        if duration_ms >= MIN_NOTE_MS:
            current["freq_hz"] = float(np.median(np.array(current["freq_samples"])))
            current["note"] = note_name(current["midi"])
            current["duration_ms"] = round(duration_ms)
            del current["freq_samples"]
            notes.append(current)
        current = {
            "start_s": frame.time_s,
            "end_s": frame.time_s + (HOP_SIZE / SAMPLE_RATE),
            "midi": frame.midi,
            "pitch_class": frame.pitch_class,
            "freq_samples": [frame.freq_hz],
        }

    if current is not None:
        duration_ms = (current["end_s"] - current["start_s"]) * 1000.0
        if duration_ms >= MIN_NOTE_MS:
            current["freq_hz"] = float(np.median(np.array(current["freq_samples"])))
            current["note"] = note_name(current["midi"])
            current["duration_ms"] = round(duration_ms)
            del current["freq_samples"]
            notes.append(current)

    return notes


def pitch_classes(notes: list[dict]) -> list[str]:
    return [NOTE_NAMES[note["pitch_class"]] for note in notes]


def load_json_if_present(path: Path | None) -> dict | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_inputs(prefix: str | None, audio_path: str | None, analysis_path: str | None) -> tuple[Path | None, Path | None]:
    if audio_path or analysis_path:
        return (
            Path(audio_path).expanduser() if audio_path else None,
            Path(analysis_path).expanduser() if analysis_path else None,
        )

    if not prefix:
        raise SystemExit("Provide a take prefix or explicit --audio / --analysis path.")

    audio_match = None
    analysis_match = None
    for base_dir in DEFAULT_SEARCH_DIRS:
        if not base_dir.exists():
            continue
        for path in sorted(base_dir.glob(f"{prefix}*")):
            if path.suffix.lower() in {".webm", ".m4a", ".wav", ".ogg"} and audio_match is None:
                audio_match = path
            if path.suffix.lower() == ".json" and analysis_match is None:
                analysis_match = path
    return audio_match, analysis_match


def build_summary(audio_path: Path, analysis_path: Path | None) -> dict:
    app_analysis = load_json_if_present(analysis_path)
    samples = decode_audio(audio_path)
    frames = analyze_frames(samples)
    notes = merge_frames(frames)
    metadata = ffprobe_metadata(audio_path)
    mean_volume, max_volume = measure_volume(audio_path)

    summary = {
        "audio": str(audio_path),
        "analysis": str(analysis_path) if analysis_path else None,
        "duration_s": float(metadata.get("format", {}).get("duration", 0.0) or 0.0),
        "mean_volume": mean_volume,
        "max_volume": max_volume,
        "offline_notes": [
            {
                "start_s": round(note["start_s"], 2),
                "end_s": round(note["end_s"], 2),
                "duration_ms": note["duration_ms"],
                "note": note["note"],
                "pitch_class": NOTE_NAMES[note["pitch_class"]],
                "freq_hz": round(note["freq_hz"], 1),
            }
            for note in notes
        ],
        "offline_pitch_classes": pitch_classes(notes),
    }

    if app_analysis:
        raw_notes = app_analysis.get("rawNotes") or []
        normalized_notes = app_analysis.get("notes") or []
        summary["app"] = {
            "scale": app_analysis.get("scale"),
            "degreeSketch": app_analysis.get("degreeSketch"),
            "raw_notes": [note.get("note") for note in raw_notes],
            "normalized_notes": [note.get("note") for note in normalized_notes],
            "normalized_pitch_classes": [
                NOTE_NAMES[note.get("pitchClass", -1)]
                for note in normalized_notes
                if isinstance(note.get("pitchClass"), int) and 0 <= note.get("pitchClass") < 12
            ],
        }
    return summary


def print_summary(summary: dict) -> None:
    print(f"Audio: {summary['audio']}")
    if summary.get("analysis"):
        print(f"Analysis JSON: {summary['analysis']}")
    print(f"Duration: {summary['duration_s']:.2f}s")
    print(f"Volume: mean {summary.get('mean_volume') or 'n/a'}, max {summary.get('max_volume') or 'n/a'}")
    offline = summary.get("offline_notes", [])
    if offline:
        print("Offline notes:")
        for note in offline:
            print(
                f"  {note['start_s']:.2f}-{note['end_s']:.2f}s  "
                f"{note['note']:<4} {note['freq_hz']:>6.1f} Hz"
            )
    else:
        print("Offline notes: none recovered")

    app = summary.get("app")
    if app:
        scale = app.get("scale")
        if scale:
            root_name = scale.get("rootName")
            if not root_name and isinstance(scale.get("root"), int):
                root_name = NOTE_NAMES[scale["root"]]
            print(f"App scale: {root_name} {scale.get('scale')} (confidence {scale.get('confidence')})")
        print("App normalized notes:", " ".join(app.get("normalized_notes") or []) or "none")
        print("App normalized pitch classes:", " ".join(app.get("normalized_pitch_classes") or []) or "none")
    print("Offline pitch classes:", " ".join(summary.get("offline_pitch_classes") or []) or "none")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a Sandpad capture outside the browser.")
    parser.add_argument("prefix", nargs="?", help="Take prefix such as pitch-detective-2026-04-14T01-08-00-415Z")
    parser.add_argument("--audio", help="Explicit path to an audio file (.webm, .m4a, .wav, .ogg)")
    parser.add_argument("--analysis", help="Explicit path to an analysis JSON file")
    parser.add_argument("--output", help="Optional path to save the computed summary as JSON")
    args = parser.parse_args()

    audio_path, analysis_path = resolve_inputs(args.prefix, args.audio, args.analysis)
    if not audio_path:
        raise SystemExit("Could not find an audio file for that prefix.")

    summary = build_summary(audio_path, analysis_path)
    print_summary(summary)

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote {output_path}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or str(exc))
        raise
