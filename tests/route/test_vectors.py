"""Route tests of the vectors (M10): D-13 and D-27.

The store is read with `list_assignment_vectors()` and `list_profile_vectors()` (D-35). The texts
that the fake embedder received are in `embedder.calls` (docs/design.md, Test policy).
"""

import pytest

from fakes import FakeEmbedder
LEAF_PATH_PREFIX = "Circuit design / Clocking"
PARTICIPATION_LINE = 3


def created_id(response) -> str:
    """Check that a POST redirected, and return the last part of the address it redirects to."""
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_node(client, name, description="", parent_id=""):
    """Post a new skill tree node and return its ID."""
    response = client.post(
        "/skill-tree/nodes",
        data={"parent_id": parent_id, "name": name, "description": description},
        follow_redirects=False,
    )
    return created_id(response)


def add_pll_leaf(client) -> str:
    """Add the branch Circuit design / Clocking / PLL and return the ID of the leaf PLL."""
    top_id = add_node(client, "Circuit design")
    clocking_id = add_node(client, "Clocking", parent_id=top_id)
    return add_node(client, "PLL", description="Phase-locked loop", parent_id=clocking_id)


def employee_form(name="Ada Invented", team="Analog", skill_gaps=""):
    """Return the form fields of an employee."""
    return {
        "name": name,
        "job_title": "Design Engineer",
        "career_level": "Senior",
        "team": team,
        "skill_gaps": skill_gaps,
    }


def add_employee(client, **fields) -> str:
    """Post a new employee and return its ID."""
    response = client.post("/employees", data=employee_form(**fields), follow_redirects=False)
    return created_id(response)


def save_employee(client, employee_id, **fields):
    """Post the changed fields of an employee and check the redirect."""
    response = client.post(
        f"/employees/{employee_id}", data=employee_form(**fields), follow_redirects=False
    )
    assert response.status_code == 303


def project_form(process_technology="TSMC 7nm"):
    """Return the form fields of a project."""
    return {
        "name": "Invented SerDes",
        "description": "An invented test chip",
        "year": "2024",
        "process_technology": process_technology,
    }


def add_project(client, **fields) -> str:
    """Post a new project and return its ID."""
    response = client.post("/projects", data=project_form(**fields), follow_redirects=False)
    return created_id(response)


def post_assignment(client, project_id, employee_id, leaf_id, description, participation="lead"):
    """Post a new assignment of a project and return the response, without following redirects."""
    return client.post(
        f"/projects/{project_id}/assignments",
        data={
            "employee_id": employee_id,
            "leaf_id": leaf_id,
            "participation": participation,
            "description": description,
        },
        follow_redirects=False,
    )


def add_assignment(client, store, project_id, employee_id, leaf_id, description, **fields) -> str:
    """Post a new assignment, check the redirect and return the ID of the new assignment."""
    before = {assignment.id for assignment in store.list_assignments()}
    response = post_assignment(client, project_id, employee_id, leaf_id, description, **fields)
    assert response.status_code == 303
    new_ids = {assignment.id for assignment in store.list_assignments()} - before
    assert len(new_ids) == 1
    return new_ids.pop()


def expected_lines(
    description,
    participation="lead",
    leaf_name="PLL",
    process_technology="TSMC 7nm",
) -> list[str]:
    """Return the 6 lines of an assignment vector on the leaf PLL (docs/design.md, Data storage)."""
    return [
        leaf_name,
        "Phase-locked loop",
        f"{LEAF_PATH_PREFIX} / {leaf_name}",
        participation,
        description,
        process_technology,
    ]


def text_lines(text) -> list[str]:
    """Split a vector text into its lines, with the participation line in lower case."""
    lines = text.split("\n")
    if len(lines) > PARTICIPATION_LINE:
        lines[PARTICIPATION_LINE] = lines[PARTICIPATION_LINE].lower()
    return lines


def assignment_vector_lines(store) -> dict[str, list[list[str]]]:
    """Return the lines of the text of each stored assignment vector, by assignment ID."""
    texts: dict[str, list[list[str]]] = {}
    for row in store.list_assignment_vectors():
        texts.setdefault(row.assignment_id, []).append(text_lines(row.text))
    return texts


def profile_vector_texts(store, employee_id) -> list[str]:
    """Return the texts of the stored profile vectors of one employee."""
    return [row.text for row in store.list_profile_vectors() if row.employee_id == employee_id]


def embedded_texts(embedder, start=0) -> list[str]:
    """Return every text that the fake embedder received, from call number `start` on."""
    return [text for call in embedder.calls[start:] for text in call]


