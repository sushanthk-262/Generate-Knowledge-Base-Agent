---
mode: agent
description: Walk the current workspace, ingest text/code/docs/slides/images/audio/video, transcribe videos, and produce a beginner-friendly Knowledge Transfer (KT) guide series under Guides/. Idempotent across runs.
tools: ['edit', 'search', 'runCommands', 'runTasks', 'usages', 'think', 'fetch', 'githubRepo', 'todos', 'extensions', 'editFiles', 'runNotebooks']
---

# /generate-knowledge-base — Workspace → Knowledge-Transfer Guide series

Primary command. This is the preferred prompt entrypoint.

You are generating a **Knowledge Transfer (KT) pack** for someone who has just been given access to this repository and has **zero prior context** on either the repo or its subject matter. The deliverable lives under `Guides/` and must be readable top-to-bottom by a newcomer.

## Inputs (prompt arguments)

- **audience** — `${input:audience:newcomer}` — one of `newcomer | engineer | manager`
  - `newcomer`: assume only general SWE/CS literacy; expand every acronym; lots of "why this exists" framing.
  - `engineer`: assume domain literacy; focus on architecture, flows, configuration knobs, pitfalls.
  - `manager`: assume no implementation context; focus on what each component does, who owns it, risks, dependencies.
- **focus** — `${input:focus:}` — optional substring filter; only ingest files whose workspace-relative path contains this string. Empty = whole workspace.
- **dry_run** — `${input:dry_run:false}` — if `true`, stop after the outline pass and print the plan. Do not write guide bodies.

## Hard rules

1. **Never invent facts.** Every non-trivial claim must be traceable to a source artifact in the workspace. If a claim came only from a Whisper transcript, tag it `〈heard-as: "..."〉` so reviewers can grep low-confidence content.
2. **Idempotent.** Re-running must not duplicate work. Use `Guides/_inventory.json` (hash per source file) to skip unchanged artifacts.
3. **Workspace-relative links only.** Every guide section that came from a file must link to that file (and slide/page/timestamp if known) via `Guides/_sources.md`.
4. **No network access** unless explicitly requested. All ingestion is local.
5. **Respect `.gitignore`** and skip `node_modules/`, `.venv/`, `venv/`, `dist/`, `build/`, `out/`, `.git/`, `__pycache__/`, `.next/`, `target/`, and anything > 100 MB unless it's a video/audio file.
6. **Install dependencies before running scripts.** Run `pip install -r tools/requirements.txt` once before calling any `python tools/*.py` command. Missing imports are a fatal preflight error.

## The pipeline (run in order, mark each step in the todo list)

### Step 0 — Environment preflight
Run:
```
pip install -r tools/requirements.txt
```
If dependency installation fails, stop and ask the user to resolve environment issues before continuing.

### Step 1 — Inventory pass
Run:
```
python tools/scan_workspace.py --root . --out Guides/_inventory.json
```
This produces `Guides/_inventory.json` with one entry per file: `{path, kind, size, sha256, mtime}` where `kind ∈ {text, code, doc, slides, image, video, audio, notebook, other}`.

If `focus` is non-empty, post-filter the inventory in memory before continuing.

### Step 2 — Video / audio pass
For every `video` or `audio` entry whose sibling `<name>.txt` is absent or older than the source, run:
```
python tools/transcribe_videos.py "<containing-folder>" --model base --recursive
```
The script is **idempotent** (skips up-to-date transcripts) and writes `<same_name>.txt` alongside each media file. Mark each transcript file `kind: text` and add it to the inventory.

Do **not** crash the pipeline if Whisper is unavailable. If `import whisper` fails, log a warning, mark the affected guides with a `> ⚠ Source videos not transcribed (whisper unavailable).` note, and continue.

### Step 3 — Document pass (PDF / PPTX / DOCX / notebooks)
Run:
```
python tools/extract_docs.py --root . --out-suffix .extracted.txt
```
Writes a sidecar `<name>.extracted.txt` per supported document. Slides keep per-slide markers (`--- Slide N: <title> ---`). Notebooks keep per-cell markers.

### Step 4 — Image pass (multimodal)
For each `image` entry without a sibling `<name>.alt.md`:
- Open the image, describe it in one paragraph (max 80 words), list any visible labels/acronyms verbatim, and save to `<name>.alt.md`.
- Cache only — do not re-describe an image whose sha256 hasn't changed.

### Step 5 — Cluster pass
Group artifacts into **topics** (one guide per topic) using, in order of priority:
1. Top-level folder name (e.g. `Platform Features/BIOS Guard/` → topic "BIOS Guard").
2. Recurring acronyms / product names in titles & transcripts (TF-IDF over titles and the first 500 tokens of each text artifact).
3. Existing `Guides/` numbering if present (preserve order; only add new files at the end).

Produce a draft outline and **stop for confirmation if `dry_run=true`**. Otherwise proceed.

### Step 6 — Outline pass
Write/update `Guides/README.md` with:
- A "Who this is for" block matching the **audience** argument.
- A reading-order table linking each numbered guide.
- A 10,000-ft picture diagram (Mermaid preferred — see style file).

### Step 7 — Author pass
For each topic, create/update `Guides/NN-<slug>.md` following [.github/instructions/kt-guide-style.instructions.md](.github/instructions/kt-guide-style.instructions.md). Domain-specific repos (Intel platform security, kernel/firmware, etc.) should also follow [.github/instructions/intel-security-domain.instructions.md](.github/instructions/intel-security-domain.instructions.md) when it applies.

Each guide must end with a **Sources** section linking back to the workspace files it was derived from.

### Step 8 — Provenance + glossary + quizzes
- Append to `Guides/_sources.md` a table: `Guide section | Source file | Slide/Page/Timestamp | Confidence (high/med/low)`.
- Maintain a single `Guides/99-glossary.md`: every acronym used anywhere, one-line definition, link to the first guide that introduces it.
- For each guide `NN-<slug>.md`, write/refresh `Guides/quizzes/NN-<slug>.md` with **5 short Q&A flashcards** drawn only from that guide's content.

### Step 9 — Final pass
- Re-read every generated guide once and fix dangling links / missing acronym definitions.
- Print a one-screen summary: guides created, guides updated, guides skipped (unchanged), transcripts generated, images captioned, low-confidence claims count.

## Failure handling

- A single artifact failing to parse is **not** fatal. Log it, skip it, note its absence in the relevant guide.
- A whole step failing (e.g. script missing) **is** fatal — stop, surface the exact command, and ask the user.

## When you are done

Tell the user:
1. How to read the pack (start at `Guides/README.md`).
2. Which artifacts were low-confidence and worth a human review pass.
3. The exact command to re-run when new material lands.
