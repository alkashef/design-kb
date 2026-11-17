"""The Search page and its preview (FR-01 to FR-07, D-18)."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the Search page, rendered with templates."""
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    def search_page(request: Request):
        """Show the Search page with no results."""
        return templates.TemplateResponse(request, "search.html", {"active_page": "search"})

    return router
