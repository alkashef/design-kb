"""The Skill tree page and its editor (FR-30, FR-33)."""

from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.domain.models import EmbeddingUnavailable
from src.services.skill_tree import SkillTreeError, SkillTreeService, UnknownNode
from src.web.errors import failure_of


def create_router(templates: Jinja2Templates) -> APIRouter:
    """Return the routes of the Skill tree page, rendered with templates."""
    router = APIRouter()

    def service_of(request: Request) -> SkillTreeService:
        """Return the skill tree service of the app."""
        return SkillTreeService(request.app.state.store, request.app.state.indexing)

    def render(request: Request, selected_id: Optional[str], message: str = "", status: int = 200):
        """Render the page with the outline, the selected node and an optional message."""
        service = service_of(request)
        selected = None
        if selected_id:
            try:
                selected = service.get(selected_id)
            except UnknownNode:
                raise HTTPException(status_code=404, detail="Unknown skill")
        context = {
            "active_page": "skill_tree",
            "children": service.children_by_parent(),
            "open_ids": service.open_ids(selected_id) if selected else set(),
            "selected": selected,
            "selected_path": service.path(selected_id) if selected else "",
            "selected_is_leaf": service.is_leaf(selected_id) if selected else False,
            "message": message,
            "leaves": service.leaves_under(selected_id) if selected else [],
            "people": service.employees_with_levels(selected_id) if selected else [],
        }
        return templates.TemplateResponse(request, "skill_tree.html", context, status_code=status)

    @router.get("/skill-tree", response_class=HTMLResponse)
    def skill_tree_page(request: Request):
        """Show the Skill tree page with no node selected."""
        return render(request, None)

    @router.get("/skill-tree/{node_id}", response_class=HTMLResponse)
    def skill_tree_node(request: Request, node_id: str):
        """Show the Skill tree page with one node selected."""
        return render(request, node_id)

    @router.post("/skill-tree/nodes")
    def add_node(
        request: Request,
        parent_id: str = Form(""),
        name: str = Form(""),
        description: str = Form(""),
    ):
        """Add a node and open it."""
        service = service_of(request)
        try:
            node_id = service.add(parent_id, name, description)
        except SkillTreeError as error:
            return render(request, parent_id or None, str(error), 422)
        except UnknownNode:
            raise HTTPException(status_code=404, detail="Unknown skill")
        return RedirectResponse(f"/skill-tree/{node_id}", status_code=303)

    @router.post("/skill-tree/nodes/{node_id}")
    def save_node(
        request: Request, node_id: str, name: str = Form(""), description: str = Form("")
    ):
        """Save the name and the description of a node."""
        service = service_of(request)
        try:
            service.save(node_id, name, description)
        except (SkillTreeError, EmbeddingUnavailable) as error:
            message, status = failure_of(error)
            return render(request, node_id, message, status)
        except UnknownNode:
            raise HTTPException(status_code=404, detail="Unknown skill")
        return RedirectResponse(f"/skill-tree/{node_id}", status_code=303)

    @router.post("/skill-tree/nodes/{node_id}/delete")
    def delete_node(request: Request, node_id: str):
        """Delete a node, or refuse with a message."""
        service = service_of(request)
        try:
            service.delete(node_id)
        except SkillTreeError as error:
            return render(request, node_id, str(error), 422)
        except UnknownNode:
            raise HTTPException(status_code=404, detail="Unknown skill")
        return RedirectResponse("/skill-tree", status_code=303)

    return router
