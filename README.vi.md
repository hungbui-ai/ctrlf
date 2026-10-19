# ⚡ ctrlf

> **Bộ định vị code siêu tốc & chỉnh sửa phẫu thuật dành riêng cho AI Coding Agents.**  
> Tiết kiệm **90–95% context tokens**, triệt tiêu độ trễ và ngăn ngừa tràn ngữ cảnh do đọc toàn bộ tệp tin.

[English](README.md) | **Tiếng Việt**

[![Tests](https://github.com/hungbui-ai/ctrlf/actions/workflows/test.yml/badge.svg)](https://github.com/hungbui-ai/ctrlf/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Ready](https://img.shields.io/badge/Protocol-MCP-orange.svg)](https://modelcontextprotocol.io)

<p align="center">
  <img src="assets/demo.gif" alt="ctrlf Demo" width="95%" />
</p>

---

## 💥 Vấn đề: Tại sao AI Coding Agents ngốn sạch Token của bạn?

Khi các Coding Agent phổ biến (Claude Code, Cursor, Windsurf, Cline, Aider) cần sửa **3 dòng code** trong một file 500 dòng:
1. Agent sẽ nạp **toàn bộ 500 dòng** vào context window của LLM (~3.500 – 4.500 tokens).
2. Khi sửa xong, Agent viết lại toàn bộ hoặc sinh tool call cồng kềnh.
3. **Tổng tiêu hao:** ~7.600 tokens chỉ cho một lần sửa nhỏ!
4. **Hậu quả:** Mau hết quota token, tăng hóa đơn API, context window bị loãng dẫn đến hiện tượng "ngáo code" (hallucination).

---

## 🚀 Giải pháp: `ctrlf` (Kiến trúc tối ưu cho Agent)

`ctrlf` trang bị cho AI Coding Agent một pipeline tương tự như phím tắt **"Ctrl + F"** trên IDE:

```
[1. Định vị] ──► ctrlf find "pattern"      ──► Trả về chính xác file & số dòng trong 5ms (~120 tokens)
[2. Soi dòng] ──► ctrlf peek file:line 5    ──► CHỈ nạp 10 dòng ngữ cảnh liên quan (~150 tokens)
[3. Vá code]  ──► ctrlf replace file -o -n  ──► Áp dụng bản vá diff phẫu thuật nguyên tử (~100 tokens)
```

### 📊 Benchmark thực tế: Sửa 1 lỗi nhỏ trong file 500 dòng

| Chỉ số | Cách làm cũ (Đọc cả file) | Dùng `ctrlf` Pipeline | Mức độ cải thiện |
| :--- | :--- | :--- | :--- |
| **Token tiêu thụ / lần** | ~7.600 tokens | **~370 tokens** | **🔥 Tiết kiệm 95.1%** |
| **Thời gian phản hồi** | 3.5s – 6.0s | **0.4s – 0.8s** | **⚡ Nhanh hơn gấp 6 lần** |
| **Ô nhiễm Context Window** | Cực lớn (file dump) | **Gần như bằng 0** | **100% Giữ sạch trí nhớ** |
| **Chi phí 100 lần sửa (Claude Sonnet 3.7)** | \$2.30 USD | **\$0.11 USD** | **💰 Giảm 20 lần chi phí** |

---

## 🛡️ Tường lửa bảo mật quyền Agent (Built-in)

Vì AI Agent có thể sinh lệnh ngoài ý muốn, `ctrlf` tích hợp sẵn cơ chế bảo vệ cấp hệ thống:

* **Chống vượt ngục thư mục (Path Traversal):** Ngăn chặn tuyệt đối việc Agent dùng `../../` để đọc/ghi ra ngoài thư mục dự án.
* **Lá chắn tệp tin nhạy cảm:** Chặn cứng truy cập vào `.env*`, `id_rsa*`, `*.pem`, `*.key`, `auth.json`, `credentials.json`, `.git/`, `~/.ssh/`.
* **Chống mơ hồ (Disambiguation Guard):** Từ chối sửa nếu đoạn code xuất hiện ở nhiều nơi mà chưa chỉ định số dòng, tránh ghi đè nhầm vị trí.
* **Cảnh báo phá hủy:** Tự động chặn nếu một lệnh thay thế làm giảm >80% kích thước file (trừ khi có cờ `--force`).
* **Ghi file nguyên tử (Atomic Write):** Ghi qua file tạm và hoán đổi bằng `os.replace` để bảo toàn quyền sở hữu và không làm hỏng file nếu đứt kết nối.

---

## 📦 Cài đặt nhanh

### Cách 1: Cài tự động 1 dòng (Linux / macOS)
```bash
curl -fsSL https://raw.githubusercontent.com/hungbui-ai/ctrlf/main/install.sh | bash
```

### Cách 2: Cài qua Pip / uv
```bash
pip install git+https://github.com/hungbui-ai/ctrlf.git
```

### Kích hoạt 1 chạm cho các Coding Agents trên máy
Chỉ cần chạy lệnh sau, `ctrlf` sẽ tự động phát hiện các Agent đã cài đặt và cấu hình MCP Server cùng luật bắt buộc:
```bash
ctrlf init
```
Kết quả hiển thị:
```
Scanning for installed AI Coding Agents...
  • Claude Code           : ✔ Configured
  • Cursor                : ✔ Configured
  • Antigravity / Gemini  : ✔ Configured
Setup complete!
```

---

## 💻 Cấu hình thủ công theo từng Agent

### 1. Cursor
Thêm vào `~/.cursor/mcp.json`:
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
Thêm vào `~/.claude.json`:
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
Và thêm vào danh sách `permissions.allow` trong `~/.claude/settings.json`:
`"Bash(ctrlf*)"`, `"mcp__ctrlf__*"`

### 3. Windsurf
Thêm vào `~/.codeium/windsurf/mcp_config.json`:
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

## 🛠️ Ví dụ sử dụng qua Terminal

```bash
# 1. Tìm hàm hoặc biến trong toàn bộ dự án
ctrlf find "handleSubmit"
ctrlf find "PORT" src/config.ts

# 2. Xem trước ngữ cảnh quanh 1 dòng code mà không mở cả file
ctrlf peek src/auth.ts:45
ctrlf peek src/auth.ts:45 10

# 3. Sửa phẫu thuật cực nhanh và xem diff màu
ctrlf replace src/config.ts --old "port: 3000" --new "port: 8080"

# 4. Xem trước diff mà không lưu vào file (dry run)
ctrlf replace src/auth.ts --old "maxRetries = 3;" --new "maxRetries = 5;" --dry-run
```

---

## 📜 Quy tắc ép buộc Agent sử dụng (Prompt Rule)

Thêm khối luật sau vào `.cursorrules`, `CLAUDE.md`, hoặc system prompt của bất kỳ Agent nào để cấm đọc tràn lan:

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

## 📄 Bản quyền (License)

Phát hành dưới giấy phép [MIT License](LICENSE). Bản quyền (c) 2026 hungbui-ai.

---

## ☕ Ủng hộ tác giả (Donate)

Nếu **ctrlf** giúp bạn tiết kiệm token và chi phí API, mời tác giả một ly cà phê nhé!

* **Quốc tế:** [![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20Me%20a%20Coffee-FF5E5B?logo=ko-fi)](https://ko-fi.com/hungbuiai) hoặc [GitHub Sponsors](https://github.com/sponsors/hungbui-ai)
* **Việt Nam (Techcombank VietQR):** Xem mã QR và thông tin chuyển khoản tại [DONATE.md](DONATE.md)

