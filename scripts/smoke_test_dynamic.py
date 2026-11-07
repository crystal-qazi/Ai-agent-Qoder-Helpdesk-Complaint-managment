"""Smoke test for parameterized routes and core POST flows."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app import create_app
from app.extensions import db
from app.models import (
    Complaint, Category, Priority, Department, SoftwareCatalog, Status, User,
    Role, Notification, SLAPolicy, WorkingSchedule, Holiday, SystemSetting
)

app = create_app(os.environ.get('FLASK_ENV', 'development'))
app.config['WTF_CSRF_ENABLED'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True

failures = []

def check(label, response, expected=(200, 302)):
    ok = response.status_code in expected
    if not ok:
        failures.append((label, response.status_code))
    print(f"{response.status_code} {label}")

with app.app_context():
    cat = Category.query.filter_by(is_active=True).first()
    pri = Priority.query.filter_by(is_active=True).first()
    dept = Department.query.filter_by(is_active=True).first()
    sw = SoftwareCatalog.query.filter_by(is_active=True).first()
    status = Status.query.filter_by(is_active=True).first()
    user = User.query.filter_by(is_active=True).first()
    role = Role.query.first()
    sla = SLAPolicy.query.first()
    schedule = WorkingSchedule.query.first()
    holiday = Holiday.query.first()
    if holiday is None:
        from datetime import date, timedelta
        holiday = Holiday(name='Smoke Test Holiday', date=date.today() + timedelta(days=30), is_active=True)
        db.session.add(holiday)
        db.session.commit()
    setting = SystemSetting.query.first()
    ids = dict(cat=cat.id, pri=pri.id, dept=dept.id, sw=sw.id, status=status.id,
               user=user.id, role=role.id, sla=sla.id, schedule=schedule.id,
               holiday=holiday.id, setting=setting.id)

client = app.test_client()
login = client.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
print(f'LOGIN: {login.status_code}')

# --- Create complaint via POST ---
form = {
    'title': 'Smoke test complaint',
    'description': 'This complaint was created by the automated smoke test.',
    'category_id': str(ids['cat']),
    'priority_id': str(ids['pri']),
    'department_id': str(ids['dept']),
    'software_id': str(ids['sw']),
    'severity': 'Medium',
    'source_type': 'portal',
    'affected_users_count': '2',
}
r = client.post('/complaints/create', data=form)
print(f'CREATE COMPLAINT: {r.status_code} -> {r.headers.get("Location")}')

with app.app_context():
    complaint = Complaint.query.order_by(Complaint.id.desc()).first()
    cid = complaint.id
    print(f'  complaint={complaint.complaint_number} sla_response={complaint.sla_response_deadline} sla_resolution={complaint.sla_resolution_deadline}')
    if not complaint.sla_resolution_deadline:
        failures.append(('sla_deadlines_missing', 0))
    # notification for detail-page test
    if Notification.query.count() == 0:
        n = Notification.create_notification(
            user_id=complaint.reported_by_user_id,
            title='Test notification',
            message='Created by smoke test',
            notification_type='assignment',
            complaint_id=cid,
        )
        db.session.commit()
        nid = n.id
    else:
        nid = Notification.query.first().id

# --- Parameterized GET routes ---
check(f'/complaints/{cid}', client.get(f'/complaints/{cid}'))
check(f'/complaints/{cid}/edit', client.get(f'/complaints/{cid}/edit'))
check(f'/notifications/{nid}', client.get(f'/notifications/{nid}'))
check(f"/admin/categories/{ids['cat']}/edit", client.get(f"/admin/categories/{ids['cat']}/edit"))
check(f"/admin/departments/{ids['dept']}/edit", client.get(f"/admin/departments/{ids['dept']}/edit"))
check(f"/admin/holidays/{ids['holiday']}/edit", client.get(f"/admin/holidays/{ids['holiday']}/edit"))
check(f"/admin/priorities/{ids['pri']}/edit", client.get(f"/admin/priorities/{ids['pri']}/edit"))
check(f"/admin/schedules/{ids['schedule']}/edit", client.get(f"/admin/schedules/{ids['schedule']}/edit"))
check(f"/admin/settings/{ids['setting']}/edit", client.get(f"/admin/settings/{ids['setting']}/edit"))
check(f"/admin/sla/{ids['sla']}/edit", client.get(f"/admin/sla/{ids['sla']}/edit"))
check(f"/admin/software/{ids['sw']}/edit", client.get(f"/admin/software/{ids['sw']}/edit"))
check(f"/admin/statuses/{ids['status']}/edit", client.get(f"/admin/statuses/{ids['status']}/edit"))
check(f"/users/{ids['user']}", client.get(f"/users/{ids['user']}"))
check(f"/users/{ids['user']}/edit", client.get(f"/users/{ids['user']}/edit"))
check(f"/users/roles/{ids['role']}/edit", client.get(f"/users/roles/{ids['role']}/edit"))
for rt in ['daily', 'weekly', 'monthly', 'overdue', 'sla_compliance', 'reopened']:
    check(f'/reports/preset/{rt}', client.get(f'/reports/preset/{rt}'))
for ct in ['status', 'priority', 'department', 'software', 'assignee', 'resolver', 'daily', 'weekly', 'monthly', 'sla']:
    check(f'/reports/api/chart-data/{ct}', client.get(f'/reports/api/chart-data/{ct}'))

# --- POST flows ---
check(f'assign complaint {cid}', client.post(f'/complaints/{cid}/assign', data={
    'new_assignee_id': str(ids['user']), 'assignment_reason': 'smoke test'}))
check(f'comment on {cid}', client.post(f'/complaints/{cid}/comment', data={
    'content': 'Internal smoke test comment', 'visibility': 'internal'}))
check(f'status change on {cid}', client.post(f'/complaints/{cid}/status', data={
    'status_id': str(ids['status']), 'reason': 'smoke test', 'notes': ''}))
check('mark notification read', client.post(f'/notifications/{nid}/read'))
check('csv export', client.get('/reports/export/csv'), expected=(200, 302))
check('pdf export', client.get('/reports/export/pdf'), expected=(200, 302))

print(f'\n{len(failures)} failures')
for label, status in failures:
    print(f'  FAIL {status} {label}')
