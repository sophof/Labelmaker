from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from build123d import Shape


@dataclass
class ColoredPart:
    shape: Shape
    name: str
    color: str  # hex color string, e.g. "#RRGGBB"


class LabelStyle(ABC):
    STYLE_ID: ClassVar[str]
    STYLE_NAME: ClassVar[str]
    PARAMS: ClassVar[dict]

    @abstractmethod
    def build(self, text: str, params: dict, base_color: str = "#FFFFFF", text_color: str = "#000000") -> list[ColoredPart]:
        ...
