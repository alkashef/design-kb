"""The engineer card shared by the Search preview and the Engineers detail pane (FR-05, FR-50, D-47)."""

from fastapi import HTTPException, Request

from src.domain.levels import LEVEL_NAMES
from src.services.assignments import AssignmentService
from src.services.engineers import EngineerService, UnknownEngineer


def preview_context(request: Request, engineer_id: str) -> dict:
    """Return the template values of the card of one engineer, or answer 404."""
    state = request.app.state
    engineers = EngineerService(state.store, state.options.page_size, state.indexing)
    try:
        engineer = engineers.get(engineer_id)
    except UnknownEngineer:
        raise HTTPException(status_code=404, detail="Unknown engineer")
    return {
        "engineer": engineer,
        "skill_groups": engineers.skill_groups(engineer_id),
        "assignment_rows": AssignmentService(state.store, state.indexing).for_engineer(
            engineer_id
        ),
        "level_names": LEVEL_NAMES,
    }
