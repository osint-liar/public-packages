#!/usr/bin/env python3
"""
camelize_json_inplace.py

Recursively convert ALL JSON object keys to camelCase (deep) and write changes IN PLACE.

Usage:
  python camelize_json_inplace.py <repo_root>
  python camelize_json_inplace.py <repo_root> --dry-run
  python camelize_json_inplace.py <repo_root> --no-backup
  python camelize_json_inplace.py <repo_root> --exclude node_modules --exclude .git

Notes:
- By default, creates a side-by-side backup '<file>.bak' before overwriting.
- Skips directories listed by --exclude (can be passed multiple times).
"""

from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

CAMEL_RE = re.compile(r"[_\-\s]+([a-zA-Z0-9])")

def to_camel(s: str) -> str:
    """
    Convert a key to camelCase.
    - snake_case / kebab-case / space separated -> camelCase
    - PascalCase / TitleCase -> lower first letter
    """
    if not s:
        return s
    if "_" in s or "-" in s or " " in s:
        s2 = s.strip().lower()
        return CAMEL_RE.sub(lambda m: m.group(1).upper(), s2)
    return s[0].lower() + s[1:]

def camelize_keys_deep(val: JSONValue) -> JSONValue:
    """Recursively convert all dict keys to camelCase."""
    if isinstance(val, list):
        return [camelize_keys_deep(v) for v in val]
    if isinstance(val, dict):
        out: Dict[str, Any] = {}
        for k, v in val.items():
            ck = to_camel(str(k))
            out[ck] = camelize_keys_deep(v)
        return out
    return val

def read_json_text(p: Path) -> str:
    text = p.read_text(encoding="utf-8", errors="strict")
    # Strip UTF-8 BOM if present
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    return text

def parse_json(text: str) -> JSONValue:
    return json.loads(text)

def dump_json_pretty(data: Any) -> str:
    # Pretty-print with trailing newline
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"

def should_skip_dir(dir_name: str, excludes: List[str]) -> bool:
    return dir_name in excludes

def find_json_files(root: Path, excludes: List[str]) -> List[Path]:
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # mutate dirnames in-place to prune walk
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d, excludes)]
        for f in filenames:
            if f.lower().endswith(".json"):
                out.append(Path(dirpath) / f)
    return out

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="In-place camelCase conversion for all JSON keys (deep).")
    parser.add_argument("repo_root", help="Path to the repository/root folder")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; just report changes")
    parser.add_argument("--no-backup", action="store_true", help="Do not create .bak backups")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[".git", "node_modules", "dist", "build", "out", ".venv", ".mypy_cache", ".pytest_cache"],
        help="Directory name to exclude (can be specified multiple times)"
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"Error: repo_root does not exist or is not a directory: {repo_root}", file=sys.stderr)
        return 1

    json_files = find_json_files(repo_root, args.exclude)

    changed = 0
    skipped = 0
    failed = 0
    total = len(json_files)

    print(f"Found {total} JSON files. Excludes: {args.exclude or '[]'}")
    for src in json_files:
        rel = src.relative_to(repo_root)
        try:
            original_text = read_json_text(src)
            parsed = parse_json(original_text)
            camelized = camelize_keys_deep(parsed)
            new_text = dump_json_pretty(camelized)

            if new_text == original_text:
                skipped += 1
                continue

            if args.dry_run:
                print(f"[DRY-RUN] Would update: {rel}")
                changed += 1
                continue

            if not args.no_backup:
                backup_path = src.with_suffix(src.suffix + ".bak")
                # Only create one backup per run; if exists, leave it
                if not backup_path.exists():
                    shutil.copy2(src, backup_path)

            src.write_text(new_text, encoding="utf-8")
            print(f"[UPDATED] {rel}")
            changed += 1

        except Exception as e:
            print(f"[ERROR ] {rel}: {e}", file=sys.stderr)
            failed += 1

    print("\nSummary:")
    print(f"  Total   : {total}")
    print(f"  Changed : {changed}")
    print(f"  Skipped : {skipped}")
    print(f"  Failed  : {failed}")
    if args.dry_run:
        print("\n(No files were written due to --dry-run)")

    return 0 if failed == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
