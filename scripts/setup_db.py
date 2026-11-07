"""Database setup - creates SQLite database with all tables and seed data."""
import os
import sqlite3
import json
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'helpdesk.db')

def create_tables():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create all tables
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(120), password_hash VARCHAR(255) NOT NULL,
        employee_number VARCHAR(20), first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL, phone VARCHAR(20), extension VARCHAR(10),
        is_active INTEGER DEFAULT 1, is_locked INTEGER DEFAULT 0,
        locked_at DATETIME, lock_reason TEXT, last_login_at DATETIME,
        last_login_ip VARCHAR(45), failed_login_attempts INTEGER DEFAULT 0,
        last_failed_login_at DATETIME, password_changed_at DATETIME,
        must_change_password INTEGER DEFAULT 0, department_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER, updated_by_user_id INTEGER,
        deleted_at DATETIME, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(50) UNIQUE NOT NULL,
        display_name VARCHAR(100) NOT NULL, description TEXT, is_system INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at DATETIME,
        deleted_by_user_id INTEGER, version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) UNIQUE NOT NULL,
        display_name VARCHAR(100) NOT NULL, description TEXT, module VARCHAR(50) NOT NULL,
        action VARCHAR(50) NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE user_roles (
        user_id INTEGER NOT NULL REFERENCES users(id),
        role_id INTEGER NOT NULL REFERENCES roles(id),
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        assigned_by_user_id INTEGER REFERENCES users(id),
        PRIMARY KEY (user_id, role_id))''')
    c.execute('''CREATE TABLE role_permissions (
        role_id INTEGER NOT NULL REFERENCES roles(id),
        permission_id INTEGER NOT NULL REFERENCES permissions(id),
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        assigned_by_user_id INTEGER REFERENCES users(id),
        PRIMARY KEY (role_id, permission_id))''')
    c.execute('''CREATE TABLE departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) NOT NULL,
        code VARCHAR(20) UNIQUE NOT NULL, description TEXT, phone VARCHAR(20),
        email VARCHAR(120), floor VARCHAR(50), building VARCHAR(100), manager_id INTEGER,
        is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE software_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(150) NOT NULL,
        code VARCHAR(50) UNIQUE NOT NULL, sw_version VARCHAR(50), vendor VARCHAR(100),
        license_key TEXT, license_expiry DATE, support_url VARCHAR(255), description TEXT,
        is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) NOT NULL,
        code VARCHAR(30) UNIQUE NOT NULL, parent_id INTEGER, department_id INTEGER,
        sla_policy_id INTEGER, auto_assign_to_id INTEGER, requires_asset INTEGER DEFAULT 0,
        description TEXT, is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE priorities (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(50) NOT NULL,
        code VARCHAR(20) UNIQUE NOT NULL, level INTEGER NOT NULL, color VARCHAR(7) NOT NULL,
        sla_response_hours REAL, sla_resolution_hours REAL, escalation_hours REAL,
        notify_assigned INTEGER DEFAULT 0, notify_on_breach INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE statuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(50) NOT NULL,
        code VARCHAR(20) UNIQUE NOT NULL, color VARCHAR(7) NOT NULL,
        display_order INTEGER NOT NULL DEFAULT 0, description TEXT, is_terminal INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1, notify_assigned INTEGER DEFAULT 0,
        require_resolution_summary INTEGER DEFAULT 0, allow_reopen INTEGER DEFAULT 0,
        allowed_next_statuses TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_number VARCHAR(20) UNIQUE NOT NULL,
        title VARCHAR(255) NOT NULL, description TEXT NOT NULL, severity VARCHAR(20),
        status_id INTEGER NOT NULL, priority_id INTEGER NOT NULL, category_id INTEGER,
        department_id INTEGER, software_id INTEGER, reported_by_user_id INTEGER NOT NULL,
        assigned_to_user_id INTEGER, resolved_by_user_id INTEGER, incident_started_at DATETIME,
        resolved_at DATETIME, closed_at DATETIME, resolution_summary TEXT,
        first_response_at DATETIME, assigned_at DATETIME, sla_response_deadline DATETIME,
        sla_resolution_deadline DATETIME, sla_response_status VARCHAR(20),
        sla_resolution_status VARCHAR(20), affected_users_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE complaint_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id INTEGER NOT NULL,
        assigned_to_user_id INTEGER NOT NULL, assigned_by_user_id INTEGER,
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at DATETIME,
        deleted_by_user_id INTEGER, version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE complaint_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id INTEGER NOT NULL,
        from_status_id INTEGER, to_status_id INTEGER NOT NULL, changed_by_user_id INTEGER,
        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP, comment TEXT, is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at DATETIME,
        deleted_by_user_id INTEGER, version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE complaint_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id INTEGER NOT NULL,
        action VARCHAR(100) NOT NULL, old_value TEXT, new_value TEXT, changed_by_user_id INTEGER,
        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at DATETIME,
        deleted_by_user_id INTEGER, version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL, content TEXT NOT NULL, is_internal INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id INTEGER NOT NULL,
        filename VARCHAR(255) NOT NULL, original_filename VARCHAR(255) NOT NULL,
        file_path VARCHAR(500) NOT NULL, file_size INTEGER, mime_type VARCHAR(100),
        uploaded_by_user_id INTEGER NOT NULL, is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at DATETIME,
        deleted_by_user_id INTEGER, version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE sla_policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) NOT NULL, description TEXT,
        department_id INTEGER, priority_id INTEGER, category_id INTEGER,
        response_target_minutes INTEGER NOT NULL, resolution_target_minutes INTEGER NOT NULL,
        use_business_hours INTEGER DEFAULT 1, working_schedule_id INTEGER,
        escalation_enabled INTEGER DEFAULT 0, escalation_levels TEXT,
        pause_on_pending_info INTEGER DEFAULT 1, pause_on_hold INTEGER DEFAULT 1,
        pause_on_reassignment INTEGER DEFAULT 0, pause_on_reopen INTEGER DEFAULT 1,
        pause_on_status_ids TEXT, is_active INTEGER DEFAULT 1, is_default INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE sla_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id INTEGER NOT NULL, policy_id INTEGER,
        response_target_minutes INTEGER, resolution_target_minutes INTEGER,
        response_deadline DATETIME, resolution_deadline DATETIME, response_met INTEGER,
        resolution_met INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE working_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) NOT NULL, description TEXT,
        timezone VARCHAR(50) DEFAULT 'UTC', weekly_schedule TEXT, exceptions TEXT,
        department_id INTEGER, is_active INTEGER DEFAULT 1, is_default INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) NOT NULL, date DATE NOT NULL,
        is_recurring INTEGER DEFAULT 0, description TEXT, department_id INTEGER,
        is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, recipient_id INTEGER NOT NULL,
        type VARCHAR(50) NOT NULL, title VARCHAR(255) NOT NULL, message TEXT NOT NULL,
        complaint_id INTEGER, priority VARCHAR(20) DEFAULT 'normal', is_read INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE system_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, key VARCHAR(100) UNIQUE NOT NULL, value TEXT,
        description TEXT, setting_type VARCHAR(20) DEFAULT 'string', is_active INTEGER DEFAULT 1,
        is_system INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER,
        updated_by_user_id INTEGER, deleted_at DATETIME, deleted_by_user_id INTEGER,
        version INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action VARCHAR(100) NOT NULL,
        entity_type VARCHAR(50), entity_id INTEGER, entity_repr VARCHAR(255), old_values TEXT,
        new_values TEXT, changed_fields TEXT, ip_address VARCHAR(45), user_agent TEXT,
        category VARCHAR(50), created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()
    print(f'Created database at {DB_PATH}')


