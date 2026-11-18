"""Route test of the font roles of app.css (M23, NFR-01, D-43)."""

import re

import pytest

from tests.css_helpers import Stylesheet, fetch_app_css

SIZE_THEN_FAMILY = re.compile(r"\d[\w.%]*(?:/[\w.%]+)?\s+(.+)$")
MONO = '"jetbrains mono"'
INTER = '"inter"'


@pytest.fixture
def sheet(client) -> Stylesheet:
    """The stylesheet that the Search page links, with each var(--name) resolved."""
    return Stylesheet(fetch_app_css(client))


def family_of(declarations):
    """Return the font family of the declarations: from `font-family`, else from the `font` shorthand."""
    value = None
    for name, text in declarations:
        if name == "font-family":
            value = text
        elif name == "font":
            match = SIZE_THEN_FAMILY.search(text)
            value = match.group(1) if match else text
    return value


def test_nfr_01_console_font_on_controls_and_inter_on_text(sheet):
    """Controls, navigation and paths use JetBrains Mono; body, card fields and names use Inter."""
    for selector in (".nav", ".button-outline", ".button-accent", ".query input", ".crumbs"):
        family = family_of(sheet.plain_declarations(selector))
        assert family and family.startswith(MONO), f"{selector} has the font family {family}"
    for selector in (".filters input", ".filters select"):
        family = family_of(sheet.listed_declarations(selector))
        assert family and family.startswith(MONO), f"{selector} has the font family {family}"
    for family, label in (
        (family_of(sheet.plain_declarations("body")), "body"),
        (family_of(sheet.listed_declarations(".panel input")), ".panel input"),
    ):
        assert family and family.startswith(INTER), f"{label} has the font family {family}"
    for selector in (".result-name", ".result-reason", ".preview-name", ".assignment-text"):
        family = family_of(sheet.listed_declarations(selector))
        assert not (family and family.startswith(MONO)), f"{selector} has the font family {family}"
