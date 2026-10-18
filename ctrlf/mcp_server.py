"""
FastMCP Server implementation for ctrlf.
"""

import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP
from .engine import search_code, peek_code, replace_code
from .security import SecurityError

mcp = FastMCP("ctrlf")

@mcp.tool()
def ctrlf_find(
    pattern: str, 
    path: str = ".", 
    case_sensitive: bool = False, 
    is_regex: bool = False, 
    file_type: Optional[str] = None, 
    context_lines: int = 2, 
    limit: int = 25
) -> str:
    """
    Search codebase for text or regex pattern (like IDE Ctrl+F).
    Returns file paths, line numbers, and context without loading full files into memory.
    """
    try:
        res = search_code(pattern, path, case_sensitive, is_regex, file_type, context_lines, limit)
        if not res.get("success"):
            return f"Search error: {res.get('error')}"
        raw = res.get("raw", "")
        return raw if raw else f"No matches found for '{pattern}'."
    except SecurityError as se:
        return f"Security Violation: {se}"
    except Exception as e:
        return f"Error executing search: {e}"

@mcp.tool()
def ctrlf_peek(file_path: str, line_number: int, radius: int = 6) -> str:
    """
    Peek immediate lines around a line number without reading the entire file into context.
    Use this to inspect exact syntax and indentation before editing.
    """
    try:
        res = peek_code(file_path, line_number, radius)
        out = [f"[{res['file']} (Lines {res['start_line']}-{res['end_line']} of {res['total_lines']})]"]
        for l in res["lines"]:
            marker = ">" if l["is_center"] else " "
            out.append(f"{marker} {l['line']:4d} | {l['content']}")
        return "\n".join(out)
    except SecurityError as se:
        return f"Security Violation: {se}"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def ctrlf_replace(
    file_path: str, 
    old_snippet: str, 
    new_snippet: str, 
    target_line: Optional[int] = None, 
    replace_all: bool = False,
    dry_run: bool = False,
    force: bool = False
) -> str:
    """
    Surgically replace an exact code snippet in a file.
    Performs atomic write and returns a unified diff.
    """
    try:
        res = replace_code(file_path, old_snippet, new_snippet, target_line, replace_all, dry_run, force)
        if not res.get("changed"):
            return res.get("message", "No changes made.")
        prefix = "[Dry Run - Not Saved]\n" if dry_run else f"Successfully updated '{file_path}' ({res['count']} match):\n\n"
        return prefix + res["diff"]
    except SecurityError as se:
        return f"Security Violation: {se}"
    except Exception as e:
        return f"Error: {e}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
