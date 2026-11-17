"""The app factory: connects the store, the embedder, the routes, the templates and the static files
(D-21)."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.web import request_log
from src.web.routes import employees, projects, search, skill_tree

WEB_DIR = Path(__file__).resolve().parent / "web"


@dataclass(frozen=True)
class AppOptions:
    """Holds the settings that the app needs besides the store and the embedder."""

    search_result_limit: int
    page_size: int
    load_seed: bool


def create_app(store, embedder, options: AppOptions) -> FastAPI:
    """Return the FastAPI app that uses store, embedder and options."""
    app = FastAPI(title="design-kb", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store = store
    app.state.embedder = embedder
    app.state.options = options
    templates = Jinja2Templates(directory=WEB_DIR / "templates")
    app.middleware("http")(request_log.log_request)
    app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
    app.include_router(search.create_router(templates))
    app.include_router(employees.create_router(templates))
    app.include_router(skill_tree.create_router(templates))
    app.include_router(projects.create_router(templates))
    return app
