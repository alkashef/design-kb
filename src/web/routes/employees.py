"""The Employees list, the profile and the employee form (FR-10, FR-20, FR-28)."""

from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.domain.models import CAREER_LEVELS, Employee
from src.services.employees import EmployeeError, EmployeeService, UnknownEmployee


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the employee pages, rendered with templates."""
    router = APIRouter()

    def service_of(request: Request) -> EmployeeService:
        """Return the employee service of the app."""
        return EmployeeService(request.app.state.store, request.app.state.options.page_size)

    def find(request: Request, employee_id: str) -> Employee:
        """Return the employee, or answer 404."""
        try:
            return service_of(request).get(employee_id)
        except UnknownEmployee:
            raise HTTPException(status_code=404, detail="Unknown employee")

    def render_form(request, employee, is_new, message="", status=200):
        """Render the employee form with an optional message."""
        context = {
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
        context = {
            "active_page": "employees",
            "result": service.list(filter, team, career_level, page),
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
        except EmployeeError as error:
            form = Employee("", name, job_title, career_level, team, skill_gaps)
            return render_form(request, form, True, str(error), 422)
        return RedirectResponse(f"/employees/{employee_id}", status_code=303)

    @router.get("/employees/{employee_id}", response_class=HTMLResponse)
    def employee_profile(request: Request, employee_id: str):
        """Show the profile of one employee."""
        employee = find(request, employee_id)
        return templates.TemplateResponse(
            request, "employee_profile.html", {"active_page": "employees", "employee": employee}
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
        except EmployeeError as error:
            form = Employee(employee_id, name, job_title, career_level, team, skill_gaps)
            return render_form(request, form, False, str(error), 422)
        return RedirectResponse(f"/employees/{employee_id}", status_code=303)

    @router.post("/employees/{employee_id}/delete")
    def delete_employee(request: Request, employee_id: str):
        """Delete an employee and go back to the list."""
        find(request, employee_id)
        service_of(request).delete(employee_id)
        return RedirectResponse("/employees", status_code=303)

    return router
