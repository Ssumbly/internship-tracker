"""Seed the database with clearly-labeled EXAMPLE data for demo purposes.

These companies are illustrative examples only — they do not represent
real applications submitted by any user.

Usage:  python seed.py   (creates demo@example.com / demo-password-123)
"""
from app.database import Base, SessionLocal, engine
from app import models
from app.security import hash_password
from datetime import date, timedelta

Base.metadata.create_all(bind=engine)
db = SessionLocal()
user = db.query(models.User).filter_by(email="demo@example.com").first()
if not user:
    user = models.User(email="demo@example.com", hashed_password=hash_password("demo-password-123"), full_name="Demo User")
    db.add(user)
    db.commit()
    db.refresh(user)

examples = [
    ("Example Robotics Co", "Software Engineering Intern", "saved", 14),
    ("Example Cloud Co", "Machine Learning Intern", "applied", 7),
    ("Example Fintech Co", "Software Engineering Intern", "oa", 3),
]
for company, role, status, days in examples:
    db.add(models.Application(
        owner_id=user.id, company=company, role=role, status=status,
        deadline=date.today() + timedelta(days=days),
        notes="Example seed data — not a real application.",
        resume_version="example-v1",
    ))
db.commit()
print("Seeded demo user demo@example.com with example applications.")
db.close()
