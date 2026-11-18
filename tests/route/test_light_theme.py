"""Route tests of the light theme colors of app.css (M22, NFR-01, D-43)."""

import pytest

from tests.css_helpers import Stylesheet, fetch_app_css, has_color

DARK_COLORS = [
    "#0C0D10", "#14161B", "#181B21", "#101216", "#1E2128", "#23262E", "#2A2E38",
    "#ECEEF2", "#D5D8DF", "#9AA1AD", "#6EE7B7", "#04130D", "#12221D",
]
ACCENT = "#F04A0E"


@pytest.fixture
def sheet(client) -> Stylesheet:
    """The stylesheet that the Search page links, with each var(--name) resolved."""
    return Stylesheet(fetch_app_css(client))


def assert_ground_and_text(sheet, selector, ground, text=None):
    """Assert the plain rule of the selector has the ground, and the text color when one is given."""
    declarations = sheet.plain_declarations(selector)
    assert declarations, f"app.css has no plain rule for {selector}"
    assert has_color(sheet.ground(declarations), ground), f"{selector} has the ground {sheet.ground(declarations)}"
    if text is not None:
        assert has_color(sheet.text_color(declarations), text), f"{selector} has the color {sheet.text_color(declarations)}"


def test_nfr_01_stylesheet_has_none_of_the_dark_colors(sheet):
    """No color of the dark theme of D-17 stays in the stylesheet."""
    css = sheet.css.lower()
    left_over = [color for color in DARK_COLORS if color.lower() in css]
    assert not left_over, f"app.css still holds {left_over}"


def test_nfr_01_page_ground_is_grey_with_dark_text(sheet):
    """The page is grey (#EDEDED) with near-black text (#1F1F21)."""
    assert_ground_and_text(sheet, "body", "#ededed", "#1f1f21")


def test_nfr_01_sidebar_is_graphite_with_light_text(sheet):
    """The sidebar is graphite (#2C2D30) with light text, and its active link is #45464A."""
    assert_ground_and_text(sheet, ".sidebar", "#2c2d30", "#f4f4f4")
    assert_ground_and_text(sheet, ".nav a.active", "#45464a")


def test_nfr_01_primary_button_is_orange_with_dark_text(sheet):
    """The primary button is a fill in the accent color with dark text."""
    assert_ground_and_text(sheet, ".button-accent", "#f04a0e", "#141416")


def test_nfr_01_cards_are_beige_and_their_fields_white(sheet):
    """A card is beige (#FAF6EC), and a field inside a card is white."""
    assert_ground_and_text(sheet, ".panel", "#faf6ec")
    field_rule = sheet.listed_declarations(".panel input")
    assert field_rule, "app.css has no rule whose selector list holds .panel input"
    assert has_color(sheet.ground(field_rule), "#ffffff"), f"the fields of a card have the ground {sheet.ground(field_rule)}"


def test_nfr_01_accent_is_a_fill_and_never_a_text_color(sheet):
    """The accent #F04A0E is used on fills and edges, and no rule sets it as a text color."""
    accent = ACCENT.lower()
    used_outside_color = [
        (selector, name)
        for selector, declarations in sheet.rules
        for name, value in declarations
        if not name.startswith("--") and name != "color" and accent in value
    ]
    assert used_outside_color, "no declaration other than color uses the accent"

    as_text = [
        selector
        for selector, declarations in sheet.rules
        for name, value in declarations
        if name == "color" and accent in value
    ]
    assert not as_text, f"the accent is a text color in {as_text}"
