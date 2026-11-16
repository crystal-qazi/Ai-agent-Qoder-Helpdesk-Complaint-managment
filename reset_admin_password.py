from getpass import getpass
from werkzeug.security import generate_password_hash
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    username = "admin"
    new_password = getpass("Enter new admin password: ")

    if len(new_password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    user = db.session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    if not user:
        raise ValueError("Admin user not found.")

    user.password_hash = generate_password_hash(new_password, method="scrypt")
    db.session.commit()

    print("Admin password updated successfully.")