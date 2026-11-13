"""Safe one-time data-repair: reactivate the original seeded roles.

Background
----------
The seed scripts historically inserted roles without specifying
``is_active``. Because MySQL's ``roles.is_active`` column had no
``DEFAULT 1`` constraint, seeded rows ended up with ``is_active = 0``,
which silently removed 3 of the 5 default roles from the user
creation / edit forms.

What this script does
--------------------
1. Re-enables ``is_active = 1`` ONLY for the five original seed roles
   (``admin``, ``helpdesk_agent``, ``support_agent``, ``user``,
   ``employee``) that are currently deactivated.
2. Leaves any other (custom) roles untouched — an administrator who
   intentionally deactivated a custom role keeps that state.
3. Does not modify user_role or role_permission rows.
4. Is fully idempotent: re-running it when the roles are already
   active is a no-op.

The script does NOT drop, reset, or recreate any table.
"""
import os
import sys
import pymysql

# Names of the original seeded roles (from seed_mysql.py / seed_data.py).
ORIGINAL_SEEDED_ROLES = (
    'admin',
    'helpdesk_agent',
    'support_agent',
    'user',
    'employee',
)


def load_db_config() -> dict:
    """Read MySQL config from environment or .env file."""
    if 'DATABASE_URL' in os.environ:
        # mysql+pymysql://user:pass@host:port/db
        url = os.environ['DATABASE_URL']
        rest = url.split('://', 1)[1] if '://' in url else url
        # rest = user:pass@host:port/db[/query]
        cred, _, hostportdb = rest.partition('@')
        user, _, pwd = cred.partition(':')
        hostport, _, dbname = hostportdb.partition('/')
        host, _, port = hostport.partition(':')
        return {
            'host': host or 'localhost',
            'port': int(port) if port else 3306,
            'user': user,
            'password': pwd,
            'database': dbname,
        }

    # Fall back to .env values
    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', '3306')),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'database': os.environ.get('DB_NAME', 'helpdesk_qoder'),
    }


def main() -> int:
    # Load .env if present (very small parser, no dep on python-dotenv).
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, _, v = line.partition('=')
                os.environ.setdefault(k.strip(), v.strip())

    cfg = load_db_config()
    print(f"Connecting to MySQL at {cfg['host']}:{cfg['port']}/{cfg['database']} as {cfg['user']}")
    conn = pymysql.connect(**cfg)

    try:
        cur = conn.cursor()

        # List the original roles and their current state
        cur.execute(
            "SELECT id, name, is_active, is_system FROM roles WHERE name IN %s ORDER BY name",
            (ORIGINAL_SEEDED_ROLES,),
        )
        rows = cur.fetchall()
        if not rows:
            print("No original seed roles found. Nothing to do.")
            return 0

        deactivated = [(rid, name) for rid, name, active, _ in rows if not active]
        print(f"Original seed roles present: {len(rows)}")
        for rid, name, active, sys_flag in rows:
            state = "active" if active else "INACTIVE"
            tag = " [system]" if sys_flag else ""
            print(f"  role id={rid} name={name!r:20s} {state}{tag}")

        if not deactivated:
            print("All original seed roles are already active. No changes.")
            return 0

        placeholders = ','.join(['%s'] * len(deactivated))
        ids = [rid for rid, _ in deactivated]
        cur.execute(
            f"UPDATE roles SET is_active=1 WHERE id IN ({placeholders}) AND is_active=0",
            ids,
        )
        affected = cur.rowcount
        conn.commit()
        print(f"Reactivated {affected} role(s): {', '.join(n for _, n in deactivated)}")
        print("Custom roles (if any) were left untouched.")
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
