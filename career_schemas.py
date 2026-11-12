
from pydantic import BaseModel, Field
from typing import Optional, Literal


ApplicationStatus = Literal[
    "Applied",
    "Interview",
    "Selected",
    "Rejected"
]


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: str
    password: str


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=2, max_length=150)
    position: str = Field(min_length=2, max_length=150)
    status: ApplicationStatus = "Applied"
    applied_date: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationDetailsUpdate(BaseModel):
    company: str = Field(min_length=2, max_length=150)
    position: str = Field(min_length=2, max_length=150)
    applied_date: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None


class ApplicationNotesUpdate(BaseModel):
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None
