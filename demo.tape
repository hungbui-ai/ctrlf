Output assets/demo.gif

Set FontSize 18
Set Width 1100
Set Height 640
Set Padding 20
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 35ms

# Setup workspace
Hide
Type "cd /tmp/vhs-demo && clear"
Enter
Show

# Step 1: Find
Type "# 1. Fast Locate (like Ctrl+F in 5ms)"
Enter
Sleep 600ms
Type "ctrlf find 'calculate_discount'"
Sleep 400ms
Enter
Sleep 2.5s

# Step 2: Peek
Type "# 2. Peek context around line 6 without loading full file"
Enter
Sleep 600ms
Type "ctrlf peek src/billing.py:6 3"
Sleep 400ms
Enter
Sleep 2.5s

# Step 3: Surgical Replace
Type "# 3. Surgical in-place atomic replace with unified diff"
Enter
Sleep 600ms
Type "ctrlf replace src/billing.py --old 'rate = 0.10' --new 'rate = 0.25'"
Sleep 400ms
Enter
Sleep 3.5s

# Step 4: 1-Click Init
Type "# 4. Auto-configure all AI Coding Agents (Cursor, Claude Code, etc.)"
Enter
Sleep 600ms
Type "ctrlf init"
Sleep 400ms
Enter
Sleep 4s
