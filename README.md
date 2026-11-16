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
