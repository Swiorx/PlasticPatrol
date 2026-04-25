from sqlalchemy import text
from sqlalchemy.orm import Session


def run_startup_migrations(db: Session) -> None:
    db.execute(text(
        "ALTER TABLE plastic_debris ADD COLUMN IF NOT EXISTS is_reserved BOOLEAN DEFAULT FALSE"
    ))
    db.commit()
