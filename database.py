import sqlite3
import os
import hashlib
import datetime

import os

os.makedirs('customerdata', exist_ok=True)
DB_PATH = 'customerdata/masar_home.db'
DAYS_AR = {
    0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء",
    3: "الخميس",  4: "الجمعة",  5: "السبت", 6: "الأحد"
}

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_users(c):
    c.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    try:
        c.execute('ALTER TABLE Users ADD COLUMN employee_name TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass # Column already exists
        
    c.execute('SELECT COUNT(*) FROM Users')
    if c.fetchone()[0] == 0:
        default_pw = hash_password("6065")
        users = [
            ("Admin", default_pw, "Admin", "م. علي بن عيسى"),
            ("Surveyor01", default_pw, "Surveyor", "مساح 1"),
            ("Surveyor02", default_pw, "Surveyor", "مساح 2"),
            ("Designer01", default_pw, "Designer", "مصمم 1"),
            ("Designer02", default_pw, "Designer", "مصمم 2"),
            ("Production01", default_pw, "Production", "موظف إنتاج 1"),
            ("Production02", default_pw, "Production", "موظف إنتاج 2"),
            ("Financial", default_pw, "Financial", "موظف مالي"),
            ("GM", default_pw, "Observer", "المدير التنفيذي"),
            ("CEO", default_pw, "Observer", "رئيس مجلس الإدارة")
        ]
        c.executemany('INSERT INTO Users (username, password_hash, role, employee_name) VALUES (?, ?, ?, ?)', users)
    else:
        # Update existing Admin account if it still has the old default name
        c.execute("UPDATE Users SET employee_name='م. علي بن عيسى' WHERE username='Admin' AND (employee_name='المدير العام' OR employee_name IS NULL OR employee_name='')")

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    init_users(c)
    init_activity_log(c)
    
    # Create operational checklist forms logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS MaintenanceRequests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_date TEXT,
            problem_desc TEXT,
            problem_type TEXT,
            correction_desc TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS RationRequests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_date TEXT,
            water_qty TEXT,
            water_notes TEXT,
            coffee_qty TEXT,
            coffee_notes TEXT,
            tea_qty TEXT,
            tea_notes TEXT,
            other_name TEXT,
            other_qty TEXT,
            other_notes TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Messages Table (Internal Chat)
    c.execute('''
        CREATE TABLE IF NOT EXISTS Messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_username TEXT NOT NULL,
            receiver_username TEXT, -- Made optional for group messages
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            group_id INTEGER DEFAULT NULL
        )
    ''')
    
    try:
        c.execute('ALTER TABLE Messages ADD COLUMN group_id INTEGER DEFAULT NULL')
    except sqlite3.OperationalError:
        pass # Column already exists

    # Create Group Chat Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_group_members (
            group_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            PRIMARY KEY (group_id, username)
        )
    ''')
    
    # Create Customers Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            notes TEXT
        )
    ''')
    # Create Tickets Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            title TEXT,
            description TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES Customers (id)
        )
    ''')
    # Create Checklists Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Checklists (
            check_date TEXT PRIMARY KEY,
            m1 INTEGER, m2 INTEGER, m3 INTEGER, m4 INTEGER, m_notes TEXT,
            d1 INTEGER, d2 INTEGER, d3 INTEGER, d4 INTEGER, d_notes TEXT,
            e1 INTEGER, e2 INTEGER, e3 INTEGER, e4 INTEGER, e_notes TEXT
        )
    ''')
    # Create FieldVisits Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS FieldVisits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            phone TEXT,
            address TEXT,
            furniture_type TEXT,
            site_status TEXT,
            visit_date TEXT,
            visit_time TEXT,
            visit_value REAL,
            design_value REAL DEFAULT 0.0,
            payment_status TEXT,
            map_link TEXT DEFAULT "",
            site_status_note TEXT DEFAULT "",
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_contacted INTEGER DEFAULT 0
        )
    ''')
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN is_contacted INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN map_link TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN site_status_note TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN design_value REAL DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN measurement_completed TEXT DEFAULT ""')
        c.execute('ALTER TABLE FieldVisits ADD COLUMN measurement_reason TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass # Columns already exist
        
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN document_revision_completed TEXT DEFAULT ""')
        c.execute('ALTER TABLE FieldVisits ADD COLUMN document_revision_reason TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass # Columns already exist
        
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN media_paths TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN last_modified_by TEXT DEFAULT ""')
        c.execute('ALTER TABLE FieldVisits ADD COLUMN last_modified_at TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass # Columns already exist

    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN contact_reason TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass # Column already exists

    # --- Indexes for performance ---
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender ON Messages(sender_username)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_receiver ON Messages(receiver_username)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_group ON Messages(group_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_read ON Messages(is_read)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_fieldvisits_date ON FieldVisits(visit_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_group_members ON chat_group_members(username)')
    try:
        c.execute('CREATE INDEX IF NOT EXISTS idx_activity_user ON ActivityLog(username)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_activity_raw ON ActivityLog(raw_timestamp)')
    except Exception:
        pass  # ActivityLog table created on first log_activity call

    # --- Contracts Table ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS Contracts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_no TEXT UNIQUE NOT NULL,
            title       TEXT NOT NULL,
            client_name TEXT NOT NULL,
            client_phone TEXT DEFAULT "",
            contract_date TEXT DEFAULT "",
            start_date  TEXT DEFAULT "",
            end_date    TEXT DEFAULT "",
            value       REAL DEFAULT 0.0,
            status      TEXT DEFAULT "جاري",
            notes       TEXT DEFAULT "",
            file_paths  TEXT DEFAULT "",
            created_by  TEXT DEFAULT "",
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_modified_by TEXT DEFAULT "",
            last_modified_at TEXT DEFAULT "",
            odoo_no     TEXT DEFAULT ""
        )
    ''')
    try:
        c.execute('ALTER TABLE Contracts ADD COLUMN odoo_no TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN is_canceled INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE FieldVisits ADD COLUMN is_approved INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass

    c.execute('CREATE INDEX IF NOT EXISTS idx_contracts_status ON Contracts(status)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_contracts_client ON Contracts(client_name)')

    # --- ProjectDesigns Table ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS ProjectDesigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER UNIQUE,
            designer_name TEXT DEFAULT "",
            status TEXT DEFAULT "مجدول",
            design_link TEXT DEFAULT "",
            notes TEXT DEFAULT "",
            last_updated TEXT DEFAULT "",
            odoo_no TEXT DEFAULT "",
            design_docs TEXT DEFAULT "",
            is_sent_to_production INTEGER DEFAULT 0,
            workshop_drawing TEXT DEFAULT "",
            price_final REAL DEFAULT 0.0,
            price_is_approved INTEGER DEFAULT 0,
            price_is_paid INTEGER DEFAULT 0,
            price_details TEXT DEFAULT "",
            contract_is_approved INTEGER DEFAULT 0,
            second_payment_paid INTEGER DEFAULT 0
        )
    ''')
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN odoo_no TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN design_docs TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN is_sent_to_production INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN workshop_drawing TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN price_final REAL DEFAULT 0.0")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN price_is_approved INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN price_is_paid INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN price_details TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN contract_is_approved INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE ProjectDesigns ADD COLUMN second_payment_paid INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS ProjectDesignHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER,
            designer_name TEXT,
            status TEXT,
            notes TEXT,
            username TEXT,
            employee_name TEXT,
            timestamp TEXT
        )
    ''')
    
    c.execute('CREATE INDEX IF NOT EXISTS idx_project_designs_visit ON ProjectDesigns(visit_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_fieldvisits_approved ON FieldVisits(is_approved, is_canceled)')

    conn.commit()
    conn.close()

