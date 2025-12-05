from backend.db import get_db
from werkzeug.security import generate_password_hash
from backend.cache import cache_delete


def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            is_active INTEGER DEFAULT 1
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prime_location_name TEXT NOT NULL,
            address TEXT,
            pin_code TEXT,
            price_per_hour REAL NOT NULL,
            number_of_spots INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            spot_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'A',
            level TEXT,
            remarks TEXT,
            FOREIGN KEY (lot_id) REFERENCES parking_lots(id)
        );
    """)

    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_spot_unique
        ON parking_spots(lot_id, spot_number);
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lot_id INTEGER NOT NULL,
            spot_id INTEGER NOT NULL,
            parking_in TEXT NOT NULL,
            parking_out TEXT,
            parking_cost REAL,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (lot_id) REFERENCES parking_lots(id),
            FOREIGN KEY (spot_id) REFERENCES parking_spots(id)
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS task_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL,
            file_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_path TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    c.execute("SELECT id FROM users WHERE role = 'admin'")
    admin_exists = c.fetchone()

    if admin_exists is None:
        c.execute("""
            INSERT INTO users (username, password_hash, role, email, is_active)
            VALUES (?, ?, 'admin', ?, 1)
        """, (
            "admin",
            generate_password_hash("admin123"),
            "admin@parkingapp.com"
        ))

    db.commit()
    db.close()


def create_parking_lot(name, address, pin_code, price, spot_count):
    db = get_db()
    c = db.cursor()

    c.execute("""
        INSERT INTO parking_lots (prime_location_name, address, pin_code, price_per_hour, number_of_spots)
        VALUES (?, ?, ?, ?, ?)
    """, (name, address, pin_code, price, spot_count))

    lot_id = c.lastrowid

    for i in range(1, spot_count + 1):
        c.execute("""
            INSERT INTO parking_spots (lot_id, spot_number, status)
            VALUES (?, ?, 'A')
        """, (lot_id, i))

    db.commit()

    cache_delete("admin:dashboard_summary")
    cache_delete("admin:lots_summary")
    cache_delete("user:parking_lots")
    db.close()
    return lot_id


def get_lot_summary():
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT pl.id, pl.prime_location_name, pl.address, pl.pin_code,
               pl.price_per_hour, pl.number_of_spots,
               SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END)
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        WHERE pl.is_active = 1
        GROUP BY pl.id
        ORDER BY pl.prime_location_name;
    """)

    rows = c.fetchall()
    db.close()

    result = []
    for r in rows:
        occupied = r[6] or 0
        result.append({
            "id": r[0],
            "prime_location_name": r[1],
            "address": r[2],
            "pin_code": r[3],
            "price_per_hour": r[4],
            "total_spots": r[5],
            "occupied_spots": occupied,
            "available_spots": r[5] - occupied
        })

    return result


def find_first_available_spot(lot_id):
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT id, lot_id, spot_number, status
        FROM parking_spots
        WHERE lot_id = ? AND status = 'A'
        ORDER BY spot_number ASC
        LIMIT 1;
    """, (lot_id,))

    row = c.fetchone()
    db.close()
    return row


def mark_spot_status(spot_id, status):
    db = get_db()
    c = db.cursor()

    c.execute("UPDATE parking_spots SET status = ? WHERE id = ?", (status, spot_id))

    db.commit()
    db.close()
