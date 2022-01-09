from pydantic import BaseModel
import typing as t


### SCHEMAS FOR USERS ###


class UserBase(BaseModel):
    email: str
    is_active: bool = True
    is_superuser: bool = False
    first_name: t.Optional[str] = None
    last_name: t.Optional[str] = None


class UserOut(UserBase):
    pass


class UserCreate(UserBase):
    password: str

    class Config:
        orm_mode = True


class UserEdit(UserBase):
    password: t.Optional[str] = None

    class Config:
        orm_mode = True


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


### SCHEMAS FOR TOKENS ###


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str = None
    permissions: str = "user"


### SCHEMAS FOR PROJECTS ###


class CreateAndUpdateProject(BaseModel):
    name: str
    shortDescription: str
    description: t.Optional[str]
    fundsRaised: t.Optional[float]
    teamTelegramHandle: t.Optional[str]
    bannerImgUrl: str
    isLaunched: bool


class Project(CreateAndUpdateProject):
    id: int

    class Config:
        orm_mode = True


class CreateAndUpdateProjectTeamMember(BaseModel):
    name: str
    description: t.Optional[str]
    # we do not know projectId when project is created
    projectId: t.Optional[int]
    profileImgUrl: t.Optional[str]


class ProjectTeamMember(CreateAndUpdateProjectTeamMember):
    id: int

    class Config:
        orm_mode = True


class ProjectWithTeam(Project):
    team: t.List[ProjectTeamMember]

    class Config:
        orm_mode = True


class CreateAndUpdateProjectWithTeam(CreateAndUpdateProject):
    team: t.Optional[t.List[CreateAndUpdateProjectTeamMember]]
