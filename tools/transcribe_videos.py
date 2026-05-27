"""
Generalized video/audio transcription using OpenAI Whisper.

Walks one or more folders (optionally recursively), finds media files,
and writes a <same_name>.txt transcript next to each one. Idempotent:
skips files whose transcript exists and is newer than the source.

Usage:
    python tools/transcribe_videos.py "path/to/folder" [more folders...] \
        --model base --recursive [--force]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

MEDIA_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".m4a", ".flac", ".ogg"}


def _ensure_ffmpeg_on_path() -> None:
    """imageio-ffmpeg ships ffmpeg under a versioned name; expose it as 'ffmpeg'."""
    try:
        import imageio_ffmpeg  # type: ignore
    except ImportError:
        return  # Maybe ffmpeg is already on PATH; let whisper fail loudly if not.
    src = imageio_ffmpeg.get_ffmpeg_exe()
    tmp = tempfile.mkdtemp(prefix="whisper_ffmpeg_")
    dst = os.path.join(tmp, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        if os.name != "nt":
            os.chmod(dst, 0o755)
    os.environ["PATH"] = tmp + os.pathsep + os.environ.get("PATH", "")


def collect_media(roots: list[Path], recursive: bool) -> list[Path]:
    out: list[Path] = []
    for r in roots:
        if not r.exists():
            print(f"warn: not found: {r}", file=sys.stderr)
            continue
        if r.is_file():
            if r.suffix.lower() in MEDIA_EXTS:
                out.append(r)
            continue
        it = r.rglob("*") if recursive else r.iterdir()
        for p in it:
            if p.is_file() and p.suffix.lower() in MEDIA_EXTS:
                out.append(p)
    return sorted(set(out))


def needs_transcript(media: Path, force: bool) -> bool:
    txt = media.with_suffix(".txt")
    if force:
        return True
    if not txt.exists():
        return True
    try:
        return txt.stat().st_mtime < media.stat().st_mtime
    except OSError:
        return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folders", nargs="+", help="One or more files or folders to scan")
    ap.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"])
    ap.add_argument("--recursive", action="store_true", help="Walk subfolders")
    ap.add_argument("--force", action="store_true", help="Re-transcribe even if up-to-date")
    args = ap.parse_args(argv)

    roots = [Path(f).resolve() for f in args.folders]
    media = collect_media(roots, recursive=args.recursive)
    if not media:
        print("No media files found.")
        return 0

    todo = [m for m in media if needs_transcript(m, args.force)]
    skipped = len(media) - len(todo)
    print(f"Found {len(media)} media file(s); {len(todo)} to transcribe, {skipped} up-to-date.")

    if not todo:
        return 0

    try:
        _ensure_ffmpeg_on_path()
        import whisper  # type: ignore
    except ImportError as e:
        print(f"error: whisper is not installed ({e}). "
              "Install with: pip install -r tools/requirements.txt", file=sys.stderr)
        return 3

    print(f"Loading Whisper model '{args.model}'...")
    model = whisper.load_model(args.model)
    print("Model loaded.\n")

    errors = 0
    for idx, media_path in enumerate(todo, 1):
        txt_path = media_path.with_suffix(".txt")
        print(f"[{idx}/{len(todo)}] {media_path.name}")
        try:
            result = model.transcribe(str(media_path), verbose=False)
            txt_path.write_text(result["text"].strip() + "\n", encoding="utf-8")
            print(f"             -> {txt_path.name}\n")
        except Exception as exc:  # noqa: BLE001 — keep going on individual failures
            errors += 1
            print(f"             ERROR: {exc}\n", file=sys.stderr)

    print(f"Done. {len(todo) - errors} transcribed, {errors} failed, {skipped} skipped.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
