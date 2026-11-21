"""Route tests of the panes (M27): FR-53, FR-54, FR-56, NFR-01 and D-45.

Every page is a row of panes. The tests read the markers of docs/design.md (HTML markers) and
the plain rules of the app.css that the Search page links. Only the markup and the stylesheet are
checked; the scroll itself needs a browser (docs/design.md, Test policy).
"""

import pytest

from builders import add_assignment, add_engineer, add_leaves, add_project, parse
from css_helpers import fetch_app_css, parse_rules, root_variables

ZERO_LENGTHS = {"0", "0px"}
FULL_WINDOW_HEIGHTS = {"100vh", "100dvh"}
FREE_WIDTH_FLEX = {"1 1 0", "1 1 0%", "1 1 0px"}
NO_SHRINK_FLEX = {"none", "0 0 auto"}


@pytest.fixture
def world(client):
    """Invented data through the routes: a leaf, an engineer, a project and one assignment."""
    leaves = add_leaves(client, {"PLL": "Phase locked loop design"})
    leaf_id = leaves["PLL"]
    engineer_id = add_engineer(client, "Cy Invented", skill_gaps="PLL layout")
    project_id = add_project(client)
    add_assignment(client, project_id, engineer_id, leaf_id, "Designed the PLL loop filter")
    return {"leaf_id": leaf_id, "engineer_id": engineer_id, "project_id": project_id}


def page_cases(world):
    """Return (label, address, pane IDs in order, ID of the flexible pane) for each page."""
    engineer_id = world["engineer_id"]
    return [
        ("search", "/", ["results", "preview"], "preview"),
        ("search with results", "/search?q=pll", ["results", "preview"], "preview"),
        ("engineers", "/engineers", ["engineers"], "engineers"),
        ("profile", f"/engineers/{engineer_id}", ["engineer"], "engineer"),
        ("form", f"/engineers/{engineer_id}/edit", ["engineer-form"], "engineer-form"),
        (
            "projects",
            f"/projects/{world['project_id']}",
            ["projects", "project", "assignment"],
            "project",
        ),
        ("skill tree", f"/skill-tree/{world['leaf_id']}", ["outline", "node"], "node"),
        ("settings", "/settings", ["settings"], "settings"),
    ]


def panes_of(html: str) -> list:
    """Return the elements with data-pane, in page order."""
    return [element for element in parse(html).descendants() if "data-pane" in element.attrs]


def pane_named(html: str, pane_id: str):
    """Return the one pane with the given data-pane value."""
    found = [pane for pane in panes_of(html) if pane.attrs["data-pane"] == pane_id]
    assert len(found) == 1, f"expected one pane {pane_id}, found {len(found)}"
    return found[0]


def merged_rule(client, selector: str) -> dict[str, str]:
    """Return the merged declarations of every plain rule of the selector, values as written."""
    declarations: dict[str, str] = {}
    for rule_selector, pairs in parse_rules(fetch_app_css(client)):
        if rule_selector == selector:
            for name, value in pairs:
                declarations[name] = " ".join(value.lower().split())
    return declarations


def test_fr_53_shell_has_the_height_of_the_window_and_does_not_scroll(client):
    """`.shell` is as tall as the window and hides its overflow, so only the panes scroll."""
    rule = merged_rule(client, ".shell")
    assert rule, "app.css has no plain rule for .shell"
    assert rule.get("height") in FULL_WINDOW_HEIGHTS
    assert rule.get("overflow", rule.get("overflow-y")) == "hidden"


def test_fr_53_pane_body_scrolls_vertically_on_its_own(client):
    """A pane body scrolls on its own inside a pane that is a flex column."""
    body = merged_rule(client, "[data-pane-body]")
    pane = merged_rule(client, "[data-pane]")
    assert body.get("overflow-y") == "auto"
    assert body.get("min-height") in ZERO_LENGTHS
    assert pane.get("display") == "flex"
    assert pane.get("flex-direction") == "column"
    assert pane.get("min-height") in ZERO_LENGTHS


def test_fr_54_pane_head_does_not_shrink(client):
    """A pane head keeps its height while the body scrolls."""
    head = merged_rule(client, "[data-pane-head]")
    assert head.get("flex") in NO_SHRINK_FLEX


@pytest.mark.parametrize("index", range(8))
def test_fr_53_every_pane_has_a_head_then_a_body(client, world, index):
    """Each pane has exactly 2 element children: the head first, then the body."""
    label, address, pane_ids, _ = page_cases(world)[index]
    response = client.get(address)
    assert response.status_code == 200, label
    panes = panes_of(response.text)
    assert [pane.attrs["data-pane"] for pane in panes] == pane_ids, label
    for pane in panes:
        assert len(pane.children) == 2, f"{label}: pane {pane.attrs['data-pane']} has {len(pane.children)} children"
        assert "data-pane-head" in pane.children[0].attrs, label
        assert "data-pane-body" in pane.children[1].attrs, label


