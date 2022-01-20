import json
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import typing as t

from . import models, schemas
from core.security import get_password_hash


#################################
### CRUD OPERATIONS FOR USERS ###
#################################


def get_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_user_by_email(db: Session, email: str) -> schemas.UserBase:
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.UserOut]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return user


def edit_user(
    db: Session, user_id: int, user: schemas.UserEdit
) -> schemas.User:
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    update_data = user.dict(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(user.password)
        del update_data["password"]

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def blacklist_token(db: Session, token: str):
    db_token = models.JWTBlackList(token=token)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_blacklisted_token(db: Session, token: str):
    return db.query(models.JWTBlackList).filter(models.JWTBlackList.token == token).first()


####################################
### CRUD OPERATIONS FOR PROJECTS ###
####################################

def social_compatible_project(project):
    try:
        project.socials = schemas.Socials.parse_obj(
            json.loads(project.socials))
    except:
        # make backward compatible with older data
        project.socials = schemas.Socials(telegram=project.socials)
    return project


def get_projects(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.Project]:
    data = db.query(models.Project).offset(skip).limit(limit).all()
    return [social_compatible_project(project) for project in data]


def get_project(db: Session, id: int, model="out"):
    project = db.query(models.Project).filter(models.Project.id == id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    if model == "db":
        return project
    else:
        return social_compatible_project(project)


def get_project_team(db: Session, projectId: int, skip: int = 0, limit: int = 100) -> t.List[schemas.ProjectTeamMember]:
    return db.query(models.ProjectTeam).filter(models.ProjectTeam.projectId == projectId).all()


def create_project(db: Session, project: schemas.CreateAndUpdateProjectWithTeam):
    db_project = models.Project(
        name=project.name,
        shortDescription=project.shortDescription,
        description=project.description,
        fundsRaised=project.fundsRaised,
        socials=str(project.socials.json()),
        bannerImgUrl=project.bannerImgUrl,
        isLaunched=project.isLaunched,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    if (project.team):
        set_project_team(db, db_project.id, project.team)
    return schemas.ProjectWithTeam(
        id=db_project.id,
        name=db_project.name,
        shortDescription=db_project.shortDescription,
        description=db_project.description,
        fundsRaised=db_project.fundsRaised,
        socials=schemas.Socials.parse_obj(json.loads(db_project.socials)),
        bannerImgUrl=db_project.bannerImgUrl,
        isLaunched=db_project.isLaunched,
        team=get_project_team(db, db_project.id)
    )


def set_project_team(db: Session, projectId: int, teamMembers: t.List[schemas.CreateAndUpdateProjectTeamMember]):
    db_teamMembers = list(map(lambda teamMember: models.ProjectTeam(
        name=teamMember.name, description=teamMember.description, profileImgUrl=teamMember.profileImgUrl, projectId=projectId), teamMembers))
    delete_project_team(db, projectId)
    db.add_all([member for member in db_teamMembers])
    db.commit()
    return get_project_team(db, projectId)


def delete_project(db: Session, id: int):
    project = get_project(db, id, model="db")
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="project not found")
    delete_project_team(db, id)
    db.delete(project)
    db.commit()
    return social_compatible_project(project)


def delete_project_team(db: Session, projectId: int):
    ret = get_project_team(db, projectId)
    db.query(models.ProjectTeam).filter(models.ProjectTeam.projectId ==
                                        projectId).delete(synchronize_session=False)
    db.commit()
    return ret


def edit_project(
    db: Session, id: int, project: schemas.CreateAndUpdateProjectWithTeam
):
    db_project = get_project(db, id, model="db")
    if not db_project:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="project not found")

    update_data = project.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "socials":
            setattr(db_project, key, str(project.socials.json()))
        else:
            setattr(db_project, key, value)

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    if (project.team != None):
        set_project_team(db, db_project.id, project.team)

    return schemas.ProjectWithTeam(
        id=db_project.id,
        name=db_project.name,
        shortDescription=db_project.shortDescription,
        description=db_project.description,
        fundsRaised=db_project.fundsRaised,
        socials=schemas.Socials.parse_obj(json.loads(db_project.socials)),
        bannerImgUrl=db_project.bannerImgUrl,
        isLaunched=db_project.isLaunched,
        team=get_project_team(db, db_project.id)
    )
