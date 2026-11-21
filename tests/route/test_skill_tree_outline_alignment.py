"""Route tests of the arrow alignment of the Skill tree outline (M30): NFR-01, D-48, D-19."""

import re

from builders import add_node, parse
from css_helpers import Stylesheet, fetch_app_css

BASE_PX = 28
STEP_PX = 22


def build_tree(client):
    """Add a top-level branch, a branch below it, and a leaf at depth 2. Return their ids by depth."""
    top = add_node(client, "Analog design")
    branch = add_node(client, "Clocking", parent_id=top)
    leaf = add_node(client, "PLL", parent_id=branch)
    return {top: 0, branch: 1, leaf: 2}


def style_px(element, name):
    """Return the px number of the inline style property of the element, or None."""
    match = re.search(rf"(?:^|;)\s*{name}\s*:\s*(-?\d+(?:\.\d+)?)px", element.attrs.get("style", ""))
    return float(match.group(1)) if match else None


def classes(element):
    """Return the class names of the element."""
    return element.attrs.get("class", "").split()


def rows_of(root):
    """Return each element with a data-node-id, parents before children."""
    return [el for el in root.descendants() if "data-node-id" in el.attrs]


def row_of_toggle(root, toggle):
    """Return the outline row that a caret toggle belongs to: its ancestor row, or the row beside it."""
    def find(node, path):
        if node is toggle:
            return path
        for child in node.children:
            found = find(child, path + [node])
            if found is not None:
                return found
        return None

    path = find(root, [])
    for ancestor in reversed(path):
        if "data-node-id" in ancestor.attrs:
            return ancestor
    for ancestor in reversed(path):
        beside = [el for el in ancestor.descendants() if "data-node-id" in el.attrs]
        if beside:
            return beside[0]
    return None


def test_nfr_01_branch_caret_starts_where_the_row_content_starts(client):
    depths = build_tree(client)
    root = parse(client.get("/skill-tree").text)

    rows = rows_of(root)
    assert {row.attrs["data-node-id"] for row in rows} >= set(depths)
    for row in rows:
        expected = BASE_PX + STEP_PX * depths[row.attrs["data-node-id"]]
        assert style_px(row, "padding-left") == expected
    toggles = [el for el in root.descendants() if "caret-toggle" in classes(el)]
    assert len(toggles) == 2
    for toggle in toggles:
        row = row_of_toggle(root, toggle)
        assert row is not None
        assert style_px(toggle, "left") == style_px(row, "padding-left")


def test_nfr_01_caret_boxes_are_14px_wide_with_the_glyph_at_the_left(client):
    sheet = Stylesheet(fetch_app_css(client))

    caret = sheet.plain_declarations(".caret")
    toggle = sheet.plain_declarations(".caret-toggle")

    assert sheet.property_value(caret, ("width",)) == "14px"
    assert sheet.property_value(toggle, ("width",)) == "14px"
    assert sheet.property_value(toggle, ("text-align",)) == "left"


def test_nfr_01_every_outline_row_starts_with_a_caret_box(client):
    build_tree(client)
    root = parse(client.get("/skill-tree").text)

    rows = rows_of(root)
    assert len(rows) >= 3
    for row in rows:
        assert row.children, "an outline row has no child element"
        assert "caret" in classes(row.children[0])
