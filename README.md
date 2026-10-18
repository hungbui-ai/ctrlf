# ⚡ ctrlf

> **High-speed code locator & surgical in-place editor for AI Coding Agents.**  
> Saves **90–95% of context tokens** and cuts latency by eliminating full-file dumps.

**English** | [Tiếng Việt](README.vi.md)

[![Tests](https://github.com/hungbui-ai/ctrlf/actions/workflows/test.yml/badge.svg)](https://github.com/hungbui-ai/ctrlf/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Ready](https://img.shields.io/badge/Protocol-MCP-orange.svg)](https://modelcontextprotocol.io)

<p align="center">
  <img src="assets/demo.gif" alt="ctrlf Demo" width="95%" />
</p>

---

## 💥 The Problem: Why Coding Agents Burn Your Tokens

When typical coding agents (Claude Code, Cursor, Windsurf, Cline, Aider) need to modify 3 lines of code in a 500-line file:
1. They load the **entire 500 lines** into the LLM context window (~3,500 – 4,500 tokens).
2. They regurgitate or rescan the whole file to edit it.
3. **Total Cost:** ~7,600 tokens per minor edit!
4. **Side Effects:** Your context window gets polluted, latency spikes, and hallucinations skyrocket.

---

## 🚀 The Solution: `ctrlf` (Agent-First Architecture)

`ctrlf` equips AI Coding Agents with an **IDE-like "Ctrl + F" pipeline**:

```
[1. Locate]  ──► ctrlf find "pattern"      ──► Returns exact file & line in 5ms (~120 tokens)
[2. Peek]    ──► ctrlf peek file:line 5    ──► Loads ONLY 10 lines of context (~150 tokens)
[3. Patch]   ──► ctrlf replace file -o -n  ──► Applies atomic surgical diff (~100 tokens)
```

### 📊 Real-world Benchmark: Minor Bugfix in a 500-line File

| Metric | Traditional Agent (Full File Read) | With `ctrlf` Pipeline | Improvement |
| :--- | :--- | :--- | :--- |
| **Token Consumption** | ~7,600 tokens | **~370 tokens** | **🔥 95.1% Saved** |
| **Time to First Edit** | 3.5s – 6.0s | **0.4s – 0.8s** | **⚡ 6x Faster** |
| **Context Window Pollution** | Extreme (file dumps) | **Zero (surgical)** | **100% Retained** |
| **Cost per 100 edits (Claude Sonnet 3.7)** | \$2.30 USD | **\$0.11 USD** | **💰 20x Cheaper** |

---

## 🛡️ Agent Security Firewall (Built-in)

Because AI Agents can make unpredictable tool calls, `ctrlf` includes an enterprise-grade agent safety barrier:

* **Strict Path Containment:** Blocks path traversal (`../../etc/passwd`). Agents cannot break out of the workspace.
* **Sensitive File Shield:** Hard-blocks reading or editing `.env*`, `id_rsa*`, `*.pem`, `*.key`, `auth.json`, `credentials.json`, `.git/`, `~/.ssh/`.
* **Disambiguation Guard:** Refuses ambiguous replacements if a snippet appears multiple times, preventing accidental code corruptions.
* **Destructive Change Warning:** Blocks commands that wipe out >80% of a file in one replace unless `--force` is explicitly provided.
* **Atomic Writes:** All replacements are staged in temp files and atomically moved (`os.replace`) to preserve file permissions and prevent broken state.

---

## 📦 Quick Installation

### Option 1: 1-Line Installer (Linux / macOS)
```bash
curl -fsSL https://raw.githubusercontent.com/hungbui-ai/ctrlf/main/install.sh | bash
```

### Option 2: Via Pip / uv
```bash
pip install git+https://github.com/hungbui-ai/ctrlf.git
```

### 1-Click Auto Configuration for Agents
Run the auto-installer to detect installed coding agents on your machine and inject MCP configs & rules:
```bash
ctrlf init
```
Output:
```
Scanning for installed AI Coding Agents...
  • Claude Code           : ✔ Configured
  • Cursor                : ✔ Configured
  • Antigravity / Gemini  : ✔ Configured
Setup complete!
```

---

## 💻 Manual Setup by Agent

### 1. Cursor
Add to `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "ctrlf": {
      "command": "ctrlf-mcp",
      "autoApprove": ["ctrlf_find", "ctrlf_peek", "ctrlf_replace"]
    }
  }
}
```

### 2. Claude Code
Add to `~/.claude.json`:
```json
{
  "mcpServers": {
    "ctrlf": {
      "command": "ctrlf-mcp",
      "args": []
    }
  }
}
```
And add to `~/.claude/settings.json` permissions allow:
`"Bash(ctrlf*)"`, `"mcp__ctrlf__*"`

### 3. Windsurf
Add to `~/.codeium/windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "ctrlf": {
      "command": "ctrlf-mcp"
    }
  }
}
```

---

## 🛠️ CLI Usage Examples

```bash
# 1. Search for a function or string (ignores node_modules, .git, etc.)
ctrlf find "handleSubmit"
ctrlf find "PORT" src/config.ts

# 2. Peek context around a line without opening the file
ctrlf peek src/auth.ts:45
ctrlf peek src/auth.ts:45 10

# 3. Surgically replace a snippet (creates atomic diff preview)
ctrlf replace src/config.ts --old "port: 3000" --new "port: 8080"

# 4. Preview diff without writing (dry run)
ctrlf replace src/auth.ts --old "maxRetries = 3;" --new "maxRetries = 5;" --dry-run

# 5. Programmatic JSON output for custom agent harnesses
ctrlf find "API_KEY" --json
```

---

## 📜 Mandatory System Prompt Rule for Agents

To force your agent to use `ctrlf` instead of dumping whole files, place this rule in `.cursorrules`, `CLAUDE.md`, or your agent's system prompt:

```markdown
<!-- ctrlf-rules -->
MANDATORY: Fast Code Search & Surgical In-Place Editing (ctrlf)
Before inspecting or modifying existing code, you MUST obey these rules:
1. NO FULL FILE DUMPS: You are strictly forbidden from loading entire files into context.
2. ALWAYS USE CTRLF:
   - Locate: Call `ctrlf_find` to pinpoint exact file and line numbers.
   - Inspect: Call `ctrlf_peek` to inspect only the immediate context lines.
   - Surgical Edit: Call `ctrlf_replace` to apply minimal diffs.
3. CONTEXT INTEGRITY: Keep diffs minimal and surgical to preserve token budget.
<!-- /ctrlf-rules -->
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

```bash
# Clone repo
git clone https://github.com/hungbui-ai/ctrlf.git
cd ctrlf

# Install in editable mode with dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/
```

---

## 📄 License

Distributed under the [MIT License](LICENSE). Copyright (c) 2026 hungbui-ai.
