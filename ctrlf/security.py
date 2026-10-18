"""
Security & Sandbox Firewall for ctrlf.
Guarantees Agent Safety: blocks path traversal, sensitive file access, and destructive replacements.
"""

import os
from pathlib import Path
from typing import Optional, Set

# Sensitive file patterns that AI agents must NEVER read or edit via ctrlf
SENSITIVE_PATTERNS = {
    ".env", ".env.local", ".env.production", ".env.development", ".env.test",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    "credentials.json", "service-account.json", "auth.json",
    ".npmrc", ".pypirc", ".netrc"
}

SENSITIVE_EXTENSIONS = {
    ".pem", ".key", ".keystore", ".p12", ".pfx", ".pkcs12"
}

SENSITIVE_DIRS = {
    ".ssh", ".aws", ".gnupg", ".kube", ".docker", ".git", ".hg", ".svn"
}

SYSTEM_PROTECTED_PREFIXES = (
    "/etc", "/usr", "/var", "/boot", "/sys", "/proc", "/root", "/bin", "/sbin", "/lib", "/lib64"
)

class SecurityError(Exception):
    """Raised when an operation violates agent security boundaries."""
    pass

def is_path_safe(target_path: str, root_dir: Optional[str] = None, allow_system: bool = False) -> Path:
    """
    Validate that target_path is canonical, safe, and does not target protected secrets.
    Returns resolved Path object on success, raises SecurityError on violation.
    """
    try:
        resolved = Path(target_path).expanduser().resolve()
    except Exception as e:
        raise SecurityError(f"Invalid path structure: {e}")

    # Check system directory protection
    if not allow_system:
        resolved_str = str(resolved)
        for prefix in SYSTEM_PROTECTED_PREFIXES:
            if resolved_str == prefix or resolved_str.startswith(prefix + os.sep):
                raise SecurityError(f"Access to protected system path '{resolved_str}' is denied.")

    # Check sensitive directories in path parts
    for part in resolved.parts:
        if part in SENSITIVE_DIRS:
            raise SecurityError(f"Access to sensitive directory '{part}' in path is denied.")

    # Check sensitive filenames
    filename = resolved.name.lower()
    if filename in SENSITIVE_PATTERNS:
        raise SecurityError(f"Access to sensitive credentials file '{filename}' is strictly blocked.")

    # Check sensitive extensions
    if resolved.suffix.lower() in SENSITIVE_EXTENSIONS:
        raise SecurityError(f"Access to secret/key file with extension '{resolved.suffix}' is strictly blocked.")

    # Check root confinement if root_dir is specified
    if root_dir:
        try:
            root_resolved = Path(root_dir).expanduser().resolve()
            # If resolved path is not relative to root_resolved, path traversal occurred
            resolved.relative_to(root_resolved)
        except ValueError:
            raise SecurityError(f"Path traversal detected: '{target_path}' is outside project root '{root_dir}'.")

    return resolved

def validate_replacement_safety(old_str: str, new_str: str, original_content: str, force: bool = False):
    """
    Sanity check to prevent accidental destructive code wipeouts or infinite loop injections.
    """
    if not old_str:
        raise SecurityError("Cannot replace empty string (would cause character-level pollution).")

    if not force:
        # Detect catastrophic file shrinking (>80% deletion in single replace)
        orig_len = len(original_content)
        new_len = orig_len - len(old_str) + len(new_str)
        if orig_len > 200 and new_len < orig_len * 0.2:
            raise SecurityError(
                f"Destructive change warning: replacement shrinks file by >80% "
                f"({orig_len} -> {new_len} chars). Use --force if intentional."
            )
