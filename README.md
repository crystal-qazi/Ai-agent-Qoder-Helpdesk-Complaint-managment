# IT Software Complain System

A comprehensive Flask-based complaint tracking system for hospital IT support, featuring SLA management, role-based access control, reporting, and notification systems.

## Features

- **Complaint Management**: Full CRUD with assignment, status workflow, comments, and attachments
- **Role-Based Access Control**: Configurable roles and permissions
- **SLA Tracking**: Business-hours-based SLA calculations with escalation
- **Dashboard**: Real-time statistics and charts
- **Reporting**: CSV/PDF export with multiple report types
- **Notifications**: In-app notification center
- **Audit Logging**: Complete audit trail for all actions
- **Offline-Ready**: Works on hospital intranet without internet

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Migrate
- **Frontend**: Tailwind CSS, Alpine.js, Chart.js
- **Database**: MySQL 8+ (InnoDB)
- **Testing**: pytest, Playwright
- **Security**: Bandit, pip-audit, Semgrep

## Setup

### 1. Create Database

```sql
CREATE DATABASE helpdesk_qoder CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Install Dependencies

```bash
cd hospital_complaint_system
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Initialize Database

```bash
flask db upgrade
python scripts/seed_data.py
```

### 5. Run Application

```bash
python run.py
```

Visit http://localhost:5000

**Default admin login**: `admin` / `Admin@123`

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | mysql://root:root@localhost/helpdesk_qoder |
| `SECRET_KEY` | Flask secret key | (required) |
| `SESSION_COOKIE_SECURE` | Secure cookies | false (intranet) |
| `MAX_CONTENT_LENGTH` | Max upload size | 16777216 (16MB) |

## Project Structure

```
hospital_complaint_system/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration classes
│   ├── extensions.py        # Flask extensions
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # Flask blueprints
│   ├── services/            # Business logic services
│   ├── permissions/         # RBAC decorators & policies
│   ├── validators/          # Form validation
│   └── templates/           # Jinja2 templates
├── static/                  # CSS, JS, images
├── migrations/              # Alembic migrations
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
├── uploads/                 # Attachment storage
├── requirements.txt
└── run.py
```

## Security Notes

- Passwords are hashed with Werkzeug's check_password_hash
- CSRF protection enabled via Flask-WTF
- SQL injection protection via SQLAlchemy ORM
- File uploads validated by extension and type
- All admin routes require authentication and permissions

## License

Internal hospital use.