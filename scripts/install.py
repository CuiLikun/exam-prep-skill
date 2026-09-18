#!/usr/bin/env python3
"""Copy the portable skill into a Codex or Claude Code skills directory."""
import argparse
from pathlib import Path
import shutil

NAME = "exam-prep"
SOURCE = Path(__file__).resolve().parents[1] / "skills" / NAME


def destinations(tool, dest=None, home=None):
    home = Path(home) if home else Path.home()
    if dest:
        if tool == "both":
            raise ValueError("--dest requires a single --tool.")
        return [Path(dest).expanduser().resolve() / NAME]
    roots = {"codex": home / ".agents" / "skills", "claude": home / ".claude" / "skills"}
    return [roots[key] / NAME for key in (("codex", "claude") if tool == "both" else (tool,))]


def install(targets):
    # Check every destination before making changes when installing for both tools.
    for target in targets:
        resolved = target.resolve()
        if resolved == SOURCE or SOURCE in resolved.parents:
            raise ValueError("Destination must not be inside the skill source.")
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Already exists: {target}. Back it up or choose another destination.")
    if not (SOURCE / "SKILL.md").is_file():
        raise FileNotFoundError(f"Skill source missing: {SOURCE}")
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"Installed: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=("codex", "claude", "both"), required=True)
    parser.add_argument("--dest", help="Custom parent skills directory, for one tool")
    args = parser.parse_args()
    try:
        install(destinations(args.tool, args.dest))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Install failed: {error}\n")


if __name__ == "__main__":
    main()
