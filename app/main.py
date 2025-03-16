from typing import Annotated, List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from . import models, schemas, auth, event_correlation, ai
from .database import engine, get_db, drop_tables
from .config import get_settings
from fastapi.middleware.cors import CORSMiddleware

settings = get_settings()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hazard Reporting System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if engine.connect() else "disconnected"
    }

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = auth.get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return auth.create_user(db=db, user=user)


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)]
):
    return current_user


@app.post("/locations/", response_model=schemas.Location)
async def create_location(
    location: schemas.LocationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    print("Creating location")
    db_location = models.Location(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


@app.get("/locations/", response_model=List[schemas.Location])
async def list_locations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.Location).all()


@app.post("/reports/", response_model=schemas.Report)
async def create_report(
    report: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_report = models.Report(
        **report.model_dump(),
        user_id=current_user.id
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    event_correlation.create_or_update_event(db, db_report)
    
    return db_report


@app.get("/reports/", response_model=List[schemas.Report])
async def list_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.Report).all()


@app.get("/events/", response_model=List[schemas.Event])
async def list_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.Event).all()


@app.get("/events/{event_id}", response_model=schemas.Event)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.get("/reload")
async def update_reload(
        db: Session = Depends(get_db),
):
    drop_tables()

"""@app.get("/events/location/", response_model=List[schemas.Event])
async def get_nearby_events(
    db: Session = Depends(get_db),
        current_user: models.User = Depends(auth.get_current_active_user
):
    current_location = current_user.location
    """