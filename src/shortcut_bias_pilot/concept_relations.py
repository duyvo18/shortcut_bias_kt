"""All-skill relation checks used by the LGT inference intervention."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable


@dataclass(frozen=True)
class ConceptRelations:
    """A small directed hierarchy; an empty graph means exact-only matching."""

    parents: dict[str, frozenset[str]]
    mode: str = "exact_unrelated"

    @classmethod
    def exact_only(cls) -> "ConceptRelations":
        return cls({}, "exact_unrelated")

    @classmethod
    def from_parent_pairs(cls, pairs: Iterable[tuple[object, object]]) -> "ConceptRelations":
        parents: dict[str, set[str]] = {}
        for child, parent in pairs:
            if child is None or parent is None:
                continue
            parents.setdefault(str(child), set()).add(str(parent))
        return cls({key: frozenset(value) for key, value in parents.items()}, "hierarchy_aware")

    def ancestors(self, concept: object) -> set[str]:
        todo = list(self.parents.get(str(concept), ()))
        seen: set[str] = set()
        while todo:
            value = todo.pop()
            if value not in seen:
                seen.add(value)
                todo.extend(self.parents.get(value, ()))
        return seen

    def relation(self, source: object, target: object) -> str:
        source, target = str(source), str(target)
        if source == target:
            return "same"
        if self.mode == "exact_unrelated":
            return "unrelated"
        source_anc, target_anc = self.ancestors(source), self.ancestors(target)
        if target in source_anc:
            return "descendant"
        if source in target_anc:
            return "ancestor"
        if source_anc & target_anc:
            return "sibling"
        return "unrelated"

    def event_is_unrelated(self, source_skills: Iterable[object], target_skills: Iterable[object]) -> tuple[bool, list[str]]:
        relations = [self.relation(source, target) for source, target in product(source_skills, target_skills)]
        return bool(relations) and all(value == "unrelated" for value in relations), relations
