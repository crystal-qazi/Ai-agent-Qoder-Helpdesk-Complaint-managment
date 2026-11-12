"""
Seed data script for IT Software Complain System.
Uses raw SQL to avoid SQLAlchemy circular dependency issues.
Usage: python scripts/seed_data.py
"""
import os
import sys
import sqlite3
import json
import re
from werkzeug.security import generate_password_hash

# Load .env file
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# Read database URL from environment
db_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/helpdesk.db')

def get_connection():
    """Get database connection based on URL."""
    if db_url.startswith('mysql'):
        match = re.match(r'mysql\+pymysql://([^:]+):([^@]*)@([^:/]+)(?::(\d+))?/(\w+)', db_url)
        if not match:
            raise ValueError("Could not parse DATABASE_URL")
        user, password, host, port, dbname = match.groups()
        import pymysql
        conn = pymysql.connect(host=host, port=int(port or 3306), user=user, password=password, database=dbname)
        return conn, 'mysql'
    elif db_url.startswith('postgresql'):
        match = re.match(r'postgresql://([^:]+):([^@]*)@([^:/]+)(?::(\d+))?/(\w+)', db_url)
        if not match:
            raise ValueError("Could not parse DATABASE_URL")
        user, password, host, port, dbname = match.groups()
        import psycopg2
        conn = psycopg2.connect(host=host, port=int(port or 5432), user=user, password=password, database=dbname)
        return conn, 'postgres'
    else:
        # SQLite
        db_path = db_url.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            db_path = os.path.join(BASE_DIR, db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        return conn, 'sqlite'

def execute_sql(c, sql, params=None, dialect='sqlite'):
    """Execute SQL with proper placeholders."""
    if dialect == 'mysql':
        c.execute(sql, params)
    else:
        c.execute(sql, params)

print("=" * 50)
print("IT Software Complain System - Seed Data")
print("=" * 50)

conn, dialect = get_connection()
c = conn.cursor()
print(f"Database dialect: {dialect}")

# Create tables
tables = {
    'users': '''id {id_type} PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL, email VARCHAR(120), password_hash VARCHAR(255) NOT NULL, employee_number VARCHAR(20), first_name VARCHAR(50) NOT NULL, last_name VARCHAR(50) NOT NULL, phone VARCHAR(20), extension VARCHAR(10), is_active INTEGER DEFAULT 1, is_locked INTEGER DEFAULT 0, locked_at DATETIME, lock_reason TEXT, last_login_at TIMESTAMP, last_login_ip VARCHAR(45), failed_login_attempts INTEGER DEFAULT 0, last_failed_login_at TIMESTAMP, password_changed_at TIMESTAMP, must_change_password INTEGER DEFAULT 0, department_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'roles': '''id {id_type} PRIMARY KEY, name VARCHAR(50) UNIQUE NOT NULL, display_name VARCHAR(100) NOT NULL, description TEXT, is_system INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'permissions': '''id {id_type} PRIMARY KEY, name VARCHAR(100) UNIQUE NOT NULL, display_name VARCHAR(100) NOT NULL, description TEXT, module VARCHAR(50) NOT NULL, action VARCHAR(50) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'user_roles': '''user_id INTEGER NOT NULL, role_id INTEGER NOT NULL, assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, assigned_by_user_id INTEGER, PRIMARY KEY (user_id, role_id)''',
    'role_permissions': '''role_id INTEGER NOT NULL, permission_id INTEGER NOT NULL, assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, assigned_by_user_id INTEGER, PRIMARY KEY (role_id, permission_id)''',
    'departments': '''id {id_type} PRIMARY KEY, name VARCHAR(100) NOT NULL, code VARCHAR(20) UNIQUE NOT NULL, description TEXT, phone VARCHAR(20), email VARCHAR(120), floor VARCHAR(50), building VARCHAR(100), manager_id INTEGER, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'software_catalog': '''id {id_type} PRIMARY KEY, name VARCHAR(150) NOT NULL, code VARCHAR(50) UNIQUE NOT NULL, sw_version VARCHAR(50), vendor VARCHAR(100), license_key TEXT, license_expiry DATE, support_url VARCHAR(255), description TEXT, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'categories': '''id {id_type} PRIMARY KEY, name VARCHAR(100) NOT NULL, code VARCHAR(30) UNIQUE NOT NULL, parent_id INTEGER, department_id INTEGER, sla_policy_id INTEGER, auto_assign_to_id INTEGER, requires_asset INTEGER DEFAULT 0, description TEXT, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'priorities': '''id {id_type} PRIMARY KEY, name VARCHAR(50) NOT NULL, code VARCHAR(20) UNIQUE NOT NULL, level INTEGER NOT NULL, color VARCHAR(7) NOT NULL, sla_response_hours REAL, sla_resolution_hours REAL, escalation_hours REAL, notify_assigned INTEGER DEFAULT 0, notify_on_breach INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'statuses': '''id {id_type} PRIMARY KEY, name VARCHAR(50) NOT NULL, code VARCHAR(20) UNIQUE NOT NULL, color VARCHAR(7) NOT NULL, display_order INTEGER NOT NULL DEFAULT 0, description TEXT, is_terminal INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, notify_assigned INTEGER DEFAULT 0, require_resolution_summary INTEGER DEFAULT 0, allow_reopen INTEGER DEFAULT 0, allowed_next_statuses TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'complaints': '''id {id_type} PRIMARY KEY, complaint_number VARCHAR(20) UNIQUE NOT NULL, title VARCHAR(255) NOT NULL, description TEXT NOT NULL, severity VARCHAR(20), status_id INTEGER NOT NULL, priority_id INTEGER NOT NULL, category_id INTEGER, department_id INTEGER, software_id INTEGER, reported_by_user_id INTEGER NOT NULL, assigned_to_user_id INTEGER, resolved_by_user_id INTEGER, incident_started_at TIMESTAMP, resolved_at TIMESTAMP, closed_at TIMESTAMP, resolution_summary TEXT, first_response_at TIMESTAMP, assigned_at TIMESTAMP, sla_response_deadline TIMESTAMP, sla_resolution_deadline TIMESTAMP, sla_response_status VARCHAR(20), sla_resolution_status VARCHAR(20), affected_users_count INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'sla_policies': '''id {id_type} PRIMARY KEY, name VARCHAR(100) NOT NULL, description TEXT, department_id INTEGER, priority_id INTEGER, category_id INTEGER, response_target_minutes INTEGER NOT NULL, resolution_target_minutes INTEGER NOT NULL, use_business_hours INTEGER DEFAULT 1, working_schedule_id INTEGER, escalation_enabled INTEGER DEFAULT 0, escalation_levels TEXT, pause_on_pending_info INTEGER DEFAULT 1, pause_on_hold INTEGER DEFAULT 1, pause_on_reassignment INTEGER DEFAULT 0, pause_on_reopen INTEGER DEFAULT 1, pause_on_status_ids TEXT, is_active INTEGER DEFAULT 1, is_default INTEGER DEFAULT 0, sort_order INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'working_schedules': '''id {id_type} PRIMARY KEY, name VARCHAR(100) NOT NULL, description TEXT, timezone VARCHAR(50) DEFAULT 'UTC', weekly_schedule TEXT, exceptions TEXT, department_id INTEGER, is_active INTEGER DEFAULT 1, is_default INTEGER DEFAULT 0, sort_order INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'holidays': '''id {id_type} PRIMARY KEY, name VARCHAR(100) NOT NULL, date DATE NOT NULL, is_recurring INTEGER DEFAULT 0, description TEXT, department_id INTEGER, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'notifications': '''id {id_type} PRIMARY KEY, recipient_id INTEGER NOT NULL, type VARCHAR(50) NOT NULL, title VARCHAR(255) NOT NULL, message TEXT NOT NULL, complaint_id INTEGER, priority VARCHAR(20) DEFAULT 'normal', is_read INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP''',
    'system_settings': '''id {id_type} PRIMARY KEY, key VARCHAR(100) UNIQUE NOT NULL, value TEXT, description TEXT, setting_type VARCHAR(20) DEFAULT 'string', is_active INTEGER DEFAULT 1, is_system INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'audit_logs': '''id {id_type} PRIMARY KEY, user_id INTEGER, action VARCHAR(100) NOT NULL, entity_type VARCHAR(50), entity_id INTEGER, entity_repr VARCHAR(255), old_values TEXT, new_values TEXT, changed_fields TEXT, ip_address VARCHAR(45), user_agent TEXT, category VARCHAR(50), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP''',
    'user_profiles': '''id {id_type} PRIMARY KEY, user_id INTEGER UNIQUE NOT NULL, title VARCHAR(100), hire_date DATE, manager_id INTEGER, avatar_path VARCHAR(255), preferences TEXT, email_notifications INTEGER DEFAULT 1, in_app_notifications INTEGER DEFAULT 1, notify_on_assignment INTEGER DEFAULT 1, notify_on_status_change INTEGER DEFAULT 1, notify_on_comments INTEGER DEFAULT 1, notify_on_sla_breach INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'login_attempts': '''id {id_type} PRIMARY KEY, user_id INTEGER, username_attempted VARCHAR(50) NOT NULL, ip_address VARCHAR(45) NOT NULL, user_agent TEXT, success INTEGER DEFAULT 0, failure_reason VARCHAR(100), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP''',
    'complaint_assignments': '''id {id_type} PRIMARY KEY, complaint_id INTEGER NOT NULL, assigned_to_user_id INTEGER NOT NULL, assigned_by_user_id INTEGER, assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'complaint_status_history': '''id {id_type} PRIMARY KEY, complaint_id INTEGER NOT NULL, from_status_id INTEGER, to_status_id INTEGER NOT NULL, changed_by_user_id INTEGER, changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, comment TEXT, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'complaint_history': '''id {id_type} PRIMARY KEY, complaint_id INTEGER NOT NULL, action VARCHAR(100) NOT NULL, old_value TEXT, new_value TEXT, changed_by_user_id INTEGER, changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'comments': '''id {id_type} PRIMARY KEY, complaint_id INTEGER NOT NULL, user_id INTEGER NOT NULL, content TEXT NOT NULL, is_internal INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'attachments': '''id {id_type} PRIMARY KEY, complaint_id INTEGER NOT NULL, filename VARCHAR(255) NOT NULL, original_filename VARCHAR(255) NOT NULL, file_path VARCHAR(500) NOT NULL, file_size INTEGER, mime_type VARCHAR(100), uploaded_by_user_id INTEGER NOT NULL, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_by_user_id INTEGER, updated_by_user_id INTEGER, deleted_at TIMESTAMP, deleted_by_user_id INTEGER, version INTEGER DEFAULT 1''',
    'sla_history': '''id {id_type} PRIMARY KEY, complaint_id INTEGER NOT NULL, policy_id INTEGER, response_target_minutes INTEGER, resolution_target_minutes INTEGER, response_deadline TIMESTAMP, resolution_deadline TIMESTAMP, response_met INTEGER, resolution_met INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1''',
}

for table_name, columns in tables.items():
    # Check if this is a junction table with a composite PK and no id column
    if '{id_type}' not in columns and 'PRIMARY KEY (' in columns:
        # Strip the trailing PRIMARY KEY clause for cleaner SQL
        cols = re.sub(r'\s*,?\s*PRIMARY KEY\s*\([^)]+\)\s*', '', columns).strip()
        if dialect == 'mysql':
            c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({cols}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')
        else:
            c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({cols})')
        continue

    # Standard table: strip old id definition and rebuild
    cols = re.sub(r'\s*id\s*\{id_type\}\s*,?\s*PRIMARY KEY\s*,?', '', columns)
    cols = re.sub(r'\s+PRIMARY KEY\s*,?', '', cols)
    cols = cols.strip().lstrip(', ')
    if dialect == 'mysql':
        id_col = 'id INT AUTO_INCREMENT PRIMARY KEY'
    else:
        id_col = 'id INTEGER PRIMARY KEY AUTOINCREMENT'
    full_cols = id_col + ', ' + cols
    # Escape MySQL reserved words used as column identifiers
    if dialect == 'mysql':
        for rw in ('key', 'order'):
            full_cols = re.sub(rf'\b{rw}\b(?=[\s`,])', f'`{rw}`', full_cols)
    if dialect == 'mysql':
        c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({full_cols}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')
    else:
        c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({full_cols})')
print('Tables created')

# Seed permissions
permissions = [
    ('dashboard.view', 'View Dashboard', 'dashboard', 'view'),
    ('dashboard.analytics', 'View Analytics', 'dashboard', 'analytics'),
    ('complaints.create', 'Create Complaint', 'complaints', 'create'),
    ('complaints.view_all', 'View All Complaints', 'complaints', 'view_all'),
    ('complaints.view_my', 'View My Complaints', 'complaints', 'view_my'),
    ('complaints.edit', 'Edit Complaint', 'complaints', 'edit'),
    ('complaints.assign', 'Assign Complaint', 'complaints', 'assign'),
    ('complaints.transfer', 'Transfer Complaint', 'complaints', 'transfer'),
    ('complaints.change_status_own', 'Change Status of Own Complaints', 'complaints', 'change_status_own'),
    ('complaints.change_status_all', 'Change Status of Any Complaint', 'complaints', 'change_status_all'),
    ('complaints.status_unlock', 'Access Restricted Statuses', 'complaints', 'status_unlock'),
    ('complaints.delete', 'Delete Complaints', 'complaints', 'delete'),
    ('users.view', 'View Users', 'users', 'view'),
    ('users.create', 'Create Users', 'users', 'create'),
    ('users.edit', 'Edit Users', 'users', 'edit'),
    ('users.delete', 'Delete Users', 'users', 'delete'),
    ('admin.view', 'View Admin Panel', 'admin', 'view'),
    ('admin.manage_departments', 'Manage Departments', 'admin', 'manage_departments'),
    ('admin.manage_software', 'Manage Software Catalog', 'admin', 'manage_software'),
    ('admin.manage_categories', 'Manage Categories', 'admin', 'manage_categories'),
    ('admin.manage_priorities', 'Manage Priorities', 'admin', 'manage_priorities'),
    ('admin.manage_statuses', 'Manage Statuses', 'admin', 'manage_statuses'),
    ('admin.manage_sla', 'Manage SLA Policies', 'admin', 'manage_sla'),
    ('admin.manage_schedules', 'Manage Working Schedules', 'admin', 'manage_schedules'),
    ('admin.manage_holidays', 'Manage Holidays', 'admin', 'manage_holidays'),
    ('admin.manage_settings', 'Manage System Settings', 'admin', 'manage_settings'),
    ('reports.view', 'View Reports', 'reports', 'view'),
    ('reports.export', 'Export Reports', 'reports', 'export'),
    ('notifications.view', 'View Notifications', 'notifications', 'view'),
    # Comment permissions
    ('comments.add_internal', 'Add Internal Comments', 'comments', 'add_internal'),
    ('comments.add_reporter_visible', 'Add Reporter-Visible Comments', 'comments', 'add_reporter_visible'),
    ('comments.view_internal', 'View Internal Comments', 'comments', 'view_internal'),
    # Attachment permissions
    ('attachments.upload', 'Upload Attachments', 'attachments', 'upload'),
    ('attachments.download_all', 'Download All Attachments', 'attachments', 'download_all'),
    ('attachments.delete', 'Delete Attachments', 'attachments', 'delete'),
    ('attachments.delete_own', 'Delete Own Attachments', 'attachments', 'delete_own'),
    # Admin/management permissions
    ('users.manage', 'Manage Users', 'users', 'manage'),
    ('roles.manage', 'Manage Roles', 'roles', 'manage'),
    ('permissions.manage', 'Manage Permissions', 'permissions', 'manage'),
    ('departments.manage', 'Manage Departments', 'departments', 'manage'),
    ('software.manage', 'Manage Software', 'software', 'manage'),
    ('categories.manage', 'Manage Categories', 'categories', 'manage'),
    ('priorities.manage', 'Manage Priorities', 'priorities', 'manage'),
    ('statuses.manage', 'Manage Statuses', 'statuses', 'manage'),
    ('sla.manage', 'Manage SLA Policies', 'sla', 'manage'),
    ('audit.view', 'View Audit Logs', 'audit', 'view'),
    ('settings.manage', 'Manage Settings', 'settings', 'manage'),
    ('config.manage', 'Manage Configuration', 'config', 'manage'),
]
insert_sql = 'INSERT IGNORE' if dialect == 'mysql' else 'INSERT OR IGNORE'
param_style = '%s' if dialect == 'mysql' else '?'
for name, display, module, action in permissions:
    c.execute(f'{insert_sql} INTO permissions (name, display_name, module, action) VALUES ({param_style}, {param_style}, {param_style}, {param_style})', (name, display, module, action))
print(f'Inserted {len(permissions)} permissions')

# Seed roles
all_perms = [p[0] for p in permissions]
roles_data = [
    ('admin', 'Administrator', True, all_perms),
    ('helpdesk_agent', 'Helpdesk Agent', False, ['dashboard.view', 'dashboard.analytics', 'complaints.create', 'complaints.view_all', 'complaints.view_my', 'complaints.edit', 'complaints.assign', 'complaints.transfer', 'complaints.change_status_own', 'complaints.change_status_all', 'complaints.status_unlock', 'comments.add_internal', 'comments.add_reporter_visible', 'comments.view_internal', 'attachments.upload', 'attachments.download_all', 'reports.view', 'reports.export', 'notifications.view']),
    ('support_agent', 'Support Agent', False, ['dashboard.view', 'dashboard.analytics', 'complaints.create', 'complaints.view_my', 'complaints.edit', 'complaints.transfer', 'complaints.change_status_own', 'comments.add_internal', 'comments.add_reporter_visible', 'comments.view_internal', 'attachments.upload', 'attachments.download_all', 'reports.view', 'reports.export', 'notifications.view']),
    ('user', 'End User', False, ['dashboard.view', 'complaints.create', 'comments.add_reporter_visible', 'notifications.view']),
    ('employee', 'Internal Employee', False, ['dashboard.view', 'complaints.create', 'complaints.view_my', 'notifications.view']),
]
for name, display, is_system, perm_codes in roles_data:
    c.execute(f'{insert_sql} INTO roles (name, display_name, is_system) VALUES ({param_style}, {param_style}, {param_style})', (name, display, is_system))
    c.execute('SELECT id FROM roles WHERE name=' + param_style, (name,))
    role_id = c.fetchone()[0]
    for perm_code in perm_codes:
        c.execute('SELECT id FROM permissions WHERE name=' + param_style, (perm_code,))
        perm = c.fetchone()
        if perm:
            c.execute(f'{insert_sql} INTO role_permissions (role_id, permission_id) VALUES ({param_style}, {param_style})', (role_id, perm[0]))
print(f'Inserted {len(roles_data)} roles')

# Seed admin user
admin = c.execute("SELECT id FROM users WHERE username='admin'") and c.fetchone()
if not admin:
    c.execute(f"INSERT INTO users (username, email, first_name, last_name, employee_number, password_hash, is_active) VALUES ({param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, 1)", ('admin', 'admin@hospital.local', 'System', 'Administrator', 'ADMIN001', generate_password_hash('Admin@123')))
    admin_id = c.lastrowid
    role_id = c.execute("SELECT id FROM roles WHERE name='admin'") and c.fetchone()[0]
    c.execute(f"INSERT INTO user_roles (user_id, role_id) VALUES ({param_style}, {param_style})", (admin_id, role_id))
    print(f'Created admin user (ID: {admin_id})')
else:
    print('Admin user already exists')

# Seed statuses
statuses = [
    ('New',         'new',        '#3b82f6', 1, 0, 1, 0, 1, 'intake',   None, 'Initial complaint', '[2,3,4,5,6,9]', 1),
    ('Assigned',    'assigned',   '#8b5cf6', 2, 0, 1, 0, 0, 'processing', None, 'Waiting for work', '[3,4,5,7]', 0),
    ('In Progress', 'in_progress','#f59e0b', 3, 0, 1, 0, 0, 'processing', None, 'Work underway', '[4,5,6]', 0),
    ('Pending Info','pending_info','#f97316', 4, 0, 1, 0, 0, 'processing', None, 'Awaiting response', '[3,5,6]', 0),
    ('On Hold',     'on_hold',    '#6b7280', 5, 0, 1, 0, 0, 'processing', None, 'Temporarily paused', '[3,4,6]', 0),
    ('Resolved',    'resolved',   '#10b981', 6, 0, 1, 1, 1, 'resolution', None, 'Issue resolved', '[8]', 0),
    ('Closed',      'closed',     '#6b7280', 7, 1, 1, 0, 0, 'resolution', None, 'Formally closed', '[]', 0),
    ('Reopened',    'reopened',   '#ef4444', 8, 0, 1, 0, 0, 'processing', None, 'Reopened after close', '[3,4,5,6]', 0),
    ('Rejected',    'rejected',   '#dc2626', 9, 1, 1, 1, 0, 'resolution', None, 'Request rejected', '[]', 0),
]
for name, code, color, order, terminal, active, requires_reason, requires_resolution, category, icon, desc, allowed_transitions, is_initial in statuses:
    c.execute(f'{insert_sql} INTO statuses (name, code, color, sort_order, is_terminal, is_active, requires_reason, requires_resolution, category, icon, description, allowed_transitions, is_initial) VALUES ({param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style})', (name, code, color, order, terminal, active, requires_reason, requires_resolution, category, icon, desc, allowed_transitions, is_initial))
print(f'Inserted {len(statuses)} statuses')

# Seed priorities
priorities = [
    ('Critical', 'CRITICAL', '#ef4444', 1, 1, 4, 2, 1, 1),
    ('High',     'HIGH',     '#f97316', 2, 4, 24, 8, 1, 1),
    ('Medium',   'MEDIUM',   '#3b82f6', 3, 24, 72, 24, 0, 0),
    ('Low',      'LOW',      '#6b7280', 4, 72, 168, 48, 0, 0),
]
for name, code, color, level, resp, res, esc, notify, breach in priorities:
    c.execute(f'{insert_sql} INTO priorities (name, code, color, level, sla_response_hours, sla_resolution_hours, escalation_hours, notify_assigned, notify_on_breach, sort_order, is_active) VALUES ({param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, {param_style}, 1)', (name, code, color, level, resp, res, esc, notify, breach, level))
print(f'Inserted {len(priorities)} priorities')

# Seed departments
depts = [('IT Helpdesk',  'ITH',  'IT support desk'),
         ('Network Operations', 'NET', 'Network infrastructure'),
         ('Clinical Systems', 'CLI', 'Clinical system support'),
         ('Patient Administration', 'PAT', 'Patient records admin'),
         ('Billing', 'BIL', 'Billing department')]
for i, (name, code, desc) in enumerate(depts, 1):
    c.execute(f'{insert_sql} INTO departments (name, code, description, sort_order, is_active) VALUES ({param_style}, {param_style}, {param_style}, {param_style}, 1)', (name, code, desc, i))
print(f'Inserted {len(depts)} departments')

# Seed working schedule
weekly = {'monday': {'start': '09:00', 'end': '17:00'}, 'tuesday': {'start': '09:00', 'end': '17:00'}, 'wednesday': {'start': '09:00', 'end': '17:00'}, 'thursday': {'start': '09:00', 'end': '17:00'}, 'friday': {'start': '09:00', 'end': '17:00'}, 'saturday': None, 'sunday': None}
c.execute(f'{insert_sql} INTO working_schedules (name, timezone, weekly_schedule, is_default, is_active) VALUES ({param_style}, {param_style}, {param_style}, {param_style}, 1)', ('Standard Business Hours', 'UTC', json.dumps(weekly), 1))
print('Inserted working schedule')

conn.commit()
conn.close()

print('\nSetup complete!')