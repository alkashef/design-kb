"""D-44: the sidebar and the Engineers page use the term "engineer"."""
import re

from tests.route.test_app_shell import links_of


def test_d_44_sidebar_and_engineers_page_use_the_term(client):
    response = client.get("/engineers")

    assert response.status_code == 200
    links = links_of(response.text)
    assert ("Engineers", "/engineers") in links
    assert ("Add engineer", "/engineers/new") in links
    assert re.search(r"<h1[^>]*>\s*Engineers\s*</h1>", response.text)
