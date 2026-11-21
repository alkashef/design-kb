"""The engineer service: lists, shows, creates, edits and deletes engineers (FR-10, FR-20, FR-28)."""

import logging
from dataclasses import dataclass
from typing import Dict, List

from src.domain import levels, skill_tree
from src.domain.models import CAREER_LEVELS, Engineer
from src.services.thresholds import ThresholdService

logger = logging.getLogger(__name__)

ID_PREFIX = "E-"
TOP_SKILL_COUNT = 2
TOP_LEVEL_GROUP = "Top level"


class EngineerError(Exception):
    """Raised when an entry is rejected; the message is shown to the user."""


class UnknownEngineer(Exception):
    """Raised when an engineer ID is not in the store."""


@dataclass
class EngineerPage:
    """One page of the Engineers list."""

    rows: List[Engineer]
    page: int
    page_count: int
    total: int


@dataclass
class SkillLevel:
    """The level of an engineer in one leaf and where it comes from (FR-11)."""

    leaf_id: str
    name: str
    level: int
    source: str


@dataclass
class SkillGroup:
    """The leaves under one parent path, with the level of the engineer in each."""

    path: str
    leaves: List[SkillLevel]


def _plural(count: int, word: str) -> str:
    """Return count and the word, such as '1 project' or '3 projects'."""
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _level_source(lead_count: int, member_count: int, flag: str, level: int) -> str:
    """Return the text that tells where the level comes from."""
    if flag == "expert":
        return "Expert flag"
    if lead_count + member_count > 0:
        parts = []
        if lead_count:
            parts.append(f"lead in {_plural(lead_count, 'project')}")
        if member_count:
            parts.append(f"member in {_plural(member_count, 'project')}")
        return ("Computed: " if level else "No level from ") + ", ".join(parts)
    if flag == "aware":
        return "Aware flag"
    return "No projects, no flag"


