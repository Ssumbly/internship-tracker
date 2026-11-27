from datetime import date, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .security import create_access_token, get_current_user, hash_password, verify_password

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Internship Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Auth ----------

@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ---------- Applications ----------

def _get_owned(db: Session, app_id: int, user: models.User) -> models.Application:
    app_obj = (
        db.query(models.Application)
        .filter(models.Application.id == app_id, models.Application.owner_id == user.id)
        .first()
    )
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_obj


@app.post("/applications", response_model=schemas.ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    app_obj = models.Application(**payload.model_dump(), owner_id=current_user.id)
    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)
    return app_obj


@app.get("/applications", response_model=list[schemas.ApplicationOut])
def list_applications(
    status_filter: models.ApplicationStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Application).filter(models.Application.owner_id == current_user.id)
    if status_filter is not None:
        q = q.filter(models.Application.status == status_filter)
    return q.order_by(models.Application.deadline.is_(None), models.Application.deadline).all()


@app.get("/applications/{app_id}", response_model=schemas.ApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return _get_owned(db, app_id, current_user)


@app.put("/applications/{app_id}", response_model=schemas.ApplicationOut)
def update_application(
    app_id: int,
    payload: schemas.ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    app_obj = _get_owned(db, app_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(app_obj, field, value)
    db.commit()
    db.refresh(app_obj)
    return app_obj


@app.delete("/applications/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(app_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_obj = _get_owned(db, app_id, current_user)
    db.delete(app_obj)
    db.commit()
    return None


# ---------- Stats ----------

@app.get("/stats", response_model=schemas.StatsOut)
def stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    apps = db.query(models.Application).filter(models.Application.owner_id == current_user.id).all()
    by_status = {s.value: 0 for s in models.ApplicationStatus}
    for a in apps:
        by_status[a.status.value] += 1
    today = date.today()
    upcoming = sorted(
        (a for a in apps if a.deadline and today <= a.deadline <= today + timedelta(days=30)
         and a.status not in (models.ApplicationStatus.rejected, models.ApplicationStatus.offer)),
        key=lambda a: a.deadline,
    )
    return {"total": len(apps), "by_status": by_status, "upcoming_deadlines": upcoming}
