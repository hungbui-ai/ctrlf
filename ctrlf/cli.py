"""
CLI Entrypoint for ctrlf.
"""

import sys
import os
import json
import argparse
from typing import Optional

from .engine import search_code, peek_code, replace_code
from .security import SecurityError
from .installer import run_setup
from . import __version__

# ANSI Colors
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
DIM = "\033[90m"
RESET = "\033[0m"

def color(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"{code}{text}{RESET}"
    return text

def print_diff(diff_str: str):
    for line in diff_str.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            print(color(line, GREEN))
        elif line.startswith("-") and not line.startswith("---"):
            print(color(line, RED))
        elif line.startswith("@@"):
            print(color(line, CYAN))
        else:
            print(line)

def main():
    parser = argparse.ArgumentParser(
        prog="ctrlf",
        description="ctrlf - High-speed code locator and surgical in-place editor for AI Agents & Devs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ctrlf find "handleSubmit"
  ctrlf peek src/auth.ts:45
  ctrlf replace src/config.ts --old "port: 3000" --new "port: 8080"
  ctrlf init
        """
    )
    parser.add_argument("-v", "--version", action="version", version=f"ctrlf {__version__}")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to execute")

    # FIND
    p_find = subparsers.add_parser("find", aliases=["search", "f"], help="Find text or regex pattern")
    p_find.add_argument("pattern", help="Text or regex to search for")
    p_find.add_argument("path", nargs="?", default=".", help="Directory or file path")
    p_find.add_argument("-c", "--case-sensitive", action="store_true", help="Match case strictly")
    p_find.add_argument("-r", "--regex", action="store_true", help="Treat pattern as regex")
    p_find.add_argument("-t", "--type", dest="file_type", help="Filter by file extension/type")
    p_find.add_argument("-C", "--context", type=int, default=2, help="Lines of surrounding context")
    p_find.add_argument("-n", "--limit", type=int, default=25, help="Max results")

    # PEEK
    p_peek = subparsers.add_parser("peek", aliases=["view", "p"], help="Preview lines around a specific line number")
    p_peek.add_argument("target", help="Format: <file>:<line> (e.g. src/auth.ts:45)")
    p_peek.add_argument("radius", nargs="?", type=int, default=6, help="Context lines radius")

    # REPLACE
    p_replace = subparsers.add_parser("replace", aliases=["rep", "r"], help="Surgically replace a snippet in a file")
    p_replace.add_argument("file", help="File to edit")
    p_replace.add_argument("-o", "--old", required=True, help="Exact old snippet to replace")
    p_replace.add_argument("-n", "--new", required=True, help="New replacement snippet")
    p_replace.add_argument("-l", "--line", type=int, default=None, help="Target line number (if multiple occurrences)")
    p_replace.add_argument("-a", "--all", action="store_true", help="Replace all occurrences")
    p_replace.add_argument("--dry-run", action="store_true", help="Preview diff without saving")
    p_replace.add_argument("--force", action="store_true", help="Bypass safety shrinking guard")

    # INIT
    p_init = subparsers.add_parser("init", aliases=["setup"], help="Auto-configure MCP & rules for installed Coding Agents")
    p_init.add_argument("--cmd", default="ctrlf-mcp", help="Command or path for ctrlf MCP server")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        return 0

    try:
        if args.subcommand in ("find", "search", "f"):
            res = search_code(args.pattern, args.path, args.case_sensitive, args.regex, 
                              args.file_type, args.context, args.limit)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if not res.get("success"):
                    print(color(f"Error: {res.get('error')}", RED), file=sys.stderr)
                    return 1
                raw = res.get("raw", "")
                if raw:
                    print(raw)
                else:
                    print(color(f"No matches found for '{args.pattern}'.", YELLOW))
            return 0

        elif args.subcommand in ("peek", "view", "p"):
            if ":" not in args.target:
                print(color("Error: target must be in format <file>:<line>", RED), file=sys.stderr)
                return 1
            fpath, lno_str = args.target.split(":", 1)
            res = peek_code(fpath, int(lno_str), args.radius)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(color(f"[{res['file']} (Lines {res['start_line']}-{res['end_line']} of {res['total_lines']})]", BOLD + CYAN))
                for l in res["lines"]:
                    marker = color(">", GREEN + BOLD) if l["is_center"] else " "
                    lno = color(f"{l['line']:4d}", BOLD if l["is_center"] else DIM)
                    content = color(l["content"], BOLD) if l["is_center"] else l["content"]
                    print(f"{marker} {lno} | {content}")
            return 0

        elif args.subcommand in ("replace", "rep", "r"):
            res = replace_code(args.file, args.old, args.new, args.line, args.all, args.dry_run, args.force)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if not res.get("changed"):
                    print(color(res.get("message", "No changes made."), YELLOW))
                    return 0
                title = f"=== Changes for '{res['file']}' ({res['count']} match) ==="
                print(color(title, BOLD))
                print_diff(res["diff"])
                if res.get("dry_run"):
                    print(color("\n[Dry run: No files modified]", YELLOW))
                else:
                    print(color(f"\n✔ Successfully updated '{res['file']}'.", GREEN + BOLD))
            return 0

        elif args.subcommand in ("init", "setup"):
            print(color("Scanning for installed AI Coding Agents...", BOLD))
            results = run_setup(args.cmd)
            for agent, ok in results.items():
                status = color("✔ Configured", GREEN + BOLD) if ok else color("Not found / Skipped", DIM)
                print(f"  • {agent:<22}: {status}")
            print(color("\nSetup complete! All detected agents now have ctrlf MCP and mandatory rules active.", GREEN + BOLD))
            return 0

    except SecurityError as se:
        print(color(f"Agent Security Firewall: {se}", RED + BOLD), file=sys.stderr)
        return 2
    except Exception as e:
        print(color(f"Error: {e}", RED), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
