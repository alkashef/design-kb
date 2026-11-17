"""Route tests of the assignments (M6): FR-22, FR-28, FR-29, FR-40, FR-41 and FR-42."""

from html.parser import HTMLParser


class AssignmentPage(HTMLParser):
    """Collects the assignment rows, the leaf lists and the alerts of a page."""

    def __init__(self):
        """Start with no rows, no options and no alerts."""
        super().__init__()
        self.rows: dict[str, list[str]] = {}
        self.leaf_options: list[str] = []
        self.alerts = 0
        self._row_id = None
        self._row_tag = None
        self._depth = 0
        self._in_leaf_select = False
        self._in_option = False
        self._option_selected = False

    def handle_starttag(self, tag, attrs):
        """Track the current assignment row, the leaf select and the alerts."""
        attributes = dict(attrs)
        if attributes.get("role") == "alert":
            self.alerts += 1
        if self._row_id is not None and tag == self._row_tag:
            self._depth += 1
        if "data-assignment-id" in attributes and self._row_id is None:
            self._row_id = attributes["data-assignment-id"]
            self._row_tag = tag
            self._depth = 1
            self.rows.setdefault(self._row_id, [])
        if tag == "select" and attributes.get("name") == "leaf_id":
            self._in_leaf_select = True
        if tag == "option":
            self._in_option = True
            self._option_selected = "selected" in attributes
            if self._in_leaf_select and attributes.get("value"):
                self.leaf_options.append(attributes["value"])
        if tag == "input" and self._row_id is not None and attributes.get("value"):
            is_unchecked_radio = attributes.get("type") == "radio" and "checked" not in attributes
            if not is_unchecked_radio:
                self.rows[self._row_id].append(attributes["value"])

    def handle_endtag(self, tag):
        """Close the current row, the option and the leaf select."""
        if tag == "option":
            self._in_option = False
        if tag == "select":
            self._in_leaf_select = False
            self._in_option = False
        if self._row_id is not None and tag == self._row_tag:
            self._depth -= 1
            if self._depth == 0:
                self._row_id = None
                self._row_tag = None

    def handle_data(self, data):
        """Keep the text of the current row, but not the text of an option that is not selected."""
        if self._row_id is None:
            return
        if self._in_option and not self._option_selected:
            return
        self.rows[self._row_id].append(data)

    def row_text(self, assignment_id: str) -> str:
        """Return the text of one row in lower case, or an empty text when there is no such row."""
        return " ".join(self.rows.get(assignment_id, [])).lower()


def read_page(response) -> AssignmentPage:
    """Parse the HTML of a response."""
    page = AssignmentPage()
    page.feed(response.text)
    return page


