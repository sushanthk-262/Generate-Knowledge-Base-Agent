"""
Scan a workspace and produce an inventory of every relevant file.

Output: JSON list of {path, kind, size, sha256, mtime} entries.
Used by /generate-knowledge-base as the first pipeline step.

Usage:
    python tools/scan_workspace.py --root . --out Guides/_inventory.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn",
    "node_modules", ".venv", "venv", "env",
    "dist", "build", "out", "target", ".next", ".nuxt",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".idea", ".vscode-test",
}

# Always-skip file size cap (bytes). Videos/audio are exempt.
HARD_SIZE_CAP = 100 * 1024 * 1024  # 100 MB

EXT_KIND = {
    # text / code
    ".md": "text", ".rst": "text", ".txt": "text", ".log": "text",
    ".py": "code", ".js": "code", ".ts": "code", ".tsx": "code", ".jsx": "code",
    ".c": "code", ".h": "code", ".cpp": "code", ".hpp": "code", ".cc": "code",
    ".cs": "code", ".java": "code", ".go": "code", ".rs": "code", ".rb": "code",
    ".sh": "code", ".bat": "code", ".ps1": "code",
    ".json": "code", ".yaml": "code", ".yml": "code", ".toml": "code", ".xml": "code",
    ".html": "code", ".css": "code",
    # docs
    ".pdf": "doc", ".docx": "doc", ".doc": "doc",
    # slides
    ".pptx": "slides", ".ppt": "slides", ".vsdx": "slides",
    # images
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image",
    ".webp": "image", ".bmp": "image", ".svg": "image",
    # video
    ".mp4": "video", ".mkv": "video", ".mov": "video", ".avi": "video", ".webm": "video",
    # audio
    ".mp3": "audio", ".wav": "audio", ".m4a": "audio", ".flac": "audio", ".ogg": "audio",
    # notebooks
    ".ipynb": "notebook",
}

MEDIA_KINDS = {"video", "audio"}


def classify(path: Path) -> str:
    return EXT_KIND.get(path.suffix.lower(), "other")


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_gitignore_dirs(root: Path) -> set[str]:
    """Cheap gitignore: only honor top-level directory names listed in .gitignore."""
    gi = root / ".gitignore"
    if not gi.exists():
        return set()
    out: set[str] = set()
    for line in gi.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip leading ./ and trailing /
        line = line.lstrip("/").rstrip("/")
        if "/" not in line and "*" not in line:
            out.add(line)
    return out


def scan(root: Path, hash_media: bool, respect_gitignore: bool) -> list[dict]:
    skip = set(SKIP_DIRS)
    if respect_gitignore:
        skip |= load_gitignore_dirs(root)
    inventory: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune in-place so os.walk doesn't descend into skipped dirs.
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".") or d in {".github"}]

        for name in filenames:
            p = Path(dirpath) / name
            try:
                st = p.stat()
            except OSError:
                continue

            kind = classify(p)
            if kind == "other":
                # Keep "other" only if small text-ish; otherwise drop.
                if st.st_size > 64 * 1024:
                    continue
            if kind not in MEDIA_KINDS and st.st_size > HARD_SIZE_CAP:
                continue

            rel = p.relative_to(root).as_posix()
            entry = {
                "path": rel,
                "kind": kind,
                "size": st.st_size,
                "mtime": int(st.st_mtime),
            }
            # Hashing large media is expensive; only do it when asked.
            if kind not in MEDIA_KINDS or hash_media:
                try:
                    entry["sha256"] = sha256_of(p)
                except OSError:
                    entry["sha256"] = None
            inventory.append(entry)

    inventory.sort(key=lambda e: e["path"])
    return inventory


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="Workspace root (default: cwd)")
    ap.add_argument("--out", default="Guides/_inventory.json", help="Output JSON path")
    ap.add_argument(
        "--hash-media",
        action="store_true",
        help="Also hash video/audio files (slow). Off by default.",
    )
    ap.add_argument(
        "--respect-gitignore",
        action="store_true",
        help="Skip top-level directories listed in .gitignore. Off by default because "
             "KT source material (recordings, slides, PDFs) is often gitignored on purpose.",
    )
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root not found: {root}", file=sys.stderr)
        return 2

    inv = scan(root, hash_media=args.hash_media, respect_gitignore=args.respect_gitignore)

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(inv, indent=2), encoding="utf-8")

    counts: dict[str, int] = {}
    for e in inv:
        counts[e["kind"]] = counts.get(e["kind"], 0) + 1
    print(f"Scanned {len(inv)} files into {out_path.relative_to(root)}")
    for k in sorted(counts):
        print(f"  {k:9s} {counts[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
