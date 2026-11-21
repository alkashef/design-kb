"""Route tests of the Engineer detail pane (M29): FR-10, FR-50, FR-51, FR-52 and AC-02 cases 1 to 3.

The tests read the markers of docs/design.md (HTML markers, D-47). The widths and the hidden
columns need a browser, so NFR-01 is checked by hand (docs/design.md, Test policy).
"""

from urllib.parse import parse_qs, urlsplit

import pytest

from builders import (
    add_assignment,
    add_engineer,
    add_leaves,
    add_project,
    leaf_tags,
    parse,
)

HANDLE = "handle"
LIST_PANE = "engineers"
DETAIL_PANE = "engineer-detail"
SLOT_ID = "engineer-detail-slot"
LEAF_NAME = "PLL"
PROJECT_NAME = "Invented SerDes"
ASSIGNMENT_TEXT = "Designed the PLL loop filter"
GAPS_TEXT = "Needs layout practice"


@pytest.fixture
def world(client):
    """Invented data through the routes: Cy Invented with a leaf, a project, an assignment and gaps."""
    leaves = add_leaves(client, {LEAF_NAME: "Phase locked loop design"})
    cy_id = add_engineer(
        client,
        "Cy Invented",
        job_title="Design Engineer",
        team="Mixed-signal",
        skill_gaps=GAPS_TEXT,
    )
    other_id = add_engineer(client, "Dee Other", job_title="Layout Engineer", team="Analog")
    third_id = add_engineer(client, "Eli Third", job_title="Test Engineer", team="Analog")
    project_id = add_project(client, name=PROJECT_NAME)
    add_assignment(client, project_id, cy_id, leaves[LEAF_NAME], ASSIGNMENT_TEXT)
    return {
        "leaf_id": leaves[LEAF_NAME],
        "cy_id": cy_id,
        "other_id": other_id,
        "third_id": third_id,
    }


def find_by_attr(root, name, value=None):
    """Return the elements below root that have the attribute (and the value, when given)."""
    return [
        element
        for element in root.descendants()
        if name in element.attrs and (value is None or element.attrs[name] == value)
    ]


def find_parent(element, pane_id):
    """Return the element that has a child with data-pane equal to pane_id, or None."""
    for child in element.children:
        if child.attrs.get("data-pane") == pane_id:
            return element
    for child in element.children:
        found = find_parent(child, pane_id)
        if found is not None:
            return found
    return None


def row_order(html: str, pane_id: str = LIST_PANE) -> list[str]:
    """Return the panes (their IDs) and handles ("handle") below the row of the pane, in page order.

    The row is the parent of the pane. The handle and the detail pane may sit inside the slot, so
    the order is read from all descendants of the row, not only from its children (D-47).
    """
    row = find_parent(parse(html), pane_id)
    assert row is not None, f"no pane {pane_id} in the page"
    order = []
    for element in row.descendants():
        if "data-pane-handle" in element.attrs:
            order.append(HANDLE)
        elif "data-pane" in element.attrs:
            order.append(element.attrs["data-pane"])
    return order


def pane(html: str, pane_id: str):
    """Return the one pane with that data-pane."""
    found = find_by_attr(parse(html), "data-pane", pane_id)
    assert len(found) == 1, f"expected one pane {pane_id}, found {len(found)}"
    return found[0]


def panes(html: str, pane_id: str) -> list:
    """Return every pane with that data-pane."""
    return find_by_attr(parse(html), "data-pane", pane_id)


def handles_of(html: str) -> list:
    """Return the elements with data-pane-handle."""
    return find_by_attr(parse(html), "data-pane-handle")


def slot_of(html: str):
    """Return the one element with the ID of the detail slot."""
    found = find_by_attr(parse(html), "id", SLOT_ID)
    assert len(found) == 1, f"expected one {SLOT_ID}, found {len(found)}"
    return found[0]


