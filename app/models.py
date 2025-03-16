from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Table, ARRAY, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# Association table for Event-Report many-to-many relationship
event_reports = Table(
    'event_reports',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id')),
    Column('report_id', Integer, ForeignKey('reports.id'))
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    reports = relationship("Report", back_populates="user")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    alert_level = Column(Integer, default=0)

    # Relationships
    reports = relationship("Report", back_populates="location")
    events = relationship("Event", back_populates="location")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    tags = Column(ARRAY(String))
    severity = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))

    # Relationships
    user = relationship("User", back_populates="reports")
    location = relationship("Location", back_populates="reports")
    events = relationship("Event", secondary=event_reports, back_populates="reports")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)
    tags = Column(ARRAY(String))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    location_id = Column(Integer, ForeignKey("locations.id"))

    # Relationships
    location = relationship("Location", back_populates="events")
    reports = relationship("Report", secondary=event_reports, back_populates="events") 