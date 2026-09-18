#!/usr/bin/env python3
"""Inventory course files without claiming to extract their content."""
import argparse
import hashlib
import json
import os
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "exam-prep-output"}
GROUPS = {
    "pdf": {".pdf"},
    "document": {".docx", ".odt", ".rtf"},
    "slides": {".pptx", ".odp"},
    "spreadsheet": {".xlsx", ".ods", ".csv", ".tsv"},
    "legacy-office": {".doc", ".ppt", ".xls"},
    "image": {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".heic"},
    "text": {".txt", ".md", ".tex", ".html", ".htm", ".json", ".xml", ".py", ".c", ".cpp", ".java"},
    "audio": {".mp3", ".wav", ".m4a", ".flac", ".ogg"},
    "video": {".mp4", ".mkv", ".mov", ".webm", ".avi"},
    "archive": {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"},
    "ebook": {".epub", ".mobi", ".azw", ".azw3"},
}
ROUTES = {
    "pdf": "Extract page text; inspect figures and OCR image-only pages.",
    "document": "Read structure, tables, equations and embedded images.",
    "slides": "Read every slide, figures, equations and speaker notes.",
    "spreadsheet": "Read sheets/cells; distinguish formulas from cached values.",
    "legacy-office": "Convert a copy with an available Office tool, then inspect.",
    "image": "Use available vision/OCR and verify symbols.",
    "text": "Decode text and preserve section/line locators.",
    "audio": "Transcribe with timestamps if available.",
    "video": "Transcribe and inspect relevant frames if available.",
    "archive": "Inspect members and safe extraction limits before unpacking.",
    "ebook": "Use an available ebook parser/converter.",
    "unknown": "Inspect format; record unsupported content rather than guessing.",
}


def classify(path):
    return next((kind for kind, exts in GROUPS.items() if path.suffix.lower() in exts), "unknown")


def collect(root, excluded=(), output=None):
    """IDs are path-derived; hashes identify exact copies, not semantic copies."""
    original = Path(root).expanduser()
    if original.is_symlink():
        raise ValueError("Input root must not be a symbolic link.")
    root = original.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Input must be a directory.")
    output = Path(output).resolve() if output else None
    excluded_paths = {(root / item).resolve() for item in excluded}
    for path in excluded_paths:
        if path != root and root not in path.parents:
            raise ValueError("Excluded paths must stay inside the input directory.")
    skipped = []
    files = []
    errors = []

    def is_excluded(path):
        return any(path == item or item in path.parents for item in excluded_paths)

    def walk_error(error):
        errors.append(str(error))

    for folder, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        folder = Path(folder)
        kept = []
        for name in sorted(dirs):
            path = folder / name
            if path.is_symlink() or name in SKIP_DIRS or is_excluded(path):
                skipped.append({"path": path.relative_to(root).as_posix(), "reason": "link or excluded directory"})
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = folder / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink() or is_excluded(path) or path == output:
                skipped.append({"path": relative, "reason": "link, excluded file, or output manifest"})
                continue
            files.append(path)

    records, seen_hashes = [], {}
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        source_id = "S-" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:12]
        kind = classify(path)
        record = {
            "id": source_id, "path": relative, "kind": kind,
            "route": ROUTES[kind], "status": "pending", "size_bytes": None,
            "sha256": None, "duplicate_of": None, "coverage": None,
            "locator": None, "issues": [],
        }
        try:
            record["size_bytes"] = path.stat().st_size
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            record["sha256"] = digest.hexdigest()
            record["duplicate_of"] = seen_hashes.get(record["sha256"])
            seen_hashes.setdefault(record["sha256"], source_id)
        except OSError as error:
            record["status"] = "unreadable"
            record["issues"].append(str(error))
        records.append(record)
    return {
        "schema_version": 1, "input_root": str(root),
        "note": "Inventory only. pending means content has not been extracted.",
        "sources": records, "skipped": skipped, "scan_errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--exclude", action="append", default=[], help="Relative file/directory to exclude; repeatable")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        if args.output.exists() and not args.overwrite:
            raise ValueError("Output exists; choose a new path or pass --overwrite.")
        result = collect(args.input, args.exclude, args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w" if args.overwrite else "x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(f"Inventoried {len(result['sources'])} files: {args.output}")
        return 1 if result["scan_errors"] else 0
    except (OSError, ValueError) as error:
        parser.exit(1, f"Inventory failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
