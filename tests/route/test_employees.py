"""Route tests of the Employees pages (M4): FR-10, FR-20 and FR-28."""

import re

TEST_PAGE_SIZE = 10


def employee_form(name="Ada Invented", team="Analog", career_level="Senior", **extra):
    """Return the form fields of an employee, with invented defaults."""
    fields = {
        "name": name,
        "job_title": "Design Engineer",
        "career_level": career_level,
        "team": team,
        "skill_gaps": "",
    }
    fields.update(extra)
    return fields


def add_employee(client, **fields):
    """Post a new employee and return its ID, taken from the redirect address."""
    response = client.post("/employees", data=employee_form(**fields), follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["location"]
    assert re.fullmatch(r"/employees/E-\d{4}", location)
    return location.rsplit("/", 1)[1]


def listed_ids(client, **params):
    """Return the employee IDs of the rows that the Employees list shows."""
    response = client.get("/employees", params=params)
    assert response.status_code == 200
    return re.findall(r'data-employee-id="([^"]+)"', response.text)


def test_fr_20_create_employee_gets_the_next_id_and_opens_the_profile(client):
    first = add_employee(client, name="Ada Invented")
    second = add_employee(client, name="Bo Invented")
    assert first == "E-0001"
    assert second == "E-0002"
    page = client.get(f"/employees/{second}")
    assert page.status_code == 200
    assert "Bo Invented" in page.text


def test_fr_20_edit_employee_saves_the_new_values(client):
    employee_id = add_employee(client, name="Ada Invented", team="Analog")
    response = client.post(
        f"/employees/{employee_id}",
        data=employee_form(
            name="Ada Renamed",
            team="Digital",
            career_level="Staff",
            skill_gaps="Needs jitter analysis",
        ),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == f"/employees/{employee_id}"
    page = client.get(f"/employees/{employee_id}").text
    assert "Ada Renamed" in page
    assert "Digital" in page
    assert "Staff" in page
    assert "Needs jitter analysis" in page
    assert "Ada Invented" not in page


def test_fr_10_open_employee_shows_the_profile_page(client):
    employee_id = add_employee(
        client, name="Cy Invented", team="Mixed-signal", skill_gaps="Needs layout practice"
    )
    page = client.get(f"/employees/{employee_id}")
    assert page.status_code == 200
    for text in ("Cy Invented", "Design Engineer", "Mixed-signal", "Senior", employee_id):
        assert text in page.text
    assert "Needs layout practice" in page.text


def test_fr_10_unknown_employee_gives_404(client):
    assert client.get("/employees/E-9999").status_code == 404


def test_fr_10_list_filters_by_name_team_and_career_level(client):
    ada = add_employee(client, name="Ada Invented", team="Analog", career_level="Senior")
    bo = add_employee(client, name="Bo Invented", team="Digital", career_level="Junior")
    cy = add_employee(client, name="Cy Other", team="Analog", career_level="Junior")
    assert sorted(listed_ids(client)) == sorted([ada, bo, cy])
    assert sorted(listed_ids(client, filter="Invented")) == sorted([ada, bo])
    assert listed_ids(client, filter=bo) == [bo]
    assert sorted(listed_ids(client, team="Analog")) == sorted([ada, cy])
    assert sorted(listed_ids(client, career_level="Junior")) == sorted([bo, cy])
    assert listed_ids(client, team="Analog", career_level="Junior") == [cy]


def test_fr_10_list_shows_page_size_rows_on_one_page(client):
    for number in range(TEST_PAGE_SIZE + 1):
        add_employee(client, name=f"Person {number:02d}")
    first_page = listed_ids(client)
    second_page = listed_ids(client, page=2)
    assert len(first_page) == TEST_PAGE_SIZE
    assert len(second_page) == 1
    assert not set(first_page) & set(second_page)


def test_fr_28_delete_employee_removes_it_from_the_list(client):
    keep = add_employee(client, name="Keep Invented")
    gone = add_employee(client, name="Gone Invented")
    response = client.post(f"/employees/{gone}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/employees"
    assert listed_ids(client) == [keep]
    assert client.get(f"/employees/{gone}").status_code == 404
