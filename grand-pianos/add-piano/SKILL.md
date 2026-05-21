---
name: add-piano
description: Add a new model entry to the grand-pianos challenge index page. Use when the user says "add [model name]", "add a new piano", or asks to update the grand-pianos index with a new entry.
---

Add a new AI-generated piano to the grand-pianos challenge index at
`grand-pianos/index.html` inside the Sandpad repo.

---

## Step 1 — Find the file

Run the helper script to locate the untracked HTML file and get its metadata:

```bash
bash /Users/erik.kastner/workspace/scratch/Sandpad/grand-pianos/add-piano/add-piano.sh "<model-name-fragment>"
```

The script searches untracked files in `grand-pianos/` (git ls-files --others).
If no match, it lists all candidates — ask the user to clarify.
The script also outputs the file's **creation date** (macOS birthtime); use this for the changelog entry.

---

## Step 2 — Analyze the piano

Read the full HTML file. Assess three dimensions:

### Sound (1–5) — synthesis quality
| Score | Meaning |
|-------|---------|
| 1 | Single oscillator, no real envelope, sounds toy-like |
| 2 | Basic ADSR, 1–2 harmonics |
| 3 | 3–5 harmonics, envelope shaping, basic noise burst |
| 4 | 6+ harmonics, hammer noise, chorus/detune, velocity, proper multi-stage release |
| 5 | Research-grade: physical modeling, convolution reverb, velocity layers, string resonance simulation |

### KB Layout (1–5) — visual keyboard correctness
| Score | Meaning |
|-------|---------|
| 1 | Fundamentally broken — upside-down, black keys off keyboard, etc. |
| 2 | Severe errors — black keys bunched wrong, completely wrong positions |
| 3 | Roughly correct but CSS drift across octave boundaries |
| 4 | Mostly correct, minor offset (~½ key-width or less) |
| 5 | Perfect — black keys properly straddle white-key boundaries across all octaves |

### Design (1–5) — visual polish
| Score | Meaning |
|-------|---------|
| 1 | Bare / no styling |
| 2 | Basic functional styling |
| 3 | Competent, cohesive aesthetic |
| 4 | Distinctive, polished, memorable |
| 5 | Exceptional — standout aesthetic that elevates the instrument |

Also note: key count, octave range, special features (demo playback, sustain pedal, reverb,
octave shift, keyboard shortcuts), notable quirks or bugs.

---

## Step 3 — Present scores to user

**Do not edit any files yet.** Tell the user:
- The matched filename
- File creation date
- Your proposed scores with 1-sentence reasoning each
- Key features and quirks
- Where it would rank in the current list

Ask the user to confirm or adjust scores before proceeding.

---

## Step 4 — Determine ranking position

After score confirmation, decide placement:

- **Exemplar** (`—`): reserved for the multi-turn opus-4.6-improved entry only
- **Main competition** (top ranked cards): Sound ≥ 4, or overall exceptional
- **The Incomplete & Broken** (after the "Plot Twist" / Codex surprise divider): Sound ≤ 3 with broken layout, limited range, or missing features

Within a tier, rank by overall quality. Use Sound×2 + KB Layout + Design as a rough tiebreaker, but apply judgment — a 5/1/5 and a 3/5/3 aren't directly comparable.

---

## Step 5 — Update index.html

File: `/Users/erik.kastner/workspace/scratch/Sandpad/grand-pianos/index.html`

### 5a. Increment model count (4 places)
1. Header stat: `<div class="stat-num">N</div>` → N+1
2. Header sub: `"One prompt. N models."` → N+1
3. Intro paragraph: `"N models received the identical brief..."` (the number word, e.g. "Fourteen" → "Fifteen")
4. Prompt card meta: `"Used for N of M models"` → N+1 of M+1

### 5b. Renumber displaced cards
For all cards ranked >= the insertion point, increment their `card-rank` div by 1.
**Go highest-to-lowest** to avoid string collision (e.g. change 12→13 before 11→12).

### 5c. Insert the new article

```html
  <!-- [Model Name] -->
  <article class="piano-card">
    <div class="card-header">
      <div class="card-rank">NN</div>
      <div>
        <div class="card-model-name">[Model Name]</div>
        <div class="card-badges">
          <span class="badge badge-platform">[platform e.g. t3.chat]</span>
          <span class="badge badge-keys">[N keys · range · octave-shiftable if applicable]</span>
          <!-- <span class="badge badge-broken">Limited Range</span>  ← only if broken -->
        </div>
      </div>
      <div class="card-scores">
        <div class="score-row">
          <span class="score-label">Sound</span>
          <div class="score-dots">
            [DOTS]
          </div>
        </div>
        <div class="score-row">
          <span class="score-label">KB Layout</span>
          <div class="score-dots">
            [DOTS]
          </div>
        </div>
        <div class="score-row">
          <span class="score-label">Design</span>
          <div class="score-dots">
            [DOTS]
          </div>
        </div>
      </div>
    </div>
    <div class="card-body">
      <p class="card-summary">[2–3 sentence summary: synthesis, layout, design highlights]</p>
      <div class="feature-list">
        <span class="feat">[feature]</span>
        <!-- repeat as needed; add ★ to standout features -->
      </div>
      <!-- Only include quirk-note if there's a real bug/limitation: -->
      <!-- <div class="quirk-note">⚠ [short description of the problem]</div> -->
    </div>
    <div class="card-embed">
      <iframe src="[filename].html" loading="lazy" title="[Model Name]"></iframe>
      <div class="embed-controls">
        <span class="embed-hint">Click keys to play[· Space = sustain · Z/X = octave etc.]</span>
        <button class="expand-btn" onclick="toggleExpand(this)">Expand</button>
      </div>
    </div>
  </article>
```

**Score dots** — use `<div class="sdot on"></div>` for filled, `<div class="sdot"></div>` for empty.
Score 3/5 example: `on on on off off` → 3 `sdot on` then 2 `sdot`.

### 5d. Add changelog entry

Inside `<header>`, find `<aside class="changelog">` → `<ul>`.
**Prepend** a new `<li>` as the first entry:

```html
<li><time datetime="YYYY-MM-DD">YYYY-MM-DD</time>Added [Model Name] ([tier], rank NN).</li>
```

Tier is "main competition" or "incomplete/broken".

---

## Step 6 — Commit and push

```bash
cd /Users/erik.kastner/workspace/scratch/Sandpad
git add grand-pianos/
git commit -m "$(cat <<'EOF'
Add [Model Name] to grand-pianos index (rank NN)

[One sentence about what makes this entry notable.]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
git push
```