def list_rows(html: str) -> list:
    """Return the rows of the Engineers list: the elements of the list pane with data-engineer-id."""
    return find_by_attr(pane(html, LIST_PANE), "data-engineer-id")


def test_fr_10_selected_engineer_shows_the_detail_pane_beside_the_list(client, world):
    """With `selected`, the slot holds a handle and the detail pane after the list pane."""
    page = client.get("/engineers", params={"selected": world["cy_id"]})
    assert page.status_code == 200
    assert slot_of(page.text) is not None
    assert row_order(page.text) == [LIST_PANE, HANDLE, DETAIL_PANE]
    detail = pane(page.text, DETAIL_PANE)
    assert detail.attrs.get("data-engineer-id") == world["cy_id"]
    list_ids = {row.attrs["data-engineer-id"] for row in list_rows(page.text)}
    assert list_ids == {world["cy_id"], world["other_id"], world["third_id"]}
    assert "data-pane-flex" in detail.attrs
    assert "data-pane-flex" not in pane(page.text, LIST_PANE).attrs


def test_fr_10_without_selection_the_list_pane_is_alone_and_flexible(client, world):
    """With no `selected`, the slot is empty, there is no handle, and the list pane is flexible."""
    page = client.get("/engineers")
    assert page.status_code == 200
    slot = slot_of(page.text)
    assert slot.children == []
    assert slot.text() == ""
    assert handles_of(page.text) == []
    assert panes(page.text, DETAIL_PANE) == []
    assert "data-pane-flex" in pane(page.text, LIST_PANE).attrs


def test_fr_10_unknown_selected_engineer_shows_no_pane(client, world):
    """An unknown `selected` ID answers 200 with an empty slot."""
    page = client.get("/engineers", params={"selected": "E-9999"})
    assert page.status_code == 200
    assert slot_of(page.text).children == []
    assert panes(page.text, DETAIL_PANE) == []
    assert handles_of(page.text) == []


def test_fr_10_each_row_links_to_the_selection_and_carries_the_htmx_attributes(client, world):
    """A row is a link to the selection that keeps the filters, with the HTMX attributes of D-47."""
    page = client.get("/engineers", params={"team": "Analog"})
    assert page.status_code == 200
    rows = list_rows(page.text)
    assert {row.attrs["data-engineer-id"] for row in rows} == {world["other_id"], world["third_id"]}
    for row in rows:
        engineer_id = row.attrs["data-engineer-id"]
        assert row.tag == "a"
        href = row.attrs.get("href", "")
        assert href.startswith("/engineers?")
        query = parse_qs(urlsplit(href).query)
        assert query.get("selected") == [engineer_id]
        assert query.get("team") == ["Analog"]
        assert row.attrs.get("hx-get") == f"/engineer-panel/{engineer_id}"
        assert row.attrs.get("hx-target") == f"#{SLOT_ID}"
        assert "hx-push-url" in row.attrs


def test_fr_10_panel_route_gives_the_pane_of_the_chosen_engineer(client, world):
    """`GET /engineer-panel/<id>` gives one handle and one pane of that engineer."""
    for engineer_id in (world["cy_id"], world["other_id"]):
        part = client.get(f"/engineer-panel/{engineer_id}")
        assert part.status_code == 200
        assert len(handles_of(part.text)) == 1
        detail = pane(part.text, DETAIL_PANE)
        assert detail.attrs.get("data-engineer-id") == engineer_id


def test_fr_10_unknown_engineer_on_the_panel_route_gives_404(client, world):
    """An unknown ID on the panel route answers 404, a known ID answers 200."""
    assert client.get(f"/engineer-panel/{world['cy_id']}").status_code == 200
    assert client.get("/engineer-panel/E-9999").status_code == 404


