"""The Project page: the project list and the detail of one project (FR-21, FR-28)."""

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.services.projects import ProjectError, ProjectService, UnknownProject


def _fields(name, description, year, process_technology) -> dict:
    """Return the form values as a dict for the template."""
    return {
        "name": name,
        "description": description,
        "year": year,
        "process_technology": process_technology,
    }


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the project page, rendered with templates."""
    router = APIRouter()

    def service_of(request: Request) -> ProjectService:
        """Return the project service of the app."""
        return ProjectService(request.app.state.store)

    def render(request, selected, mode="view", form=None, message="", status=200):
        """Render the page: mode is view, new or edit; form holds the field values to show."""
        context = {
            "active_page": "projects",
            "projects": service_of(request).list(),
            "selected": selected,
            "mode": mode,
            "form": form or {},
            "message": message,
        }
        return templates.TemplateResponse(request, "projects.html", context, status_code=status)

    def find(request: Request, project_id: str):
        """Return the project, or answer 404."""
        try:
            return service_of(request).get(project_id)
        except UnknownProject:
            raise HTTPException(status_code=404, detail="Unknown project")

    @router.get("/projects", response_class=HTMLResponse)
    def project_list(request: Request):
        """Show the page with the first project selected."""
        projects = service_of(request).list()
        return render(request, projects[0] if projects else None)

    @router.get("/projects/new", response_class=HTMLResponse)
    def new_project_form(request: Request):
        """Show the form for a new project."""
        return render(request, None, "new")

    @router.post("/projects")
    def create_project(
        request: Request,
        name: str = Form(""),
        description: str = Form(""),
        year: str = Form(""),
        process_technology: str = Form(""),
    ):
        """Create a project and select it."""
        try:
            project_id = service_of(request).add(name, description, year, process_technology)
        except ProjectError as error:
            form = _fields(name, description, year, process_technology)
            return render(request, None, "new", form, str(error), 422)
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    @router.get("/projects/{project_id}", response_class=HTMLResponse)
    def project_detail(request: Request, project_id: str):
        """Show the page with one project selected."""
        return render(request, find(request, project_id))

    @router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
    def edit_project_form(request: Request, project_id: str):
        """Show the form of an existing project."""
        project = find(request, project_id)
        form = _fields(project.name, project.description, project.year, project.process_technology)
        return render(request, project, "edit", form)

    @router.post("/projects/{project_id}")
    def save_project(
        request: Request,
        project_id: str,
        name: str = Form(""),
        description: str = Form(""),
        year: str = Form(""),
        process_technology: str = Form(""),
    ):
        """Save a project and select it."""
        project = find(request, project_id)
        try:
            service_of(request).save(project_id, name, description, year, process_technology)
        except ProjectError as error:
            form = _fields(name, description, year, process_technology)
            return render(request, project, "edit", form, str(error), 422)
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    @router.post("/projects/{project_id}/delete")
    def delete_project(request: Request, project_id: str):
        """Delete a project and go back to the list."""
        find(request, project_id)
        service_of(request).delete(project_id)
        return RedirectResponse("/projects", status_code=303)

    return router
