"""The Employees list, the profile, the employee form and the flags (FR-10, FR-11, FR-20, FR-23, FR-28)."""

from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.domain.levels import LEVEL_NAMES
from src.domain.models import CAREER_LEVELS, EmbeddingUnavailable, Employee
from src.services.assignments import AssignmentService
from src.services.employees import EmployeeError, EmployeeService, UnknownEmployee
from src.services.flags import FlagError, FlagService
from src.web.errors import failure_of


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the employee pages, rendered with templates."""
    router = APIRouter()

    def service_of(request: Request) -> EmployeeService:
        """Return the employee service of the app."""
        state = request.app.state
        return EmployeeService(state.store, state.options.page_size, state.indexing)

    def find(request: Request, employee_id: str) -> Employee:
        """Return the employee, or answer 404."""
        try:
            return service_of(request).get(employee_id)
        except UnknownEmployee:
            raise HTTPException(status_code=404, detail="Unknown employee")

    def render_form(request, employee, is_new, message="", status=200, flag_message=""):
        """Render the employee form with an optional message, and the flags of an existing employee."""
        flag_service = FlagService(request.app.state.store)
        context = {
            "flags": [] if is_new else flag_service.for_employee(employee.id),
            "leaf_options": flag_service.leaf_options(),
            "flag_message": flag_message,
            "level_names": LEVEL_NAMES,
            "active_page": "employees",
            "employee": employee,
            "is_new": is_new,
            "career_levels": CAREER_LEVELS,
            "message": message,
        }
        return templates.TemplateResponse(
            request, "employee_form.html", context, status_code=status
        )

    @router.get("/employees", response_class=HTMLResponse)
    def employee_list(
        request: Request, filter: str = "", team: str = "", career_level: str = "", page: int = 1
    ):
        """Show one page of the Employees list."""
        service = service_of(request)
        result = service.list(filter, team, career_level, page)
        context = {
            "active_page": "employees",
            "result": result,
            "top_skills": service.top_skills([e.id for e in result.rows]),
            "level_names": LEVEL_NAMES,
            "filter": filter,
            "team": team,
            "career_level": career_level,
            "teams": service.teams(),
            "career_levels": CAREER_LEVELS,
            "query": urlencode({"filter": filter, "team": team, "career_level": career_level}),
        }
        return templates.TemplateResponse(request, "employees.html", context)

    @router.get("/employees/new", response_class=HTMLResponse)
    def new_employee_form(request: Request):
        """Show the form for a new employee."""
        return render_form(request, Employee("", "", "", "Mid", ""), True)

    @router.post("/employees")
    def create_employee(
        request: Request,
        name: str = Form(""),
        job_title: str = Form(""),
        career_level: str = Form(""),
        team: str = Form(""),
        skill_gaps: str = Form(""),
    ):
        """Create an employee and open the profile."""
        try:
            employee_id = service_of(request).add(name, job_title, career_level, team, skill_gaps)
        except (EmployeeError, EmbeddingUnavailable) as error:
            message, status = failure_of(error)
            form = Employee("", name, job_title, career_level, team, skill_gaps)
            return render_form(request, form, True, message, status)
        return RedirectResponse(f"/employees/{employee_id}", status_code=303)

    @router.get("/employees/{employee_id}", response_class=HTMLResponse)
    def employee_profile(request: Request, employee_id: str):
        """Show the profile of one employee."""
        employee = find(request, employee_id)
        return templates.TemplateResponse(
            request,
            "employee_profile.html",
            {
                "active_page": "employees",
                "employee": employee,
                "skill_groups": service_of(request).skill_groups(employee_id),
                "level_names": LEVEL_NAMES,
                "assignment_rows": AssignmentService(
                    request.app.state.store, request.app.state.indexing
                ).for_employee(employee_id),
            },
        )

    @router.get("/employees/{employee_id}/edit", response_class=HTMLResponse)
    def edit_employee_form(request: Request, employee_id: str):
        """Show the form of an existing employee."""
        return render_form(request, find(request, employee_id), False)

    @router.post("/employees/{employee_id}")
    def save_employee(
        request: Request,
        employee_id: str,
        name: str = Form(""),
        job_title: str = Form(""),
        career_level: str = Form(""),
        team: str = Form(""),
        skill_gaps: str = Form(""),
    ):
        """Save an employee and open the profile."""
        try:
            service_of(request).save(employee_id, name, job_title, career_level, team, skill_gaps)
        except UnknownEmployee:
            raise HTTPException(status_code=404, detail="Unknown employee")
        except (EmployeeError, EmbeddingUnavailable) as error:
            message, status = failure_of(error)
            form = Employee(employee_id, name, job_title, career_level, team, skill_gaps)
            return render_form(request, form, False, message, status)
        return RedirectResponse(f"/employees/{employee_id}", status_code=303)

    @router.post("/employees/{employee_id}/delete")
    def delete_employee(request: Request, employee_id: str):
        """Delete an employee and go back to the list."""
        find(request, employee_id)
        service_of(request).delete(employee_id)
        return RedirectResponse("/employees", status_code=303)

    @router.post("/employees/{employee_id}/flags")
    def set_flag(
        request: Request, employee_id: str, leaf_id: str = Form(""), flag: str = Form("")
    ):
        """Set the Aware or Expert flag of an employee on a leaf."""
        employee = find(request, employee_id)
        try:
            FlagService(request.app.state.store).set(employee_id, leaf_id, flag)
        except FlagError as error:
            return render_form(request, employee, False, status=422, flag_message=str(error))
        return RedirectResponse(f"/employees/{employee_id}/edit", status_code=303)

    @router.post("/employees/{employee_id}/flags/{leaf_id}/delete")
    def remove_flag(request: Request, employee_id: str, leaf_id: str):
        """Remove the flag of an employee on a leaf."""
        find(request, employee_id)
        FlagService(request.app.state.store).remove(employee_id, leaf_id)
        return RedirectResponse(f"/employees/{employee_id}/edit", status_code=303)

    return router
