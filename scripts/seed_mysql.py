"""Seed MySQL database directly."""
import pymysql
import json
from werkzeug.security import generate_password_hash

conn = pymysql.connect(host='localhost', port=3306, user='root', password='root', database='helpdesk_qoder')
c = conn.cursor()

print("Creating tables...")
tables = [
    ('software_catalog', 'id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(150) NOT NULL, code VARCHAR(50) UNIQUE NOT NULL, vendor VARCHAR(100), license_key TEXT, license_expiry DATE, support_url VARCHAR(255), description TEXT, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('categories', 'id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, code VARCHAR(30) UNIQUE NOT NULL, parent_id INT, department_id INT, sla_policy_id INT, auto_assign_to_id INT, requires_asset TINYINT DEFAULT 0, description TEXT, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('complaints', 'id INT AUTO_INCREMENT PRIMARY KEY, complaint_number VARCHAR(30) UNIQUE NOT NULL, title VARCHAR(255) NOT NULL, description TEXT NOT NULL, severity VARCHAR(20), status_id INT NOT NULL, priority_id INT NOT NULL, category_id INT, department_id INT, software_id INT, reported_by_user_id INT NOT NULL, assigned_to_user_id INT, resolved_by_user_id INT, incident_started_at DATETIME, resolved_at DATETIME, closed_at DATETIME, resolution_summary TEXT, first_response_at DATETIME, assigned_at DATETIME, sla_response_deadline DATETIME, sla_resolution_deadline DATETIME, sla_response_status VARCHAR(20), sla_resolution_status VARCHAR(20), affected_users_count INT DEFAULT 0, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('sla_policies', 'id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, description TEXT, department_id INT, priority_id INT, category_id INT, response_target_minutes INT NOT NULL, resolution_target_minutes INT NOT NULL, use_business_hours TINYINT DEFAULT 1, working_schedule_id INT, escalation_enabled TINYINT DEFAULT 0, escalation_levels JSON, pause_on_pending_info TINYINT DEFAULT 1, pause_on_hold TINYINT DEFAULT 1, pause_on_reassignment TINYINT DEFAULT 0, pause_on_reopen TINYINT DEFAULT 1, pause_on_status_ids JSON, is_active TINYINT DEFAULT 1, is_default TINYINT DEFAULT 0, sort_order INT DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('working_schedules', 'id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, description TEXT, timezone VARCHAR(50) DEFAULT "UTC", weekly_schedule JSON, exceptions JSON, department_id INT, is_active TINYINT DEFAULT 1, is_default TINYINT DEFAULT 0, sort_order INT DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('holidays', 'id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, date DATE NOT NULL, is_recurring TINYINT DEFAULT 0, description TEXT, department_id INT, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('notifications', 'id INT AUTO_INCREMENT PRIMARY KEY, recipient_id INT NOT NULL, type VARCHAR(50) NOT NULL, title VARCHAR(255) NOT NULL, message TEXT NOT NULL, complaint_id INT, priority VARCHAR(20) DEFAULT "normal", is_read TINYINT DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
    ('system_settings', 'id INT AUTO_INCREMENT PRIMARY KEY, key VARCHAR(100) UNIQUE NOT NULL, value TEXT, description TEXT, setting_type VARCHAR(20) DEFAULT "string", is_active TINYINT DEFAULT 1, is_system TINYINT DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('audit_logs', 'id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, action VARCHAR(100) NOT NULL, entity_type VARCHAR(50), entity_id INT, entity_repr VARCHAR(255), old_values JSON, new_values JSON, changed_fields JSON, ip_address VARCHAR(45), user_agent TEXT, category VARCHAR(50), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ('user_profiles', 'id INT AUTO_INCREMENT PRIMARY KEY, user_id INT UNIQUE NOT NULL, title VARCHAR(100), hire_date DATE, manager_id INT, avatar_path VARCHAR(255), preferences JSON, email_notifications TINYINT DEFAULT 1, in_app_notifications TINYINT DEFAULT 1, notify_on_assignment TINYINT DEFAULT 1, notify_on_status_change TINYINT DEFAULT 1, notify_on_comments TINYINT DEFAULT 1, notify_on_sla_breach TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('login_attempts', 'id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, username_attempted VARCHAR(50) NOT NULL, ip_address VARCHAR(45) NOT NULL, user_agent TEXT, success TINYINT DEFAULT 0, failure_reason VARCHAR(100), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ('complaint_assignments', 'id INT AUTO_INCREMENT PRIMARY KEY, complaint_id INT NOT NULL, assigned_to_user_id INT NOT NULL, assigned_by_user_id INT, assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('complaint_status_history', 'id INT AUTO_INCREMENT PRIMARY KEY, complaint_id INT NOT NULL, from_status_id INT, to_status_id INT NOT NULL, changed_by_user_id INT, changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, comment TEXT, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('complaint_history', 'id INT AUTO_INCREMENT PRIMARY KEY, complaint_id INT NOT NULL, action VARCHAR(100) NOT NULL, old_value TEXT, new_value TEXT, changed_by_user_id INT, changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('comments', 'id INT AUTO_INCREMENT PRIMARY KEY, complaint_id INT NOT NULL, user_id INT NOT NULL, content TEXT NOT NULL, is_internal TINYINT DEFAULT 0, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('attachments', 'id INT AUTO_INCREMENT PRIMARY KEY, complaint_id INT NOT NULL, filename VARCHAR(255) NOT NULL, original_filename VARCHAR(255) NOT NULL, file_path VARCHAR(500) NOT NULL, file_size INT, mime_type VARCHAR(100), uploaded_by_user_id INT NOT NULL, is_active TINYINT DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, created_by_user_id INT, updated_by_user_id INT, deleted_at DATETIME, deleted_by_user_id INT'),
    ('sla_history', 'id INT AUTO_INCREMENT PRIMARY KEY, complaint_id INT NOT NULL, policy_id INT, response_target_minutes INT, resolution_target_minutes INT, response_deadline DATETIME, resolution_deadline DATETIME, response_met TINYINT, resolution_met TINYINT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active TINYINT DEFAULT 1'),
]

for table_name, sql in tables:
    try:
        c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({sql}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')
        print(f'Created: {table_name}')
    except Exception as e:
        print(f'Error {table_name}: {e}')

conn.commit()
print("\nSeeding data...")

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
for name, display, module, action in permissions:
    c.execute('INSERT IGNORE INTO permissions (name, display_name, module, action) VALUES (%s, %s, %s, %s)', (name, display, module, action))
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
    c.execute('INSERT IGNORE INTO roles (name, display_name, is_system) VALUES (%s, %s, %s)', (name, display, is_system))
    role_id = c.lastrowid
    if role_id == 0:
        c.execute('SELECT id FROM roles WHERE name=%s', (name,))
        role_id = c.fetchone()[0]
    for perm_code in perm_codes:
        c.execute('SELECT id FROM permissions WHERE name=%s', (perm_code,))
        perm = c.fetchone()
        if perm:
            c.execute('INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES (%s, %s)', (role_id, perm[0]))
print(f'Inserted {len(roles_data)} roles')

# Seed admin user
admin = c.execute('SELECT id FROM users WHERE username=%s', ('admin',)).fetchone()
if not admin:
    c.execute('INSERT INTO users (username, email, first_name, last_name, employee_number, password_hash, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s)', ('admin', 'admin@hospital.local', 'System', 'Administrator', 'ADMIN001', generate_password_hash('Admin@123'), True))
    admin_id = c.lastrowid
    c.execute('SELECT id FROM roles WHERE name=%s', ('admin',))
    role_id = c.fetchone()[0]
    c.execute('INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)', (admin_id, role_id))
    print(f'Created admin user (ID: {admin_id})')
else:
    print('Admin user already exists')

# Seed statuses
statuses = [
    ('New', 'new', '#3b82f6', 1, True, True, 'Initial status', 'open', None, False, False, '[2,3,4,5,6,9]', True),
    ('Assigned', 'assigned', '#8b5cf6', 2, True, True, 'Assigned', 'processing', 'user-check', False, False, '[3,4,5,7]', False),
    ('In Progress', 'in_progress', '#f59e0b', 3, True, True, 'Work in progress', 'processing', 'loader', False, False, '[4,5,6]', False),
    ('Pending Info', 'pending_info', '#f97316', 4, True, True, 'Waiting for info', 'pending', 'help-circle', True, False, '[3,5,6]', False),
    ('On Hold', 'on_hold', '#6b7280', 5, True, True, 'Paused', 'pending', 'pause', False, False, '[3,4,6]', False),
    ('Resolved', 'resolved', '#10b981', 6, True, False, 'Resolved', 'resolved', 'check-circle', False, True, '[8]', False),
    ('Closed', 'closed', '#6b7280', 7, True, False, 'Closed', 'closed', 'lock', False, False, '[]', False),
    ('Reopened', 'reopened', '#ef4444', 8, True, True, 'Reopened', 'open', 'rotate-ccw', False, False, '[3,4,5,6]', False),
    ('Rejected', 'rejected', '#dc2626', 9, True, False, 'Rejected', 'closed', 'x-circle', False, False, '[]', False),
]
for name, code, color, order, terminal, active, desc, category, icon, requires_reason, requires_resolution, allowed_transitions, is_initial in statuses:
    c.execute('INSERT IGNORE INTO statuses (name, code, color, sort_order, is_terminal, is_active, description, category, icon, requires_reason, requires_resolution, allowed_transitions, is_initial) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (name, code, color, order, terminal, active, desc, category, icon, requires_reason, requires_resolution, allowed_transitions, is_initial))
print(f'Inserted {len(statuses)} statuses')

# Seed priorities
priorities = [
    ('Critical', 'CRITICAL', '#ef4444', 1, 1, 4, 2, True, True, 1),
    ('High', 'HIGH', '#f97316', 2, 4, 24, 8, True, True, 2),
    ('Medium', 'MEDIUM', '#3b82f6', 3, 24, 72, 24, False, False, 3),
    ('Low', 'LOW', '#6b7280', 4, 72, 168, 48, False, False, 4),
]
for name, code, color, level, resp, res, esc, notify, breach, sort_order in priorities:
    c.execute('INSERT IGNORE INTO priorities (name, code, color, level, sla_response_hours, sla_resolution_hours, escalation_hours, notify_assigned, notify_on_breach, sort_order, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (name, code, color, level, resp, res, esc, notify, breach, sort_order, True))
print(f'Inserted {len(priorities)} priorities')

# Seed departments
depts = [('IT Helpdesk', 'ITH'), ('Network Operations', 'NET'), ('Clinical Systems', 'CLI'), ('Patient Administration', 'PAT'), ('Billing', 'BIL')]
for name, code in depts:
    c.execute('INSERT IGNORE INTO departments (name, code, is_active) VALUES (%s, %s, %s)', (name, code, True))
print(f'Inserted {len(depts)} departments')

# Seed working schedule (use integer weekday keys 0=Monday..6=Sunday to match WorkingSchedule model)
weekly = {
    '0': {'start': '09:00', 'end': '17:00'},
    '1': {'start': '09:00', 'end': '17:00'},
    '2': {'start': '09:00', 'end': '17:00'},
    '3': {'start': '09:00', 'end': '17:00'},
    '4': {'start': '09:00', 'end': '17:00'},
    '5': None,
    '6': None,
}
c.execute('INSERT IGNORE INTO working_schedules (name, timezone, weekly_schedule, is_default, is_active) VALUES (%s, %s, %s, %s, %s)', ('Standard Business Hours', 'UTC', json.dumps(weekly), True, True))
print('Inserted working schedule')

conn.commit()
conn.close()
print('\nSetup complete!')