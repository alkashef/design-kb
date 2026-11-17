"""Route tests of the app shell (M1): the Search page opens with no login (NFR-02)."""

from html.parser import HTMLParser

SIDEBAR_LINKS = {
    "Search": {"/", "/search"},
    "Employees": {"/employees"},
    "Skill tree": {"/skill-tree"},
    "Projects": {"/projects"},
    "Settings": {"/settings"},
}


class LinkCollector(HTMLParser):
    """Collects the text and the href of each link of a page."""

    def __init__(self):
        """Start with no links."""
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        """Start a link at an <a> tag."""
        if tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._text = []

    def handle_data(self, data):
        """Keep the text inside the open link."""
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        """Close the open link and keep its text and href."""
        if tag == "a" and self._href is not None:
            text = " ".join("".join(self._text).split())
            self.links.append((text, self._href))
            self._href = None


def links_of(html: str) -> list[tuple[str, str]]:
    """Return the (text, href) pairs of the links of a page."""
    collector = LinkCollector()
    collector.feed(html)
    return collector.links


def test_nfr_02_search_page_opens_with_no_login(client):
    """GET / answers 200 with no credentials and shows the five sidebar links."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 200
    links = links_of(response.text)
    for text, paths in SIDEBAR_LINKS.items():
        assert any(
            link_text == text and href in paths for link_text, href in links
        ), f"no link '{text}' to {sorted(paths)} on the Search page"
