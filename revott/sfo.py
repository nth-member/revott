"""The SFO: what X ranges over, and the structure carried on it.

X is free and continuous. The 400 BB keys are a structure on it -- positions
that carry framework text and name successors -- not a list X is confined to.
Nothing here selects positions by whether evidence was once found for them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "keys.json"


@dataclass
class Key:
    x: float
    strands: list[str] = field(default_factory=list)
    successors: list[tuple[float, float]] = field(default_factory=list)
    # Where this key carries no text of its own, the last preceding key that
    # does. Its framework is what stands at this position.
    carried_from: float | None = None
    carried: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        """The key's own text, empty where it has none."""
        return " || ".join(self.strands) if self.strands else ""

    @property
    def bare(self) -> bool:
        """True where the key carries no framework text of its own."""
        return not self.strands

    @property
    def standing(self) -> list[str]:
        """The framework standing at this position, owned or carried."""
        return self.strands or self.carried

    @property
    def standing_text(self) -> str:
        return " || ".join(self.standing) if self.standing else ""

    @property
    def gap_to_carrier(self) -> float | None:
        if self.carried_from is None:
            return None
        return round(self.x - self.carried_from, 6)


@dataclass
class Edge:
    source: float
    target: float
    gap: float
    stated: bool = True

    @property
    def implied_gap(self) -> float:
        return round(self.target - self.source, 6)

    @property
    def gap_agrees(self) -> bool:
        return abs(self.implied_gap - self.gap) <= 0.005

    @property
    def default(self) -> bool:
        """Set by SFO.__init__ for the backbone; see there."""
        return getattr(self, "_default", False)


@lru_cache(maxsize=1)
def _raw() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


class SFO:
    """The key structure: 400 positions, their text, and their relations."""

    def __init__(self) -> None:
        raw = _raw()
        self.keys: dict[float, Key] = {}
        for record in raw["keys"]:
            self.keys[record["x"]] = Key(
                x=record["x"],
                strands=list(record["strands"]),
                successors=[(float(t), float(g)) for t, g in record["successors"]],
            )
        self.order = sorted(self.keys)
        self.next_x = dict(zip(self.order, self.order[1:]))

        # Carry-over: a key with no text of its own stands under the framework of
        # the last preceding key that has one. The distinction is kept -- carried
        # is never presented as owned.
        last_x, last_strands = None, []
        for x in self.order:
            key = self.keys[x]
            if key.strands:
                last_x, last_strands = x, key.strands
            elif last_x is not None:
                key.carried_from = last_x
                key.carried = list(last_strands)

        self.edges: list[Edge] = []
        for key in self.keys.values():
            for target, gap in key.successors:
                self.edges.append(Edge(key.x, target, gap))
        for record in raw.get("implied_backbone", []):
            self.edges.append(
                Edge(record["from"], record["to"], record["gap"], stated=False)
            )
        for edge in self.edges:
            edge._default = self.next_x.get(edge.source) == edge.target

        self.out: dict[float, list[Edge]] = {}
        self.into: dict[float, list[Edge]] = {}
        for edge in self.edges:
            self.out.setdefault(edge.source, []).append(edge)
            self.into.setdefault(edge.target, []).append(edge)

        self.errata = raw.get("errata_applied", [])

    def __len__(self) -> int:
        return len(self.keys)

    @property
    def span(self) -> tuple[float, float]:
        return self.order[0], self.order[-1]

    def successors(self, x: float) -> list[Edge]:
        return self.out.get(x, [])

    def predecessors(self, x: float) -> list[Edge]:
        return self.into.get(x, [])

    def default_edge(self, x: float) -> Edge | None:
        target = self.next_x.get(x)
        if target is None:
            return None
        return next((e for e in self.out.get(x, []) if e.target == target), None)

    def nearest(self, x: float) -> Key:
        """The key standing at or before X -- what holds at an arbitrary position."""
        best = None
        for key in self.order:
            if key <= x:
                best = key
            else:
                break
        return self.keys[best if best is not None else self.order[0]]

    def backbone(self) -> list[Edge]:
        return [e for e in self.edges if e.default]

    def long_range(self) -> list[Edge]:
        return [e for e in self.edges if not e.default]

    def roots(self) -> list[float]:
        return [x for x in self.order if not self.into.get(x)]

    def sinks(self) -> list[float]:
        return [x for x in self.order if not self.out.get(x)]

    def disputed(self) -> list[Edge]:
        return [e for e in self.edges if not e.gap_agrees]
