"""The Settings page: the level thresholds (FR-31, FR-32, FR-35, FR-36)."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.domain.levels import LEVEL_NAMES
from src.services.thresholds import THRESHOLD_LEVELS, ThresholdError, ThresholdService

logger = logging.getLogger(__name__)

FIELD_NAMES = ("lead_from", "lead_to", "member_from", "member_to")


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the Settings page, rendered with templates."""
    router = APIRouter()

    def render(request: Request, values: dict, message: str = "", status: int = 200):
        """Render the page with the field values and an optional message."""
        context = {
            "active_page": "settings",
            "levels": THRESHOLD_LEVELS,
            "level_names": LEVEL_NAMES,
            "values": values,
            "message": message,
        }
        return templates.TemplateResponse(request, "settings.html", context, status_code=status)

    def saved_values(request: Request) -> dict:
        """Return the saved thresholds as the text of the form fields."""
        values = {}
        for t in ThresholdService(request.app.state.store).current():
            for field in FIELD_NAMES:
                number = getattr(t, field)
                values[f"level{t.level}_{field}"] = "" if number is None else str(number)
        return values

    @router.get("/settings", response_class=HTMLResponse)
    def settings_page(request: Request):
        """Show the thresholds."""
        return render(request, saved_values(request))

    @router.post("/settings/thresholds")
    async def save_thresholds(request: Request):
        """Save the thresholds, or show the page again with a message."""
        form = await request.form()
        fields = {key: str(value) for key, value in form.items()}
        try:
            ThresholdService(request.app.state.store).save(fields)
        except ThresholdError as error:
            logger.warning("Rejected the thresholds.")
            return render(request, fields, message=str(error), status=422)
        return RedirectResponse("/settings", status_code=303)

    @router.post("/settings/thresholds/reset")
    def reset_thresholds(request: Request):
        """Restore the default thresholds."""
        ThresholdService(request.app.state.store).reset()
        return RedirectResponse("/settings", status_code=303)

    return router