def seed_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Permissions
    perms = [
        ('dashboard:view', 'View Dashboard', 'dashboard', 'view'),
        ('dashboard:analytics', 'View Analytics', 'dashboard', 'analytics'),
        ('complaints:create', 'Create Complaint', 'complaints', 'create'),
        ('complaints:view', 'View Complaints', 'complaints', 'view'),
        ('complaints:edit', 'Edit Complaints', 'complaints', 'edit'),
        ('complaints:assign', 'Assign Complaints', 'complaints', 'assign'),
        ('complaints:close', 'Close Complaints', 'complaints', 'close'),
        ('complaints:delete', 'Delete Complaints', 'complaints', 'delete'),
        ('users:view', 'View Users', 'users', 'view'),
        ('users:create', 'Create Users', 'users', 'create'),
        ('users:edit', 'Edit Users', 'users', 'edit'),
        ('users:delete', 'Delete Users', 'users', 'delete'),
        ('admin:view', 'View Admin Panel', 'admin', 'view'),
        ('admin:manage_departments', 'Manage Departments', 'admin', 'manage_departments'),
        ('admin:manage_software', 'Manage Software Catalog', 'admin', 'manage_software'),
        ('admin:manage_categories', 'Manage Categories', 'admin', 'manage_categories'),
        ('admin:manage_priorities', 'Manage Priorities', 'admin', 'manage_priorities'),
        ('admin:manage_statuses', 'Manage Statuses', 'admin', 'manage_statuses'),
        ('admin:manage_sla', 'Manage SLA Policies', 'admin', 'manage_sla'),
        ('admin:manage_schedules', 'Manage Working Schedules', 'admin', 'manage_schedules'),
        ('admin:manage_holidays', 'Manage Holidays', 'admin', 'manage_holidays'),
        ('admin:manage_settings', 'Manage System Settings', 'admin', 'manage_settings'),
        ('reports:view', 'View Reports', 'reports', 'view'),
        ('reports:export', 'Export Reports', 'reports', 'export'),
        ('notifications:view', 'View Notifications', 'notifications', 'view'),
    ]
    for n, d, m, a in perms:
        c.execute('INSERT OR IGNORE INTO permissions (name, display_name, module, action) VALUES (?, ?, ?, ?)', (n, d, m, a))
    print(f'Inserted {len(perms)} permissions')

    # Roles
    roles = [
        ('admin', 'Administrator', 1, ['dashboard:view', 'dashboard:analytics', 'complaints:create', 'complaints:view', 'complaints:edit', 'complaints:assign', 'complaints:close', 'complaints:delete', 'users:view', 'users:create', 'users:edit', 'users:delete', 'admin:view', 'admin:manage_departments', 'admin:manage_software', 'admin:manage_categories', 'admin:manage_priorities', 'admin:manage_statuses', 'admin:manage_sla', 'admin:manage_schedules', 'admin:manage_holidays', 'admin:manage_settings', 'reports:view', 'reports:export', 'notifications:view']),
        ('support', 'Support Agent', 0, ['dashboard:view', 'complaints:create', 'complaints:view', 'complaints:edit', 'complaints:assign', 'complaints:close', 'reports:view', 'reports:export', 'notifications:view']),
        ('user', 'End User', 0, ['dashboard:view', 'complaints:create', 'complaints:view', 'notifications:view']),
    ]
    for n, d, s, pcs in roles:
        c.execute('INSERT OR IGNORE INTO roles (name, display_name, is_system) VALUES (?, ?, ?)', (n, d, s))
        rid = c.execute('SELECT id FROM roles WHERE name=?', (n,)).fetchone()[0]
        for pc in pcs:
            p = c.execute('SELECT id FROM permissions WHERE name=?', (pc,)).fetchone()
            if p:
                c.execute('INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)', (rid, p[0]))
    print(f'Inserted {len(roles)} roles')

    # Admin user
    admin = c.execute('SELECT id FROM users WHERE username=?', ('admin',)).fetchone()
    if not admin:
        c.execute('INSERT INTO users (username, email, first_name, last_name, employee_number, password_hash, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)', ('admin', 'admin@hospital.local', 'System', 'Administrator', 'ADMIN001', generate_password_hash('Admin@123')))
        aid = c.lastrowid
        rid = c.execute('SELECT id FROM roles WHERE name=?', ('admin',)).fetchone()[0]
        c.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (aid, rid))
        print(f'Created admin user (ID: {aid})')

    # Statuses
    statuses = [('New', 'new', '#3b82f6', 1, 1, 0), ('Assigned', 'assigned', '#8b5cf6', 2, 1, 0), ('In Progress', 'in_progress', '#f59e0b', 3, 1, 0), ('Pending Info', 'pending_info', '#f97316', 4, 1, 0), ('On Hold', 'on_hold', '#6b7280', 5, 1, 0), ('Resolved', 'resolved', '#10b981', 6, 1, 1), ('Closed', 'closed', '#6b7280', 7, 1, 1), ('Reopened', 'reopened', '#ef4444', 8, 1, 0), ('Rejected', 'rejected', '#dc2626', 9, 1, 1)]
    for n, code, color, order, terminal, active in statuses:
        c.execute('INSERT OR IGNORE INTO statuses (name, code, color, display_order, is_terminal, is_active) VALUES (?, ?, ?, ?, ?, ?)', (n, code, color, order, terminal, active))
    print(f'Inserted {len(statuses)} statuses')

    # Priorities
    priorities = [('Critical', 'CRITICAL', '#ef4444', 1, 1, 4, 2), ('High', 'HIGH', '#f97316', 2, 4, 24, 8), ('Medium', 'MEDIUM', '#3b82f6', 3, 24, 72, 24), ('Low', 'LOW', '#6b7280', 4, 72, 168, 48)]
    for n, code, color, level, resp, res, esc in priorities:
        c.execute('INSERT OR IGNORE INTO priorities (name, code, color, level, sla_response_hours, sla_resolution_hours, escalation_hours, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, 1)', (n, code, color, level, resp, res, esc))
    print(f'Inserted {len(priorities)} priorities')

    # Departments
    depts = [('IT Helpdesk', 'ITH'), ('Network Operations', 'NET'), ('Clinical Systems', 'CLI'), ('Patient Administration', 'PAT'), ('Billing', 'BIL')]
    for n, code in depts:
        c.execute('INSERT OR IGNORE INTO departments (name, code, is_active) VALUES (?, ?, 1)', (n, code))
    print(f'Inserted {len(depts)} departments')

    # Working schedule
    weekly = {'monday': {'start': '09:00', 'end': '17:00'}, 'tuesday': {'start': '09:00', 'end': '17:00'}, 'wednesday': {'start': '09:00', 'end': '17:00'}, 'thursday': {'start': '09:00', 'end': '17:00'}, 'friday': {'start': '09:00', 'end': '17:00'}, 'saturday': None, 'sunday': None}
    c.execute("INSERT OR IGNORE INTO working_schedules (name, timezone, weekly_schedule, is_default, is_active) VALUES (?, ?, ?, ?, 1)", ('Standard Business Hours', 'UTC', json.dumps(weekly), 1))
    print('Inserted working schedule')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    print('=' * 50)
    print('Hospital Complaint Tracking System - Database Setup')
    print('=' * 50)
    print(f'Database path: {DB_PATH}')
    create_tables()
    seed_data()

    # Verify
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    conn.close()
    print(f'\nDatabase has {len(tables)} tables:')
    for t in tables:
        print(f'  - {t}')
    print('\nSetup complete!')