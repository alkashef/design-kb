"""The Engineers list, the profile, the engineer form and the flags (FR-10, FR-11, FR-20, FR-23, FR-28)."""

from urllib.parse import parse_qs, urlencode, urlsplit

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.domain.levels import LEVEL_NAMES
from src.domain.models import CAREER_LEVELS, EmbeddingUnavailable, Engineer
from src.services.assignments import AssignmentService
from src.services.engineers import EngineerError, EngineerService, UnknownEngineer
from src.services.flags import FlagError, FlagService
from src.web.errors import failure_of
from src.web.preview import preview_context


LIST_KEYS = ("filter", "team", "career_level", "page")
PANEL_PART = "partials/engineer_panel.html"


def list_query(values: dict) -> str:
    """Return the query string of the Engineers list: the filters and the page, without empty values."""
    return urlencode({key: values.get(key, "") for key in LIST_KEYS if values.get(key, "")})


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the engineer pages, rendered with templates."""
    router = APIRouter()

    def service_of(request: Request) -> EngineerService:
        """Return the engineer service of the app."""
        state = request.app.state
        return EngineerService(state.store, state.options.page_size, state.indexing)

    def find(request: Request, engineer_id: str) -> Engineer:
        """Return the engineer, or answer 404."""
        try:
            return service_of(request).get(engineer_id)
        except UnknownEngineer:
            raise HTTPException(status_code=404, detail="Unknown engineer")

    def render_form(request, engineer, is_new, message="", status=200, flag_message=""):
        """Render the engineer form with an optional message, and the flags of an existing engineer."""
        flag_service = FlagService(request.app.state.store)
        context = {
            "flags": [] if is_new else flag_service.for_engineer(engineer.id),
            "leaf_options": flag_service.leaf_options(),
            "flag_message": flag_message,
            "level_names": LEVEL_NAMES,
            "active_page": "engineers",
            "engineer": engineer,
            "is_new": is_new,
            "career_levels": CAREER_LEVELS,
            "message": message,
        }
        return templates.TemplateResponse(
            request, "engineer_form.html", context, status_code=status
        )

    def selection_of(request: Request, engineer_id: str):
        """Return the card values of the selected engineer, or None for no or an unknown ID."""
        if not engineer_id:
            return None
        try:
            return preview_context(request, engineer_id)
        except HTTPException:
            return None

    @router.get("/engineers", response_class=HTMLResponse)
    def engineer_list(
        request: Request,
        filter: str = "",
        team: str = "",
        career_level: str = "",
        page: int = 1,
        selected: str = "",
    ):
        """Show one page of the Engineers list, with the detail pane of the selected engineer."""
        service = service_of(request)
        result = service.list(filter, team, career_level, page)
        preview = selection_of(request, selected)
        list_values = {"filter": filter, "team": team, "career_level": career_level}
        if page > 1:
            list_values["page"] = str(page)
        context = {
            "active_page": "engineers",
            "result": result,
            "top_skills": service.top_skills([e.id for e in result.rows]),
            "level_names": LEVEL_NAMES,
            "filter": filter,
            "team": team,
            "career_level": career_level,
            "teams": service.teams(),
            "career_levels": CAREER_LEVELS,
            "query": urlencode({"filter": filter, "team": team, "career_level": career_level}),
            "list_query": list_query(list_values),
            "preview": preview,
            "selected_id": selected if preview else "",
            "close_href": "/engineers?" + list_query(list_values),
        }
        return templates.TemplateResponse(request, "engineers.html", context)

    @router.get("/engineer-panel", response_class=HTMLResponse)
    def empty_engineer_panel():
        """Give the empty content of the detail slot."""
        return HTMLResponse("")

    @router.get("/engineer-panel/{engineer_id}", response_class=HTMLResponse)
    def engineer_panel(request: Request, engineer_id: str):
        """Give the handle and the detail pane of one engineer, for the detail slot."""
        current = parse_qs(urlsplit(request.headers.get("HX-Current-URL", "")).query)
        values = {key: current.get(key, [""])[0] for key in LIST_KEYS}
        context = {
            "preview": preview_context(request, engineer_id),
            "close_href": "/engineers?" + list_query(values),
        }
        return templates.TemplateResponse(request, PANEL_PART, context)

    @router.get("/engineers/new", response_class=HTMLResponse)
    def new_engineer_form(request: Request):
        """Show the form for a new engineer."""
        return render_form(request, Engineer("", "", "", "Mid", ""), True)

    @router.post("/engineers")
    def create_engineer(
        request: Request,
        name: str = Form(""),
        job_title: str = Form(""),
        career_level: str = Form(""),
        team: str = Form(""),
        skill_gaps: str = Form(""),
    ):
        """Create an engineer and open the profile."""
        try:
            engineer_id = service_of(request).add(name, job_title, career_level, team, skill_gaps)
        except (EngineerError, EmbeddingUnavailable) as error:
            message, status = failure_of(error)
            form = Engineer("", name, job_title, career_level, team, skill_gaps)
            return render_form(request, form, True, message, status)
        return RedirectResponse(f"/engineers/{engineer_id}", status_code=303)

    @router.get("/engineers/{engineer_id}", response_class=HTMLResponse)
    def engineer_profile(request: Request, engineer_id: str):
        """Show the profile of one engineer."""
        engineer = find(request, engineer_id)
        return templates.TemplateResponse(
            request,
            "engineer_profile.html",
            {
                "active_page": "engineers",
                "engineer": engineer,
                "skill_groups": service_of(request).skill_groups(engineer_id),
                "level_names": LEVEL_NAMES,
                "assignment_rows": AssignmentService(
                    request.app.state.store, request.app.state.indexing
                ).for_engineer(engineer_id),
            },
        )

    @router.get("/engineers/{engineer_id}/edit", response_class=HTMLResponse)
    def edit_engineer_form(request: Request, engineer_id: str):
        """Show the form of an existing engineer."""
        return render_form(request, find(request, engineer_id), False)

    @router.post("/engineers/{engineer_id}")
    def save_engineer(
        request: Request,
        engineer_id: str,
        name: str = Form(""),
        job_title: str = Form(""),
        career_level: str = Form(""),
        team: str = Form(""),
        skill_gaps: str = Form(""),
    ):
        """Save an engineer and open the profile."""
        try:
            service_of(request).save(engineer_id, name, job_title, career_level, team, skill_gaps)
        except UnknownEngineer:
            raise HTTPException(status_code=404, detail="Unknown engineer")
        except (EngineerError, EmbeddingUnavailable) as error:
            message, status = failure_of(error)
            form = Engineer(engineer_id, name, job_title, career_level, team, skill_gaps)
            return render_form(request, form, False, message, status)
        return RedirectResponse(f"/engineers/{engineer_id}", status_code=303)

    @router.post("/engineers/{engineer_id}/delete")
    def delete_engineer(request: Request, engineer_id: str):
        """Delete an engineer and go back to the list."""
        find(request, engineer_id)
        service_of(request).delete(engineer_id)
        return RedirectResponse("/engineers", status_code=303)

    @router.post("/engineers/{engineer_id}/flags")
    def set_flag(
        request: Request, engineer_id: str, leaf_id: str = Form(""), flag: str = Form("")
    ):
        """Set the Aware or Expert flag of an engineer on a leaf."""
        engineer = find(request, engineer_id)
        try:
            FlagService(request.app.state.store).set(engineer_id, leaf_id, flag)
        except FlagError as error:
            return render_form(request, engineer, False, status=422, flag_message=str(error))
        return RedirectResponse(f"/engineers/{engineer_id}/edit", status_code=303)

    @router.post("/engineers/{engineer_id}/flags/{leaf_id}/delete")
    def remove_flag(request: Request, engineer_id: str, leaf_id: str):
        """Remove the flag of an engineer on a leaf."""
        find(request, engineer_id)
        FlagService(request.app.state.store).remove(engineer_id, leaf_id)
        return RedirectResponse(f"/engineers/{engineer_id}/edit", status_code=303)

    return router
