"""Route tests of the panel handles (M28): FR-55, FR-57, FR-58 and D-46.

The tests read the markers of docs/design.md (HTML markers), the plain rules of the app.css that
the Search page links, and the file /static/panes.js. The drag, the minimum width and the kept
widths need a browser, so they are checked by hand (docs/design.md, Test policy).
"""

import re

import pytest

from builders import add_assignment, add_engineer, add_leaves, add_project, parse
from css_helpers import fetch_app_css, parse_rules

HANDLE = "handle"
RESET_TEXT = "Reset widths"
ADD_ENGINEER_TEXT = "Add engineer"
PANES_JS_ADDRESS = "/static/panes.js"
FIXED_PANE_WIDTHS = {"results": 460, "outline": 420, "projects": 420, "assignment": 340}
HANDLE_WIDTH_VALUES = {"8px", "0 0 8px"}
ONE_LINE_JSDOC = re.compile(r"^\s*/\*\*.*\*/\s*$")
FUNCTION_WORD = re.compile(r"\bfunction\b")


@pytest.fixture
def world(client):
    """Invented data through the routes: a leaf, an engineer, a project and one assignment."""
    leaves = add_leaves(client, {"PLL": "Phase locked loop design"})
    leaf_id = leaves["PLL"]
    engineer_id = add_engineer(client, "Cy Invented", skill_gaps="PLL layout")
    project_id = add_project(client)
    add_assignment(client, project_id, engineer_id, leaf_id, "Designed the PLL loop filter")
    return {"leaf_id": leaf_id, "engineer_id": engineer_id, "project_id": project_id}


