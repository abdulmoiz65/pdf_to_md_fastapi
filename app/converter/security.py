"""Encryption detection, password auth, and permission reporting."""

from __future__ import annotations

import fitz


class SecurityHandler:
    """Handle password-protected and encrypted PDFs."""

    @staticmethod
    def check_encryption(doc: fitz.Document) -> tuple[bool, str]:
        """Return ``(is_encrypted, message)``."""
        if doc.is_encrypted:
            if doc.needs_pass:
                return True, "PDF is password-protected and needs authentication."
            return True, "PDF is encrypted but accessible (owner password only)."
        return False, "PDF is not encrypted."

    @staticmethod
    def authenticate(doc: fitz.Document, password: str) -> bool:
        """Attempt to authenticate with *password*. Returns True on success."""
        return doc.authenticate(password) > 0

    @staticmethod
    def get_permissions_info(doc: fitz.Document) -> str:
        """Return a Markdown section describing the PDF's permissions."""
        if not doc.is_encrypted:
            return ""

        perms = doc.permissions
        rows = [
            "\n## 🔐 Security Info\n",
            f"- **Encrypted:** Yes",
            f"- **Can Print:** {'Yes' if perms & fitz.PDF_PERM_PRINT else 'No'}",
            f"- **Can Copy:** {'Yes' if perms & fitz.PDF_PERM_COPY else 'No'}",
            f"- **Can Modify:** {'Yes' if perms & fitz.PDF_PERM_MODIFY else 'No'}",
            "",
        ]
        return "\n".join(rows)
