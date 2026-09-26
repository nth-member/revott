"""The SFO: what X ranges over, and the structure carried on it.

X is free and continuous. The 400 BB keys are a structure on it -- positions
that carry framework text and name successors -- not a list X is confined to.
Nothing here selects positions by whether evidence was once found for them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "keys.json"

# The layers of a key's text.
#
#   marking      the clearly marked context: "Primordial Follicles"
#   apocalypse   parallel primary contexts, of equal standing with the marking:
#                nS seal, nT trumpet, nV vial, nH horns, with suffix "hidden"
#                for the hidden series -- "6T" is the sixth trumpet
#   derived      embedded sub-contexts derived on another scale: "-25.99dysi".
#                Never led with.
#
# A key with no primary layer of its own -- no text, or a derived sub-context
# only -- stands under the primary layers of the last preceding key that has
# any, marked as carried and never presented as owned.
APOCALYPSE = re.compile(r"(?<![\w.])(\d+)([STVH])(hidden)?(?![\w])")
DERIVED = re.compile(r"^\s*(-?\d+(?:\.\d+)?dysi)\s*(?:\.\.\.)?\s*(.*)$")
_SERIES = {"S": "seal", "T": "trumpet", "V": "vial", "H": "horns"}
_ORD = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
        6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth"}


def apocalypse_name(marker: str) -> str:
    """'6T' -> 'sixth trumpet'; '7Shidden' -> 'seventh seal (hidden)'; '10H' -> 'ten horns'."""
    m = APOCALYPSE.fullmatch(marker)
    if not m:
        return marker
    n, s, hidden = int(m.group(1)), m.group(2), m.group(3)
    if s == "H":
        name = f"{n} horns" if n not in (10,) else "ten horns"
    else:
        name = f"{_ORD.get(n, str(n) + 'th')} {_SERIES[s]}"
    return name + (" (hidden)" if hidden else "")


def layers(strands: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Split a key's strands into (marking, apocalypse, derived)."""
    marks, apoc, derived = [], [], []
    for st in strands:
        g = DERIVED.match(st)
        if g:
            derived.append(g.group(1))
            st = g.group(2)
        apoc += ["".join(t) for t in APOCALYPSE.findall(st)]
        if APOCALYPSE.sub("", st).strip(" .|"):
            marks.append(st.strip())
    return marks, apoc, derived


@dataclass
class Key:
    x: float
    strands: list[str] = field(default_factory=list)
    successors: list[tuple[float, float]] = field(default_factory=list)
    # Where this key carries no text of its own, the last preceding key that
    # does. Its framework is what stands at this position.
    carried_from: float | None = None
    carried: list[str] = field(default_factory=list)
    # The layered reading, set by SFO.__init__.
    marks: list[str] = field(default_factory=list)
    apoc: list[str] = field(default_factory=list)
    derived: list[str] = field(default_factory=list)
    primary_from: float | None = None      # set where the primary layers are carried
    carried_marks: list[str] = field(default_factory=list)
    carried_apoc: list[str] = field(default_factory=list)

    @property
    def has_primary(self) -> bool:
        return bool(self.marks or self.apoc)

    @property
    def primary_marks(self) -> list[str]:
        return self.marks if self.has_primary else self.carried_marks

    @property
    def primary_apoc(self) -> list[str]:
        return self.apoc if self.has_primary else self.carried_apoc

    @property
    def reading(self) -> str:
        """The key read in layers: marking, then the apocalypse sequence, then derived."""
        parts = list(self.primary_marks)
        parts += [f"{a} = {apocalypse_name(a)}" for a in self.primary_apoc]
        text = " || ".join(parts) if parts else "—"
        if not self.has_primary and self.primary_from is not None:
            text += f"  [carried from {self.primary_from:g}]"
        if self.derived:
            text += "  (derived: " + ", ".join(self.derived) + ")"
        return text

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

        # The layered reading, with carry-over of the primary layers.
        last = None
        for x in self.order:
            key = self.keys[x]
            key.marks, key.apoc, key.derived = layers(key.strands)
            if key.has_primary:
                last = key
            elif last is not None:
                key.primary_from = last.x
                key.carried_marks = list(last.marks)
                key.carried_apoc = list(last.apoc)

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
