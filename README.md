# generate-knowledge-base-agent — Generate Knowledge Base agent + KT workflow

A drop-in **Copilot custom agent + prompt workflow** (agent + instructions + tooling) that ingests
an arbitrary workspace — text, code, slides, PDFs, images, audio, video — and
produces a beginner-friendly Knowledge Transfer (KT) guide series under
`Guides/`.

Built for the case where someone joins a team and inherits a repo full of
recordings, decks, and docs, and needs a single readable path from
"never heard of this" → "I can hold a conversation about it".

## What's in this folder

```
generate-knowledge-base-agent/
├── .github/
│   ├── prompts/
│   │   ├── generate-knowledge-base.prompt.md  ← primary slash-command workflow
│   │   └── generate-kt-guides.prompt.md       ← legacy compatibility alias
│   ├── agents/
│   │   └── generate-knowledge-base.agent.md   ← custom agent (recommended)
│   └── instructions/
│       ├── kt-guide-style.instructions.md     ← auto-applied to Guides/**/*.md
│       └── intel-security-domain.instructions.md  ← example domain overlay
├── tools/
│   ├── scan_workspace.py        ← inventory every file (path/kind/size/sha)
│   ├── transcribe_videos.py     ← Whisper, recursive, idempotent
│   ├── extract_docs.py          ← PDF / PPTX / DOCX / .ipynb → text sidecars
│   └── requirements.txt
└── AGENTS.md                    ← orientation for any AI coding agent
```

## Install into a target repo

```powershell
# from the root of the target repo
$src = "<path>\kt-skill"
Copy-Item -Recurse "$src\.github" .
Copy-Item -Recurse "$src\tools"    .
Copy-Item          "$src\AGENTS.md" .   # or merge if you already have one
pip install -r tools\requirements.txt
```

Then, in VS Code Copilot Chat (agent mode):

- Recommended: select **Generate Knowledge Base** custom agent.
- Prompt command: run `/generate-knowledge-base`.
- Legacy alias: `/generate-kt-guides`.

Always install dependencies before running the scripts used by the workflow:

```powershell
pip install -r tools\requirements.txt
```

The prompt will ask for:
- **audience** — `newcomer` (default) | `engineer` | `manager`
- **focus** — substring filter on source paths (empty = whole workspace)
- **dry_run** — `true` to stop after the outline pass

## What the skill does (9 passes, all idempotent)

1. **Preflight** — install Python dependencies from `tools/requirements.txt`.
2. **Inventory** — `scan_workspace.py` → `Guides/_inventory.json`.
3. **Transcribe** — Whisper turns every video/audio into a sibling `.txt`.
4. **Extract** — PDFs / PPTX / DOCX / notebooks → `.extracted.txt` sidecars
   (with per-slide / per-page / per-cell markers).
5. **Caption** — multimodal pass writes `<image>.alt.md` for diagrams/screenshots.
6. **Cluster** — group artifacts into topics (folder names + TF-IDF on titles).
7. **Outline** — write `Guides/README.md` with the reading order.
8. **Author** — one `Guides/NN-<slug>.md` per topic, following the style file.
9. **Provenance + glossary + quizzes** — `Guides/_sources.md`,
   `Guides/99-glossary.md`, and `Guides/quizzes/NN-<slug>.md` (5 flashcards each).
10. **Final pass** — fix dangling links, print a one-screen summary.

Re-runs only rewrite guides whose source artifacts changed (sha256 in the
inventory).

## Domain overlays

[`intel-security-domain.instructions.md`](.github/instructions/intel-security-domain.instructions.md)
is shipped as a **template/example** of a domain overlay (Intel platform
security: Boot Guard, TXT, TPM, TDX, CSME, …). To adapt this skill to a
different domain:

1. Copy the file, rename it (e.g. `.github/instructions/k8s-domain.instructions.md`).
2. Replace its terminology table, required framing, and cross-reference table.
3. Keep the YAML frontmatter (`applyTo: "Guides/**/*.md"`) intact.
4. Either delete the Intel one or leave it — it's inert outside Intel-security repos.

## Conventions the skill enforces

- **No invented facts.** Every claim traces to a source artifact listed in
  `Guides/_sources.md`.
- **Transcript-only claims get a `〈heard-as: "..."〉` tag** so reviewers can grep
  low-confidence content.
- **Mermaid diagrams** preferred over ASCII for sequence/flow/architecture.
- **Workspace-relative links only** — no `file://`, no absolute paths.
- **Persona-aware depth** — the `audience` argument changes expansion level
  (acronyms, "why this exists" framing, code depth).

## CLI usage without an agent

Each tool runs standalone:

```powershell
pip install -r tools\requirements.txt

# 1. Inventory the workspace (gitignored folders are INCLUDED by default —
#    KT source material is often gitignored on purpose).
python tools\scan_workspace.py --root . --out Guides\_inventory.json

# 2. Transcribe everything under a folder, recursively, skipping up-to-date files.
python tools\transcribe_videos.py "path\to\recordings" --recursive --model base

# 3. Extract text from every PDF / PPTX / DOCX / .ipynb in the repo.
python tools\extract_docs.py --root .
```

## Splitting into its own repo

```powershell
cd generate-knowledge-base-agent
git init
git add .
git commit -m "Initial commit: generate-knowledge-base-agent"
gh repo create <owner>/generate-knowledge-base-agent --public --source=. --remote=origin --push
```

## License

[MIT](LICENSE) © 2026 Sushanth.