def all_page_addresses(world):
    """Return (label, address) of each of the 8 pages."""
    engineer_id = world["engineer_id"]
    return [
        ("search", "/"),
        ("search with results", "/search?q=pll"),
        ("engineers", "/engineers"),
        ("profile", f"/engineers/{engineer_id}"),
        ("form", f"/engineers/{engineer_id}/edit"),
        ("projects", f"/projects/{world['project_id']}"),
        ("skill tree", f"/skill-tree/{world['leaf_id']}"),
        ("settings", "/settings"),
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


def row_order(html: str, pane_id: str) -> list[str]:
    """Return the panes (their IDs) and handles ("handle") that sit beside the pane, in order."""
    row = find_parent(parse(html), pane_id)
    assert row is not None, f"no pane {pane_id} in the page"
    order = []
    for child in row.children:
        if "data-pane-handle" in child.attrs:
            order.append(HANDLE)
        elif "data-pane" in child.attrs:
            order.append(child.attrs["data-pane"])
    return order


def handles_of(html: str) -> list:
    """Return the elements with data-pane-handle."""
    return [element for element in parse(html).descendants() if "data-pane-handle" in element.attrs]


def merged_rule(client, selector: str) -> dict[str, str]:
    """Return the merged declarations of every plain rule of the selector, spaces made plain."""
    wanted = selector.replace("'", '"')
    declarations: dict[str, str] = {}
    for rule_selector, pairs in parse_rules(fetch_app_css(client)):
        if rule_selector.replace("'", '"') == wanted:
            for name, value in pairs:
                declarations[name] = re.sub(r"\s*,\s*", ",", " ".join(value.lower().split()))
    return declarations


def sidebar_of(html: str):
    """Return the one element whose class list holds `sidebar`."""
    found = [
        element
        for element in parse(html).descendants()
        if "sidebar" in element.attrs.get("class", "").split()
    ]
    assert len(found) == 1, f"expected one sidebar, found {len(found)}"
    return found[0]


def test_fr_55_search_page_has_one_handle_between_results_and_preview(client, world):
    """The Search page and its swapped part have results, one vertical handle, then preview."""
    page = client.get("/")
    assert page.status_code == 200
    assert row_order(page.text, "results") == ["results", HANDLE, "preview"]
    handles = handles_of(page.text)
    assert len(handles) == 1
    assert handles[0].attrs.get("role") == "separator"
    assert handles[0].attrs.get("aria-orientation") == "vertical"

    swapped = client.get("/search?q=pll", headers={"HX-Request": "true"})
    assert swapped.status_code == 200
    assert row_order(swapped.text, "results") == ["results", HANDLE, "preview"]
    assert len(handles_of(swapped.text)) == 1


def test_fr_55_projects_page_has_a_handle_between_each_two_panes(client, world):
    """With a project selected: projects, handle, project, handle, assignment. With none: 3 parts."""
    selected = client.get(f"/projects/{world['project_id']}")
    assert selected.status_code == 200
    assert row_order(selected.text, "projects") == ["projects", HANDLE, "project", HANDLE, "assignment"]
    for handle in handles_of(selected.text):
        assert handle.attrs.get("role") == "separator"
        assert handle.attrs.get("aria-orientation") == "vertical"


def test_fr_55_projects_page_with_no_project_has_one_handle(client):
    """With no project in the store the Projects page is projects, handle, project."""
    page = client.get("/projects")
    assert page.status_code == 200
    assert row_order(page.text, "projects") == ["projects", HANDLE, "project"]


def test_fr_55_skill_tree_page_has_one_handle_between_outline_and_node(client, world):
    """The Skill tree page is outline, handle, node."""
    page = client.get(f"/skill-tree/{world['leaf_id']}")
    assert page.status_code == 200
    assert row_order(page.text, "outline") == ["outline", HANDLE, "node"]
    handles = handles_of(page.text)
    assert len(handles) == 1
    assert handles[0].attrs.get("role") == "separator"
    assert handles[0].attrs.get("aria-orientation") == "vertical"


def test_fr_55_pages_with_one_pane_have_no_handle(client, world):
    """The Engineers list, a profile, the Edit engineer form and Settings have no handle."""
    engineer_id = world["engineer_id"]
    for address in ("/engineers", f"/engineers/{engineer_id}", f"/engineers/{engineer_id}/edit", "/settings"):
        response = client.get(address)
        assert response.status_code == 200, address
        assert handles_of(response.text) == [], address


def test_fr_58_every_page_has_the_reset_button_in_the_sidebar(client, world):
    """Each page has one data-pane-reset in the sidebar, "Reset widths", before "Add engineer"."""
    for label, address in all_page_addresses(world):
        response = client.get(address)
        assert response.status_code == 200, label
        sidebar = sidebar_of(response.text)
        parts = list(sidebar.descendants())
        resets = [part for part in parts if "data-pane-reset" in part.attrs]
        assert len(resets) == 1, label
        assert resets[0].text() == RESET_TEXT, label
        add_links = [part for part in parts if part.tag == "a" and part.text() == ADD_ENGINEER_TEXT]
        assert len(add_links) == 1, label
        assert parts.index(resets[0]) < parts.index(add_links[0]), label
        in_page = [
            element for element in parse(response.text).descendants() if "data-pane-reset" in element.attrs
        ]
        assert len(in_page) == 1, label


def test_fr_57_every_page_links_panes_js_and_the_script_is_served(client, world):
    """Each page links the script /static/panes.js, and the server answers it as JavaScript."""
    for label, address in all_page_addresses(world):
        response = client.get(address)
        scripts = [
            element
            for element in parse(response.text).descendants()
            if element.tag == "script" and element.attrs.get("src") == PANES_JS_ADDRESS
        ]
        assert len(scripts) == 1, label

    served = client.get(PANES_JS_ADDRESS)
    assert served.status_code == 200
    assert "javascript" in served.headers["content-type"].lower()


def test_fr_55_fixed_panes_take_their_width_from_the_pane_width_property(client):
    """Fixed panes take `flex: 0 0 var(--pane-width, <default>)`, and the handle is 8px wide."""
    for pane_id, default in FIXED_PANE_WIDTHS.items():
        rule = merged_rule(client, f'[data-pane="{pane_id}"]')
        assert rule.get("flex") == f"0 0 var(--pane-width,{default}px)", pane_id

    handle = merged_rule(client, "[data-pane-handle]")
    assert handle.get("width") in HANDLE_WIDTH_VALUES or handle.get("flex") in HANDLE_WIDTH_VALUES
    assert handle.get("cursor") == "col-resize"


def code_lines_with_function(source: str) -> list[int]:
    """Return the indexes of the lines that hold the word `function` outside a comment line."""
    lines = source.splitlines()
    found = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("*", "/*", "//")):
            continue
        if FUNCTION_WORD.search(stripped):
            found.append(index)
    return found


def test_d_46_every_function_of_panes_js_has_a_one_line_jsdoc(client):
    """Each function declaration or expression has a one-line JSDoc comment directly before it."""
    served = client.get(PANES_JS_ADDRESS)
    assert served.status_code == 200
    lines = served.text.splitlines()
    indexes = code_lines_with_function(served.text)
    assert indexes, "panes.js holds no function"
    for index in indexes:
        before = index - 1
        while before >= 0 and not lines[before].strip():
            before -= 1
        assert before >= 0 and ONE_LINE_JSDOC.match(lines[before]), (
            f"line {index + 1} of panes.js has no one-line JSDoc before it: {lines[index].strip()}"
        )
