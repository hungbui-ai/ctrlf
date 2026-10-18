"""
Universal Agent Auto-Installer for ctrlf.
Auto-detects Cursor, Claude Code, Windsurf, Antigravity, and Hermes,
and injects MCP Server configs and mandatory rules with 1 command.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List

MANDATORY_RULE_CONTENT = """<!-- ctrlf-rules -->
<!-- version: 1 -->
# MANDATORY: Fast Code Search & Surgical In-Place Editing (ctrlf)

Before modifying or inspecting existing code in the project, you MUST obey these rules:
1. NO FULL FILE DUMPS: Never load entire files into context when locating or modifying an existing function or class.
2. ALWAYS USE CTRLF:
   - Locate: Call `ctrlf_find` (or run `ctrlf find "<keyword>"`) to get the exact file and line numbers.
   - Inspect: Call `ctrlf_peek` (or run `ctrlf peek "<file>:<line>"`) to check immediate context lines.
   - Surgical Edit: Call `ctrlf_replace` (or run `ctrlf replace "<file>" --old "..." --new "..."`) to perform minimal atomic diffs.
3. CONTEXT INTEGRITY: Keep diffs minimal and surgical to preserve token budget.
<!-- /ctrlf-rules -->
"""

def setup_claude_code(mcp_cmd: str) -> bool:
    home = Path.home()
    claude_json = home / ".claude.json"
    settings_json = home / ".claude" / "settings.json"
    claude_md = home / ".claude" / "CLAUDE.md"
    configured = False

    # 1. Inject into ~/.claude.json
    if claude_json.exists():
        try:
            with open(claude_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            mcp_servers = data.setdefault("mcpServers", {})
            mcp_servers["ctrlf"] = {
                "command": mcp_cmd,
                "args": []
            }
            with open(claude_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            configured = True
        except Exception as e:
            print(f"Warning: Failed to update ~/.claude.json: {e}", file=sys.stderr)

    # 2. Inject permissions into ~/.claude/settings.json
    if settings_json.exists():
        try:
            with open(settings_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            perms = data.setdefault("permissions", {})
            allowed = perms.setdefault("allow", [])
            for item in ["Bash(ctrlf*)", "mcp__ctrlf__ctrlf_find", "mcp__ctrlf__ctrlf_peek", "mcp__ctrlf__ctrlf_replace"]:
                if item not in allowed:
                    allowed.append(item)
            with open(settings_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            configured = True
        except Exception as e:
            print(f"Warning: Failed to update ~/.claude/settings.json: {e}", file=sys.stderr)

    # 3. Add to CLAUDE.md
    if claude_md.exists():
        try:
            content = claude_md.read_text(encoding="utf-8")
            if "ctrlf" not in content:
                claude_md.write_text(content + "\n\n" + MANDATORY_RULE_CONTENT, encoding="utf-8")
        except Exception:
            pass

    return configured

def setup_cursor(mcp_cmd: str) -> bool:
    home = Path.home()
    cursor_dir = home / ".cursor"
    mcp_file = cursor_dir / "mcp.json"
    rules_dir = cursor_dir / "rules"

    if not cursor_dir.exists():
        return False

    # 1. Inject MCP
    if mcp_file.exists():
        try:
            with open(mcp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            servers = data.setdefault("mcpServers", {})
            servers["ctrlf"] = {
                "command": mcp_cmd,
                "autoApprove": ["ctrlf_find", "ctrlf_peek", "ctrlf_replace"]
            }
            with open(mcp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to update Cursor mcp.json: {e}", file=sys.stderr)

    # 2. Inject Rule
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_file = rules_dir / "ctrlf.mdc"
    rule_file.write_text(f"""---
description: "MANDATORY: Fast Code Search & Surgical In-Place Editing (ctrlf)"
globs: **/*
alwaysApply: true
---

{MANDATORY_RULE_CONTENT}
""", encoding="utf-8")

    return True

def setup_antigravity_and_gemini(mcp_cmd: str) -> bool:
    home = Path.home()
    gemini_config = home / ".gemini" / "config" / "mcp_config.json"
    agy_config = home / ".gemini" / "antigravity" / "mcp_config.json"
    agy_rules_dir = home / ".gemini" / "antigravity" / "rules"

    configured = False
    for conf in (gemini_config, agy_config):
        if conf.exists():
            try:
                with open(conf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data.setdefault("mcpServers", {})["ctrlf"] = {"command": mcp_cmd}
                with open(conf, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                configured = True
            except Exception:
                pass

    if agy_rules_dir.exists():
        (agy_rules_dir / "ctrlf.md").write_text(MANDATORY_RULE_CONTENT, encoding="utf-8")
        configured = True

    return configured

def run_setup(mcp_cmd: str = "ctrlf-mcp") -> Dict[str, bool]:
    # Resolve full path to mcp_cmd if available
    resolved_cmd = shutil.which(mcp_cmd) or mcp_cmd

    results = {
        "Claude Code": setup_claude_code(resolved_cmd),
        "Cursor": setup_cursor(resolved_cmd),
        "Antigravity / Gemini": setup_antigravity_and_gemini(resolved_cmd)
    }
    return results
