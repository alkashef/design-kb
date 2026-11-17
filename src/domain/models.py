"""The data classes and errors of the domain (docs/design.md, Interfaces)."""

from dataclasses import dataclass
from typing import Optional


class EmbeddingUnavailable(Exception):
    """Raised by an embedder when the embedding model does not answer (D-27)."""


@dataclass
class Employee:
    """An IC design team member (spec section 2, D-25)."""

    id: str
    name: str
    job_title: str
    career_level: str
    team: str
    skill_gaps: str = ""


@dataclass
class Project:
    """A project that employees worked on."""

    id: str
    name: str
    description: str
    year: int
    process_technology: str


@dataclass
class Node:
    """A node of the skill tree; an empty parent_id marks a top-level node (D-06)."""

    id: str
    parent_id: str
    name: str
    description: str
    position: int


@dataclass
class Assignment:
    """The work of one employee in one project on one leaf; participation is lead or member."""

    id: str
    employee_id: str
    project_id: str
    leaf_id: str
    participation: str
    description: str


@dataclass
class Flag:
    """The aware or expert flag of one employee on one leaf."""

    employee_id: str
    leaf_id: str
    flag: str


@dataclass
class Threshold:
    """The count ranges of one level; None in a to field means no upper limit (FR-32)."""

    level: int
    lead_from: int
    lead_to: Optional[int]
    member_from: int
    member_to: Optional[int]
