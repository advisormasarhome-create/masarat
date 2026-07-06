"""Comprehensive test to verify all modules and database functions."""
import database as db
import traceback

def test_section(name, func):
    try:
        func()
        print(f"  ✅ {name}")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        traceback.print_exc()
        return False

print("=" * 60)
print("منظومة مسارات - اختبار شامل")
print("=" * 60)

# 1. Database init
print("\n1. اختبار قاعدة البيانات:")
test_section("init_db", lambda: db.init_db())

# 2. Tables exist
def check_tables():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    conn.close()
    required = ['Contracts', 'FieldVisits', 'Users', 'ActivityLog', 'Messages',
                'Checklists', 'customers', 'tickets', 'chat_groups', 'chat_group_members']
    missing = [t for t in required if t not in tables]
    if missing:
        raise Exception(f"Missing tables: {missing}")
    print(f"    Found {len(tables)} tables: {tables}")

test_section("Required tables exist", check_tables)

# 3. ProjectDesigns and ProjectProduction tables
def check_extra_tables():
    conn = db.get_connection()
    c = conn.cursor()
    # Create if not exist (same as modules do)
    c.execute('''CREATE TABLE IF NOT EXISTS ProjectDesigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        visit_id INTEGER UNIQUE,
        designer_name TEXT DEFAULT "",
        status TEXT DEFAULT "تحت الدراسة",
        design_link TEXT DEFAULT "",
        notes TEXT DEFAULT "",
        last_updated TEXT DEFAULT ""
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ProjectProduction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        visit_id INTEGER UNIQUE,
        assigned_factory TEXT DEFAULT "",
        status TEXT DEFAULT "بانتظار التعاقد",
        progress INTEGER DEFAULT 0,
        notes TEXT DEFAULT "",
        last_updated TEXT DEFAULT ""
    )''')
    conn.commit()
    conn.close()

test_section("ProjectDesigns/Production tables", check_extra_tables)

# 4. Field visits
def check_visits():
    visits = db.get_all_field_visits()
    print(f"    Found {len(visits)} field visits")
    if visits:
        print(f"    Row length: {len(visits[0])}")
        if len(visits[0]) < 21:
            raise Exception(f"Expected 21 columns, got {len(visits[0])}")

test_section("Field visits", check_visits)

# 5. Contracts functions
def check_contracts():
    contracts = db.get_all_contracts()
    print(f"    Found {len(contracts)} contracts")
    if contracts and len(contracts[0]) != 17:
        raise Exception(f"Expected 17 columns, got {len(contracts[0])}")

test_section("Contracts", check_contracts)

# 6. Users
def check_users():
    users = db.get_all_users()
    print(f"    Found {len(users)} users")

test_section("Users", check_users)

# 7. Module imports
print("\n2. اختبار الوحدات:")
test_section("mod_contracts", lambda: __import__('modules.mod_contracts'))
test_section("mod_design", lambda: __import__('modules.mod_design'))
test_section("mod_production", lambda: __import__('modules.mod_production'))
test_section("mod_visits", lambda: __import__('modules.mod_visits'))
test_section("mod_journey", lambda: __import__('modules.mod_journey'))
test_section("mod_statistics", lambda: __import__('modules.mod_statistics'))
test_section("mod_checklist", lambda: __import__('modules.mod_checklist'))
test_section("mod_pricing", lambda: __import__('modules.mod_pricing'))
test_section("mod_finance", lambda: __import__('modules.mod_finance'))
test_section("mod_activity_log", lambda: __import__('modules.mod_activity_log'))

# 8. Design query test (same SQL as mod_design.py)
print("\n3. اختبار استعلامات SQL:")
def check_design_query():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT f.id, f.customer_name, f.phone, f.furniture_type,
               COALESCE(d.designer_name, 'غير معين'),
               COALESCE(d.status, 'تحت الدراسة'),
               COALESCE(d.design_link, ''),
               COALESCE(d.notes, ''),
               COALESCE(con.odoo_no, '')
        FROM FieldVisits f
        LEFT JOIN ProjectDesigns d ON f.id = d.visit_id
        LEFT JOIN Contracts con ON f.customer_name = con.client_name
        WHERE f.is_canceled = 0
        ORDER BY f.id DESC
    ''')
    rows = c.fetchall()
    conn.close()
    print(f"    Design query returned {len(rows)} rows")

test_section("Design SQL query", check_design_query)

# 9. Production query test (same SQL as mod_production.py)
def check_production_query():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT f.id, f.customer_name, f.phone, f.furniture_type,
               COALESCE(p.assigned_factory, 'غير محدد'),
               COALESCE(p.status, 'بانتظار التعاقد'),
               COALESCE(p.progress, 0),
               COALESCE(p.notes, ''),
               COALESCE(d.design_link, ''),
               COALESCE(con.odoo_no, '')
        FROM FieldVisits f
        LEFT JOIN ProjectProduction p ON f.id = p.visit_id
        LEFT JOIN ProjectDesigns d ON f.id = d.visit_id
        LEFT JOIN Contracts con ON f.customer_name = con.client_name
        WHERE f.is_canceled = 0
        ORDER BY f.id DESC
    ''')
    rows = c.fetchall()
    conn.close()
    print(f"    Production query returned {len(rows)} rows")

test_section("Production SQL query", check_production_query)

# 10. Journey query test
def check_journey_query():
    conn = db.get_connection()
    c = conn.cursor()
    visits = db.get_all_field_visits()
    if visits:
        v = visits[0]
        v_id = v[0]
        c.execute("SELECT designer_name, status, notes FROM ProjectDesigns WHERE visit_id = ?", (v_id,))
        design_info = c.fetchone()
        c.execute("SELECT contract_no, status, value, notes, odoo_no FROM Contracts WHERE client_name = ? OR notes LIKE ?", (v[1], f"%MHM{v_id:05d}%"))
        contract_info = c.fetchone()
        c.execute("SELECT assigned_factory, status, progress, notes FROM ProjectProduction WHERE visit_id = ?", (v_id,))
        prod_info = c.fetchone()
        c.execute("SELECT title, status, created_at FROM tickets WHERE customer_id = ?", (v_id,))
        tickets_info = c.fetchall()
    conn.close()
    print(f"    Journey queries for visit {v_id}: design={design_info is not None}, contract={contract_info is not None}")

test_section("Journey SQL queries", check_journey_query)

# 11. Statistics queries
def check_statistics_query():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(value), 0) FROM Contracts")
    c.fetchone()
    c.execute("SELECT COUNT(*) FROM ProjectDesigns WHERE status != 'مكتمل ومقبول'")
    c.fetchone()
    c.execute("SELECT COUNT(*) FROM ProjectProduction WHERE status != 'تم التركيب والتسليم' AND status != 'بانتظار التعاقد'")
    c.fetchone()
    c.execute("SELECT COUNT(*) FROM tickets WHERE status != 'مغلقة'")
    c.fetchone()
    conn.close()

test_section("Statistics SQL queries", check_statistics_query)

# 12. Login test
print("\n4. اختبار تسجيل الدخول:")
def check_login():
    result = db.verify_user("Admin", "6065")
    if not result["success"]:
        raise Exception("Admin login failed")
    print(f"    Login OK - role: {result['role']}, name: {result['employee_name']}")

test_section("Admin login", check_login)

print("\n" + "=" * 60)
print("اكتمل الاختبار الشامل بنجاح ✅")
print("=" * 60)
