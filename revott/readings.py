"""The named readings.

The corpus carries eleven named readings over the same positions, at four
scales -- 3500D, 2800D/23, 100D and yG. They are other views of the same
domain, held here as data.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "readings.json"


@lru_cache(maxsize=1)
def _raw() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def names() -> list[str]:
    positions = _raw()["positions"]
    return sorted(positions[0]["readings"]) if positions else []


def at(x: float) -> dict[str, float]:
    """Every named reading at a position, where the corpus records them."""
    for record in _raw()["positions"]:
        if abs(record["position"] - x) < 1e-9:
            return dict(record["readings"])
    return {}


def series(name: str) -> list[tuple[float, float]]:
    """One reading across every position that carries it."""
    return [
        (r["position"], r["readings"][name])
        for r in _raw()["positions"]
        if name in r["readings"]
    ]


def covered() -> list[float]:
    return [r["position"] for r in _raw()["positions"]]