class EngineerService:
    """Reads and changes engineers through the store."""

    def __init__(self, store, page_size: int, indexing):
        """Use store (a LanceStore or a fake), the rows on one page and indexing for the vectors."""
        self._store = store
        self._page_size = page_size
        self._indexing = indexing

    def teams(self) -> List[str]:
        """Return the distinct team names, sorted."""
        return sorted({e.team for e in self._store.list_engineers() if e.team})

    def list(
        self, text: str = "", team: str = "", career_level: str = "", page: int = 1
    ) -> EngineerPage:
        """Return one page of the engineers that match the filters, ordered by ID."""
        needle = text.strip().lower()
        matches = [
            e
            for e in sorted(self._store.list_engineers(), key=lambda e: e.id)
            if (not needle or needle in e.name.lower() or needle in e.id.lower())
            and (not team or e.team == team)
            and (not career_level or e.career_level == career_level)
        ]
        page_count = max(1, -(-len(matches) // self._page_size))
        page = min(max(page, 1), page_count)
        start = (page - 1) * self._page_size
        rows = matches[start : start + self._page_size]
        return EngineerPage(rows, page, page_count, len(matches))

    def get(self, engineer_id: str) -> Engineer:
        """Return the engineer, or raise UnknownEngineer."""
        for engineer in self._store.list_engineers():
            if engineer.id == engineer_id:
                return engineer
        raise UnknownEngineer(engineer_id)

    def add(self, name: str, job_title: str, career_level: str, team: str, skill_gaps: str) -> str:
        """Add an engineer with the next free ID and return the ID."""
        engineer = self._build(self._next_id(), name, job_title, career_level, team, skill_gaps)
        vector = self._indexing.embed_profile(engineer)
        self._store.add_engineer(engineer)
        self._indexing.save_profile(engineer, vector)
        logger.info("Added an engineer.")
        return engineer.id

    def save(
        self,
        engineer_id: str,
        name: str,
        job_title: str,
        career_level: str,
        team: str,
        skill_gaps: str,
    ) -> None:
        """Change the fields of an engineer."""
        self.get(engineer_id)
        engineer = self._build(engineer_id, name, job_title, career_level, team, skill_gaps)
        vector = self._indexing.embed_profile(engineer)
        self._store.update_engineer(engineer)
        self._indexing.save_profile(engineer, vector)

    def delete(self, engineer_id: str) -> None:
        """Delete an engineer."""
        self.get(engineer_id)
        self._store.delete_assignments_of_engineer(engineer_id)
        self._store.delete_flags_of_engineer(engineer_id)
        self._store.delete_engineer(engineer_id)
        self._indexing.delete_engineer_vectors(engineer_id)
        logger.info("Deleted an engineer.")

    def skill_groups(self, engineer_id: str) -> List[SkillGroup]:
        """Return the levels of the engineer, grouped by parent path, in tree order (FR-11)."""
        nodes = self._store.list_nodes()
        assignments = self._store.list_assignments()
        levels_by_leaf = self._levels_of(engineer_id, nodes, assignments, self._store.list_flags())
        groups: Dict[str, SkillGroup] = {}
        for node, _depth in skill_tree.outline(nodes):
            if node.id not in levels_by_leaf:
                continue
            parent_path = skill_tree.path(nodes, node.parent_id) or TOP_LEVEL_GROUP
            group = groups.setdefault(parent_path, SkillGroup(parent_path, []))
            group.leaves.append(levels_by_leaf[node.id])
        return list(groups.values())

    def top_skills(self, engineer_ids: List[str]) -> Dict[str, List[SkillLevel]]:
        """Return the highest levels (at most TOP_SKILL_COUNT) of each engineer, highest first."""
        nodes = self._store.list_nodes()
        assignments = self._store.list_assignments()
        flags = self._store.list_flags()
        result = {}
        for engineer_id in engineer_ids:
            reached = [
                s
                for s in self._levels_of(engineer_id, nodes, assignments, flags).values()
                if s.level > 0
            ]
            reached.sort(key=lambda s: -s.level)
            result[engineer_id] = reached[:TOP_SKILL_COUNT]
        return result

    def levels_in(self, engineer_id: str, leaf_ids: List[str]) -> List[SkillLevel]:
        """Return the level of the engineer in each of the given leaves, in the order of leaf_ids."""
        by_leaf = self._levels_of(
            engineer_id,
            self._store.list_nodes(),
            self._store.list_assignments(),
            self._store.list_flags(),
        )
        return [by_leaf[leaf_id] for leaf_id in leaf_ids if leaf_id in by_leaf]

    def leaf_options(self) -> List[tuple]:
        """Return (leaf ID, path) of each leaf, in tree order, for a filter list."""
        nodes = self._store.list_nodes()
        return [
            (node.id, skill_tree.path(nodes, node.id))
            for node, _depth in skill_tree.outline(nodes)
            if skill_tree.is_leaf(nodes, node.id)
        ]

    def matching(
        self, team: str = "", career_level: str = "", leaf_id: str = "", min_level: int = 1
    ) -> List[Engineer]:
        """Return the engineers that meet every set filter, sorted by name (D-04, step 1).

        A leaf filter keeps the engineers whose level in that leaf is at least min_level.
        """
        nodes = self._store.list_nodes()
        assignments = self._store.list_assignments()
        flags = self._store.list_flags()
        matches = []
        for engineer in self._store.list_engineers():
            if (team and engineer.team != team) or (
                career_level and engineer.career_level != career_level
            ):
                continue
            if leaf_id:
                by_leaf = self._levels_of(engineer.id, nodes, assignments, flags)
                if leaf_id not in by_leaf or by_leaf[leaf_id].level < max(min_level, 1):
                    continue
            matches.append(engineer)
        return sorted(matches, key=lambda e: (e.name.lower(), e.id))

    def _levels_of(self, engineer_id, nodes, assignments, flags) -> Dict[str, SkillLevel]:
        """Return the SkillLevel of the engineer in each leaf, in tree order."""
        flag_of = {f.leaf_id: f.flag for f in flags if f.engineer_id == engineer_id}
        mine = [a for a in assignments if a.engineer_id == engineer_id]
        thresholds = ThresholdService(self._store).current()
        result = {}
        for node, _depth in skill_tree.outline(nodes):
            if not skill_tree.is_leaf(nodes, node.id):
                continue
            lead = sum(1 for a in mine if a.leaf_id == node.id and a.participation == "lead")
            member = sum(1 for a in mine if a.leaf_id == node.id and a.participation == "member")
            flag = flag_of.get(node.id, "")
            level = levels.effective_level(lead, member, flag or None, thresholds) or 0
            source = _level_source(lead, member, flag, level)
            result[node.id] = SkillLevel(node.id, node.name, level, source)
        return result

    def _next_id(self) -> str:
        """Return the ID after the highest one in use, such as E-0003."""
        numbers = [
            int(e.id[len(ID_PREFIX) :])
            for e in self._store.list_engineers()
            if e.id.startswith(ID_PREFIX) and e.id[len(ID_PREFIX) :].isdigit()
        ]
        return f"{ID_PREFIX}{max(numbers, default=0) + 1:04d}"

    @staticmethod
    def _build(
        engineer_id: str, name: str, job_title: str, career_level: str, team: str, skill_gaps: str
    ) -> Engineer:
        """Return the checked Engineer, or raise EngineerError."""
        if not name.strip():
            raise EngineerError("The name is required.")
        if career_level not in CAREER_LEVELS:
            raise EngineerError("Choose a career level from the list.")
        return Engineer(
            engineer_id,
            name.strip(),
            job_title.strip(),
            career_level,
            team.strip(),
            skill_gaps.strip(),
        )