def test_fr_50_detail_pane_shows_the_attributes_the_levels_the_projects_and_the_skill_gaps(
    client, world
):
    """The pane shows the attributes, the level of the leaf, the project and the assignment."""
    page = client.get("/engineers", params={"selected": world["cy_id"]})
    detail = pane(page.text, DETAIL_PANE)
    text = detail.text()
    for expected in (
        "Cy Invented",
        "Design Engineer",
        "Senior",
        "Mixed-signal",
        world["cy_id"],
        GAPS_TEXT,
        PROJECT_NAME,
        ASSIGNMENT_TEXT,
    ):
        assert expected in text, expected
    tags = leaf_tags(detail)
    assert [tag.attrs["data-leaf-id"] for tag in tags] == [world["leaf_id"]]
    assert tags[0].attrs.get("data-level") in {"1", "2", "3", "4", "5"}


def test_fr_51_open_full_profile_links_to_the_profile_page(client, world):
    """The pane has `data-open-profile` with the profile address, and that address answers 200."""
    page = client.get("/engineers", params={"selected": world["cy_id"]})
    links = find_by_attr(pane(page.text, DETAIL_PANE), "data-open-profile")
    assert len(links) == 1
    assert links[0].attrs.get("href") == f"/engineers/{world['cy_id']}"
    assert client.get(links[0].attrs["href"]).status_code == 200


def test_fr_52_close_control_links_to_the_list_and_to_the_empty_panel(client, world):
    """Close links to the list with the filters and no `selected`, and to the empty panel route."""
    page = client.get("/engineers", params={"selected": world["cy_id"], "team": "Mixed-signal"})
    closers = find_by_attr(pane(page.text, DETAIL_PANE), "data-detail-close")
    assert len(closers) == 1
    close = closers[0]
    href = close.attrs.get("href", "")
    assert href.startswith("/engineers?")
    query = parse_qs(urlsplit(href).query)
    assert "selected" not in query
    assert query.get("team") == ["Mixed-signal"]
    assert close.attrs.get("hx-get") == "/engineer-panel"
    assert "hx-push-url" in close.attrs

    empty = client.get("/engineer-panel")
    assert empty.status_code == 200
    assert panes(empty.text, DETAIL_PANE) == []
    assert handles_of(empty.text) == []


def test_ac_02_case_1_selecting_a_row_shows_the_panel_and_narrows_the_list(client, world):
    """Case 1: Cy Invented is E-0001; the panel shows the 5 facts and the list is not flexible."""
    assert world["cy_id"] == "E-0001"
    before = client.get("/engineers")
    assert panes(before.text, DETAIL_PANE) == []
    assert "data-pane-flex" in pane(before.text, LIST_PANE).attrs

    page = client.get("/engineers", params={"selected": "E-0001"})
    text = pane(page.text, DETAIL_PANE).text()
    for expected in ("Cy Invented", "Design Engineer", "Mixed-signal", "Senior", "E-0001"):
        assert expected in text, expected
    assert "data-pane-flex" not in pane(page.text, LIST_PANE).attrs


def test_ac_02_case_2_selecting_another_engineer_shows_one_panel_for_it(client, world):
    """Case 2: the panel route of another engineer gives exactly one pane, of that engineer."""
    part = client.get(f"/engineer-panel/{world['other_id']}")
    assert part.status_code == 200
    found = panes(part.text, DETAIL_PANE)
    assert len(found) == 1
    assert found[0].attrs.get("data-engineer-id") == world["other_id"]
    assert "Dee Other" in found[0].text()
    assert "Cy Invented" not in found[0].text()


def test_ac_02_case_3_closing_the_panel_gives_back_the_list_alone(client, world):
    """Case 3: the address of Close gives the page with an empty slot and a flexible list."""
    opened = client.get("/engineers", params={"selected": world["cy_id"]})
    close = find_by_attr(pane(opened.text, DETAIL_PANE), "data-detail-close")[0]
    closed = client.get(close.attrs["href"])
    assert closed.status_code == 200
    assert slot_of(closed.text).children == []
    assert handles_of(closed.text) == []
    assert panes(closed.text, DETAIL_PANE) == []
    assert "data-pane-flex" in pane(closed.text, LIST_PANE).attrs
