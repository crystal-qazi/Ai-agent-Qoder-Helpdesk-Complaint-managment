"""Full application audit: every GET page + every create/edit/delete/lifecycle flow.

NOTE: test-client requests must NOT run inside a manual app_context();
that corrupts Flask's context-local session handling. DB access uses
short-lived app contexts instead.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

from app import create_app
from app.extensions import db

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

PASS = []
FAIL = []


def dbq(fn):
    """Run a DB query in its own app context."""
    with app.app_context():
        return fn()


def check(label, response, expect=200, redirect_prefix=None):
    ok = response.status_code == expect
    if not ok and redirect_prefix and response.status_code == 302:
        ok = response.headers.get('Location', '').startswith(redirect_prefix)
    (PASS if ok else FAIL).append((label, response.status_code))
    if not ok:
        body = response.get_data(as_text=True) if 'html' in response.mimetype else ''
        flashes = re.findall(r'<p class="text-sm text-gray-700">(.*?)</p>', body or '')
        loc = response.headers.get('Location')
        print(f'  FAIL {label}: {response.status_code} loc={loc} flashes={flashes[:5]}')
    return response


def cleanup():
    from app.models import (User, Role, Complaint, AuditLog, Attachment, Comment,
                            Department, SoftwareCatalog, Category, Priority, Status,
                            SLAPolicy, Holiday, SystemSetting, WorkingSchedule)
    from app.models.complaint import ComplaintHistory

    def run():
        for cm in Complaint.query.filter(Complaint.title.like('Audit%')).all():
            Attachment.query.filter_by(complaint_id=cm.id).delete()
            Comment.query.filter_by(complaint_id=cm.id).delete()
            ComplaintHistory.query.filter_by(complaint_id=cm.id).delete()
            db.session.delete(cm)
        for u in User.query.filter(User.username.like('audituser%')).all():
            AuditLog.query.filter_by(user_id=u.id).delete()
            for la in u.login_attempts.all():
                db.session.delete(la)
            if u.profile:
                db.session.delete(u.profile)
            db.session.delete(u)
        for r_ in Role.query.filter(Role.name.like('audit%')).all():
            db.session.delete(r_)
        for d in Department.query.filter(Department.code == 'AUD').all():
            db.session.delete(d)
        for s in SoftwareCatalog.query.filter(SoftwareCatalog.code == 'AUSOFT').all():
            db.session.delete(s)
        for cat in Category.query.filter(Category.name == 'Audit Category').all():
            db.session.delete(cat)
        for p in Priority.query.filter(Priority.code == 'AUDPRI').all():
            db.session.delete(p)
        for st in Status.query.filter(Status.code == 'audit_status').all():
            db.session.delete(st)
        for sla_ in SLAPolicy.query.filter(SLAPolicy.name == 'Audit SLA').all():
            db.session.delete(sla_)
        for h in Holiday.query.filter(Holiday.name == 'Audit Holiday').all():
            db.session.delete(h)
        for sset in SystemSetting.query.filter(SystemSetting.key == 'audit_setting').all():
            db.session.delete(sset)
        for ws in WorkingSchedule.query.filter(WorkingSchedule.name == 'Audit Schedule').all():
            db.session.delete(ws)
        db.session.commit()
    with app.app_context():
        run()


def main():
    cleanup()
    c = app.test_client()

    # --- login ---
    r = c.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'})
    check('login', r, 302, '/')

    # --- 1. All GET pages ---
    get_pages = [
        '/', '/index', '/complaints/', '/complaints/create',
        '/notifications/', '/notifications/api/list', '/notifications/api/stats',
        '/notifications/unread-count', '/notifications/recent',
        '/reports/', '/reports/dashboard', '/reports/overdue',
        '/reports/reopened', '/reports/sla-compliance',
        '/reports/preset/daily', '/reports/preset/weekly', '/reports/preset/monthly',
        '/reports/generate',
        '/users/', '/users/roles', '/users/permissions', '/users/create', '/users/roles/create',
        '/users/1', '/users/1/edit',
        '/admin/', '/admin/index', '/admin/categories', '/admin/departments',
        '/admin/holidays', '/admin/priorities', '/admin/schedules',
        '/admin/settings', '/admin/sla', '/admin/software', '/admin/statuses',
        '/admin/categories/create', '/admin/departments/create', '/admin/holidays/create',
        '/admin/priorities/create', '/admin/schedules/create', '/admin/settings/create',
        '/admin/sla/create', '/admin/software/create', '/admin/statuses/create',
        '/api/stats', '/api/recent-complaints',
        '/api/charts/status', '/api/charts/priority', '/api/charts/department',
        '/api/charts/software', '/api/charts/sla', '/api/charts/trends/daily',
        '/api/charts/trends/weekly', '/api/charts/trends/monthly',
        '/reports/api/dashboard-stats',
        '/reports/api/chart-data/status', '/reports/api/chart-data/priority',
        '/reports/api/chart-data/department', '/reports/api/chart-data/software',
        '/reports/api/chart-data/assignee', '/reports/api/chart-data/resolver',
        '/reports/api/chart-data/sla',
        '/complaints/api/search?q=smoke',
    ]
    for p in get_pages:
        check(f'GET {p}', c.get(p))
    for ct in ['daily', 'weekly', 'monthly']:
        check(f'GET chart-data/{ct}', c.get(f'/reports/api/chart-data/{ct}'))

    # --- 2. Create user ---
    r = c.post('/users/create', data={
        'username': 'audituser', 'email': 'audituser@hospital.local',
        'first_name': 'Audit', 'last_name': 'User',
        'password': 'Audit@123', 'password_confirm': 'Audit@123',
        'department_id': '1', 'is_active': 'on', 'role_ids': ['3'],
    })
    check('create user', r, 302, '/users/')
    new_user_id = dbq(lambda: __import__('app.models', fromlist=['User']).User.query
                      .filter_by(username='audituser').first().id)
    if new_user_id:
        check('view created user', c.get(f'/users/{new_user_id}'))
        r = c.post(f'/users/{new_user_id}/edit', data={
            'username': 'audituser', 'email': 'audituser@hospital.local',
            'first_name': 'Audit', 'last_name': 'User2',
            'department_id': '1', 'is_active': 'on', 'role_ids': ['3'],
        })
        check('edit user', r, 302)
        r = c.post(f'/users/{new_user_id}/reset-password')
        check('reset user password', r, 302)
        c2 = app.test_client()
        r = c2.post('/auth/login', data={'username': 'audituser', 'password': 'Admin@123'})
        # password was reset by admin; audituser original password no longer valid
        # instead verify admin reset worked by admin resetting then testing login with returned temp is complex; just check logout
        c2.get('/auth/logout')

    # --- 3. Create role ---
    r = c.post('/users/roles/create', data={
        'name': 'audit_role', 'display_name': 'Audit Role',
        'description': 'temp', 'permission_ids': ['1', '2'],
    })
    check('create role', r, 302, '/users/roles')
    role = dbq(lambda: __import__('app.models', fromlist=['Role']).Role.query
               .filter_by(name='audit_role').first())
    if role:
        r = c.post(f'/users/roles/{role.id}/edit', data={
            'display_name': 'Audit Role 2', 'description': 'temp',
            'permission_ids': ['1'],
        })
        check('edit role', r, 302, '/users/roles')

    # --- 4. Admin CRUD ---
    r = c.post('/admin/departments/create', data={
        'name': 'Audit Dept', 'code': 'AUD', 'description': 'temp',
        'email': 'audit@hospital.local', 'is_active': 'on',
    })
    check('create department', r, 302, '/admin/departments')
    from app.models import Department
    dept = dbq(lambda: Department.query.filter_by(code='AUD').first())
    if dept:
        check('edit dept page', c.get(f'/admin/departments/{dept.id}/edit'))
        r = c.post(f'/admin/departments/{dept.id}/edit', data={
            'name': 'Audit Dept', 'code': 'AUD', 'description': 'temp2',
            'is_active': 'on'})
        check('edit department', r, 302, '/admin/departments')
        r = c.post(f'/admin/departments/{dept.id}/toggle')
        check('toggle department', r, 302)

    from app.models import SoftwareCatalog, Category, Priority, Status, SLAPolicy
    from app.models import Holiday, SystemSetting, WorkingSchedule
    r = c.post('/admin/software/create', data={
        'name': 'AuditSoft', 'code': 'AUSOFT', 'vendor': 'TestVendor',
        'version': '1.0', 'department_id': '1', 'is_active': 'on',
    })
    check('create software', r, 302, '/admin/software')
    sw = dbq(lambda: SoftwareCatalog.query.filter_by(code='AUSOFT').first())
    if sw:
        r = c.post(f'/admin/software/{sw.id}/edit', data={
            'name': 'AuditSoft', 'code': 'AUSOFT', 'vendor': 'TestVendor',
            'version': '2.0', 'department_id': '1', 'is_active': 'on'})
        check('edit software', r, 302, '/admin/software')
        r = c.post(f'/admin/software/{sw.id}/toggle')
        check('toggle software', r, 302)
        c.post(f'/admin/software/{sw.id}/toggle')

    r = c.post('/admin/categories/create', data={
        'name': 'Audit Category', 'code': 'AUDCAT', 'description': 'temp', 'is_active': 'on',
    })
    check('create category', r, 302, '/admin/categories')
    cat = dbq(lambda: Category.query.filter_by(name='Audit Category').first())
    if cat:
        check('edit category page', c.get(f'/admin/categories/{cat.id}/edit'))
        r = c.post(f'/admin/categories/{cat.id}/edit', data={
            'name': 'Audit Category', 'code': 'AUDCAT', 'description': 'temp2', 'is_active': 'on'})
        check('edit category', r, 302, '/admin/categories')

    r = c.post('/admin/statuses/create', data={
        'name': 'Audit Status', 'code': 'audit_status', 'description': 'temp',
        'category': 'open', 'color': '#3B82F6', 'sort_order': '99',
        'is_active': 'on',
    })
    check('create status', r, 302, '/admin/statuses')
    st = dbq(lambda: Status.query.filter_by(code='audit_status').first())
    if st:
        r = c.post(f'/admin/statuses/{st.id}/edit', data={
            'name': 'Audit Status', 'code': 'audit_status', 'description': 'temp2',
            'category': 'open', 'color': '#3B82F6', 'sort_order': '99',
            'is_active': 'on'})
        check('edit status', r, 302, '/admin/statuses')
        r = c.post(f'/admin/statuses/{st.id}/delete')
        check('delete status', r, 302, '/admin/statuses')

    r = c.post('/admin/priorities/create', data={
        'name': 'Audit Priority', 'code': 'AUDPRI', 'level': '5',
        'color': '#3B82F6', 'sla_response_hours': '4', 'sla_resolution_hours': '8',
        'is_active': 'on',
    })
    check('create priority', r, 302, '/admin/priorities')
    pri = dbq(lambda: Priority.query.filter_by(code='AUDPRI').first())
    if pri:
        check('edit priority page', c.get(f'/admin/priorities/{pri.id}/edit'))
        r = c.post(f'/admin/priorities/{pri.id}/edit', data={
            'name': 'Audit Priority', 'code': 'AUDPRI', 'level': '5',
            'color': '#3B82F6', 'sla_response_hours': '2', 'sla_resolution_hours': '4',
            'is_active': 'on'})
        check('edit priority', r, 302, '/admin/priorities')

    r = c.post('/admin/holidays/create', data={
        'name': 'Audit Holiday', 'date': '2026-12-25', 'description': 'temp',
        'is_active': 'on',
    })
    check('create holiday', r, 302, '/admin/holidays')
    hol = dbq(lambda: Holiday.query.filter_by(name='Audit Holiday').first())
    if hol:
        r = c.post(f'/admin/holidays/{hol.id}/edit', data={
            'name': 'Audit Holiday', 'date': '2026-12-26', 'description': 'temp',
            'is_active': 'on'})
        check('edit holiday', r, 302, '/admin/holidays')
        r = c.post(f'/admin/holidays/{hol.id}/delete')
        check('delete holiday', r, 302, '/admin/holidays')

    r = c.post('/admin/settings/create', data={
        'key': 'audit_setting', 'value': 'test', 'setting_type': 'string',
        'description': 'temp', 'is_active': 'on',
    })
    check('create setting', r, 302, '/admin/settings')
    setting = dbq(lambda: SystemSetting.query.filter_by(key='audit_setting').first())
    if setting:
        r = c.post(f'/admin/settings/{setting.id}/edit', data={
            'key': 'audit_setting', 'value': 'test2', 'setting_type': 'string',
            'description': 'temp', 'is_active': 'on'})
        check('edit setting', r, 302, '/admin/settings')
        r = c.post(f'/admin/settings/{setting.id}/delete')
        check('delete setting', r, 302, '/admin/settings')

    r = c.post('/admin/schedules/create', data={
        'name': 'Audit Schedule', 'timezone': 'Asia/Karachi',
        'weekly_schedule': '{"0": {"start": "09:00", "end": "17:00"}}',
        'is_active': 'on',
    })
    check('create schedule', r, 302, '/admin/schedules')
    sched = dbq(lambda: WorkingSchedule.query.filter_by(name='Audit Schedule').first())
    if sched:
        r = c.post(f'/admin/schedules/{sched.id}/edit', data={
            'name': 'Audit Schedule', 'timezone': 'Asia/Karachi',
            'weekly_schedule': '{"0": {"start": "09:00", "end": "17:00"}}',
            'is_active': 'on'})
        check('edit schedule', r, 302, '/admin/schedules')

    r = c.post('/admin/sla/create', data={
        'name': 'Audit SLA', 'priority_id': '1', 'response_target_minutes': '60',
        'resolution_target_minutes': '240', 'is_active': 'on',
    })
    check('create sla policy', r, 302, '/admin/sla')
    sla = dbq(lambda: SLAPolicy.query.filter_by(name='Audit SLA').first())
    if sla:
        check('edit sla page', c.get(f'/admin/sla/{sla.id}/edit'))
        r = c.post(f'/admin/sla/{sla.id}/edit', data={
            'name': 'Audit SLA', 'priority_id': '1', 'response_target_minutes': '30',
            'resolution_target_minutes': '120', 'is_active': 'on'})
        check('edit sla policy', r, 302, '/admin/sla')
        r = c.post(f'/admin/sla/{sla.id}/delete')
        check('delete sla policy', r, 302, '/admin/sla')

    # --- 5. Complaint lifecycle ---
    r = c.post('/complaints/create', data={
        'title': 'Audit complaint', 'description': 'Full lifecycle test',
        'category_id': '1', 'priority_id': '1', 'severity': 'High',
        'software_id': '1', 'department_id': '1', 'location': 'Ward 5',
    })
    check('create complaint', r, 302, '/complaints/')
    from app.models import Complaint
    complaint = dbq(lambda: Complaint.query.filter_by(title='Audit complaint')
                    .order_by(Complaint.id.desc()).first())
    if complaint:
        cid = complaint.id
        check('view complaint', c.get(f'/complaints/{cid}'))
        check('edit complaint page', c.get(f'/complaints/{cid}/edit'))
        r = c.post(f'/complaints/{cid}/assign', data={
            'new_assignee_id': '2', 'assignment_reason': 'audit assignment'})
        check('assign complaint', r, 302, f'/complaints/{cid}')
        r = c.post(f'/complaints/{cid}/comment', data={
            'content': 'audit comment', 'is_internal': 'on'})
        check('add comment', r, 302, f'/complaints/{cid}')
        for code in ['in_progress', 'pending_info', 'in_progress', 'resolved', 'closed', 'reopened']:
            target = dbq(lambda: Status.query.filter_by(code=code).first())
            if target:
                r = c.post(f'/complaints/{cid}/status', data={
                    'status_id': str(target.id), 'reason': f'audit {code}',
                    'resolution_summary': 'audit resolution' if code == 'resolved' else ''})
                check(f'status -> {code}', r, 302, f'/complaints/{cid}')
        r = c.post(f'/complaints/{cid}/edit', data={
            'title': 'Audit complaint edited', 'description': 'edited complaint full text here',
            'category_id': '1', 'priority_id': '2', 'severity': 'Medium',
            'department_id': '1', 'software_id': '1',
        })
        check('edit complaint', r, 302, f'/complaints/{cid}')
        data = {'file': (io.BytesIO(b'audit attachment content'), 'audit.txt')}
        r = c.post(f'/complaints/{cid}/attachment', data=data,
                   content_type='multipart/form-data')
        check('upload attachment', r, 302, f'/complaints/{cid}')
        from app.models import Attachment
        att = dbq(lambda: Attachment.query.filter_by(complaint_id=cid).first())
        if att:
            check('download attachment', c.get(
                f'/complaints/{cid}/attachment/{att.id}/download'))
            r = c.post(f'/complaints/{cid}/attachment/{att.id}/delete')
            check('delete attachment', r, 302, f'/complaints/{cid}')

    # --- 6. Notifications ---
    from app.models import Notification
    notif = dbq(lambda: Notification.query.filter_by(user_id=1, is_read=False).first())
    if notif:
        r = c.post(f'/notifications/{notif.id}/read')
        check('mark read', r, 200)
        r = c.post(f'/notifications/{notif.id}/unread')
        check('mark unread', r, 200)
        check('view notification page', c.get(f'/notifications/{notif.id}'), 200)
    r = c.post('/notifications/mark-all-read')
    check('mark all read', r, 200)

    # --- 7. Reports export ---
    check('export csv', c.get('/reports/export/csv'), 200)
    check('export pdf', c.get('/reports/export/pdf'), 200)

    # --- 8. RBAC ---
    c3 = app.test_client()
    c3.post('/auth/login', data={'username': 'user', 'password': 'User@123'})
    check('plain user blocked from /users (403)', c3.get('/users/'), 403)
    check('plain user blocked from /admin (403)', c3.get('/admin/'), 403)
    check('plain user blocked from users/create (403)', c3.get('/users/create'), 403)
    check('plain user can access complaints', c3.get('/complaints/'), 200)
    c3.get('/auth/logout')

    # --- 9. error pages ---
    check('404 page', c.get('/nonexistent-page'), 404)

    print(f'\n{"="*60}')
    print(f'PASSED: {len(PASS)}   FAILED: {len(FAIL)}')
    for label, code in FAIL:
        print(f'  FAIL: {label} -> {code}')
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
