import pytest
import os
from pathlib import Path
from ctrlf.engine import search_code, peek_code, replace_code

def test_peek_and_replace(tmp_path):
    test_file = tmp_path / "app.py"
    test_file.write_text("def hello():\n    print('Hello World')\n    return True\n")

    # Peek
    peek_res = peek_code(str(test_file), 2, radius=1)
    assert peek_res["success"] is True
    assert len(peek_res["lines"]) == 3
    assert peek_res["lines"][1]["is_center"] is True
    assert "print('Hello World')" in peek_res["lines"][1]["content"]

    # Replace
    rep_res = replace_code(str(test_file), "print('Hello World')", "print('Hello ctrlf')")
    assert rep_res["success"] is True
    assert rep_res["count"] == 1
    assert "-    print('Hello World')" in rep_res["diff"]
    assert "+    print('Hello ctrlf')" in rep_res["diff"]

    # Verify content
    updated = test_file.read_text()
    assert "Hello ctrlf" in updated
    assert "Hello World" not in updated

def test_replace_disambiguation(tmp_path):
    test_file = tmp_path / "multi.py"
    test_file.write_text("x = 1\nx = 1\nx = 1\n")

    # Without target_line or replace_all, should raise ValueError
    with pytest.raises(ValueError, match="Multiple matches"):
        replace_code(str(test_file), "x = 1", "x = 2")

    # With replace_all
    rep_res = replace_code(str(test_file), "x = 1", "x = 2", replace_all=True)
    assert rep_res["count"] == 3
    assert test_file.read_text() == "x = 2\nx = 2\nx = 2\n"
