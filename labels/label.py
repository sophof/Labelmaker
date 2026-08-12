from dataclasses import dataclass

from labels.label_style import LabelStyle


@dataclass
class Label:
    style: LabelStyle
    box_params: dict        # width, height, depth, side_margin — from YAML
    text: str
    font: str
    bold: bool
    italic: bool
    font_size: float
    text_style: str
    base_color: str
    text_color: str
    column_separator: str
    line_spacing: float = 1.0

    def params(self) -> dict:
        """Merge box geometry params with text/style params for style.build()."""
        return {
            **self.box_params,
            "font": self.font,
            "bold": self.bold,
            "italic": self.italic,
            "font_size": self.font_size,
            "text_style": self.text_style,
            "column_separator": self.column_separator,
            "line_spacing": self.line_spacing,
        }
