"""Set allowed_transitions on all status records in both SQLite and MySQL."""
import json
import os
import sqlite3
import pymysql

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS_TRANSITIONS = {
    'new':        [2, 3, 4, 5, 6, 9],   # New → Assigned, In Progress, Pending Info, On Hold, Resolved, Rejected
    'assigned':   [3, 4, 5, 7],         # Assigned → In Progress, Pending Info, On Hold, Closed
    'in_progress':[4, 5, 6],            # In Progress → Pending Info, On Hold, Resolved
    'pending_info':[3, 5, 6],           # Pending Info → In Progress, On Hold, Resolved
    'on_hold':    [3, 4, 6],            # On Hold → In Progress, Pending Info, Resolved
    'resolved':   [8],                   # Resolved → Reopened
    'closed':     [],                    # Closed → terminal
    'reopened':   [3, 4, 5, 6],         # Reopened → In Progress, Pending Info, On Hold, Resolved
    'rejected':   [],                    # Rejected → terminal
}


def migrate_sqlite():
    db_path = os.path.join(BASE_DIR, 'instance', 'helpdesk.db')
    if not os.path.exists(db_path):
        print('SQLite DB not found at', db_path)
        return
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute('SELECT id, code FROM statuses ORDER BY display_order')
        rows = c.fetchall()
    except sqlite3.OperationalError:
        # Column doesn't exist yet — add it
        c.execute('ALTER TABLE statuses ADD COLUMN allowed_transitions TEXT DEFAULT NULL')
        print('Added allowed_transitions column to SQLite statuses table')
        conn.commit()
        c.execute('SELECT id, code FROM statuses ORDER BY display_order')
        rows = c.fetchall()

    updated = 0
    for sid, code in rows:
        targets = STATUS_TRANSITIONS.get(code, [])
        c.execute('UPDATE statuses SET allowed_transitions = ? WHERE id = ?',
                  (json.dumps(targets), sid))
        updated += 1
    conn.commit()
    conn.close()
    print(f'SQLite: Updated allowed_transitions for {updated} statuses')


def migrate_mysql():
    dotenv_path = os.path.join(BASE_DIR, '.env')
    host = 'localhost'
    user = 'root'
    password = 'root'
    database = 'helpdesk_qoder'
    if os.path.exists(dotenv_path):
        with open(dotenv_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('DB_HOST='): host = line.split('=', 1)[1]
                elif line.startswith('DB_USER='): user = line.split('=', 1)[1]
                elif line.startswith('DB_PASSWORD='): password = line.split('=', 1)[1]
                elif line.startswith('DB_NAME='): database = line.split('=', 1)[1]
    try:
        conn = pymysql.connect(host=host, user=user, password=password, database=database)
    except pymysql.err.OperationalError as e:
        print('MySQL connection failed:', e)
        return
    c = conn.cursor()
    try:
        c.execute('SELECT id, code FROM statuses ORDER BY sort_order')
        rows = c.fetchall()
    except pymysql.err.OperationalError:
        # Column may not exist; create it
        c.execute('ALTER TABLE statuses ADD COLUMN allowed_transitions JSON DEFAULT NULL')
        conn.commit()
        c.execute('SELECT id, code FROM statuses ORDER BY sort_order')
        rows = c.fetchall()

    updated = 0
    for sid, code in rows:
        targets = STATUS_TRANSITIONS.get(code, [])
        c.execute('UPDATE statuses SET allowed_transitions = %s WHERE id = %s',
                  (json.dumps(targets), sid))
        updated += 1
    conn.commit()
    conn.close()
    print(f'MySQL: Updated allowed_transitions for {updated} statuses')


if __name__ == '__main__':
    migrate_sqlite()
    migrate_mysql()
    print('Done.')
