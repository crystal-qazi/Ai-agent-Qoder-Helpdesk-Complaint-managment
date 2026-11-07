"""Authenticated GET smoke test for all static routes."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))
app.config['WTF_CSRF_ENABLED'] = False
app.config['PROPAGATE_EXCEPTIONS'] = False

client = app.test_client()
login = client.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'})
print(f'LOGIN: {login.status_code} -> {login.headers.get("Location")}')

failures = []
checked = 0
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'GET' not in rule.methods or rule.endpoint == 'static':
        continue
    if rule.arguments:
        continue
    if rule.rule == '/auth/logout':
        continue
    response = client.get(rule.rule)
    checked += 1
    if response.status_code not in (200, 302):
        failures.append((rule.rule, response.status_code))
    print(f'{response.status_code} {rule.rule}')

print(f'\nChecked {checked} routes, {len(failures)} failures')
for rule, status in failures:
    print(f'  FAIL {status} {rule}')