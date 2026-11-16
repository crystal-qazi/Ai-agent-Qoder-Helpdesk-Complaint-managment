"""Seed the development database with safe demo/reference data.

Run only after: set FLASK_ENV=development && flask db upgrade
This script never drops tables or creates schema. Alembic owns the schema.
"""
import os
import sys
import argparse
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from app.models import (
    User, Role, Permission, Department, Category, Priority, Status,
    SoftwareCatalog, Complaint, WorkingSchedule, SLAPolicy,
)

PERMISSIONS = [
    ("dashboard.view", "View Dashboard", "dashboard", "view"),
    ("complaints.create", "Create Complaint", "complaints", "create"),
    ("complaints.view_all", "View All Complaints", "complaints", "view_all"),
    ("complaints.view_my", "View My Complaints", "complaints", "view_my"),
    ("complaints.edit", "Edit Complaint", "complaints", "edit"),
    ("complaints.assign", "Assign Complaint", "complaints", "assign"),
    ("complaints.transfer", "Transfer Complaint", "complaints", "transfer"),
    ("complaints.change_status_own", "Change Own Complaint Status", "complaints", "change_status_own"),
    ("complaints.change_status_all", "Change Any Complaint Status", "complaints", "change_status_all"),
    ("complaints.status_unlock", "Access Restricted Statuses", "complaints", "status_unlock"),
    ("comments.add_internal", "Add Internal Comment", "comments", "add_internal"),
    ("comments.add_reporter_visible", "Add Reporter Comment", "comments", "add_reporter_visible"),
    ("comments.view_internal", "View Internal Comments", "comments", "view_internal"),
    ("attachments.upload", "Upload Attachments", "attachments", "upload"),
    ("attachments.download_all", "Download All Attachments", "attachments", "download_all"),
    ("attachments.delete", "Delete Attachments", "attachments", "delete"),
    ("attachments.delete_own", "Delete Own Attachments", "attachments", "delete_own"),
    ("reports.view", "View Reports", "reports", "view"),
    ("reports.export", "Export Reports", "reports", "export"),
    ("users.view", "View Users", "users", "view"),
    ("users.edit", "Edit Users", "users", "edit"),
    ("users.manage", "Manage Users", "users", "manage"),
    ("roles.manage", "Manage Roles", "roles", "manage"),
    ("permissions.manage", "Manage Permissions", "permissions", "manage"),
    ("config.manage", "Manage Configuration", "config", "manage"),
    ("settings.manage", "Manage Settings", "settings", "manage"),
    ("departments.manage", "Manage Departments", "departments", "manage"),
    ("categories.manage", "Manage Categories", "categories", "manage"),
    ("priorities.manage", "Manage Priorities", "priorities", "manage"),
    ("statuses.manage", "Manage Statuses", "statuses", "manage"),
    ("sla.manage", "Manage SLA Policies", "sla", "manage"),
    ("software.manage", "Manage Software", "software", "manage"),
    ("audit.view", "View Audit Logs", "audit", "view"),
    ("notifications.view", "View Notifications", "notifications", "view"),
]

ROLE_PERMISSIONS = {
    "admin": [p[0] for p in PERMISSIONS],
    "helpdesk_agent": [
        "dashboard.view", "complaints.create", "complaints.view_all",
        "complaints.view_my", "complaints.edit", "complaints.assign",
        "complaints.transfer", "complaints.change_status_own",
        "complaints.change_status_all", "complaints.status_unlock",
        "comments.add_internal", "comments.add_reporter_visible",
        "comments.view_internal", "attachments.upload",
        "attachments.download_all", "attachments.delete",
        "reports.view", "reports.export", "users.view",
    ],
    "support_agent": [
        "dashboard.view", "complaints.create", "complaints.view_my",
        "complaints.edit", "complaints.transfer",
        "complaints.change_status_own", "comments.add_internal",
        "comments.add_reporter_visible", "comments.view_internal",
        "attachments.upload", "attachments.download_all",
        "reports.view", "reports.export", "notifications.view",
    ],
    "user": [
        "dashboard.view", "complaints.create",
        "comments.add_reporter_visible", "attachments.upload",
        "attachments.delete_own",
    ],
}

def get_or_create(model, lookup, defaults):
    obj = model.query.filter_by(**lookup).first()
    if obj is None:
        obj = model(**defaults)
        db.session.add(obj)
        db.session.flush()
    return obj

