from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .models import ApplicationStatus

# Email is validated with a simple pattern to keep the dependency list light.
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        if not EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v.lower()


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApplicationBase(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=160)
    location: Optional[str] = None
    status: ApplicationStatus = ApplicationStatus.saved
    deadline: Optional[date] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None
    resume_version: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    deadline: Optional[date] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None
    resume_version: Optional[str] = None


class ApplicationOut(ApplicationBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    total: int
    by_status: dict[str, int]
    upcoming_deadlines: list[ApplicationOut]
