"""The Search page and its preview (FR-01 to FR-07, D-18)."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.domain.levels import LEVEL_NAMES
from src.domain.models import EmbeddingUnavailable
from src.services.assignments import AssignmentService
from src.services.employees import EmployeeService, UnknownEmployee
from src.services.search import SearchService
from src.web.errors import search_failure

SEARCH_PAGE = "search.html"
BODY_PART = "partials/search_body.html"
PREVIEW_PART = "partials/preview.html"


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the Search page, rendered with templates."""
    router = APIRouter()

    def employees_of(request: Request) -> EmployeeService:
        """Return the employee service of the app."""
        state = request.app.state
        return EmployeeService(state.store, state.options.page_size, state.indexing)

    def preview_of(request: Request, employee_id: str) -> dict:
        """Return the template values of the preview of one employee, or answer 404."""
        employees = employees_of(request)
        try:
            employee = employees.get(employee_id)
        except UnknownEmployee:
            raise HTTPException(status_code=404, detail="Unknown employee")
        state = request.app.state
        return {
            "employee": employee,
            "skill_groups": employees.skill_groups(employee_id),
            "assignment_rows": AssignmentService(state.store, state.indexing).for_employee(
                employee_id
            ),
            "level_names": LEVEL_NAMES,
        }

    def render_search(request: Request, query: str):
        """Render the Search page, or only its results and preview for an HTMX request."""
        state = request.app.state
        search = SearchService(
            state.store, state.embedder, employees_of(request), state.options.search_result_limit
        )
        message, status, results = "", 200, []
        try:
            results = search.experience(query)
        except EmbeddingUnavailable:
            message, status = search_failure()
        context = {
            "active_page": "search",
            "q": query,
            "results": results,
            "level_names": LEVEL_NAMES,
            "message": message,
            "preview": preview_of(request, results[0].employee.id) if results else None,
        }
        template = BODY_PART if request.headers.get("HX-Request") else SEARCH_PAGE
        return templates.TemplateResponse(request, template, context, status_code=status)

    @router.get("/", response_class=HTMLResponse)
    def search_page(request: Request):
        """Show the Search page with no results."""
        return render_search(request, "")

    @router.get("/search", response_class=HTMLResponse)
    def search_results(request: Request, q: str = ""):
        """Show the results for the query and the preview of the first result."""
        return render_search(request, q)

    @router.get("/search/preview/{employee_id}", response_class=HTMLResponse)
    def search_preview(request: Request, employee_id: str):
        """Show the preview part for one employee."""
        return templates.TemplateResponse(
            request, PREVIEW_PART, {"preview": preview_of(request, employee_id)}
        )

    return router
