"""Seed SQLite dev database for local testing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DATABASE_URL', 'sqlite:///instance/dev.db')

from app import create_app
from app.extensions import db
import app.models  # noqa: F401 registers all tables

app = create_app('development')

with app.app_context():
    db.create_all()

    from app.models.user import User, Role, Permission
    from app.models.department import Department
    from app.models.category import Category
    from app.models.priority import Priority
    from app.models.status import Status
    from app.models.complaint import Complaint
    from app.models.software import SoftwareCatalog

    # Create categories, priority, dept, statuses (idempotent)
    if not Department.query.filter_by(code='IT').first():
        dept = Department(name='IT Helpdesk', code='IT', description='IT dept', is_active=True)
        db.session.add(dept)
        db.session.flush()
    else:
        dept = Department.query.filter_by(code='IT').first()

    if not Category.query.filter_by(code='HARDWARE').first():
        cat = Category(name='Hardware', code='HARDWARE', description='Hardware issues', is_active=True)
        db.session.add(cat)
        db.session.flush()
    else:
        cat = Category.query.filter_by(code='HARDWARE').first()

    if not Priority.query.filter_by(code='MEDIUM').first():
        pri = Priority(name='Medium', code='MEDIUM', level=3, color='#3B82F6', sort_order=3, is_active=True)
        db.session.add(pri)
        db.session.flush()
    else:
        pri = Priority.query.filter_by(code='MEDIUM').first()

    new_s = Status.query.filter_by(code='new').first()
    assigned_s = Status.query.filter_by(code='assigned').first()
    if not new_s:
        new_s = Status(name='New', code='new', category='open', is_initial=True, is_active=True, sort_order=1)
        db.session.add(new_s)
    if not assigned_s:
        assigned_s = Status(name='Assigned', code='assigned', category='open', is_active=True, sort_order=2)
        db.session.add(assigned_s)
    db.session.flush()

    # Create permissions and roles
    perm_defs = [
        ('complaints.view_all', 'View All Complaints', 'complaints', 'view_all'),
        ('complaints.view_my', 'View My Complaints', 'complaints', 'view_my'),
        ('complaints.create', 'Create Complaint', 'complaints', 'create'),
        ('complaints.edit', 'Edit Complaint', 'complaints', 'edit'),
        ('complaints.assign', 'Assign Complaint', 'complaints', 'assign'),
        ('comments.add_internal', 'Add Internal Comment', 'comments', 'add_internal'),
        ('notifications.view', 'View Notifications', 'notifications', 'view'),
    ]
    perm_map = {}
    for name, disp, mod, act in perm_defs:
        p = Permission.query.filter_by(name=name).first()
        if not p:
            p = Permission(name=name, display_name=disp, module=mod, action=act)
            db.session.add(p)
        perm_map[name] = p
    db.session.flush()

    if not Role.query.filter_by(name='admin').first():
        admin_role = Role(name='admin', display_name='Admin', is_system=True)
        admin_role.permissions.extend([perm_map['complaints.view_all'], perm_map['complaints.create'],
                                        perm_map['complaints.edit'], perm_map['complaints.assign'],
                                        perm_map['comments.add_internal']])
        db.session.add(admin_role)
    else:
        admin_role = Role.query.filter_by(name='admin').first()

    if not Role.query.filter_by(name='helpdesk_agent').first():
        agent_role = Role(name='helpdesk_agent', display_name='Helpdesk Agent', is_system=True)
        agent_role.permissions.extend([perm_map['complaints.view_all'], perm_map['complaints.view_my'],
                                        perm_map['complaints.create'], perm_map['complaints.edit'],
                                        perm_map['complaints.assign'], perm_map['comments.add_internal'],
                                        perm_map['notifications.view']])
        db.session.add(agent_role)
    else:
        agent_role = Role.query.filter_by(name='helpdesk_agent').first()

    if not Role.query.filter_by(name='user').first():
        user_role = Role(name='user', display_name='End User', is_system=True)
        user_role.permissions.extend([perm_map['complaints.view_my'], perm_map['complaints.create'],
                                       perm_map['notifications.view']])
        db.session.add(user_role)
    else:
        user_role = Role.query.filter_by(name='user').first()
    db.session.flush()

    # Create users
    def ensure_user(username, password, role):
        u = User.query.filter_by(username=username).first()
        if not u:
            u = User(username=username, email=f'{username}@test.local',
                     first_name=username.capitalize(), last_name='User', is_active=True)
            u.set_password(password)
            u.roles.append(role)
            db.session.add(u)
        else:
            if not u.is_active:
                u.is_active = True
        return u

    admin = ensure_user('admin', 'Admin@123', admin_role)
    agent = ensure_user('agent', 'Karachi@123', agent_role)
    enduser = ensure_user('enduser', 'User@123', user_role)
    db.session.flush()

    # Ensure a default software catalog entry exists so Complaint FKs resolve
    sw = SoftwareCatalog.query.filter_by(code='DEV-DEFAULT').first()
    if not sw:
        sw = SoftwareCatalog(name='Default Software', code='DEV-DEFAULT', is_active=True)
        db.session.add(sw)
    db.session.flush()

    # Create complaints
    existing_nums = {c.complaint_number for c in Complaint.query.all()}
    if 'ITC-2026-000001' not in existing_nums:
        c1 = Complaint(complaint_number='ITC-2026-000001', title='Laptop broken',
                       description='My laptop will not start', category_id=cat.id,
                       priority_id=pri.id, status_id=new_s.id, department_id=dept.id,
                       software_id=sw.id, reported_by_user_id=enduser.id,
                       assigned_to_user_id=agent.id, created_by_user_id=admin.id, source_type='portal')
        db.session.add(c1)
    if 'ITC-2026-000002' not in existing_nums:
        c2 = Complaint(complaint_number='ITC-2026-000002', title='Printer offline',
                       description='Printer not working', category_id=cat.id,
                       priority_id=pri.id, status_id=new_s.id, department_id=dept.id,
                       software_id=sw.id, reported_by_user_id=enduser.id,
                       assigned_to_user_id=None, created_by_user_id=admin.id, source_type='phone')
        db.session.add(c2)
    if 'ITC-2026-000003' not in existing_nums:
        c3 = Complaint(complaint_number='ITC-2026-000003', title='Network down',
                       description='WiFi not working', category_id=cat.id,
                       priority_id=pri.id, status_id=new_s.id, department_id=dept.id,
                       software_id=sw.id, reported_by_user_id=admin.id,
                       assigned_to_user_id=agent.id, created_by_user_id=admin.id, source_type='walk_in')
        db.session.add(c3)

    db.session.commit()
    print(f'Done. Users: admin, agent, enduser')
    print(f'Complaints: {Complaint.query.count()}')
    print(f'Agent view_all={agent.has_permission("complaints.view_all")}, view_my={agent.has_permission("complaints.view_my")}')
    print(f'Enduser view_all={enduser.has_permission("complaints.view_all")}, view_my={enduser.has_permission("complaints.view_my")}')
