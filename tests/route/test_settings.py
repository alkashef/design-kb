"""Route tests of the Settings page (M9): FR-31, FR-32, FR-35, FR-36."""

from html.parser import HTMLParser

LEVELS = (2, 3, 4)
FIELDS = ("lead_from", "lead_to", "member_from", "member_to")

# The default thresholds of spec section 2.5, as the text of the form fields.
DEFAULTS = {
    "level2_lead_from": "0",
    "level2_lead_to": "0",
    "level2_member_from": "1",
    "level2_member_to": "",
    "level3_lead_from": "1",
    "level3_lead_to": "2",
    "level3_member_from": "0",
    "level3_member_to": "",
    "level4_lead_from": "3",
    "level4_lead_to": "",
    "level4_member_from": "0",
    "level4_member_to": "",
}


class SettingsPage(HTMLParser):
    """Collects the values of the threshold inputs, the alerts and the levels of a page."""

    def __init__(self):
        """Start with nothing collected."""
        super().__init__()
        self.values: dict[str, str] = {}
        self.levels: dict[str, int] = {}
        self.alerts = 0

    def handle_starttag(self, tag, attrs):
        """Keep each named input value, each level marker and each alert."""
        attributes = dict(attrs)
        if tag == "input" and attributes.get("name", "").startswith("level"):
            self.values[attributes["name"]] = attributes.get("value") or ""
        if "data-leaf-id" in attributes and "data-level" in attributes:
            self.levels[attributes["data-leaf-id"]] = int(attributes["data-level"])
        if attributes.get("role") == "alert":
            self.alerts += 1


def read_page(response) -> SettingsPage:
    """Parse the HTML of a response."""
    page = SettingsPage()
    page.feed(response.text)
    return page


def settings_values(client) -> dict[str, str]:
    """Return the threshold values that the Settings page shows."""
    response = client.get("/settings")
    assert response.status_code == 200
    return read_page(response).values


def post_thresholds(client, **changes):
    """Post all 12 fields (the defaults plus the changes) and return the response."""
    fields = dict(DEFAULTS)
    fields.update(changes)
    return client.post("/settings/thresholds", data=fields, follow_redirects=False)


def add_node(client, name):
    """Post a new top-level skill tree node and return its ID."""
    response = client.post(
        "/skill-tree/nodes",
        data={"parent_id": "", "name": name, "description": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_employee(client):
    """Post a new employee and return its ID."""
    response = client.post(
        "/employees",
        data={
            "name": "Ada Invented",
            "job_title": "Design Engineer",
            "career_level": "Senior",
            "team": "Analog",
            "skill_gaps": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_lead_assignments(client, employee_id, leaf_id, count):
    """Give the employee `count` lead assignments in the leaf, each on its own project."""
    for number in range(count):
        project = client.post(
            "/projects",
            data={
                "name": f"Invented chip {number}",
                "description": "A test chip",
                "year": "2024",
                "process_technology": "7nm",
            },
            follow_redirects=False,
        )
        assert project.status_code == 303
        project_id = project.headers["location"].rsplit("/", 1)[1]
        response = client.post(
            f"/projects/{project_id}/assignments",
            data={
                "employee_id": employee_id,
                "leaf_id": leaf_id,
                "participation": "lead",
                "description": "Led it",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303


def level_on_profile(client, employee_id, leaf_id) -> int:
    """Return the level that the profile page shows for the leaf."""
    response = client.get(f"/employees/{employee_id}")
    assert response.status_code == 200
    return read_page(response).levels[leaf_id]


def test_fr_32_settings_page_shows_the_default_ranges(client):
    assert settings_values(client) == DEFAULTS


def test_fr_31_saved_ranges_change_the_level_on_a_profile(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client)
    add_lead_assignments(client, employee_id, leaf_id, 1)
    assert level_on_profile(client, employee_id, leaf_id) == 3

    response = post_thresholds(client, level3_lead_from="2", level3_lead_to="4")

    assert response.status_code == 303
    assert response.headers["location"] == "/settings"
    assert settings_values(client)["level3_lead_from"] == "2"
    assert level_on_profile(client, employee_id, leaf_id) == 0


def test_fr_31_empty_to_value_means_no_upper_limit(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client)
    add_lead_assignments(client, employee_id, leaf_id, 5)
    # Level 4 needs 50 or more lead projects. Level 3 has no upper limit, so 5 leads give level 3.
    response = post_thresholds(
        client, level3_lead_from="1", level3_lead_to="", level4_lead_from="50"
    )

    assert response.status_code == 303
    assert settings_values(client)["level3_lead_to"] == ""
    assert level_on_profile(client, employee_id, leaf_id) == 3


def test_fr_35_value_that_is_not_a_whole_number_is_rejected_with_a_message(client):
    for bad_value in ("abc", "1.5", "-1", " "):
        response = post_thresholds(client, level2_member_from=bad_value)

        assert response.status_code == 422, bad_value
        assert read_page(response).alerts >= 1, bad_value
    # Nothing was saved.
    assert settings_values(client) == DEFAULTS


def test_fr_35_from_value_above_its_to_value_is_rejected_with_a_message(client):
    response = post_thresholds(client, level3_lead_from="5", level3_lead_to="2")

    assert response.status_code == 422
    assert read_page(response).alerts >= 1
    assert settings_values(client) == DEFAULTS


def test_fr_36_reset_restores_the_default_ranges(client):
    post_thresholds(client, level3_lead_from="2", level3_lead_to="4", level4_lead_from="9")
    assert settings_values(client) != DEFAULTS

    response = client.post("/settings/thresholds/reset", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/settings"
    assert settings_values(client) == DEFAULTS
