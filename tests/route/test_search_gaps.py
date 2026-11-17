"""Route tests of the gap search (M14): FR-03, FR-06, D-09, D-10, D-14, D-29.

The fake embedder matches by shared words, so the skill gaps share words with the query.
"""

from builders import (
    add_employee,
    reason_of,
    result_ids,
    row_of,
)

GAP_QUERY = "needs radio frequency front end exposure"
GAP_TEXT = "Needs radio frequency front end exposure"
OTHER_GAP_TEXT = "Wants to learn memory compiler scripting"


def search_gaps(client, **params):
    """Call the search page in gap mode with the given parameters and return its HTML."""
    response = client.get("/search", params={"mode": "gaps", **params})
    assert response.status_code == 200
    return response.text


def test_fr_06_gap_query_ranks_the_employee_with_the_matching_skill_gap_first(client):
    other = add_employee(client, "Ben Invented", skill_gaps=OTHER_GAP_TEXT)
    match = add_employee(client, "Ada Invented", skill_gaps=GAP_TEXT)

    ids = result_ids(search_gaps(client, q=GAP_QUERY))

    assert ids[0] == match
    assert other in ids or ids == [match]


def test_fr_06_gap_result_shows_the_skill_gap_text_as_reason(client):
    match = add_employee(client, "Ada Invented", skill_gaps=GAP_TEXT)
    add_employee(client, "Ben Invented", skill_gaps=OTHER_GAP_TEXT)

    row = row_of(search_gaps(client, q=GAP_QUERY), match)

    assert GAP_TEXT in reason_of(row)
    assert OTHER_GAP_TEXT not in reason_of(row)


def test_fr_06_employee_with_empty_skill_gaps_is_not_in_the_gap_results(client):
    no_gaps = add_employee(client, "Cy Invented", skill_gaps="")
    match = add_employee(client, "Ada Invented", skill_gaps=GAP_TEXT)

    ids = result_ids(search_gaps(client, q=GAP_QUERY))

    assert match in ids
    assert no_gaps not in ids


def test_fr_03_filters_apply_in_gap_search(client):
    clocking = add_employee(client, "Ada Invented", team="Clocking", skill_gaps=GAP_TEXT)
    memory = add_employee(client, "Ben Invented", team="Memory", skill_gaps=GAP_TEXT)
    assert set(result_ids(search_gaps(client, q=GAP_QUERY))) == {clocking, memory}

    ids = result_ids(search_gaps(client, q=GAP_QUERY, team="Clocking"))

    assert ids == [clocking]