def main():
    parser = argparse.ArgumentParser(description="Seed Helpdesk reference data.")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Seed production reference data and an admin only; do not create demo users or complaints.",
    )
    args = parser.parse_args()
    environment = "production" if args.production else "development"
    expected_database = "Helpdesk_qoder_prod" if args.production else "helpdesk_qoder_dev"
    app = create_app(environment)

    with app.app_context():
        with db.engine.connect() as conn:
            actual_db = conn.exec_driver_sql("SELECT DATABASE()").scalar()
        if actual_db != expected_database:
            raise SystemExit(
                f"Wrong database: connected to {actual_db!r}; expected {expected_database!r}. "
                "No seed data was written."
            )
        print(f"Target database: {actual_db}")
        print("No tables will be dropped or created. Run flask db upgrade first.")

        # Permissions and roles
        permission_map = {}
        for name, label, module, action in PERMISSIONS:
            permission_map[name] = get_or_create(
                Permission, {"name": name},
                {"name": name, "display_name": label, "module": module, "action": action},
            )
        role_map = {}
        role_labels = {
            "admin": ("Administrator", "Full system access"),
            "helpdesk_agent": ("Helpdesk Agent", "Manage and assign incoming complaints"),
            "support_agent": ("Support Agent", "Resolve assigned complaints"),
            "user": ("End User", "Submit and track own complaints"),
        }
        for role_name, permission_names in ROLE_PERMISSIONS.items():
            label, description = role_labels[role_name]
            role = get_or_create(
                Role, {"name": role_name},
                {"name": role_name, "display_name": label, "description": description, "is_system": True},
            )
            existing = {p.name for p in role.permissions.all()}
            for perm_name in permission_names:
                if perm_name not in existing:
                    role.permissions.append(permission_map[perm_name])
            role_map[role_name] = role

        # Departments
        departments = {}
        for name, code, description, location in [
            ("IT Helpdesk", "IT", "First-line IT support", "Ground Floor"),
            ("Network Operations", "NET", "Network and connectivity", "Basement"),
            ("Clinical Systems", "CLN", "HIS, LIS and clinical applications", "Second Floor"),
            ("Patient Administration", "PAT", "Admissions and patient records", "First Floor"),
            ("Billing", "BIL", "Billing and finance systems", "Third Floor"),
        ]:
            departments[code] = get_or_create(
                Department, {"code": code},
                {"name": name, "code": code, "description": description, "location": location},
            )

        # Complaint categories, priorities, statuses and software catalog
        categories = {}
        for name, code, description in [
            ("Hardware", "HARDWARE", "Computers, printers and peripherals"),
            ("Software", "SOFTWARE", "Applications and software"),
            ("Network", "NETWORK", "Network and Wi-Fi"),
            ("Access & Accounts", "ACCESS", "Accounts and permissions"),
            ("Printing", "PRINTING", "Printers and print queues"),
            ("Clinical Application", "CLINICAL", "Hospital clinical applications"),
        ]:
            categories[code] = get_or_create(
                Category, {"code": code},
                {"name": name, "code": code, "description": description, "is_active": True},
            )

        priorities = {}
        for name, code, level, color, icon, desc in [
            ("Critical", "CRITICAL", 1, "#EF4444", "alert-octagon", "Patient safety or full outage"),
            ("High", "HIGH", 2, "#F97316", "alert-triangle", "Major disruption"),
            ("Medium", "MEDIUM", 3, "#3B82F6", "alert-circle", "Limited impact"),
            ("Low", "LOW", 4, "#6B7280", "info", "Minor issue"),
        ]:
            priorities[code] = get_or_create(
                Priority, {"code": code},
                {"name": name, "code": code, "level": level, "color": color,
                 "icon": icon, "description": desc, "sort_order": level, "is_active": True},
            )

        statuses = {}
        for name, code, category, initial, terminal, resolution, color, order in [
            ("New", "new", "open", True, False, False, "#3B82F6", 1),
            ("Assigned", "assigned", "open", False, False, False, "#8B5CF6", 2),
            ("In Progress", "in_progress", "in_progress", False, False, False, "#F59E0B", 3),
            ("Pending Info", "pending_info", "pending", False, False, False, "#F97316", 4),
            ("On Hold", "on_hold", "pending", False, False, False, "#6B7280", 5),
            ("Resolved", "resolved", "resolved", False, False, True, "#10B981", 6),
            ("Closed", "closed", "closed", False, True, False, "#4B5563", 7),
            ("Reopened", "reopened", "open", False, False, False, "#EF4444", 8),
            ("Rejected", "rejected", "closed", False, True, False, "#DC2626", 9),
        ]:
            statuses[code] = get_or_create(
                Status, {"code": code},
                {"name": name, "code": code, "category": category,
                 "is_initial": initial, "is_terminal": terminal,
                 "requires_resolution": resolution, "color": color,
                 "sort_order": order, "is_active": True},
            )

        software = {}
        for name, code, description, vendor in [
            ("Hospital Information System", "HIS", "Core hospital information system", "Demo Vendor"),
            ("Laboratory Information System", "LIS", "Laboratory orders and results", "Demo Vendor"),
            ("PACS", "PACS", "Medical imaging archive", "Demo Vendor"),
            ("Email", "EMAIL", "Corporate email service", "Demo Vendor"),
            ("Network Services", "NETWORK-SVC", "Network infrastructure", "Internal IT"),
        ]:
            software[code] = get_or_create(
                SoftwareCatalog, {"code": code},
                {"name": name, "code": code, "description": description,
                 "vendor": vendor, "department_id": departments["CLN"].id, "is_active": True},
            )

        # Default working schedule and SLA policies
        schedule = get_or_create(
            WorkingSchedule, {"name": "Standard Business Hours"},
            {"name": "Standard Business Hours", "description": "Monday-Friday 09:00-17:00",
             "timezone": "Asia/Karachi",
             "weekly_schedule": {
                 "0": {"start": "09:00", "end": "17:00"},
                 "1": {"start": "09:00", "end": "17:00"},
                 "2": {"start": "09:00", "end": "17:00"},
                 "3": {"start": "09:00", "end": "17:00"},
                 "4": {"start": "09:00", "end": "17:00"},
                 "5": None, "6": None},
             "exceptions": {}, "is_active": True, "is_default": True},
        )
        sla_targets = {"CRITICAL": (60, 240), "HIGH": (240, 1440),
                       "MEDIUM": (480, 2880), "LOW": (1440, 5760)}
        for code, (response, resolution) in sla_targets.items():
            policy = get_or_create(
                SLAPolicy, {"name": f"{priorities[code].name} Priority SLA"},
                {"name": f"{priorities[code].name} Priority SLA",
                 "description": f"Default {priorities[code].name.lower()} priority SLA",
                 "priority_id": priorities[code].id,
                 "response_target_minutes": response,
                 "resolution_target_minutes": resolution,
                 "use_business_hours": True, "working_schedule_id": schedule.id,
                 "is_active": True, "is_default": code == "MEDIUM",
                 "sort_order": priorities[code].level},
            )
            priorities[code].default_sla_policy_id = policy.id

        # Users: admin password is set interactively; demo accounts are for local testing only.
        admin = User.query.filter_by(username="admin").first()
        if admin is None:
            password = getpass("Set a NEW admin password (min 12 chars): ")
            confirm = getpass("Confirm admin password: ")
            if password != confirm or len(password) < 12:
                raise SystemExit("Passwords must match and contain at least 12 characters.")
            admin = User(username="admin", email="admin@hospital.local",
                         first_name="System", last_name="Administrator",
                         employee_number="ADMIN001", is_active=True)
            admin.set_password(password)
            admin.roles.append(role_map["admin"])
            db.session.add(admin)
            db.session.flush()
        else:
            print("Admin account already exists; password left unchanged.")

        if not args.production:
            def ensure_demo_user(username, email, first, last, emp, dept, role, password):
                user = User.query.filter_by(username=username).first()
                if user is None:
                    user = User(username=username, email=email, first_name=first, last_name=last,
                                employee_number=emp, department_id=dept.id, is_active=True)
                    user.set_password(password)
                    user.roles.append(role_map[role])
                    db.session.add(user)
                    db.session.flush()
                return user

            helpdesk = ensure_demo_user("demo_helpdesk", "demo_helpdesk@example.local",
                                        "Demo", "Helpdesk", "DHD001", departments["IT"],
                                        "helpdesk_agent", "DemoHelpdesk@123")
            support = ensure_demo_user("demo_support", "demo_support@example.local",
                                       "Demo", "Support", "DSP001", departments["IT"],
                                       "support_agent", "DemoSupport@123")
            reporter = ensure_demo_user("demo_user", "demo_user@example.local",
                                        "Demo", "Reporter", "DUS001", departments["PAT"],
                                        "user", "DemoUser@123")

            # Three sample complaints; unique complaint numbers make reruns safe.
            samples = [
                ("HD-DEMO-0001", "HIS login is slow", "Users report slow login to the training HIS.",
                 "SOFTWARE", "HIGH", "in_progress", "HIS", "portal", reporter, helpdesk),
                ("HD-DEMO-0002", "Ward printer is offline", "The ward printer is not responding.",
                 "PRINTING", "MEDIUM", "new", "HIS", "phone", reporter, None),
                ("HD-DEMO-0003", "Wi-Fi drops intermittently", "Connectivity drops in the outpatient area.",
                 "NETWORK", "LOW", "assigned", "NETWORK-SVC", "walk_in", reporter, support),
            ]
            for number, title, description, cat, pri, status, sw, source, reporter_user, assignee in samples:
                if not Complaint.query.filter_by(complaint_number=number).first():
                    complaint = Complaint(
                        complaint_number=number, title=title, description=description,
                        category_id=categories[cat].id, priority_id=priorities[pri].id,
                        status_id=statuses[status].id, department_id=departments["IT"].id,
                        software_id=software[sw].id,
                        reported_by_user_id=reporter_user.id,
                        created_by_user_id=admin.id,
                        assigned_to_user_id=assignee.id if assignee else None,
                        source_type=source, severity=priorities[pri].name,
                        affected_location="Demo Ward / Outpatient",
                    )
                    db.session.add(complaint)


        db.session.commit()
        print(f"Database {actual_db} seeded successfully.")
        if not args.production:
            print("Development demo users:")
            print("  demo_helpdesk / DemoHelpdesk@123")
            print("  demo_support  / DemoSupport@123")
            print("  demo_user     / DemoUser@123")
            print(f"Sample complaints: {Complaint.query.count()}")
            print("Change/remove demo passwords before sharing this environment.")
        else:
            print("Production seeded with reference data and the admin account only.")


if __name__ == "__main__":
    main()
