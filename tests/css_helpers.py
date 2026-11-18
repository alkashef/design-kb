"""Helpers that read the stylesheet the Search page links (route tests of the look, NFR-01, D-43)."""

import re

COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
VAR_REFERENCE = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,[^()]*)?\)")
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
MAX_VAR_DEPTH = 10


def fetch_app_css(client) -> str:
    """Return the text of the app.css that the Search page links, without its comments."""
    page = client.get("/")
    hrefs = re.findall(r'<link[^>]+href="([^"]+\.css)"', page.text)
    app_css = [href for href in hrefs if href.endswith("app.css")]
    assert app_css, "the Search page links no app.css"
    response = client.get(app_css[0])
    assert response.status_code == 200
    return COMMENT.sub("", response.text)


def parse_rules(css: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """Return each rule as its selector text and its (property, value) pairs, in file order."""
    rules = []
    for selector, body in RULE.findall(css):
        declarations = []
        for part in body.split(";"):
            if ":" in part:
                name, value = part.split(":", 1)
                declarations.append((name.strip().lower(), value.strip()))
        rules.append((selector.strip(), declarations))
    return rules


def root_variables(rules) -> dict[str, str]:
    """Return the custom properties that the `:root` rules define."""
    variables: dict[str, str] = {}
    for selector, declarations in rules:
        if selector == ":root":
            for name, value in declarations:
                if name.startswith("--"):
                    variables[name] = value
    return variables


def resolve(value: str, variables: dict[str, str]) -> str:
    """Replace each var(--name) in the value by the value of :root, and lower-case the result."""
    for _ in range(MAX_VAR_DEPTH):
        replaced = VAR_REFERENCE.sub(lambda match: variables.get(match.group(1), ""), value)
        if replaced == value:
            break
        value = replaced
    return value.strip().lower()


class Stylesheet:
    """The rules of app.css with every var(--name) resolved through :root."""

    def __init__(self, css: str):
        self.css = css
        raw_rules = parse_rules(css)
        variables = root_variables(raw_rules)
        self.rules = [
            (selector, [(name, resolve(value, variables)) for name, value in declarations])
            for selector, declarations in raw_rules
        ]

    def plain_declarations(self, selector: str) -> list[tuple[str, str]]:
        """Return the declarations of every rule whose selector is exactly the selector, in order."""
        found = []
        for rule_selector, declarations in self.rules:
            if rule_selector == selector:
                found.extend(declarations)
        return found

    def listed_declarations(self, selector: str) -> list[tuple[str, str]]:
        """Return the declarations of every rule whose selector list holds the selector, in order."""
        found = []
        for rule_selector, declarations in self.rules:
            if selector in [part.strip() for part in rule_selector.split(",")]:
                found.extend(declarations)
        return found

    def property_value(self, declarations: list[tuple[str, str]], names: tuple[str, ...]) -> str | None:
        """Return the value of the last declaration whose name is one of the names."""
        values = [value for name, value in declarations if name in names]
        return values[-1] if values else None

    def ground(self, declarations: list[tuple[str, str]]) -> str | None:
        """Return the `background` or `background-color` value of the declarations."""
        return self.property_value(declarations, ("background", "background-color"))

    def text_color(self, declarations: list[tuple[str, str]]) -> str | None:
        """Return the `color` value of the declarations."""
        return self.property_value(declarations, ("color",))


def has_color(value: str | None, color: str) -> bool:
    """Return True when the value is the color, or holds it as one of its tokens."""
    if value is None:
        return False
    return color.lower() in value.lower().split()
