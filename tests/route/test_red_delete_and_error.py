"""Route tests of the red Delete buttons and the red error message (M24, NFR-01, D-43)."""

import re
from html.parser import HTMLParser

import pytest

from tests.css_helpers import Stylesheet, fetch_app_css, has_color

RED = "#b42318"


@pytest.fixture
def sheet(client) -> Stylesheet:
    """The stylesheet that the Search page links, with each var(--name) resolved."""
    return Stylesheet(fetch_app_css(client))


class FormButtons(HTMLParser):
    """Collect, for each form, its action and the attributes of its submit buttons."""

    def __init__(self):
        super().__init__()
        self.forms = []
        self._current = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "form":
            self._current = {"action": attributes.get("action") or "", "buttons": []}
            self.forms.append(self._current)
        elif self._current is not None and (
            tag == "button" and attributes.get("type", "submit") == "submit"
            or tag == "input" and attributes.get("type") == "submit"
        ):
            self._current["buttons"].append(attributes)

    def handle_endtag(self, tag):
        if tag == "form":
            self._current = None


def forms_of(html: str) -> list[dict]:
    """Return the forms of the page with their submit buttons."""
    parser = FormButtons()
    parser.feed(html)
    return parser.forms


def border_values(sheet, declarations):
    """Return the values of the border declarations of a rule."""
    return [v for n, v in declarations if n in ("border", "border-color")]


def test_nfr_01_error_message_is_red_text_on_a_red_tint(sheet):
    """An element with role="alert" has red text, a red tint ground and a red border."""
    declarations = sheet.listed_declarations('[role="alert"]')
    assert sheet.text_color(declarations) == RED
    assert sheet.ground(declarations) is not None
    assert has_color(sheet.ground(declarations), "#fbeae7")
    assert any(has_color(value, "#e5a9a2") for value in border_values(sheet, declarations))


def test_nfr_01_delete_buttons_of_employee_and_project_are_marked(seeded_client):
    """The submit button of each Delete form has the class button-danger."""
    profile = forms_of(seeded_client.get("/employees/E-0001").text)
    employee = [f for f in profile if f["action"].rstrip("/") == "/employees/E-0001/delete"]
    assert employee, "no form posts to /employees/E-0001/delete"
    assert employee[0]["buttons"]
    assert all("button-danger" in (b.get("class") or "").split() for b in employee[0]["buttons"])

    projects = forms_of(seeded_client.get("/projects").text)
    project = [
        f for f in projects
        if re.fullmatch(r"/projects/.+/delete", f["action"])
    ]
    assert project, "no form posts to /projects/<id>/delete"
    for form in project:
        assert form["buttons"]
        assert all("button-danger" in (b.get("class") or "").split() for b in form["buttons"])


def test_nfr_01_delete_button_is_a_red_outline(sheet):
    """The plain .button-danger rule has red text, a red-tinted border and no fill."""
    declarations = sheet.plain_declarations(".button-danger")
    assert sheet.text_color(declarations) == RED
    assert any(has_color(value, "#d9a098") for value in border_values(sheet, declarations))
    ground = sheet.ground(declarations)
    assert ground is None or ground in ("transparent", "none")
