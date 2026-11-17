"""Route tests of the search filters (M13): FR-03, FR-04, FR-07, D-04, D-28, D-29.

AC-01 needs the live embedding model and is checked by hand (docs/design.md, Test policy).
The fake embedder matches by shared words, so the assignments share words with the query.
"""

from builders import (
    add_assignment,
    add_leaves,
    add_project,
    created_id,
    parse,
    result_count,
    result_ids,
)

QUERY = "fractional jitter loop"
TEXT = "Led the fractional jitter loop design"
LEAVES = {"PLL": "Phase-locked loop", "SRAM": "Static memory"}


def add_person(client, name, team="Analog", career_level="Senior") -> str:
    """Post a new employee with the given team and career level and return its ID."""
    response = client.post(
        "/employees",
        data={
            "name": name,
            "job_title": "Design Engineer",
            "career_level": career_level,
            "team": team,
            "skill_gaps": "",
        },
        follow_redirects=False,
    )
    return created_id(response)


def add_flag(client, employee_id, leaf_id, flag):
    """Post a flag and check that it is accepted."""
    response = client.post(
        f"/employees/{employee_id}/flags",
        data={"leaf_id": leaf_id, "flag": flag},
        follow_redirects=False,
    )
    assert response.status_code == 303


def search(client, **params):
    """Call the search page with the given parameters and return its HTML."""
    response = client.get("/search", params=params)
    assert response.status_code == 200
    return response.text


def lead_pll(client, employee_id, leaf_id, times=1):
    """Give an employee `times` lead assignments on a leaf, each on its own project."""
    for number in range(times):
        project_id = add_project(client, name=f"Invented Chip {employee_id} {number}")
        add_assignment(client, project_id, employee_id, leaf_id, TEXT, participation="lead")


def test_fr_03_search_page_offers_team_career_level_and_leaf_with_minimum_level(client):
    leaves = add_leaves(client, LEAVES)

    response = client.get("/search")

    assert response.status_code == 200
    root = parse(response.text)
    forms = [e for e in root.descendants() if e.tag == "form" and e.attrs.get("method", "").lower() == "get"]
    assert forms, "the filters are one GET form"
    named = {}
    for form in forms:
        for element in form.descendants():
            if "name" in element.attrs:
                named.setdefault(element.attrs["name"], element)
    for field in ("team", "career_level", "leaf_id", "min_level"):
        assert field in named, field
    assert named["leaf_id"].tag == "select"
    options = {o.attrs["value"] for o in named["leaf_id"].descendants() if o.tag == "option" and o.attrs.get("value")}
    assert options == set(leaves.values())


def test_fr_04_team_filter_ranks_only_employees_of_that_team(client):
    leaves = add_leaves(client, LEAVES)
    ada = add_person(client, "Ada Invented", team="Clocking")
    ben = add_person(client, "Ben Invented", team="Memory")
    lead_pll(client, ada, leaves["PLL"])
    lead_pll(client, ben, leaves["PLL"])
    assert set(result_ids(search(client, q=QUERY))) == {ada, ben}

    html = search(client, q=QUERY, team="Clocking")

    assert result_ids(html) == [ada]
    assert result_count(html) == "1"


def test_fr_04_leaf_filter_keeps_only_employees_at_the_minimum_level_or_higher(client):
    leaves = add_leaves(client, LEAVES)
    lead = add_person(client, "Ada Invented")
    senior_lead = add_person(client, "Dan Invented")
    member = add_person(client, "Ben Invented")
    other_leaf = add_person(client, "Cy Invented")
    lead_pll(client, lead, leaves["PLL"], times=1)
    lead_pll(client, senior_lead, leaves["PLL"], times=3)
    project_id = add_project(client, name="Invented Member Chip")
    add_assignment(client, project_id, member, leaves["PLL"], TEXT, participation="member")
    add_assignment(client, project_id, other_leaf, leaves["SRAM"], TEXT, participation="lead")

    html = search(client, q=QUERY, leaf_id=leaves["PLL"], min_level="3")

    assert set(result_ids(html)) == {lead, senior_lead}


def test_fr_03_aware_and_expert_flags_count_as_levels_1_and_5_in_the_filter(client):
    leaves = add_leaves(client, LEAVES)
    leaf = leaves["PLL"]
    aware = add_person(client, "Ann Invented")
    expert = add_person(client, "Bob Invented")
    member = add_person(client, "Cat Invented")
    add_flag(client, aware, leaf, "aware")
    add_flag(client, expert, leaf, "expert")
    project_id = add_project(client)
    add_assignment(client, project_id, member, leaf, TEXT, participation="member")

    def listed(minimum):
        return set(result_ids(search(client, leaf_id=leaf, min_level=minimum)))

    assert listed("1") == {aware, expert, member}
    assert listed("2") == {expert, member}
    assert listed("5") == {expert}


def test_fr_04_employee_must_meet_all_set_filters(client):
    leaves = add_leaves(client, LEAVES)
    leaf = leaves["PLL"]
    match = add_person(client, "Ada Invented", team="Clocking", career_level="Senior")
    wrong_level = add_person(client, "Ben Invented", team="Clocking", career_level="Junior")
    wrong_team = add_person(client, "Cy Invented", team="Memory", career_level="Senior")
    low_skill = add_person(client, "Dee Invented", team="Clocking", career_level="Senior")
    for employee_id in (match, wrong_level, wrong_team):
        lead_pll(client, employee_id, leaf)
    project_id = add_project(client, name="Invented Member Chip")
    add_assignment(client, project_id, low_skill, leaf, TEXT, participation="member")

    html = search(
        client,
        q=QUERY,
        team="Clocking",
        career_level="Senior",
        leaf_id=leaf,
        min_level="3",
    )

    assert result_ids(html) == [match]


def test_fr_07_filters_with_no_query_list_all_matching_employees_by_name(client):
    add_leaves(client, LEAVES)
    zed = add_person(client, "Zed Invented", team="Clocking")
    amy = add_person(client, "Amy Invented", team="Clocking")
    mia = add_person(client, "Mia Invented", team="Clocking")
    add_person(client, "Ben Invented", team="Memory")

    html = search(client, team="Clocking")

    assert result_ids(html) == [amy, mia, zed]
    assert result_count(html) == "3"
