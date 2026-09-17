"""A4 integration helper kept separate to minimize changes to historical agenda routers."""

from fastapi import APIRouter

from backend.routers import agenda_resources


def install_agenda_a4_routes(agenda_router: APIRouter) -> None:
    """Mount A4 resource CRUD exactly once under the existing /agenda router."""
    marker = "_agenda_a4_resources_installed"
    if getattr(agenda_router, marker, False):
        return
    agenda_router.include_router(agenda_resources.router)
    setattr(agenda_router, marker, True)
