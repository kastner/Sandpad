#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
CAPTURES_DIR = ROOT / "captures"
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
MIME_EXTENSIONS = {
    "audio/webm": ".webm",
    "audio/webm;codecs=opus": ".webm",
    "audio/mp4": ".m4a",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
}


def sanitize_name(value: str, fallback: str) -> str:
    candidate = Path(value or "").name
    if not candidate or not SAFE_NAME.fullmatch(candidate):
        return fallback
    return candidate


def guess_recording_name(take_id: str, filename: str | None, mime_type: str | None) -> str:
    if filename:
        safe = sanitize_name(filename, "")
        if safe:
            return safe
    suffix = MIME_EXTENSIONS.get((mime_type or "").split(";")[0].strip(), ".webm")
    return f"pitch-detective-{take_id}{suffix}"


def json_response(handler: SimpleHTTPRequestHandler, payload: dict, status: int = HTTPStatus.OK) -> None:
    raw = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(raw)


def write_capture(payload: dict) -> dict:
    take_id = sanitize_name(payload.get("takeId") or "", "")
    if not take_id:
        raise ValueError("A safe takeId is required.")

    analysis = payload.get("analysis")
    if not isinstance(analysis, dict):
        raise ValueError("The upload payload must include an analysis object.")

    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

    analysis_filename = sanitize_name(
        payload.get("analysisFilename") or f"pitch-detective-{take_id}-analysis.json",
        f"pitch-detective-{take_id}-analysis.json",
    )
    if not analysis_filename.endswith(".json"):
        analysis_filename = f"{analysis_filename}.json"
    analysis_path = CAPTURES_DIR / analysis_filename
    analysis_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    recording_base64 = payload.get("recordingBase64")
    recording_filename = None
    recording_path = None
    if recording_base64:
        recording_filename = sanitize_name(
            guess_recording_name(
                take_id,
                payload.get("recordingFilename"),
                payload.get("recordingMimeType"),
            ),
            f"pitch-detective-{take_id}.webm",
        )
        recording_path = CAPTURES_DIR / recording_filename
        recording_path.write_bytes(base64.b64decode(recording_base64))

    result = {
        "ok": True,
        "takeId": take_id,
        "uploadedAt": payload.get("uploadedAt"),
        "analysisFilename": analysis_filename,
        "analysisPath": str(analysis_path.relative_to(ROOT)),
        "recordingFilename": recording_filename,
        "recordingPath": str(recording_path.relative_to(ROOT)) if recording_path else None,
    }

    latest_path = CAPTURES_DIR / "latest.json"
    latest_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    with (CAPTURES_DIR / "index.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result) + "\n")

    return result


class SandpadHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            json_response(
                self,
                {
                    "ok": True,
                    "capturesDir": str(CAPTURES_DIR.relative_to(ROOT)),
                },
            )
            return
        if parsed.path == "/api/latest":
            latest_path = CAPTURES_DIR / "latest.json"
            latest = json.loads(latest_path.read_text(encoding="utf-8")) if latest_path.exists() else None
            json_response(self, {"ok": True, "latest": latest})
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/upload":
            json_response(self, {"ok": False, "error": "Unknown endpoint."}, HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            json_response(self, {"ok": False, "error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
            return

        try:
            result = write_capture(payload)
        except ValueError as exc:
            json_response(self, {"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except Exception as exc:  # pragma: no cover
            json_response(self, {"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        json_response(self, result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Sandpad locally and collect browser captures.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=4173, type=int)
    args = parser.parse_args()

    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), SandpadHandler)
    print(f"Serving {ROOT} at http://{args.host}:{args.port}")
    print(f"Captures will be saved in {CAPTURES_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