def add_node(client, name, parent_id=""):
    """Post a new skill tree node and return its ID."""
    response = client.post(
        "/skill-tree/nodes",
        data={"parent_id": parent_id, "name": name, "description": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_employee(client, name="Ada Invented"):
    """Post a new employee and return its ID."""
    fields = {
        "name": name,
        "job_title": "Design Engineer",
        "career_level": "Senior",
        "team": "Analog",
        "skill_gaps": "",
    }
    response = client.post("/employees", data=fields, follow_redirects=False)
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def add_project(client, name="Invented SerDes"):
    """Post a new project and return its ID."""
    fields = {
        "name": name,
        "description": "An invented test chip",
        "year": "2024",
        "process_technology": "7nm",
    }
    response = client.post("/projects", data=fields, follow_redirects=False)
    assert response.status_code == 303
    return response.headers["location"].rsplit("/", 1)[1]


def assignment_form(employee_id, leaf_id, participation="lead", description="Designed it"):
    """Return the form fields of a new assignment."""
    return {
        "employee_id": employee_id,
        "leaf_id": leaf_id,
        "participation": participation,
        "description": description,
    }


def post_assignment(client, project_id, **fields):
    """Post a new assignment of a project and return the response, without following redirects."""
    return client.post(
        f"/projects/{project_id}/assignments",
        data=assignment_form(**fields),
        follow_redirects=False,
    )


def add_assignment(client, project_id, **fields):
    """Post a new assignment, check the redirect and return the ID of the new assignment."""
    before = set(project_rows(client, project_id).rows)
    response = post_assignment(client, project_id, **fields)
    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project_id}"
    new_ids = set(project_rows(client, project_id).rows) - before
    assert len(new_ids) == 1
    return new_ids.pop()


def project_rows(client, project_id) -> AssignmentPage:
    """Return the parsed page of a project."""
    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    return read_page(response)


def profile_rows(client, employee_id) -> AssignmentPage:
    """Return the parsed profile page of an employee."""
    response = client.get(f"/employees/{employee_id}")
    assert response.status_code == 200
    return read_page(response)


def test_fr_22_create_assignment_shows_on_the_project_and_on_the_profile(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client, "Ada Invented")
    project_id = add_project(client, "Invented SerDes")

    assignment_id = add_assignment(
        client, project_id, employee_id=employee_id, leaf_id=leaf_id,
        participation="lead", description="Designed the invented loop filter",
    )

    on_project = project_rows(client, project_id).row_text(assignment_id)
    for text in ("ada invented", "pll", "lead", "designed the invented loop filter"):
        assert text in on_project
    on_profile = profile_rows(client, employee_id).row_text(assignment_id)
    for text in ("invented serdes", "pll", "lead", "designed the invented loop filter"):
        assert text in on_profile


def test_fr_22_edit_assignment_saves_participation_and_description(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client)
    project_id = add_project(client)
    assignment_id = add_assignment(
        client, project_id, employee_id=employee_id, leaf_id=leaf_id,
        participation="lead", description="Designed the invented loop filter",
    )

    response = client.post(
        f"/assignments/{assignment_id}",
        data={
            "leaf_id": leaf_id,
            "participation": "member",
            "description": "Reviewed the invented loop filter",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project_id}"
    for text in (
        project_rows(client, project_id).row_text(assignment_id),
        profile_rows(client, employee_id).row_text(assignment_id),
    ):
        assert "member" in text
        assert "lead" not in text
        assert "reviewed the invented loop filter" in text
        assert "designed the invented loop filter" not in text


def test_fr_28_delete_assignment_removes_it(client):
    leaf_id = add_node(client, "PLL")
    other_leaf_id = add_node(client, "CDR")
    employee_id = add_employee(client)
    project_id = add_project(client)
    gone = add_assignment(client, project_id, employee_id=employee_id, leaf_id=leaf_id)
    keep = add_assignment(client, project_id, employee_id=employee_id, leaf_id=other_leaf_id)

    response = client.post(f"/assignments/{gone}/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project_id}"
    assert list(project_rows(client, project_id).rows) == [keep]
    assert list(profile_rows(client, employee_id).rows) == [keep]


def test_fr_29_delete_employee_deletes_its_assignments(client):
    leaf_id = add_node(client, "PLL")
    gone_employee = add_employee(client, "Gone Invented")
    keep_employee = add_employee(client, "Keep Invented")
    project_id = add_project(client)
    gone = add_assignment(client, project_id, employee_id=gone_employee, leaf_id=leaf_id)
    keep = add_assignment(client, project_id, employee_id=keep_employee, leaf_id=leaf_id)

    response = client.post(f"/employees/{gone_employee}/delete", follow_redirects=False)

    assert response.status_code == 303
    assert gone not in project_rows(client, project_id).rows
    assert list(project_rows(client, project_id).rows) == [keep]
    assert client.post(f"/assignments/{gone}/delete", follow_redirects=False).status_code == 404


def test_fr_29_delete_project_deletes_its_assignments(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client)
    gone_project = add_project(client, "Gone Invented")
    keep_project = add_project(client, "Keep Invented")
    gone = add_assignment(client, gone_project, employee_id=employee_id, leaf_id=leaf_id)
    keep = add_assignment(client, keep_project, employee_id=employee_id, leaf_id=leaf_id)

    response = client.post(f"/projects/{gone_project}/delete", follow_redirects=False)

    assert response.status_code == 303
    assert gone not in profile_rows(client, employee_id).rows
    assert list(profile_rows(client, employee_id).rows) == [keep]
    assert client.post(f"/assignments/{gone}/delete", follow_redirects=False).status_code == 404


def test_fr_40_assignment_form_lists_only_leaves(client):
    parent_id = add_node(client, "Clocking")
    pll_id = add_node(client, "PLL", parent_id=parent_id)
    cdr_id = add_node(client, "CDR", parent_id=parent_id)
    top_leaf_id = add_node(client, "Verification")
    project_id = add_project(client)

    options = set(project_rows(client, project_id).leaf_options)

    assert options == {pll_id, cdr_id, top_leaf_id}
    assert parent_id not in options


def test_fr_41_assignment_on_a_node_with_children_is_rejected_with_a_message(client):
    parent_id = add_node(client, "Clocking")
    add_node(client, "PLL", parent_id=parent_id)
    employee_id = add_employee(client)
    project_id = add_project(client)

    response = post_assignment(client, project_id, employee_id=employee_id, leaf_id=parent_id)

    assert response.status_code == 422
    assert read_page(response).alerts >= 1
    assert project_rows(client, project_id).rows == {}
    assert profile_rows(client, employee_id).rows == {}


def test_fr_42_second_assignment_for_the_same_employee_project_and_leaf_is_rejected(client):
    leaf_id = add_node(client, "PLL")
    employee_id = add_employee(client)
    project_id = add_project(client)
    first = add_assignment(client, project_id, employee_id=employee_id, leaf_id=leaf_id)

    response = post_assignment(
        client, project_id, employee_id=employee_id, leaf_id=leaf_id,
        participation="member", description="A second try",
    )

    assert response.status_code == 422
    assert read_page(response).alerts >= 1
    assert list(project_rows(client, project_id).rows) == [first]


def test_fr_42_same_leaf_for_another_employee_or_another_project_is_accepted(client):
    leaf_id = add_node(client, "PLL")
    ada = add_employee(client, "Ada Invented")
    bo = add_employee(client, "Bo Invented")
    first_project = add_project(client, "First Invented")
    second_project = add_project(client, "Second Invented")
    add_assignment(client, first_project, employee_id=ada, leaf_id=leaf_id)

    other_employee = post_assignment(client, first_project, employee_id=bo, leaf_id=leaf_id)
    other_project = post_assignment(client, second_project, employee_id=ada, leaf_id=leaf_id)

    assert other_employee.status_code == 303
    assert other_project.status_code == 303
    assert len(project_rows(client, first_project).rows) == 2
    assert len(project_rows(client, second_project).rows) == 1
