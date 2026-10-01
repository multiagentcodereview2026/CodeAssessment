"""Explicit development-only instructor account provisioning.

Set DEV_INSTRUCTOR_USERNAME, DEV_INSTRUCTOR_EMAIL, and
DEV_INSTRUCTOR_PASSWORD before running this script. Existing credentials are
never changed unless DEV_INSTRUCTOR_RESET_PASSWORD=true is set explicitly.
"""
import os
import sys

from sqlalchemy import or_, func

from auth import hash_password, verify_password
from database import SessionLocal
import models


def main() -> None:
    username = os.getenv("DEV_INSTRUCTOR_USERNAME", "").strip()
    email = os.getenv("DEV_INSTRUCTOR_EMAIL", "").strip().lower()
    password = os.getenv("DEV_INSTRUCTOR_PASSWORD", "")
    full_name = os.getenv("DEV_INSTRUCTOR_FULL_NAME", "Instructor").strip()
    reset_password = os.getenv("DEV_INSTRUCTOR_RESET_PASSWORD", "").lower() == "true"

    if not username or "@" not in email or len(password) < 6:
        raise SystemExit(
            "Set DEV_INSTRUCTOR_USERNAME, DEV_INSTRUCTOR_EMAIL, and "
            "DEV_INSTRUCTOR_PASSWORD (minimum 6 characters)."
        )

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(
            or_(models.User.username == username, func.lower(models.User.email) == email)
        ).first()
        if user is None:
            user = models.User(
                username=username,
                email=email,
                full_name=full_name or username,
                hashed_password=hash_password(password),
                role="instructor",
                is_active=True,
            )
            db.add(user)
            db.flush()
        else:
            if user.username != username or user.email.lower() != email or user.role != "instructor":
                raise SystemExit("Configured identity conflicts with an existing account.")
            if not verify_password(password, user.hashed_password):
                if not reset_password:
                    raise SystemExit(
                        "Account exists with different credentials. Set "
                        "DEV_INSTRUCTOR_RESET_PASSWORD=true for an explicit reset."
                    )
                user.hashed_password = hash_password(password)

        if user.instructor_profile is None:
            db.add(models.Instructor(user_id=user.id, department="Computer Science"))
        db.commit()
        print(f"Development instructor account ready: {username}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Unable to provision development instructor: {error}", file=sys.stderr)
        raise
