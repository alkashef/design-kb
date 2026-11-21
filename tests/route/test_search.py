"""Route tests of the experience search (M12): FR-01, FR-05, D-10, D-11, D-14, D-18, D-28.

FR-02 (match by meaning) needs the live embedding model and is checked by hand (docs/design.md,
Test policy). The fake embedder matches by shared words, so these tests use shared words.
"""

from builders import (
    add_assignment,
    add_engineer,
    add_leaves,
    add_project,
    leaf_tags,
    page_text,
    reason_of,
    result_count,
    result_ids,
    row_of,
    parse,
)
from conftest import TEST_SEARCH_RESULT_LIMIT

LEAVES = {
    "PLL": "Phase-locked loop",
    "SRAM": "Static memory",
    "ADC": "Analog to digital converter",
    "Bandgap": "Voltage reference",
}
JITTER_QUERY = "fractional jitter loop"
JITTER_TEXT = "Led the fractional jitter loop design"
LEAD_LEVEL_NAME = "Lead"
LEAD_LEVEL = "3"


def search(client, query, mode="experience"):
    """Call the search page with a query and check that it answers with a page."""
    response = client.get("/search", params={"q": query, "mode": mode})
    assert response.status_code == 200
    return response.text


def three_engineers(client, ada_gaps="", ben_gaps=""):
    """Add Ada (PLL jitter), Ben (SRAM) and Cy (ADC); return their IDs by first name."""
    leaves = add_leaves(client, LEAVES)
    project_id = add_project(client)
    ada = add_engineer(
        client, "Ada Invented", job_title="Clock Architect", team="Clocking", skill_gaps=ada_gaps
    )
    ben = add_engineer(
        client, "Ben Invented", job_title="Memory Designer", team="Memory", skill_gaps=ben_gaps
    )
    cy = add_engineer(client, "Cy Invented", job_title="Data Converter Designer", team="Mixed")
    add_assignment(client, project_id, ada, leaves["PLL"], JITTER_TEXT)
    add_assignment(client, project_id, ben, leaves["SRAM"], "Designed the bitcell array layout")
    add_assignment(client, project_id, cy, leaves["ADC"], "Calibrated the pipeline converter")
    return {"ada": ada, "ben": ben, "cy": cy, "leaves": leaves, "project": project_id}


def test_fr_01_query_ranks_the_engineer_with_the_matching_assignment_first(client):
    people = three_engineers(client)

    ids = result_ids(search(client, JITTER_QUERY))

    assert ids[0] == people["ada"]


def test_fr_01_query_shows_at_most_search_result_limit_engineers(client):
    leaves = add_leaves(client, LEAVES)
    project_id = add_project(client)
    for number in range(TEST_SEARCH_RESULT_LIMIT + 1):
        engineer_id = add_engineer(client, f"Person{number} Invented")
        add_assignment(
            client,
            project_id,
            engineer_id,
            leaves["PLL"],
            f"Balanced the clock tree skew number {number}",
        )

    html = search(client, "clock tree skew")

    assert len(result_ids(html)) == TEST_SEARCH_RESULT_LIMIT
    assert result_count(html) == str(TEST_SEARCH_RESULT_LIMIT)


def test_fr_01_no_query_and_no_filter_shows_no_results(client):
    three_engineers(client)

    response = client.get("/search")

    assert response.status_code == 200
    html = response.text
    assert result_ids(html) == []
    assert result_count(html) == "0"


def test_fr_05_result_shows_name_job_title_team_and_the_best_assignment_as_reason(client):
    people = three_engineers(client)
    other_project_id = add_project(client, name="Invented Reference Chip")
    other_text = "Designed the bandgap reference circuit"
    add_assignment(client, other_project_id, people["ada"], people["leaves"]["Bandgap"], other_text)

    row = row_of(search(client, JITTER_QUERY), people["ada"])

    text = row.text()
    assert "Ada Invented" in text
    assert "Clock Architect" in text
    assert "Clocking" in text
    assert JITTER_TEXT in reason_of(row)
    assert other_text not in reason_of(row)


def test_fr_05_result_shows_at_most_3_leaf_tags(client):
    leaves = add_leaves(
        client,
        {
            "PLL": "Phase-locked loop",
            "CDR": "Clock and data recovery",
            "VCO": "Voltage controlled oscillator",
            "DLL": "Delay-locked loop",
        },
    )
    engineer_id = add_engineer(client, "Ada Invented")
    assignments = [
        ("PLL", "Measured jitter and noise and skew and drift"),
        ("CDR", "Measured jitter and noise and skew"),
        ("VCO", "Measured jitter and noise"),
        ("DLL", "Measured jitter"),
        ("PLL", "Measured jitter and noise and drift"),
    ]
    for number, (leaf_name, description) in enumerate(assignments):
        project_id = add_project(client, name=f"Invented Chip {number}")
        add_assignment(client, project_id, engineer_id, leaves[leaf_name], description)

    row = row_of(search(client, "jitter noise skew drift"), engineer_id)

    tags = leaf_tags(row)
    assert [tag.attrs["data-leaf-id"] for tag in tags] == [
        leaves["PLL"],
        leaves["CDR"],
        leaves["VCO"],
    ]
    assert tags[0].attrs["data-level"] == LEAD_LEVEL
    assert tags[0].text() == f"PLL · {LEAD_LEVEL_NAME}"


def test_fr_05_preview_shows_the_first_result(client):
    first_gaps = "Needs exposure to RF front ends"
    second_gaps = "Needs exposure to memory compilers"
    three_engineers(client, ada_gaps=first_gaps, ben_gaps=second_gaps)

    # Skill gaps show in the preview only: a result of experience search does not show them.
    text = page_text(search(client, JITTER_QUERY))

    assert first_gaps in text
    assert second_gaps not in text


def test_fr_05_preview_route_shows_the_chosen_engineer(client):
    ben_gaps = "Needs exposure to memory compilers"
    people = three_engineers(client, ada_gaps="Needs exposure to RF front ends", ben_gaps=ben_gaps)

    response = client.get(f"/search/preview/{people['ben']}", params={"mode": "experience"})

    assert response.status_code == 200
    shown = {
        element.attrs["data-engineer-id"]
        for element in parse(response.text).descendants()
        if "data-engineer-id" in element.attrs
    }
    assert shown == {people["ben"]}
    assert "Ben Invented" in response.text
    assert ben_gaps in response.text
    assert "Needs exposure to RF front ends" not in response.text
