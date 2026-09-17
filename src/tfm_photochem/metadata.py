"""Common provenance types used by every model configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Parameter:
    """A numerical parameter together with reproducibility metadata."""

    value: float | int
    unit: str
    reference: str
    year: int
    configuration: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)

