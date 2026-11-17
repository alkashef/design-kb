"""The Project page: the project list, the detail of one project and its assignments
(FR-21, FR-22, FR-28)."""

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.domain.entry_rules import PARTICIPATIONS
from src.services.assignments import AssignmentError, AssignmentService, UnknownAssignment
from src.services.projects import ProjectError, ProjectService, UnknownProject


def _fields(name, description, year, process_technology) -> dict:
    """Return the form values as a dict for the template."""
    return {
        "name": name,
        "description": description,
        "year": year,
        "process_technology": process_technology,
    }


def _assignment_fields(employee_id, leaf_id, participation, description) -> dict:
    """Return the assignment form values as a dict for the template."""
    return {
        "employee_id": employee_id,
        "leaf_id": leaf_id,
        "participation": participation,
        "description": description,
    }


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the project page, rendered with templates."""
    router = APIRouter()

    def service_of(request: Request) -> ProjectService:
        """Return the project service of the app."""
        return ProjectService(request.app.state.store)

    def assignments_of(request: Request) -> AssignmentService:
        """Return the assignment service of the app."""
        return AssignmentService(request.app.state.store)

    def render(
        request, selected, mode="view", form=None, message="", status=200, assignment_form=None,
        editing_id="",
    ):
        """Render the page: mode is view, new or edit; form holds the field values to show.

        assignment_form holds the values of the assignment panel, and editing_id is the ID of
        the assignment that the panel edits (empty for a new assignment).
        """
        assignments = assignments_of(request)
        context = {
            "active_page": "projects",
            "projects": service_of(request).list(),
            "selected": selected,
            "mode": mode,
            "form": form or {},
            "message": message,
            "assignment_rows": assignments.for_project(selected.id) if selected else [],
            "employees": assignments.employee_options(),
            "leaves": assignments.leaf_options(),
            "participations": PARTICIPATIONS,
            "assignment_form": assignment_form or _assignment_fields("", "", "member", ""),
            "editing_id": editing_id,
        }
        return templates.TemplateResponse(request, "projects.html", context, status_code=status)

    def find_assignment(request: Request, assignment_id: str):
        """Return the assignment, or answer 404."""
        try:
            return assignments_of(request).get(assignment_id)
        except UnknownAssignment:
            raise HTTPException(status_code=404, detail="Unknown assignment")

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
    def project_detail(request: Request, project_id: str, edit_assignment: str = ""):
        """Show the page with one project selected; edit_assignment opens that assignment."""
        project = find(request, project_id)
        if not edit_assignment:
            return render(request, project)
        assignment = find_assignment(request, edit_assignment)
        if assignment.project_id != project_id:
            raise HTTPException(status_code=404, detail="Unknown assignment")
        form = _assignment_fields(
            assignment.employee_id, assignment.leaf_id, assignment.participation,
            assignment.description,
        )
        return render(request, project, assignment_form=form, editing_id=assignment.id)

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

    @router.post("/projects/{project_id}/assignments")
    def create_assignment(
        request: Request,
        project_id: str,
        employee_id: str = Form(""),
        leaf_id: str = Form(""),
        participation: str = Form(""),
        description: str = Form(""),
    ):
        """Create an assignment and go back to the project."""
        project = find(request, project_id)
        try:
            assignments_of(request).add(project_id, employee_id, leaf_id, participation, description)
        except AssignmentError as error:
            form = _assignment_fields(employee_id, leaf_id, participation, description)
            return render(request, project, message=str(error), status=422, assignment_form=form)
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    @router.post("/assignments/{assignment_id}")
    def save_assignment(
        request: Request,
        assignment_id: str,
        leaf_id: str = Form(""),
        participation: str = Form(""),
        description: str = Form(""),
    ):
        """Save an assignment and go back to its project."""
        assignment = find_assignment(request, assignment_id)
        try:
            assignments_of(request).save(assignment_id, leaf_id, participation, description)
        except AssignmentError as error:
            project = find(request, assignment.project_id)
            form = _assignment_fields(assignment.employee_id, leaf_id, participation, description)
            return render(
                request, project, message=str(error), status=422, assignment_form=form,
                editing_id=assignment_id,
            )
        return RedirectResponse(f"/projects/{assignment.project_id}", status_code=303)

    @router.post("/assignments/{assignment_id}/delete")
    def delete_assignment(request: Request, assignment_id: str):
        """Delete an assignment and go back to its project."""
        assignment = find_assignment(request, assignment_id)
        assignments_of(request).delete(assignment_id)
        return RedirectResponse(f"/projects/{assignment.project_id}", status_code=303)

    return router
