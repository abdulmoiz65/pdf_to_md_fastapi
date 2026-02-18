"""Text formatting — bold, italic, underline detection from font flags."""

from __future__ import annotations


class TextFormatter:
    """Convert raw spans into Markdown-formatted text based on font flags."""

    # PyMuPDF font flag constants
    FLAG_BOLD = 1 << 4       # 16
    FLAG_ITALIC = 1 << 1     # 2
    FLAG_SUPERSCRIPT = 1 << 0  # 1

    @staticmethod
    def is_bold(flags: int) -> bool:
        return bool(flags & TextFormatter.FLAG_BOLD)

    @staticmethod
    def is_italic(flags: int) -> bool:
        return bool(flags & TextFormatter.FLAG_ITALIC)

    @staticmethod
    def apply_formatting(span: dict) -> str:
        """Apply Markdown formatting to a single span dict.

        Expected span keys: 'text', 'flags' (int).
        Returns the formatted text string.
        """
        text = span.get("text", "").rstrip()
        if not text:
            return ""

        flags = span.get("flags", 0)
        bold = TextFormatter.is_bold(flags)
        italic = TextFormatter.is_italic(flags)

        if bold and italic:
            text = f"***{text}***"
        elif bold:
            text = f"**{text}**"
        elif italic:
            text = f"*{text}*"

        return text

    @staticmethod
    def format_line(spans: list[dict]) -> tuple[str, float, bool]:
        """Format an entire line (list of spans).

        Returns (formatted_text, max_font_size, is_bold).
        """
        parts: list[str] = []
        max_size = 0.0
        line_bold = False

        for span in spans:
            formatted = TextFormatter.apply_formatting(span)
            if formatted:
                parts.append(formatted)
            size = span.get("size", 0)
            if size > max_size:
                max_size = size
            if TextFormatter.is_bold(span.get("flags", 0)):
                line_bold = True

        return " ".join(parts), max_size, line_bold