# --- Customer Functions ---
def add_customer(name, phone, address, notes):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO customers (name, phone, address, notes) VALUES (?, ?, ?, ?)", (name, phone, address, notes))
    conn.commit()
    conn.close()

def get_all_customers():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers")
    rows = c.fetchall()
    conn.close()
    return rows

def update_customer(customer_id, name, phone, address, notes):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE customers 
        SET name = ?, phone = ?, address = ?, notes = ?
        WHERE id = ?
    ''', (name, phone, address, notes, customer_id))
    conn.commit()
    conn.close()

def delete_customer(customer_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()

# --- Ticket Functions ---
def add_ticket(customer_id, title, description, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO tickets (customer_id, title, description, status) VALUES (?, ?, ?, ?)", 
              (customer_id, title, description, status))
    conn.commit()
    conn.close()

def get_all_tickets():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT t.id, f.customer_name, t.title, t.description, t.status, t.created_at
        FROM tickets t
        LEFT JOIN FieldVisits f ON t.customer_id = f.id
        ORDER BY t.id DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def update_ticket_status(ticket_id, new_status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
    conn.commit()
    conn.close()

def delete_ticket(ticket_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM Tickets WHERE id = ?', (ticket_id,))
    conn.commit()
    conn.close()

# Checklist Functions
def save_checklist(date_str, m1, m2, m3, m4, m_notes, d1, d2, d3, d4, d_notes, e1, e2, e3, e4, e_notes):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO Checklists (check_date, m1, m2, m3, m4, m_notes, d1, d2, d3, d4, d_notes, e1, e2, e3, e4, e_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(check_date) DO UPDATE SET
            m1=excluded.m1, m2=excluded.m2, m3=excluded.m3, m4=excluded.m4, m_notes=excluded.m_notes,
            d1=excluded.d1, d2=excluded.d2, d3=excluded.d3, d4=excluded.d4, d_notes=excluded.d_notes,
            e1=excluded.e1, e2=excluded.e2, e3=excluded.e3, e4=excluded.e4, e_notes=excluded.e_notes
    ''', (date_str, m1, m2, m3, m4, m_notes, d1, d2, d3, d4, d_notes, e1, e2, e3, e4, e_notes))
    conn.commit()
    conn.close()

