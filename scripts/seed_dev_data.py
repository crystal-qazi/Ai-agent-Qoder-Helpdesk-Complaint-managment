"""Seed fictional demo data into the development database only.

Run after: set FLASK_ENV=development && flask db upgrade
Safe to rerun: inserts missing rows only; never drops tables or updates passwords.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

if os.environ.get("FLASK_ENV", "development").lower() != "development":
    raise SystemExit("Refusing to seed: FLASK_ENV must be development.")

from sqlalchemy import text
from app import create_app
from app.extensions import db
import app.models  # noqa: F401
from app.models import (
    User, Role, Permission, Department, Category, Priority, Status,
    SoftwareCatalog, WorkingSchedule, SLAPolicy, Complaint,
)
from scripts.reset_and_seed import (
    PERMISSIONS, AGENT_PERMISSIONS, SUPPORT_AGENT_PERMISSIONS,
    USER_PERMISSIONS, STATUSES, PRIORITIES, SLA_TARGETS, DEPARTMENTS,
    CATEGORIES, SOFTWARE,
)

# The legacy role list references this permission but omitted its definition.
PERMISSION_DEFS = list(PERMISSIONS) + [
    ("notifications.view", "View Notifications", "notifications", "view")
]
app = create_app("development")


def ensure(model, key, values):
    row = model.query.filter_by(**key).first()
    if row is None:
        row = model(**values)
        db.session.add(row)
        db.session.flush()
    return row


def main():
    with app.app_context():
        with db.engine.connect() as conn:
            database, hostname = conn.execute(
                text("SELECT DATABASE(), @@hostname")
            ).one()
        if database != "helpdesk_qoder_dev":
            raise SystemExit(
                f"Safety stop: connected to {database!r}; expected helpdesk_qoder_dev."
            )
        print(f"Target verified: {database} on {hostname}")

        try:
            departments = {}
            for name, code, description, location in DEPARTMENTS:
                departments[code] = ensure(
                    Department, {"code": code},
                    {"name": name, "code": code, "description": description,
                     "location": location, "is_active": True},
                )

            permissions = {}
            for name, display, module, action in PERMISSION_DEFS:
                permissions[name] = ensure(
                    Permission, {"name": name},
                    {"name": name, "display_name": display, "module": module,
                     "action": action, "is_active": True},
                )

            role_specs = [
                ("admin", "Administrator", list(permissions)),
                ("helpdesk_agent", "Helpdesk Agent", AGENT_PERMISSIONS),
                ("support_agent", "Support Agent", SUPPORT_AGENT_PERMISSIONS),
                ("user", "End User", USER_PERMISSIONS),
            ]
            roles = {}
            for name, display, permission_names in role_specs:
                role = ensure(
                    Role, {"name": name},
                    {"name": name, "display_name": display,
                     "description": f"Development demo role: {display}",
                     "is_system": True, "is_active": True},
                )
                existing = {p.name for p in role.permissions.all()}
                for permission_name in permission_names:
                    if permission_name not in permissions:
                        raise RuntimeError(f"Missing permission definition: {permission_name}")
                    if permission_name not in existing:
                        role.permissions.append(permissions[permission_name])
                roles[name] = role

            statuses = {}
            for name, code, category, initial, terminal, reason, resolution, color, icon, order in STATUSES:
                statuses[code] = ensure(
                    Status, {"code": code},
                    {"name": name, "code": code, "category": category,
                     "is_initial": initial, "is_terminal": terminal,
                     "requires_reason": reason, "requires_resolution": resolution,
                     "color": color, "icon": icon, "sort_order": order,
                     "is_active": True},
                )

            priorities = {}
            for name, code, level, color, icon, description, order in PRIORITIES:
                priorities[code] = ensure(
                    Priority, {"code": code},
                    {"name": name, "code": code, "level": level, "color": color,
                     "icon": icon, "description": description, "sort_order": order,
                     "is_active": True},
                )

            schedule = ensure(
                WorkingSchedule, {"name": "Standard Business Hours"},
                {"name": "Standard Business Hours",
                 "description": "Monday-Friday, 09:00-17:00 Pakistan time",
                 "timezone": "Asia/Karachi",
                 "weekly_schedule": {
                     **{str(day): {"start": "09:00", "end": "17:00"} for day in range(5)},
                     "5": None, "6": None},
                 "exceptions": {}, "is_active": True, "is_default": True},
            )

            for code, (response_minutes, resolution_minutes) in SLA_TARGETS.items():
                priority = priorities[code]
                policy = ensure(
                    SLAPolicy, {"name": f"{priority.name} Priority SLA"},
                    {"name": f"{priority.name} Priority SLA",
                     "description": f"Development SLA for {priority.name}",
                     "priority_id": priority.id,
                     "response_target_minutes": response_minutes,
                     "resolution_target_minutes": resolution_minutes,
                     "use_business_hours": True, "working_schedule_id": schedule.id,
                     "escalation_enabled": code in ("CRITICAL", "HIGH"),
                     "pause_on_pending_info": True, "pause_on_hold": True,
                     "is_active": True, "is_default": code == "MEDIUM",
                     "sort_order": priority.level},
                )
                priority.default_sla_policy_id = policy.id

            categories = {}
            for name, code, description in CATEGORIES:
                categories[code] = ensure(
                    Category, {"code": code},
                    {"name": name, "code": code, "description": description,
                     "is_active": True},
                )

            software = {}
            for name, code, description, vendor in SOFTWARE:
                software[code] = ensure(
                    SoftwareCatalog, {"code": code},
                    {"name": name, "code": code, "description": description,
                     "vendor": vendor, "department_id": departments["CLN"].id,
                     "is_active": True},
                )

            # Fictional accounts. Passwords are intentionally development-only.
            account_specs = [
                ("admin", "admin@hospital.local", "System", "Administrator", "ADMIN001", "IT", "admin", "Admin@123"),
                ("helpdesk", "helpdesk@hospital.local", "Helpdesk", "Agent", "HD001", "IT", "helpdesk_agent", "Helpdesk@123"),
                ("support", "support@hospital.local", "Support", "Agent", "SA001", "IT", "support_agent", "Support@123"),
                ("user", "user@hospital.local", "Hospital", "User", "USR001", "PAT", "user", "User@123"),
            ]
            users = {}
            for username, email, first, last, employee_no, dept, role_name, password in account_specs:
                user = User.query.filter_by(username=username).first()
                if user is None:
                    user = User(username=username, email=email, first_name=first,
                                last_name=last, employee_number=employee_no,
                                department_id=departments[dept].id, is_active=True)
                    user.set_password(password)
                    user.roles.append(roles[role_name])
                    db.session.add(user)
                    db.session.flush()
                elif not user.roles.filter_by(name=role_name).first():
                    user.roles.append(roles[role_name])
                users[username] = user

            samples = [
                ("DEV-2026-0001", "Demo: HIS login problem",
                 "Fictional training complaint: user cannot sign in to HIS.",
                 "SOFTWARE", "HIGH", "new", "HIS", "user", "helpdesk"),
                ("DEV-2026-0002", "Demo: Printer not responding",
                 "Fictional training complaint: department printer is offline.",
                 "PRINTING", "MEDIUM", "in_progress", "HIS", "user", "support"),
                ("DEV-2026-0003", "Demo: Network connectivity",
                 "Fictional training complaint: workstation connection is unstable.",
                 "NETWORK", "LOW", "assigned", "EMAIL", "admin", "helpdesk"),
            ]
            for number, title, description, cat, pri, status, sw, reporter, assignee in samples:
                if not Complaint.query.filter_by(complaint_number=number).first():
                    db.session.add(Complaint(
                        complaint_number=number, title=title, description=description,
                        category_id=categories[cat].id, priority_id=priorities[pri].id,
                        status_id=statuses[status].id, department_id=departments["IT"].id,
                        software_id=software[sw].id,
                        reported_by_user_id=users[reporter].id,
                        created_by_user_id=users[reporter].id,
                        assigned_to_user_id=users[assignee].id, source_type="portal",
                    ))

            db.session.commit()
            print("Development seed completed.")
            print("Accounts: admin, helpdesk, support, user")
            print("Sample complaints: DEV-2026-0001, DEV-2026-0002, DEV-2026-0003")
            print("Change every demo password. Never use these accounts in production.")
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.remove()


if __name__ == "__main__":
    main()
