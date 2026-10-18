import pytest
import os
from pathlib import Path
from ctrlf.security import is_path_safe, validate_replacement_safety, SecurityError

def test_block_sensitive_files():
    with pytest.raises(SecurityError, match="strictly blocked"):
        is_path_safe(".env")

    with pytest.raises(SecurityError, match="strictly blocked"):
        is_path_safe("config/.env.local")

    with pytest.raises(SecurityError, match="strictly blocked"):
        is_path_safe("id_rsa")

    with pytest.raises(SecurityError, match="strictly blocked"):
        is_path_safe("cert.pem")

def test_block_sensitive_dirs():
    with pytest.raises(SecurityError, match="sensitive directory"):
        is_path_safe("~/.ssh/config")

    with pytest.raises(SecurityError, match="sensitive directory"):
        is_path_safe(".git/config")

def test_path_traversal(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("classified")

    with pytest.raises(SecurityError, match="Path traversal"):
        is_path_safe(str(secret), root_dir=str(root))

def test_empty_string_replace_guard():
    with pytest.raises(SecurityError, match="empty string"):
        validate_replacement_safety("", "something", "original content")
