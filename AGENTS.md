# AGENTS.md — orientation for AI coding agents

This repository is **kt-skill**: a portable Knowledge Transfer (KT) generator
designed to be copied into any target workspace. It does not contain KT
content of its own — only the prompt, instructions, and tooling that produce
KT content elsewhere.

## Repo layout

- `.github/prompts/generate-kt-guides.prompt.md` — the invokable workflow.
  Triggered with `/generate-kt-guides` in Copilot Chat agent mode.
- `.github/instructions/kt-guide-style.instructions.md` — auto-applied to
  `Guides/**/*.md` in any target repo that installs this skill.
- `.github/instructions/intel-security-domain.instructions.md` — **example**
  domain overlay. Copy and adapt for other domains; delete if irrelevant.
- `tools/` — repo-agnostic pipeline scripts (scan, transcribe, extract).
  See [tools/requirements.txt](tools/requirements.txt).
- `README.md` — install + usage instructions for end users.

## How a target repo invokes the skill

Once `.github/`, `tools/`, and `AGENTS.md` have been copied into the target
repo and `pip install -r tools/requirements.txt` has been run, an agent (or
human) runs:

```
/generate-kt-guides
```

The prompt orchestrates a 9-step pipeline (inventory → transcribe → extract →
caption → cluster → outline → author → provenance/glossary/quizzes → final).
See the prompt file for the full step list.

## Rules every agent must follow when editing this repo

1. **Treat this repo as a library, not as a KT target.** Do not create a
   `Guides/` folder here. Do not invoke `/generate-kt-guides` on this repo —
   there's nothing meaningful to summarize.
2. When you change [`tools/`](tools/), keep the scripts **idempotent** and
   **dependency-light**. Optional dependencies (e.g. `whisper`, `pypdf`) must
   import lazily and fail with an actionable error message — never crash the
   pipeline.
3. When you change [`.github/instructions/kt-guide-style.instructions.md`](.github/instructions/kt-guide-style.instructions.md):
   - Keep the `applyTo: "Guides/**/*.md"` frontmatter.
   - Preserve the file-skeleton contract (`In one sentence`, `Threat → Mitigation`,
     `Key concepts`, `How it works`, `Configuration knobs`, `Pitfalls`,
     `Where this connects`, `Sources`).
4. When you change [`.github/prompts/generate-kt-guides.prompt.md`](.github/prompts/generate-kt-guides.prompt.md):
   - Keep the three prompt arguments (`audience`, `focus`, `dry_run`).
   - Keep the pipeline numbered and idempotent.
   - Any new step must specify its idempotency rule and its failure mode.
5. The **domain overlay** file is intentionally repo-specific. New overlays
   should live alongside it in `.github/instructions/`, follow the same
   structure (terminology table → required framing → cross-references →
   source-preference order), and use the `applyTo: "Guides/**/*.md"` pattern.

## Porting checklist (when copying this skill into a target repo)

- [ ] Copy `.github/`, `tools/`, and `AGENTS.md` (or merge with an existing one).
- [ ] `pip install -r tools/requirements.txt`.
- [ ] Decide on a domain overlay: keep the Intel one as an example, replace it,
      or delete it.
- [ ] Run `/generate-kt-guides` with `dry_run=true` first to review the outline.
- [ ] Commit `Guides/_inventory.json` alongside `Guides/*.md` so re-runs are
      genuinely idempotent across machines.
