"""
Core engine for ctrlf.
Provides fast search, peek, and atomic surgical replace with diff and safety guards.
"""

import os
import sys
import re
import difflib
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from .security import is_path_safe, validate_replacement_safety, SecurityError

EXCLUDE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", 
    ".cache", "dist", "build", "target", ".next", ".nuxt",
    ".idea", ".vscode", ".tox", ".cargo", "coverage", ".hermes", ".claude"
}

def search_code(
    pattern: str, 
    path: str = ".", 
    case_sensitive: bool = False, 
    is_regex: bool = False, 
    file_type: Optional[str] = None, 
    context_lines: int = 2, 
    limit: int = 25,
    root_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search codebase using ripgrep (with Python fallback).
    Enforces security boundaries. Returns structured match dictionary.
    """
    target_path = is_path_safe(path, root_dir)
    target_str = str(target_path)

    rg_bin = shutil.which("rg")
    if rg_bin:
        cmd = [
            rg_bin,
            "--line-number",
            "--color=never",
            f"--context={context_lines}",
            "--max-count", str(limit),
        ]
        if not case_sensitive:
            cmd.append("--smart-case")
        else:
            cmd.append("--case-sensitive")
        if not is_regex:
            cmd.append("--fixed-strings")
        if file_type:
            cmd.extend(["--type", file_type])
        for ex in EXCLUDE_DIRS:
            cmd.extend(["--glob", f"!**/{ex}/**"])
        cmd.extend(["--", pattern, target_str])

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
            raw_output = res.stdout.strip()
            return {
                "success": True,
                "engine": "ripgrep",
                "raw": raw_output,
                "count": raw_output.count("\n") if raw_output else 0
            }
        except Exception as e:
            return {"success": False, "error": f"Ripgrep failed: {e}"}

    # Python fallback
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern if is_regex else re.escape(pattern), flags)
    except re.error as e:
        return {"success": False, "error": f"Invalid regex: {e}"}

    matches = []
    total = 0
    paths_to_search = [target_path] if target_path.is_file() else []
    if target_path.is_dir():
        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                paths_to_search.append(Path(root) / f)

    lines_output = []
    for fpath in paths_to_search:
        try:
            # Check individual file safety
            is_path_safe(str(fpath), root_dir)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()
        except Exception:
            continue

        matched_indices = [idx for idx, line in enumerate(lines) if regex.search(line)]
        if not matched_indices:
            continue

        lines_output.append(f"\n{fpath}")
        printed = set()
        for idx in matched_indices:
            total += 1
            for j in range(max(0, idx - context_lines), min(len(lines), idx + context_lines + 1)):
                if j not in printed:
                    printed.add(j)
                    marker = ">" if j == idx else " "
                    lines_output.append(f"{marker} {j+1:4d} | {lines[j].rstrip()}")
            if total >= limit:
                break
        if total >= limit:
            break

    return {
        "success": True,
        "engine": "python-fallback",
        "raw": "\n".join(lines_output),
        "count": total
    }

def peek_code(
    file_path: str, 
    line_number: int, 
    radius: int = 6, 
    root_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Peek lines around target line without reading entire file."""
    safe_path = is_path_safe(file_path, root_dir)
    if not safe_path.is_file():
        raise FileNotFoundError(f"File not found: '{file_path}'")

    with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total_lines = len(lines)
    center = line_number - 1
    start = max(0, center - radius)
    end = min(total_lines, center + radius + 1)

    result_lines = []
    for i in range(start, end):
        result_lines.append({
            "line": i + 1,
            "is_center": (i == center),
            "content": lines[i].rstrip("\r\n")
        })

    return {
        "success": True,
        "file": str(safe_path),
        "total_lines": total_lines,
        "start_line": start + 1,
        "end_line": end,
        "lines": result_lines
    }

def replace_code(
    file_path: str, 
    old_snippet: str, 
    new_snippet: str, 
    target_line: Optional[int] = None, 
    replace_all: bool = False,
    dry_run: bool = False,
    force: bool = False,
    root_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Surgically replace exact string in file with atomic write and security verification.
    """
    safe_path = is_path_safe(file_path, root_dir)
    if not safe_path.is_file():
        raise FileNotFoundError(f"File not found: '{file_path}'")

    with open(safe_path, "r", encoding="utf-8") as f:
        content = f.read()

    validate_replacement_safety(old_snippet, new_snippet, content, force)

    # Locate occurrences
    occurrences = []
    start = 0
    while True:
        pos = content.find(old_snippet, start)
        if pos == -1:
            break
        lno = content.count("\n", 0, pos) + 1
        occurrences.append((pos, pos + len(old_snippet), lno))
        start = pos + len(old_snippet)

    if not occurrences:
        raise ValueError(f"Snippet not found in '{file_path}'. Verify whitespace or use peek.")

    if replace_all:
        new_content = content.replace(old_snippet, new_snippet)
        count = len(occurrences)
    elif len(occurrences) == 1:
        s, e, _ = occurrences[0]
        new_content = content[:s] + new_snippet + content[e:]
        count = 1
    else:
        if target_line is not None:
            best = min(occurrences, key=lambda occ: abs(occ[2] - target_line))
            s, e, lno = best
            new_content = content[:s] + new_snippet + content[e:]
            count = 1
        else:
            lnos = [occ[2] for occ in occurrences]
            raise ValueError(f"Multiple matches ({len(occurrences)}) at lines {lnos}. Specify target_line or replace_all.")

    # Generate unified diff
    orig_lines = content.splitlines(keepends=True)
    mod_lines = new_content.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        orig_lines, mod_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=2
    ))
    diff_str = "".join(diff)

    if not diff_str:
        return {"success": True, "changed": False, "message": "Content identical; no changes made."}

    if not dry_run:
        # Atomic write
        tmp_file = str(safe_path) + ".tmp_ctrlf"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            shutil.copymode(safe_path, tmp_file)
            os.replace(tmp_file, safe_path)
        except Exception as e:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            raise IOError(f"Failed to save file '{file_path}': {e}")

    return {
        "success": True,
        "changed": True,
        "file": str(safe_path),
        "count": count,
        "diff": diff_str,
        "dry_run": dry_run
    }
