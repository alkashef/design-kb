"""Route tests of the seed data load (M11): NFR-04, NFR-05, D-26 and D-27.

The store is read with its public lists (docs/design.md, Interfaces). The expected values come from
`seed_data.build()`.
"""

from html.parser import HTMLParser

from fastapi.testclient import TestClient

from src.app import AppOptions, create_app
from src.domain import seed_data
from src.domain.models import Employee
from fakes import FAKE_VECTOR_SIZE

EXPECTED_EMPLOYEES = 40
EXPECTED_PROJECTS = 15
EXPECTED_LEVEL_BY_FLAG = {"aware": 1, "expert": 5}


class LevelMarkers(HTMLParser):
    """Collects the level of each leaf that a page shows."""

    def __init__(self):
        """Start with nothing collected."""
        super().__init__()
        self.levels: dict[str, int] = {}

    def handle_starttag(self, tag, attrs):
        """Keep each element that has a leaf ID and a level."""
        attributes = dict(attrs)
        if "data-leaf-id" in attributes and "data-level" in attributes:
            self.levels[attributes["data-leaf-id"]] = int(attributes["data-level"])


class ProjectRows(HTMLParser):
    """Collects the IDs of the project rows of a page."""

    def __init__(self):
        """Start with nothing collected."""
        super().__init__()
        self.project_ids: list[str] = []

    def handle_starttag(self, tag, attrs):
        """Keep each data-project-id."""
        attributes = dict(attrs)
        if "data-project-id" in attributes:
            self.project_ids.append(attributes["data-project-id"])


def test_nfr_04_first_start_loads_the_seed_data_into_an_empty_store(seeded_client, store):
    seed = seed_data.build()

    assert len(store.list_employees()) == EXPECTED_EMPLOYEES
    assert {e.id for e in store.list_employees()} == {e.id for e in seed.employees}
    assert {n.id for n in store.list_nodes()} == {n.id for n in seed.nodes}
    assert {a.id for a in store.list_assignments()} == {a.id for a in seed.assignments}
    page = ProjectRows()
    page.feed(seeded_client.get("/projects").text)
    assert set(page.project_ids) == {p.id for p in seed.projects}
    assert len(seed.projects) == EXPECTED_PROJECTS


def test_nfr_04_first_start_embeds_one_vector_per_assignment_and_one_profile_per_skill_gap(
    seeded_client, store
):
    seed = seed_data.build()

    vectors = store.list_assignment_vectors()
    assert {v.assignment_id for v in vectors} == {a.id for a in seed.assignments}
    assert len(vectors) == len(seed.assignments)
    assert all(len(v.vector) == FAKE_VECTOR_SIZE for v in vectors)
    with_gaps = {e.id for e in seed.employees if e.skill_gaps and e.skill_gaps.strip()}
    assert {p.employee_id for p in store.list_profile_vectors()} == with_gaps


def test_nfr_05_first_start_shows_the_flag_levels_of_the_seed_on_the_profile(seeded_client):
    seed = seed_data.build()
    assert seed.flags, "the seed holds at least one flag to show"

    for flag in seed.flags:
        page = LevelMarkers()
        page.feed(seeded_client.get(f"/employees/{flag.employee_id}").text)
        has_assignment = any(
            a.employee_id == flag.employee_id and a.leaf_id == flag.leaf_id
            for a in seed.assignments
        )
        if flag.flag == "expert" or not has_assignment:
            assert page.levels[flag.leaf_id] == EXPECTED_LEVEL_BY_FLAG[flag.flag]


def test_nfr_04_start_with_employees_in_the_store_loads_nothing(store, embedder):
    store.add_employee(
        Employee(
            id="E-0001",
            name="Kept Invented",
            job_title="Design Engineer",
            career_level="Mid",
            team="Digital",
            skill_gaps="",
        )
    )
    options = AppOptions(search_result_limit=10, page_size=10, load_seed=True)

    with TestClient(create_app(store, embedder, options)):
        pass

    assert [e.id for e in store.list_employees()] == ["E-0001"]
    assert store.list_nodes() == []
    assert store.list_assignments() == []
    assert store.list_assignment_vectors() == []

