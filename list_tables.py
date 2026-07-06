import database as db
conn = db.get_connection()
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print([r[0] for r in c.fetchall()])
conn.close()
