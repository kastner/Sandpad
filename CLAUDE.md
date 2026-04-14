# CLAUDE.md — Claude Code Project Settings

See **[AGENTS.md](./AGENTS.md)** for the full agent guide: file map, invariants, feature checklists, pipeline descriptions, and commit style.

---

## Quick-start for Claude Code

```bash
# Serve locally with auto-capture (recommended for debugging)
python3 dev_server.py --port 4173
# → open http://127.0.0.1:4173/pitch-detective.html

# Static serve (no capture server)
python3 -m http.server 4173
```

## Primary File

`pitch-detective.html` — everything is here (HTML + CSS + JS, ~3300+ lines).

## Model Recommendation

Use **opus** sub-agents for anything touching pitch detection, scale inference, canvas rendering, or Web Audio. Use sonnet for docs, small UI tweaks, and config work.

## Commit Attribution

```
Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
Use the appropriate model slug for whichever model did the bulk of the work.
