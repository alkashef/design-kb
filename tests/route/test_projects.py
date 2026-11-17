"""Route tests of the Project pages (M5): FR-21 and FR-28."""

import re


def project_form(name="Invented SerDes", **extra):
    """Return the form fields of a project, with invented defaults."""
    fields = {
        "name": name,
        "description": "An invented test chip",
        "year": "2024",
        "process_technology": "7nm",
    }
    fields.update(extra)
    return fields


def add_project(client, **fields):
    """Post a new project and return its ID, taken from the redirect address."""
    response = client.post("/projects", data=project_form(**fields), follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["location"]
    assert re.fullmatch(r"/projects/[^/]+", location)
    return location.rsplit("/", 1)[1]


def listed_project_ids(client):
    """Return the project IDs of the rows that the project list shows."""
    response = client.get("/projects")
    assert response.status_code == 200
    return re.findall(r'data-project-id="([^"]+)"', response.text)


def test_fr_21_create_project_shows_in_the_list_and_is_selected(client):
    project_id = add_project(
        client, name="Invented SerDes", description="Chip about eyes", year="2023"
    )
    assert project_id in listed_project_ids(client)
    page = client.get(f"/projects/{project_id}")
    assert page.status_code == 200
    assert "Invented SerDes" in page.text
    assert "Chip about eyes" in page.text
    assert "2023" in page.text
    assert "7nm" in page.text


def test_fr_21_edit_project_saves_the_new_values(client):
    project_id = add_project(client, name="Invented SerDes")
    response = client.post(
        f"/projects/{project_id}",
        data=project_form(
            name="Renamed PLL", description="Now about clocks", year="2025",
            process_technology="5nm",
        ),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project_id}"
    page = client.get(f"/projects/{project_id}").text
    assert "Renamed PLL" in page
    assert "Now about clocks" in page
    assert "2025" in page
    assert "5nm" in page
    assert "Invented SerDes" not in page


def test_fr_28_delete_project_removes_it_from_the_list(client):
    keep = add_project(client, name="Keep Invented")
    gone = add_project(client, name="Gone Invented")
    response = client.post(f"/projects/{gone}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/projects"
    assert listed_project_ids(client) == [keep]
    assert client.get(f"/projects/{gone}").status_code == 404
