"""Route test of the split-page bodies (M18): they grow with their content so the sidebar stays in view (NFR-01)."""

import re

ZERO_LENGTHS = {"0", "0px", "0%"}
SPLIT_BODY_SELECTORS = [".search-body", ".tree-body"]


def plain_rule_declarations(css: str, selector: str) -> dict[str, str]:
    """Return the property/value pairs of every plain rule for the selector, merged in order."""
    declarations: dict[str, str] = {}
    for rule_selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if rule_selector.strip() != selector:
            continue
        for part in body.split(";"):
            if ":" in part:
                name, value = part.split(":", 1)
                declarations[name.strip().lower()] = value.strip().lower()
    return declarations


def test_nfr_01_split_view_bodies_grow_with_content(client):
    """The stylesheet that the Search page links lets each split body grow past zero height."""
    page = client.get("/")
    hrefs = re.findall(r'<link[^>]+href="([^"]+\.css)"', page.text)
    app_css = [href for href in hrefs if href.endswith("app.css")]
    assert app_css, "the Search page links no app.css"

    response = client.get(app_css[0])
    assert response.status_code == 200

    for selector in SPLIT_BODY_SELECTORS:
        rule = plain_rule_declarations(response.text, selector)
        assert rule, f"app.css has no plain rule for {selector}"
        assert rule.get("min-height") not in ZERO_LENGTHS, f"{selector} keeps min-height: 0"

        parts = rule.get("flex", "").split()
        assert len(parts) == 3, f"{selector} has no full flex shorthand"
        assert parts[2] not in ZERO_LENGTHS, f"{selector} has a flex basis of 0"
