"""Remove stale complaint permissions from the database.

Run once after switching to the new 10-permission complaint model.
Handles both SQLite and MySQL via DATABASE_URL.
"""
import re
import os
from dotenv import load_dotenv
load_dotenv()

db_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/helpdesk.db')


def get_connection():
    if db_url.startswith('mysql'):
        match = re.match(r'mysql\+pymysql://([^:]+):([^@]*)@([^:/]+)(?::(\d+))?/(\w+)', db_url)
        user, password, host, port, dbname = match.groups()
        import pymysql
        conn = pymysql.connect(host=host, port=int(port or 3306), user=user, password=password, database=dbname)
        return conn, 'mysql'
    else:
        import sqlite3
        path = db_url.replace('sqlite:///', '')
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        conn = sqlite3.connect(path)
        return conn, 'sqlite'


def upsert_ignore(cursor, dialect, table, columns, values):
    """Insert ignoring duplicates; works on both MySQL and SQLite."""
    if dialect == 'mysql':
        ph = ', '.join(['%s'] * len(values))
        cols = ', '.join(columns)
        cursor.execute(f'INSERT IGNORE INTO {table} ({cols}) VALUES ({ph})', values)
    else:
        ph = ', '.join(['?'] * len(values))
        cols = ', '.join(columns)
        cursor.execute(f'INSERT OR IGNORE INTO {table} ({cols}) VALUES ({ph})', values)


STALE_PERMISSION_NAMES = {
    'complaints.view',
    'complaints.edit_own',
    'complaints.update',
    'complaints.reassign',
    'complaints.reassign_own',
    'complaints.change_status',
    'complaints.resolve',
    'complaints.close',
    'complaints.reopen',
    'complaints.reopen_own',
    'complaints.reject',
}


def main():
    conn, dialect = get_connection()
    c = conn.cursor()
    print(f'Database: {dialect}')

    # Look up IDs of stale permissions
    param_style = '%s' if dialect == 'mysql' else '?'
    placeholders = ','.join([param_style] * len(STALE_PERMISSION_NAMES))
    c.execute(f'SELECT id, name FROM permissions WHERE name IN ({placeholders})', sorted(STALE_PERMISSION_NAMES))
    stale_rows = c.fetchall()
    stale_ids = [r[0] for r in stale_rows]
    print(f'Stale permissions found: {[r[1] for r in stale_rows]}')

    if stale_ids:
        ids_ph = ','.join([param_style] * len(stale_ids))
        # Delete junction rows first (FK safety)
        c.execute(f'DELETE FROM role_permissions WHERE permission_id IN ({ids_ph})', stale_ids)
        print(f'Removed {c.rowcount} role_permission rows')
        c.execute(f'DELETE FROM permissions WHERE id IN ({ids_ph})', stale_ids)
        print(f'Removed {c.rowcount} stale permissions')

    # Re-sync admin role to current permissions only
    c.execute("SELECT id FROM roles WHERE name='admin'")
    admin_row = c.fetchone()
    if admin_row:
        admin_id = admin_row[0]
        c.execute(f'DELETE FROM role_permissions WHERE role_id={admin_id}')
        c.execute('SELECT id FROM permissions')
        all_ids = [r[0] for r in c.fetchall()]
        for pid in all_ids:
            upsert_ignore(c, dialect, 'role_permissions', ('role_id', 'permission_id'), (admin_id, pid))
        print(f'Re-synced admin role: {len(all_ids)} permissions')

    # Remove stale roles that have no matching name in the new schema
    STALE_ROLE_NAMES = {'agent', 'support', 'engineer', 'audit_role'}
    placeholders = ','.join([param_style] * len(STALE_ROLE_NAMES))
    c.execute(f'SELECT id, name FROM roles WHERE name IN ({placeholders})', sorted(STALE_ROLE_NAMES))
    stale_roles = c.fetchall()
    if stale_roles:
        # Warn before removing roles that may still have active user assignments
        print(f'WARNING: Removing stale roles: {[r[1] for r in stale_roles]}')
        role_ids = [r[0] for r in stale_roles]
        ids_ph = ','.join([param_style] * len(role_ids))
        c.execute(f'DELETE FROM user_roles WHERE role_id IN ({ids_ph})', role_ids)
        print(f'Removed {c.rowcount} user_role rows')
        c.execute(f'DELETE FROM role_permissions WHERE role_id IN ({ids_ph})', role_ids)
        print(f'Removed {c.rowcount} role_permission rows')
        c.execute(f'DELETE FROM roles WHERE id IN ({ids_ph})', role_ids)
        print(f'Removed {c.rowcount} stale roles')

    c.execute('SELECT COUNT(*) FROM permissions')
    print(f'Permissions remaining: {c.fetchone()[0]}')
    c.execute('SELECT COUNT(*) FROM roles')
    print(f'Roles remaining: {c.fetchone()[0]}')

    conn.commit()
    conn.close()
    print('\nCleanup complete.')


if __name__ == '__main__':
    main()