def test_fr_54_head_of_engineers_holds_the_title_and_the_filters(client, world):
    """The Engineers head holds the h1, the filter input and the team and career level selects."""
    head = pane_named(client.get("/engineers").text, "engineers").children[0]
    parts = list(head.descendants())
    titles = [part.text() for part in parts if part.tag == "h1"]
    assert "Engineers" in titles
    assert [part for part in parts if part.tag == "input" and part.attrs.get("name") == "filter"]
    for name in ("team", "career_level"):
        assert [part for part in parts if part.tag == "select" and part.attrs.get("name") == name], name


def test_fr_54_head_of_results_holds_the_count_and_the_query_is_not_in_a_body(client, world):
    """The results head holds the result count, and the query box is in no pane body."""
    html = client.get("/search?q=pll").text
    head = pane_named(html, "results").children[0]
    counted = [head, *head.descendants()]
    assert [part for part in counted if "data-result-count" in part.attrs]

    query_inputs = [
        part for part in parse(html).descendants() if part.tag == "input" and part.attrs.get("name") == "q"
    ]
    assert query_inputs, "the Search page has no query input"
    in_bodies = {
        id(inner)
        for pane in panes_of(html)
        for inner in pane.children[1].descendants()
    }
    for query_input in query_inputs:
        assert id(query_input) not in in_bodies


def test_fr_54_head_of_projects_holds_the_title(client, world):
    """The Projects head holds the h1 "Projects"."""
    html = client.get(f"/projects/{world['project_id']}").text
    head = pane_named(html, "projects").children[0]
    assert "Projects" in [part.text() for part in head.descendants() if part.tag == "h1"]


def test_fr_54_head_of_outline_holds_the_title_and_the_add_top_level_form(client, world):
    """The outline head holds the h1 "Skill tree" and the input of the form that adds a node."""
    html = client.get(f"/skill-tree/{world['leaf_id']}").text
    head = pane_named(html, "outline").children[0]
    parts = list(head.descendants())
    assert "Skill tree" in [part.text() for part in parts if part.tag == "h1"]
    forms = [part for part in parts if part.tag == "form" and part.attrs.get("action") == "/skill-tree/nodes"]
    assert forms, "the outline head has no form that posts to /skill-tree/nodes"
    assert [part for form in forms for part in form.descendants() if part.tag == "input"]


def test_fr_54_head_of_settings_holds_the_title(client):
    """The Settings head holds the h1 "Settings"."""
    head = pane_named(client.get("/settings").text, "settings").children[0]
    assert "Settings" in [part.text() for part in head.descendants() if part.tag == "h1"]


@pytest.mark.parametrize("index", range(8))
def test_fr_53_exactly_one_pane_of_a_page_takes_the_free_width(client, world, index):
    """Exactly one pane of each page has data-pane-flex, and it is the pane that the design names."""
    label, address, _, flexible_id = page_cases(world)[index]
    panes = panes_of(client.get(address).text)
    flexible = [pane.attrs["data-pane"] for pane in panes if "data-pane-flex" in pane.attrs]
    assert flexible == [flexible_id], label


def test_fr_53_flexible_pane_rule_takes_the_free_width(client):
    """The rule `[data-pane-flex]` gives the pane the free width of its row."""
    rule = merged_rule(client, "[data-pane-flex]")
    assert rule.get("flex") in FREE_WIDTH_FLEX


def test_fr_56_stylesheet_gives_each_pane_a_minimum_width_of_240px(client):
    """`:root` defines --pane-min as 240px, and a pane never gets narrower than it."""
    variables = root_variables(parse_rules(fetch_app_css(client)))
    assert variables.get("--pane-min", "").replace(" ", "").lower() == "240px"
    assert merged_rule(client, "[data-pane]").get("min-width") == "var(--pane-min)"


@pytest.mark.parametrize(
    ("address", "page_key"),
    [
        ("/", "search"),
        ("/engineers", "engineers"),
        ("/skill-tree", "skill_tree"),
        ("/projects", "projects"),
        ("/settings", "settings"),
    ],
)
def test_nfr_01_body_names_its_page(client, address, page_key):
    """`<body>` has data-page with the key of the page (D-46)."""
    bodies = [element for element in parse(client.get(address).text).descendants() if element.tag == "body"]
    assert len(bodies) == 1
    assert bodies[0].attrs.get("data-page") == page_key

