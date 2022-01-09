from fastapi import APIRouter, Request, Depends, Response, encoders
import typing as t
from core.auth import get_current_active_superuser

from db.session import get_db
from db.crud import (
    get_project_team,
    get_projects,
    get_project,
    create_project,
    edit_project,
    delete_project
)
from db.schemas import CreateAndUpdateProjectWithTeam, Project, ProjectWithTeam

projects_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[Project],
    response_model_exclude_none=True,
    name="projects:all-projects"
)
async def projects_list(
    response: Response,
    db=Depends(get_db),
):
    """
    Get all projects
    """
    projects = get_projects(db)
    return projects


@r.get(
    "/{project_id}",
    response_model=ProjectWithTeam,
    response_model_exclude_none=True,
    name="projects:project-details"
)
async def project_details(
    request: Request,
    project_id: int,
    db=Depends(get_db),
):
    """
    Get any project details
    """
    project = get_project(db, project_id)
    project_team = get_project_team(db, project_id)
    return ProjectWithTeam(
        id=project.id,
        name=project.name,
        fundsRaised=project.fundsRaised,
        shortDescription=project.shortDescription,
        description=project.description,
        teamTelegramHandle=project.teamTelegramHandle,
        bannerImgUrl=project.bannerImgUrl,
        isLaunched=project.isLaunched,
        team=project_team
    )


@r.post("/", response_model=ProjectWithTeam, response_model_exclude_none=True, name="projects:create")
async def project_create(
    request: Request,
    project: CreateAndUpdateProjectWithTeam,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new project
    """
    return create_project(db, project)


@r.put(
    "/{project_id}", response_model=ProjectWithTeam, response_model_exclude_none=True, name="projects:edit"
)
async def project_edit(
    request: Request,
    project_id: int,
    project: CreateAndUpdateProjectWithTeam,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser)
):
    """
    Update existing project
    """
    return edit_project(db, project_id, project)


@r.delete(
    "/{project_id}", response_model=Project, response_model_exclude_none=True, name="projects:delete"
)
async def project_delete(
    request: Request,
    project_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing project
    """
    return delete_project(db, project_id)