def get_checklist(date_str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM Checklists WHERE check_date = ?', (date_str,))
    res = c.fetchone()
    conn.close()
    return res

def get_all_checklist_dates():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT check_date FROM Checklists ORDER BY check_date DESC')
    res = c.fetchall()
    conn.close()
    return [r[0] for r in res]

# Field Visits Functions
def save_field_visit(customer_name, phone, address, furniture_type, site_status, visit_date, visit_time, visit_value, payment_status, measurement_completed="نعم", measurement_reason="", document_revision_completed="نعم", document_revision_reason="", media_paths="", design_value=0.0, map_link="", site_status_note=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO FieldVisits (customer_name, phone, address, furniture_type, site_status, visit_date, visit_time, visit_value, design_value, payment_status, measurement_completed, measurement_reason, document_revision_completed, document_revision_reason, media_paths, map_link, site_status_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (customer_name, phone, address, furniture_type, site_status, visit_date, visit_time, visit_value, design_value, payment_status, measurement_completed, measurement_reason, document_revision_completed, document_revision_reason, media_paths, map_link, site_status_note))
    conn.commit()
    conn.close()

def update_field_visit(visit_id, customer_name, phone, address, furniture_type, site_status, visit_date, visit_time, visit_value, payment_status, measurement_completed, measurement_reason, document_revision_completed, document_revision_reason, media_paths, last_modified_by, last_modified_at, design_value=0.0, map_link="", site_status_note=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE FieldVisits
        SET customer_name=?, phone=?, address=?, furniture_type=?, site_status=?, visit_date=?, visit_time=?, visit_value=?, design_value=?, payment_status=?, measurement_completed=?, measurement_reason=?, document_revision_completed=?, document_revision_reason=?, media_paths=?, last_modified_by=?, last_modified_at=?, map_link=?, site_status_note=?
        WHERE id=?
    ''', (customer_name, phone, address, furniture_type, site_status, visit_date, visit_time, visit_value, design_value, payment_status, measurement_completed, measurement_reason, document_revision_completed, document_revision_reason, media_paths, last_modified_by, last_modified_at, map_link, site_status_note, visit_id))
    conn.commit()
    conn.close()

def get_next_visit_id():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT MAX(id) FROM FieldVisits')
    max_id = c.fetchone()[0]
    conn.close()
    return (max_id or 0) + 1

def get_all_field_visits():
    conn = get_connection()
    c = conn.cursor()
    # Explicit column list to guarantee indices match existing code
    query = '''
    SELECT 
        id, customer_name, phone, address, furniture_type, site_status, 
        visit_date, visit_time, visit_value, payment_status, created_at, 
        is_contacted, measurement_completed, measurement_reason, 
        document_revision_completed, document_revision_reason, media_paths, 
        last_modified_by, last_modified_at, contact_reason, is_canceled, 
        is_approved, approved_at, design_value, map_link, site_status_note
    FROM FieldVisits ORDER BY created_at DESC
    '''
    c.execute(query)
    res = c.fetchall()
    conn.close()
    return res

def mark_visit_contacted(visit_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE FieldVisits SET is_contacted = 1 WHERE id = ?', (visit_id,))
    conn.commit()
    conn.close()

def mark_visit_not_contacted(visit_id, reason):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE FieldVisits SET is_contacted = 2, contact_reason = ? WHERE id = ?', (reason, visit_id))
    conn.commit()
    conn.close()

# User Authentication Functions
def verify_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT password_hash, role, employee_name FROM Users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    
    if row and row[0] == hash_password(password):
        return {"success": True, "role": row[1], "employee_name": row[2] if len(row) > 2 else username}
    return {"success": False, "role": None, "employee_name": None}

def change_password(username, old_password, new_password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT password_hash FROM Users WHERE username=?', (username,))
    row = c.fetchone()
    
    if row and row[0] == hash_password(old_password):
        c.execute('UPDATE Users SET password_hash=? WHERE username=?', (hash_password(new_password), username))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# Admin Account Management Functions


def get_all_usernames():
    """Return ALL usernames (including Admin) for filter dropdowns."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT username FROM Users ORDER BY username')
    res = c.fetchall()
    conn.close()
    return [r[0] for r in res]

def get_users_map():
    """Return two dicts: username→employee_name and employee_name→username."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT username, employee_name FROM Users ORDER BY username')
    rows = c.fetchall()
    conn.close()
    u_to_e = {r[0]: r[1] if r[1] else r[0] for r in rows}
    e_to_u = {(r[1] if r[1] else r[0]): r[0] for r in rows}
    return u_to_e, e_to_u

def add_user(username, role, employee_name="", default_password="6065"):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO Users (username, password_hash, role, employee_name) VALUES (?, ?, ?, ?)', (username, hash_password(default_password), role, employee_name))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False # Username already exists
    conn.close()
    return success

def delete_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM Users WHERE id=? AND username != "Admin"', (user_id,))
    conn.commit()
    conn.close()

def reset_password(user_id, new_password="6065"):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE Users SET password_hash=? WHERE id=?', (hash_password(new_password), user_id))
    conn.commit()
    conn.close()

def update_user_details(user_id, role, employee_name, new_password=None):
    conn = get_connection()
    c = conn.cursor()
    if new_password and new_password.strip() != "":
        c.execute('UPDATE Users SET role=?, employee_name=?, password_hash=? WHERE id=?', 
                  (role, employee_name, hash_password(new_password), user_id))
    else:
        c.execute('UPDATE Users SET role=?, employee_name=? WHERE id=?', 
                  (role, employee_name, user_id))
    conn.commit()
    conn.close()


# --- Activity Log Functions ---

def init_activity_log(c):
    c.execute('''
        CREATE TABLE IF NOT EXISTS ActivityLog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            employee_name TEXT DEFAULT "",
            action_type TEXT NOT NULL,
            module TEXT DEFAULT "",
            details TEXT DEFAULT "",
            timestamp TEXT NOT NULL,
            raw_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Add raw_timestamp column to existing tables if missing
    try:
        c.execute('ALTER TABLE ActivityLog ADD COLUMN raw_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP')
    except Exception:
        pass

def log_activity(username, employee_name, action_type, module="", details=""):
    """Log a user action with full Arabic-formatted timestamp: day + date + exact time."""
    try:
        now = datetime.datetime.now()
        day_name = DAYS_AR[now.weekday()]
        formatted_ts = f"{day_name} | {now.strftime('%Y-%m-%d')} | {now.strftime('%H:%M:%S')}"
        raw_ts = now.strftime('%Y-%m-%d %H:%M:%S')

        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO ActivityLog (username, employee_name, action_type, module, details, timestamp, raw_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, employee_name, action_type, module, details, formatted_ts, raw_ts))
        conn.commit()
        conn.close()
    except Exception:
        pass  # Never let logging break the main app

def get_activity_logs(date_from=None, date_to=None, username_filter=None, action_type_filter=None, module_filter=None):
    """Retrieve activity logs with optional filters."""
    conn = get_connection()
    c = conn.cursor()
    
    query = "SELECT id, username, employee_name, action_type, module, details, timestamp FROM ActivityLog WHERE 1=1"
    params = []
    
    if date_from:
        query += " AND DATE(raw_timestamp) >= ?"
        params.append(str(date_from))
    if date_to:
        query += " AND DATE(raw_timestamp) <= ?"
        params.append(str(date_to))
    if username_filter and username_filter != "الكل":
        query += " AND username = ?"
        params.append(username_filter)
    if action_type_filter and action_type_filter != "الكل":
        query += " AND action_type = ?"
        params.append(action_type_filter)
    if module_filter and module_filter != "الكل":
        query += " AND module = ?"
        params.append(module_filter)
    
    query += " ORDER BY timestamp DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def get_distinct_log_users():
    """Get distinct usernames from activity log for filter dropdown."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT username FROM ActivityLog ORDER BY username")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def clear_activity_logs(days_older_than=None):
    """Admin can clear old logs (older than N days) or all logs."""
    conn = get_connection()
    c = conn.cursor()
    if days_older_than:
        c.execute("DELETE FROM ActivityLog WHERE timestamp < datetime('now', ? || ' days')", (f'-{days_older_than}',))
    else:
        c.execute("DELETE FROM ActivityLog")
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected

# --- MESSAGING SYSTEM ---

def send_message(sender_username, receiver_username, content):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO Messages (sender_username, receiver_username, content) 
        VALUES (?, ?, ?)
    ''', (sender_username, receiver_username, content))
    conn.commit()
    conn.close()

def get_chat_history(user1, user2, limit=200):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, sender_username, receiver_username, content, timestamp, is_read, group_id 
        FROM (
            SELECT * FROM Messages 
            WHERE (sender_username = ? AND receiver_username = ?) 
               OR (sender_username = ? AND receiver_username = ?)
            ORDER BY timestamp DESC LIMIT ?
        )
        ORDER BY timestamp ASC
    ''', (user1, user2, user2, user1, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_user_chat_history(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, sender_username, receiver_username, content, timestamp, is_read, group_id 
        FROM Messages 
        WHERE (sender_username = ? OR receiver_username = ?)
          AND group_id IS NULL
        ORDER BY timestamp ASC
    ''', (username, username))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_private_messages():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, sender_username, receiver_username, content, timestamp, is_read, group_id 
        FROM Messages 
        WHERE group_id IS NULL
        ORDER BY timestamp ASC
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def mark_messages_read(sender, receiver):
    """ Mark messages sent by `sender` to `receiver` as read. """
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE Messages 
        SET is_read = 1 
        WHERE sender_username = ? AND receiver_username = ? AND is_read = 0
    ''', (sender, receiver))
    conn.commit()
    conn.close()

def get_unread_counts(receiver_username):
    """ Return a dictionary mapping sender_username -> unread count. """
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT sender_username, COUNT(*) 
        FROM Messages 
        WHERE receiver_username = ? AND is_read = 0
        GROUP BY sender_username
    ''', (receiver_username,))
    rows = c.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, employee_name FROM Users ORDER BY employee_name")
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_users_admin():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, employee_name, password_hash FROM Users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

# --- GROUP CHAT SYSTEM ---

def create_chat_group(name, creator_username, members):
    """ Create a group and add members """
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO chat_groups (name, created_by) VALUES (?, ?)", (name, creator_username))
    group_id = c.lastrowid
    
    # Always include the creator
    all_members = set(members)
    all_members.add(creator_username)
    
    for member in all_members:
        c.execute("INSERT INTO chat_group_members (group_id, username) VALUES (?, ?)", (group_id, member))
        
    conn.commit()
    conn.close()
    return group_id

def get_user_groups(username):
    """ Get all groups the user is a member of """
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT g.id, g.name, g.created_by, g.created_at 
        FROM chat_groups g
        JOIN chat_group_members m ON g.id = m.group_id
        WHERE m.username = ?
        ORDER BY g.created_at DESC
    ''', (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_group_members(group_id):
    """ Get all members of a group """
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT u.username, u.employee_name 
        FROM chat_group_members m
        JOIN Users u ON m.username = u.username
        WHERE m.group_id = ?
    ''', (group_id,))
    rows = c.fetchall()
    conn.close()
    return [{"username": r[0], "employee_name": r[1]} for r in rows]

def send_group_message(sender_username, group_id, content):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO Messages (sender_username, receiver_username, group_id, content) 
        VALUES (?, 'GROUP_CHAT', ?, ?)
    ''', (sender_username, group_id, content))
    conn.commit()
    conn.close()

def get_group_messages(group_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, sender_username, content, timestamp 
        FROM Messages 
        WHERE group_id = ?
        ORDER BY timestamp ASC
    ''', (group_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_chat_group(group_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM chat_groups WHERE id = ?', (group_id,))
    c.execute('DELETE FROM chat_group_members WHERE group_id = ?', (group_id,))
    c.execute('DELETE FROM Messages WHERE group_id = ?', (group_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# --- CONTRACTS FUNCTIONS ---
# ─────────────────────────────────────────────────────────────

def _next_contract_no():
    """Generate next sequential contract number like CNT-0001."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM Contracts")
    max_id = c.fetchone()[0]
    conn.close()
    return f"CNT-{(max_id or 0) + 1:04d}"


def add_contract(title, client_name, client_phone, contract_date,
                 start_date, end_date, value, status, notes, created_by, odoo_no=""):
    conn = get_connection()
    c = conn.cursor()
    contract_no = _next_contract_no()
    import datetime
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO Contracts
            (contract_no, title, client_name, client_phone, contract_date,
             start_date, end_date, value, status, notes,
             created_by, created_at, last_modified_by, last_modified_at, odoo_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (contract_no, title, client_name, client_phone, contract_date,
          start_date, end_date, value, status, notes,
          created_by, now, created_by, now, odoo_no))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id, contract_no


def get_all_contracts():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, contract_no, title, client_name, client_phone,
               contract_date, start_date, end_date, value, status,
               notes, file_paths, created_by, created_at,
               last_modified_by, last_modified_at, odoo_no
        FROM Contracts ORDER BY id DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return rows


def get_contract_by_id(contract_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM Contracts WHERE id = ?', (contract_id,))
    row = c.fetchone()
    conn.close()
    return row


def update_contract(contract_id, title, client_name, client_phone,
                    contract_date, start_date, end_date, value,
                    status, notes, modified_by, odoo_no=""):
    import datetime
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE Contracts SET
            title=?, client_name=?, client_phone=?, contract_date=?,
            start_date=?, end_date=?, value=?, status=?, notes=?,
            last_modified_by=?, last_modified_at=?, odoo_no=?
        WHERE id=?
    ''', (title, client_name, client_phone, contract_date,
          start_date, end_date, value, status, notes,
          modified_by, now, odoo_no, contract_id))
    conn.commit()
    conn.close()


def delete_contract(contract_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM Contracts WHERE id = ?', (contract_id,))
    conn.commit()
    conn.close()


def update_contract_files(contract_id, file_paths_str, modified_by):
    import datetime
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE Contracts SET file_paths=?, last_modified_by=?, last_modified_at=?
        WHERE id=?
    ''', (file_paths_str, modified_by, now, contract_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# --- OPERATIONAL FORMS FUNCTIONS (MAINTENANCE & RATION) ---
# ─────────────────────────────────────────────────────────────

def save_maintenance_request(request_date, problem_desc, problem_type, correction_desc, created_by):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO MaintenanceRequests (request_date, problem_desc, problem_type, correction_desc, created_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (request_date, problem_desc, problem_type, correction_desc, created_by))
    conn.commit()
    conn.close()

def get_all_maintenance_requests():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, request_date, problem_desc, problem_type, correction_desc, created_by, created_at FROM MaintenanceRequests ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def save_ration_request(request_date, water_qty, water_notes, coffee_qty, coffee_notes, tea_qty, tea_notes, other_name, other_qty, other_notes, created_by):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO RationRequests (request_date, water_qty, water_notes, coffee_qty, coffee_notes, tea_qty, tea_notes, other_name, other_qty, other_notes, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (request_date, water_qty, water_notes, coffee_qty, coffee_notes, tea_qty, tea_notes, other_name, other_qty, other_notes, created_by))
    conn.commit()
    conn.close()

def get_all_ration_requests():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, request_date, water_qty, water_notes, coffee_qty, coffee_notes, tea_qty, tea_notes, other_name, other_qty, other_notes, created_by, created_at FROM RationRequests ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows
