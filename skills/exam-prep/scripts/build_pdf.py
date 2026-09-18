#!/usr/bin/env python3
"""Compile an agent-authored TeX document with XeLaTeX; no Python dependencies."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile


def build(source, output, overwrite=False, timeout=120):
    source = Path(source).expanduser().resolve(strict=True)
    output = Path(output).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".tex":
        raise ValueError("Source must be an existing .tex file.")
    if output.suffix.lower() != ".pdf" or source == output:
        raise ValueError("Output must be a separate .pdf file.")
    if output.exists() and not overwrite:
        raise ValueError("Output exists; choose another path or pass --overwrite.")
    engine = shutil.which("xelatex")
    if not engine:
        raise RuntimeError("XeLaTeX not found. Use TeX Live/MiKTeX with CTeX and Fandol, or another PDF route.")
    output.parent.mkdir(parents=True, exist_ok=True)
    log_path = output.with_suffix(".build.log")
    transcript = []
    with tempfile.TemporaryDirectory(prefix="exam-prep-tex-") as temp:
        temp_path = Path(temp)
        command = [
            engine, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
            "-file-line-error", "-jobname=document", f"-output-directory={temp}", str(source),
        ]
        try:
            for run in range(1, 3):
                completed = subprocess.run(
                    command, cwd=source.parent, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, encoding="utf-8", errors="replace",
                    timeout=timeout, check=False,
                )
                transcript.append(f"--- Pass {run} ---\n{completed.stdout}")
                if completed.returncode:
                    raise RuntimeError(f"XeLaTeX failed on pass {run}; see {log_path}")
            produced = temp_path / "document.pdf"
            if not produced.is_file() or not produced.read_bytes().startswith(b"%PDF-"):
                raise RuntimeError(f"No valid PDF was produced; see {log_path}")
            # Stage on the destination filesystem; do not damage an existing PDF on failure.
            with tempfile.NamedTemporaryFile(prefix=".exam-prep-", suffix=".pdf", dir=output.parent, delete=False) as staged:
                staged_path = Path(staged.name)
                with produced.open("rb") as stream:
                    shutil.copyfileobj(stream, staged)
            try:
                if overwrite:
                    staged_path.replace(output)
                else:
                    # Exclusive creation also protects against a concurrent writer.
                    with output.open("xb") as target, staged_path.open("rb") as stream:
                        shutil.copyfileobj(stream, target)
            finally:
                staged_path.unlink(missing_ok=True)
        except subprocess.TimeoutExpired as error:
            transcript.append(f"Compilation timed out after {timeout} seconds per pass.")
            raise RuntimeError(f"XeLaTeX timed out; see {log_path}") from error
        finally:
            engine_log = temp_path / "document.log"
            if engine_log.exists():
                transcript.append(engine_log.read_text(encoding="utf-8", errors="replace"))
            log_path.write_text("\n".join(transcript), encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--timeout", type=int, default=120, help="Maximum seconds per XeLaTeX pass")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        result = build(args.source, args.output, args.overwrite, args.timeout)
        print(f"Built PDF: {result}")
        print(f"Build log: {result.with_suffix('.build.log')}")
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"PDF build failed: {error}\n")


if __name__ == "__main__":
    main()
