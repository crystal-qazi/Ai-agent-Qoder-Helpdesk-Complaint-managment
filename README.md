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

## Production initialization

Set production credentials and a strong `SECRET_KEY` in the production service environment. Then run migrations explicitly:

```bat
set FLASK_ENV=production
set FLASK_APP=app:create_app
flask db upgrade
```

Start the production server:

```bat
set FLASK_ENV=production
python serve.py
```

Production startup rejects a weak/missing secret, root database credentials, missing database password, or an unexpected database name. Set `SESSION_COOKIE_SECURE=True` when serving over HTTPS.

## Schema and seed policy

- Alembic/Flask-Migrate is the only source of truth for table structure.
- Use `flask db upgrade` to create/update tables in either database.
- Do not use legacy `seed_data.py` or `seed_mysql.py`; they contain old hard-coded schema definitions.
- Do not use `db.create_all()` as a replacement for migrations.
- Never run destructive development reset scripts against production.
- Back up production before every migration.

## Admin password

```bat
python reset_admin_password.py
```

The script loads `.env` and uses the database selected by `FLASK_ENV`. Keep `FLASK_ENV=development` for the development admin account. Only set it to production when intentionally resetting the production admin account.
