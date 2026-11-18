"""Route test of the pinned sidebar (M16): the stylesheet keeps the sidebar in view (NFR-01)."""

import re


def sidebar_declarations(css: str) -> dict[str, str]:
    """Return the property/value pairs of every plain `.sidebar` rule, merged."""
    declarations: dict[str, str] = {}
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if selector.strip() != ".sidebar":
            continue
        for part in body.split(";"):
            if ":" in part:
                name, value = part.split(":", 1)
                declarations[name.strip().lower()] = value.strip().lower()
    return declarations


def test_nfr_01_sidebar_rule_pins_sidebar_to_window(client):
    """The stylesheet that the Search page links pins `.sidebar` to the window and lets it scroll."""
    page = client.get("/")
    hrefs = re.findall(r'<link[^>]+href="([^"]+\.css)"', page.text)
    app_css = [href for href in hrefs if href.endswith("app.css")]
    assert app_css, "the Search page links no app.css"

    response = client.get(app_css[0])
    assert response.status_code == 200

    rule = sidebar_declarations(response.text)
    assert rule.get("position") == "sticky"
    assert rule.get("top") in {"0", "0px"}
    assert rule.get("height") in {"100vh", "100dvh"}
    assert rule.get("overflow-y") == "auto"
    assert rule.get("align-self") == "flex-start"
