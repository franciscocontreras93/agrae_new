from abc import ABC, abstractmethod
from pathlib import Path

from exportar_rindes.core.models import InspectionResult, SourceRecord


class YieldReader(ABC):
    @abstractmethod
    def inspect(self, source: Path) -> InspectionResult: ...

    @abstractmethod
    def read(self, source: Path) -> list[SourceRecord]: ...
