from typing import List, Optional
from pydantic import BaseModel, EmailStr, conint, Field
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: str
    userType: str


class UserCreate(UserBase):
    password: str
    agreeTerms: bool


class UserInDB(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True


class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    alert_level: int = 0


class LocationCreate(LocationBase):
    pass


class Location(LocationBase):
    id: int

    class Config:
        from_attributes = True


# Basic Report response without nested objects to avoid circular dependencies
class ReportBase(BaseModel):
    content: str = Field(..., min_length=10)
    tags: List[str] = Field(..., min_items=1)
    severity: int
    location_id: int


class ReportCreate(ReportBase):
    pass


class ReportSimple(ReportBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# Full Report response with nested objects
class Report(ReportSimple):
    created_at: datetime

    class Config:
        from_attributes = True


class EventBase(BaseModel):
    description: str = Field(..., min_length=10)
    tags: List[str] = Field(..., min_items=1)
    location_id: int


class EventCreate(EventBase):
    pass


# Simple Event response without nested objects
class EventSimple(EventBase):
    id: int

    class Config:
        from_attributes = True


# Full Event response with nested objects
class Event(EventSimple):
    created_at: datetime
    reports: List[ReportSimple]

    class Config:
        from_attributes = True