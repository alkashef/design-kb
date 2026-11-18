"""Route tests of the Level thresholds table on the Settings page (M17): FR-31."""

from html.parser import HTMLParser

from tests.route.test_settings import DEFAULTS, post_thresholds

COLUMNS = ("level", "name", "source", "lead projects", "member projects")
LEVEL_NAMES = {1: "Aware", 2: "Hands-on", 3: "Lead", 4: "Senior lead", 5: "Expert"}


class TableParser(HTMLParser):
    """Collects the header cells, and the text and input names of each body row of the tables."""

    def __init__(self):
        """Start with nothing collected."""
        super().__init__()
        self.tables = 0
        self.headers: list[str] = []
        self.rows: list[dict] = []
        self._in_table = False
        self._row: dict | None = None
        self._header: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        """Open a table, a row, a header cell or record an input of the open row."""
        attributes = dict(attrs)
        if tag == "table":
            self.tables += 1
            self._in_table = True
        elif tag == "tr" and self._in_table:
            self._row = {"text": "", "inputs": {}}
        elif tag == "th" and self._in_table:
            self._header = []
        elif tag == "input" and self._row is not None and attributes.get("name"):
            self._row["inputs"][attributes["name"]] = attributes.get("value") or ""

    def handle_endtag(self, tag):
        """Close a header cell, a row or the table."""
        if tag == "th" and self._header is not None:
            self.headers.append(" ".join("".join(self._header).split()))
            self._header = None
        elif tag == "tr" and self._row is not None:
            if self._row["inputs"] or self._row["text"].strip():
                self.rows.append(self._row)
            self._row = None
        elif tag == "table":
            self._in_table = False

    def handle_data(self, data):
        """Add text to the open header cell or row."""
        if self._header is not None:
            self._header.append(data)
        elif self._row is not None:
            self._row["text"] += " " + data


def read_table(client) -> TableParser:
    """Fetch the Settings page and parse its tables."""
    response = client.get("/settings")
    assert response.status_code == 200
    parser = TableParser()
    parser.feed(response.text)
    return parser


def field_names(level: int) -> set[str]:
    """Return the 4 form field names of a level."""
    return {
        f"level{level}_{part}"
        for part in ("lead_from", "lead_to", "member_from", "member_to")
    }


def test_fr_31_settings_thresholds_are_a_table_with_the_five_columns(client):
    table = read_table(client)

    assert table.tables >= 1
    headers = [header.lower() for header in table.headers]
    assert len(headers) == 5
    for header, column in zip(headers, COLUMNS):
        assert header.startswith(column), (header, column)


def test_fr_31_settings_table_has_a_row_for_each_of_the_five_levels(client):
    rows = read_table(client).rows

    assert len(rows) == 5
    for number, row in zip(range(1, 6), rows):
        words = row["text"].split()
        assert words[0] == str(number), row["text"]
        assert LEVEL_NAMES[number] in row["text"]


def test_fr_31_settings_table_edits_levels_2_to_4_only(client):
    rows = read_table(client).rows

    assert len(rows) == 5
    for number, row in zip(range(1, 6), rows):
        if number in (2, 3, 4):
            assert set(row["inputs"]) == field_names(number)
        else:
            assert row["inputs"] == {}


def test_fr_31_settings_table_shows_the_saved_values(client):
    response = post_thresholds(
        client,
        level2_member_from="2",
        level3_lead_from="1",
        level3_lead_to="5",
        level4_lead_from="7",
        level4_member_to="9",
    )
    assert response.status_code == 303
    expected = dict(DEFAULTS)
    expected.update(
        level2_member_from="2",
        level3_lead_to="5",
        level4_lead_from="7",
        level4_member_to="9",
    )

    rows = read_table(client).rows

    shown = {}
    for row in rows:
        shown.update(row["inputs"])
    assert shown == expected
