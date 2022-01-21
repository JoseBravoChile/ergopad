from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from .session import Base

# USER MODEL


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class JWTBlackList(Base):
    __tablename__ = "jwtBlacklist"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# PROJECTS MODEL


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    fundsRaised = Column(Float)
    shortDescription = Column(String)
    description = Column(String)
    socials = Column(String)
    bannerImgUrl = Column(String)
    isLaunched = Column(Boolean)


class ProjectTeam(Base):
    __tablename__ = "projectTeams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    profileImgUrl = Column(String)
    projectId = Column(Integer)
