"""Route test of the split-page rows (M27 replaces M18): the rows no longer grow with their content (FR-53, D-45)."""

from css_helpers import fetch_app_css, parse_rules

ZERO_LENGTHS = {"0", "0px", "0%"}
SPLIT_ROW_SELECTORS = [".search-body", ".tree-body"]


def plain_rule_declarations(css: str, selector: str) -> dict[str, str]:
    """Return the property/value pairs of every plain rule for the selector, merged in order."""
    declarations: dict[str, str] = {}
    for rule_selector, pairs in parse_rules(css):
        if rule_selector == selector:
            for name, value in pairs:
                declarations[name] = value.lower()
    return declarations


def test_fr_53_split_view_rows_do_not_grow_with_content(client):
    """A split row has no positive minimum height, so the shell keeps the height of the window."""
    css = fetch_app_css(client)
    for selector in SPLIT_ROW_SELECTORS:
        min_height = plain_rule_declarations(css, selector).get("min-height")
        assert min_height is None or min_height in ZERO_LENGTHS, f"{selector} keeps min-height {min_height}"
        basis = plain_rule_declarations(css, selector).get("flex", "").split()
        assert len(basis) != 3 or basis[2] in ZERO_LENGTHS, f"{selector} keeps a flex basis above 0"
