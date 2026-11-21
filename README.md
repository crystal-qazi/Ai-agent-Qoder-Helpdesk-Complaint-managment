# Helpdesk Complaint Management System

Flask + MySQL complaint management application.

## Databases

The app selects one fixed MySQL database from `FLASK_ENV`:

| Mode | Database |
|---|---|
| `development` (default) | `helpdesk_qoder_dev` |
| `production` | `Helpdesk_qoder_prod` |
| `testing` | in-memory SQLite |

The connection URL is built safely from `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD`. Do not configure a generic `DATABASE_URL`; the app enforces the environment-specific target.

## Initial setup (Windows)

1. Create both databases:

```sql
CREATE DATABASE helpdesk_qoder_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE Helpdesk_qoder_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Install and configure:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your MySQL credentials. For local development the account needs access to the development database. Production should use a dedicated least-privilege account configured in the production service environment.

3. Create/update the development schema:

```bat
set FLASK_ENV=development
set FLASK_APP=app:create_app
flask db upgrade
```

4. Run the development server:

```bat
set FLASK_ENV=development
python run.py
```

Open http://localhost:5000.

5. Seed development reference and dummy data:

```bat
python scripts/seed_dev_mysql.py
```

The seeder checks that it is connected to `helpdesk_qoder_dev`. It creates roles, permissions, departments, categories, priorities, statuses, software, SLA defaults, an admin account, three demo accounts, and three sample complaints. It never drops tables or creates schema. It asks you to set the admin password.

Demo accounts (development only):
- `demo_helpdesk` / `DemoHelpdesk@123`
- `demo_support` / `DemoSupport@123`
- `demo_user` / `DemoUser@123`

## Production initialization

Set production credentials and a strong `SECRET_KEY` in the production service environment. Then run migrations explicitly:

```bat
set FLASK_ENV=production
set FLASK_APP=app:create_app
flask db upgrade
```

After the production migration, seed only the real reference data and create the production admin account:

```bat
python scripts/seed_dev_mysql.py --production
```

This mode checks that the target is exactly `Helpdesk_qoder_prod`. It does not create demo users or sample complaints. Set a strong production `SECRET_KEY` and use a non-root MySQL account before running it.

Start the production server:

```bat
set FLASK_ENV=production
python serve.py
```

Production startup rejects a weak/missing secret, root database credentials, missing database password, or an unexpected database name. Set `SESSION_COOKIE_SECURE=True` when serving over HTTPS.

## Schema and seed policy

- Alembic/Flask-Migrate is the only source of truth for table structure.
- Use `flask db upgrade` to create/update tables in either database.
- Run `python scripts/seed_dev_mysql.py` only for development demo data.
- Run `python scripts/seed_dev_mysql.py --production` for production reference data and its admin account only.
- Do not use legacy `seed_data.py` or `seed_mysql.py`; they contain old hard-coded schema definitions.
- Do not use `db.create_all()` as a replacement for migrations.
- Never run destructive development reset scripts against production.
- Back up production before every migration.

## Admin password

```bat
python reset_admin_password.py
```

The script loads `.env` and uses the database selected by `FLASK_ENV`. Keep `FLASK_ENV=development` for the development admin account. Only set it to production when intentionally resetting the production admin account.


## Security hardening (November 2026)

The `security-hardening` branch includes the following focused protections:

- Persistent credential/session versions. Password changes invalidate old browser sessions and remember-me cookies. Existing sessions created before this migration must sign in again.
- Server-side enforcement of `must_change_password`; authenticated users are restricted to the password-change page and logout until the password is changed.
- Password reset remains deferred. The legacy reset routes and token implementation are retained unchanged, but are disabled in production (404) until the redesigned recovery workflow is ready.
- Attachment downloads and deletions validate the resolved storage path against the configured upload root. Attachment rows are removed from the database before the physical file is unlinked.
- Complaint numbers use a transactional per-year sequence. Existing complaint numbers are used to initialize the counter, so records are not renumbered.
- Malformed numeric values in complaint create/edit, assignment, and status requests are rejected rather than raising conversion exceptions.
- SLA breach checks are available as a CLI task instead of depending only on dashboard visits.

### Apply the security migrations

After pulling/merging the security-hardening changes, back up the target database, then run:

```bat
set FLASK_ENV=development
set FLASK_APP=app:create_app
flask db upgrade
```

The new migrations add `users.session_version` and `complaint_number_sequences`. They do not drop or reseed existing data. All existing users will need to sign in again after the session-version migration.

Do not point the development command at production. For a planned production rollout, take a verified backup, set `FLASK_ENV=production`, and run `flask db upgrade` during the deployment window.

### Run SLA checks on a schedule

Run the following command from the project root:

```bat
set FLASK_ENV=production
set FLASK_APP=app:create_app
flask check-sla-breaches
```

On Windows, configure Task Scheduler to run this command at an appropriate interval (for example, every 5 minutes) using the project's virtual-environment Python/Flask executable and project directory. On Linux, schedule the equivalent command with cron or a service timer.

### Run the focused authentication regression tests

```bat
python -m unittest tests.unit.test_auth_session_hardening -v
```

The dedicated MySQL RBAC integration suite has its own test-database setup and must only be run after verifying its `TEST_DB_NAME` and connection settings. Never point integration tests at development or production databases.
