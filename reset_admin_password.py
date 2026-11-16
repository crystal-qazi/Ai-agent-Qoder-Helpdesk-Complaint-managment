"""Safely reset the password for the existing admin account.

Run from the project root:
    python reset_admin_password.py

Loads the same project .env file used by run.py before creating the app.
Does not create users, change database settings, or modify the schema.
"""
from pathlib import Path
from getpass import getpass
import os
import sys

from dotenv import load_dotenv

# Load the project's .env before importing the application/config modules.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)
sys.path.insert(0, str(BASE_DIR))

from werkzeug.security import generate_password_hash
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app import create_app
from app.extensions import db
from app.models import User


def main():
    app = create_app(os.environ.get("FLASK_ENV", "development"))

    with app.app_context():
        new_password = getpass("New admin password (minimum 12 characters): ")
        confirm_password = getpass("Confirm password: ")

        if new_password != confirm_password:
            raise SystemExit("Passwords do not match.")
        if len(new_password) < 12:
            raise SystemExit("Password must contain at least 12 characters.")

        try:
            user = db.session.execute(
                select(User).where(User.username == "admin")
            ).scalar_one_or_none()

            if user is None:
                raise SystemExit("Admin account was not found. No changes made.")

            user.password_hash = generate_password_hash(
                new_password, method="scrypt"
            )
            db.session.commit()
            print("Admin password updated successfully.")

        except OperationalError as exc:
            db.session.rollback()
            original = str(getattr(exc, "orig", exc))
            if "Plugin 'mysql_native_password' is not loaded" in original:
                raise SystemExit(
                    "MySQL rejected the account authentication plugin "
                    "(mysql_native_password). This is a MySQL server/account "
                    "configuration issue, not a password-hash issue. "
                    "No password was changed. Ask the MySQL administrator "
                    "to check the account's authentication plugin."
                ) from None
            raise SystemExit(
                "Could not connect to the database. Check the .env database "
                "settings and MySQL service. No password was changed."
            ) from None
        finally:
            db.session.remove()


if __name__ == "__main__":
    main()