def embedded_lines(embedder, start=0) -> list[list[str]]:
    """Return the lines of every text that the fake embedder received, from call `start` on."""
    return [text_lines(text) for text in embedded_texts(embedder, start)]


def test_d_13_new_assignment_embeds_its_text(client, store):
    leaf_id = add_pll_leaf(client)
    employee_id = add_employee(client)
    project_id = add_project(client)

    assignment_id = add_assignment(
        client, store, project_id, employee_id, leaf_id, "Led the fractional-N loop design"
    )

    rows = [row for row in store.list_assignment_vectors() if row.assignment_id == assignment_id]
    assert len(rows) == 1
    assert rows[0].employee_id == employee_id
    assert text_lines(rows[0].text) == expected_lines("Led the fractional-N loop design")
    expected_vector = FakeEmbedder().embed([rows[0].text])[0]
    assert list(rows[0].vector) == pytest.approx(expected_vector, abs=1e-6)


def test_d_13_changed_process_technology_embeds_the_assignments_of_the_project_again(
    client, store, embedder
):
    leaf_id = add_pll_leaf(client)
    lead_id = add_employee(client, name="Ada Invented")
    member_id = add_employee(client, name="Bruno Invented")
    project_id = add_project(client, process_technology="TSMC 7nm")
    first_id = add_assignment(client, store, project_id, lead_id, leaf_id, "Led the loop")
    second_id = add_assignment(
        client, store, project_id, member_id, leaf_id, "Measured the jitter", participation="member"
    )
    start = len(embedder.calls)

    response = client.post(
        f"/projects/{project_id}",
        data=project_form(process_technology="Samsung 5nm"),
        follow_redirects=False,
    )

    assert response.status_code == 303
    first_lines = expected_lines("Led the loop", process_technology="Samsung 5nm")
    second_lines = expected_lines(
        "Measured the jitter", participation="member", process_technology="Samsung 5nm"
    )
    assert assignment_vector_lines(store) == {first_id: [first_lines], second_id: [second_lines]}
    assert first_lines in embedded_lines(embedder, start)
    assert second_lines in embedded_lines(embedder, start)


def test_d_13_changed_leaf_name_embeds_its_assignments_again(client, store, embedder):
    leaf_id = add_pll_leaf(client)
    employee_id = add_employee(client)
    project_id = add_project(client)
    assignment_id = add_assignment(client, store, project_id, employee_id, leaf_id, "Led the loop")
    start = len(embedder.calls)

    response = client.post(
        f"/skill-tree/nodes/{leaf_id}",
        data={"name": "Fractional-N PLL", "description": "Phase-locked loop"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    lines = expected_lines("Led the loop", leaf_name="Fractional-N PLL")
    assert assignment_vector_lines(store) == {assignment_id: [lines]}
    assert lines in embedded_lines(embedder, start)


def test_d_13_changed_skill_gaps_embed_the_profile_again(client, store, embedder):
    employee_id = add_employee(client, skill_gaps="Needs SerDes equalization")
    start = len(embedder.calls)

    save_employee(client, employee_id, skill_gaps="Needs layout of an LDO")

    assert profile_vector_texts(store, employee_id) == ["Needs layout of an LDO"]
    assert "Needs layout of an LDO" in embedded_texts(embedder, start)


def test_d_13_changed_team_embeds_nothing(client, store, embedder):
    leaf_id = add_pll_leaf(client)
    employee_id = add_employee(client, team="Analog", skill_gaps="Needs SerDes equalization")
    project_id = add_project(client)
    assignment_id = add_assignment(client, store, project_id, employee_id, leaf_id, "Led the loop")
    assert profile_vector_texts(store, employee_id) == ["Needs SerDes equalization"]
    assert assignment_id in assignment_vector_lines(store)
    start = len(embedder.calls)

    save_employee(client, employee_id, team="Mixed-signal", skill_gaps="Needs SerDes equalization")

    assert embedded_texts(embedder, start) == []


def test_d_27_empty_skill_gaps_embed_no_profile(client, store):
    employee_id = add_employee(client, skill_gaps="Needs SerDes equalization")
    assert profile_vector_texts(store, employee_id) == ["Needs SerDes equalization"]

    save_employee(client, employee_id, skill_gaps="")

    assert profile_vector_texts(store, employee_id) == []


def test_d_27_model_that_does_not_answer_gives_503_and_saves_nothing(client, store, embedder):
    leaf_id = add_pll_leaf(client)
    employee_id = add_employee(client)
    project_id = add_project(client)
    embedder.available = False

    response = post_assignment(client, project_id, employee_id, leaf_id, "Led the loop")

    assert response.status_code == 503
    assert 'role="alert"' in response.text
    assert store.list_assignments() == []
    assert store.list_assignment_vectors() == []
