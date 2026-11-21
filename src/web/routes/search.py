"""The Search page and its preview (FR-01 to FR-07, D-18)."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.domain.levels import LEVEL_NAMES
from src.domain.models import CAREER_LEVELS, EmbeddingUnavailable
from src.services.assignments import AssignmentService
from src.services.engineers import EngineerService, UnknownEngineer
from src.services.search import SearchFilters, SearchService
from src.web.errors import search_failure

DEFAULT_MIN_LEVEL = 1
GAPS_MODE = "gaps"
EXPERIENCE_MODE = "experience"

SEARCH_PAGE = "search.html"
BODY_PART = "partials/search_body.html"
PREVIEW_PART = "partials/preview.html"


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the Search page, rendered with templates."""
    router = APIRouter()

    def engineers_of(request: Request) -> EngineerService:
        """Return the engineer service of the app."""
        state = request.app.state
        return EngineerService(state.store, state.options.page_size, state.indexing)

    def preview_of(request: Request, engineer_id: str) -> dict:
        """Return the template values of the preview of one engineer, or answer 404."""
        engineers = engineers_of(request)
        try:
            engineer = engineers.get(engineer_id)
        except UnknownEngineer:
            raise HTTPException(status_code=404, detail="Unknown engineer")
        state = request.app.state
        return {
            "engineer": engineer,
            "skill_groups": engineers.skill_groups(engineer_id),
            "assignment_rows": AssignmentService(state.store, state.indexing).for_engineer(
                engineer_id
            ),
            "level_names": LEVEL_NAMES,
        }

    def render_search(request: Request, query: str, filters: SearchFilters, mode: str = EXPERIENCE_MODE):
        """Render the Search page, or only its results and preview for an HTMX request."""
        state = request.app.state
        engineers = engineers_of(request)
        search = SearchService(
            state.store, state.embedder, engineers, state.options.search_result_limit
        )
        message, status, results = "", 200, []
        try:
            run = search.gaps if mode == GAPS_MODE else search.experience
            results = run(query, filters)
        except EmbeddingUnavailable:
            message, status = search_failure()
        context = {
            "active_page": "search",
            "q": query,
            "mode": mode,
            "filters": filters,
            "teams": engineers.teams(),
            "career_levels": CAREER_LEVELS,
            "leaf_options": engineers.leaf_options(),
            "results": results,
            "level_names": LEVEL_NAMES,
            "message": message,
            "preview": preview_of(request, results[0].engineer.id) if results else None,
        }
        template = BODY_PART if request.headers.get("HX-Request") else SEARCH_PAGE
        return templates.TemplateResponse(request, template, context, status_code=status)

    @router.get("/", response_class=HTMLResponse)
    def search_page(request: Request):
        """Show the Search page with no results."""
        return render_search(request, "", SearchFilters())

    @router.get("/search", response_class=HTMLResponse)
    def search_results(
        request: Request,
        q: str = "",
        mode: str = EXPERIENCE_MODE,
        team: str = "",
        career_level: str = "",
        leaf_id: str = "",
        min_level: str = "",
    ):
        """Show the results for the query and filters and the preview of the first result."""
        level = int(min_level) if min_level.isdigit() else DEFAULT_MIN_LEVEL
        filters = SearchFilters(team, career_level, leaf_id, level)
        mode = GAPS_MODE if mode == GAPS_MODE else EXPERIENCE_MODE
        return render_search(request, q, filters, mode)

    @router.get("/search/preview/{engineer_id}", response_class=HTMLResponse)
    def search_preview(request: Request, engineer_id: str):
        """Show the preview part for one engineer."""
        return templates.TemplateResponse(
            request, PREVIEW_PART, {"preview": preview_of(request, engineer_id)}
        )

    return router
