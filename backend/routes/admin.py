from flask import Blueprint, request, jsonify, g
from functools import wraps

from backend.db import get_db
from backend.models import create_parking_lot, get_lot_summary
from backend.cache import cache_get, cache_set, cache_delete

from backend.tasks.reminders import daily_user_reminder
from backend.tasks.reports import monthly_report

admin_bp = Blueprint("admin", __name__)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if not user or user.get("role") != "admin":
            return jsonify({"error": "admin access required"}), 403
        return view(*args, **kwargs)
    return wrapped


@admin_bp.get("/parking-lots/summary")
@admin_required
def lots_summary():
    cache_key = "admin:lots_summary"
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"lots": cached})

    db = get_db()
    c = db.cursor()

    c.execute("""
    SELECT 
        pl.id,
        pl.prime_location_name,
        pl.address,
        pl.pin_code,
        pl.price_per_hour,
        pl.number_of_spots,
        SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) AS occupied_spots
    FROM parking_lots pl
    LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
    GROUP BY pl.id
    ORDER BY pl.prime_location_name;
""")


    rows = c.fetchall()
    db.close()

    lots = []
    for r in rows:
        occupied = r[6] or 0
        total = r[5] or 0
        lots.append({
            "id": r[0],
            "prime_location_name": r[1],
            "address": r[2],
            "pin_code": r[3],
            "price_per_hour": r[4],
            "total_spots": r[5],
            "occupied_spots": r[6] or 0,
            "available_spots": (r[5] - (r[6] or 0)),
        })

    # cache for 30 seconds
    cache_set(cache_key, lots, ttl=30)

    return jsonify({"lots": lots})



@admin_bp.get("/parking-lots")
@admin_required
def list_parking_lots():
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT id, prime_location_name, address, pin_code,
               price_per_hour, number_of_spots, is_active
        FROM parking_lots
        ORDER BY prime_location_name;
    """)

    rows = c.fetchall()
    db.close()

    lots = []
    for r in rows:
        lots.append({
            "id": r[0],
            "prime_location_name": r[1],
            "address": r[2],
            "pin_code": r[3],
            "price_per_hour": r[4],
            "number_of_spots": r[5],
            "is_active": bool(r[6]),
        })

    return jsonify({"lots": lots})


@admin_bp.post("/parking-lots")
@admin_required
def create_lot():
    payload = request.get_json(force=True) or {}

    name = payload.get("prime_location_name")
    address = payload.get("address")
    pin_code = payload.get("pin_code")
    price = payload.get("price_per_hour")
    spot_count = payload.get("number_of_spots")

    if not name or price is None or spot_count is None:
        return jsonify({"error": "prime_location_name, price_per_hour and number_of_spots are required"}), 400

    try:
        price = float(price)
        spot_count = int(spot_count)
    except ValueError:
        return jsonify({"error": "price_per_hour must be number and number_of_spots must be integer"}), 400

    if spot_count <= 0 or price < 0:
        return jsonify({"error": "invalid values for price_per_hour or number_of_spots"}), 400

    lot_id = create_parking_lot(name, address, pin_code, price, spot_count)

    return jsonify({"id": lot_id, "message": "parking lot created"}), 201


@admin_bp.put("/parking-lots/<int:lot_id>")
@admin_required
def update_lot(lot_id):
    data = request.get_json(force=True) or {}
    new_name = data.get("prime_location_name")
    new_address = data.get("address")
    new_pin = data.get("pin_code")
    new_price = data.get("price_per_hour")
    new_spots = data.get("number_of_spots")
    new_active = data.get("is_active")

    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT number_of_spots FROM parking_lots
        WHERE id = ?
    """, (lot_id,))
    row = c.fetchone()

    if not row:
        db.close()
        return jsonify({"error": "lot not found"}), 404

    current_spots = row[0]

    c.execute("""
        UPDATE parking_lots
        SET prime_location_name = ?, address = ?, pin_code = ?, 
            price_per_hour = ?, number_of_spots = ?, is_active = ?
        WHERE id = ?
    """, (
        new_name, new_address, new_pin, new_price,
        new_spots, new_active, lot_id
    ))

    if new_spots > current_spots:
        for i in range(current_spots + 1, new_spots + 1):
            c.execute("""
                INSERT INTO parking_spots (lot_id, spot_number, status)
                VALUES (?, ?, 'A')
            """, (lot_id, i))

    if new_spots < current_spots:
        c.execute("""
            SELECT id FROM parking_spots
            WHERE lot_id = ? AND spot_number > ? AND status = 'O'
        """, (lot_id, new_spots))
        active = c.fetchone()

        if active:
            db.rollback()
            db.close()
            return jsonify({
                "error": "Cannot reduce spots, some of the removed spots are occupied"
            }), 400

        c.execute("""
            DELETE FROM parking_spots
            WHERE lot_id = ? AND spot_number > ?
        """, (lot_id, new_spots))

    db.commit()
    cache_delete("admin:dashboard_summary")
    cache_delete("admin:lots_summary")
    cache_delete("user:parking_lots")
    db.close()

    return jsonify({"message": "lot updated", "lot_id": lot_id})


@admin_bp.delete("/parking-lots/<int:lot_id>")
@admin_required
def delete_lot(lot_id):
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT COUNT(*) FROM parking_spots
        WHERE lot_id = ? AND status = 'O';
    """, (lot_id,))
    occupied_count = c.fetchone()[0]

    if occupied_count > 0:
        db.close()
        return jsonify({"error": "cannot delete lot with occupied spots"}), 400

    c.execute("DELETE FROM parking_spots WHERE lot_id = ?;", (lot_id,))
    c.execute("DELETE FROM parking_lots WHERE id = ?;", (lot_id,))

    db.commit()
    cache_delete("admin:dashboard_summary")
    cache_delete("admin:lots_summary")
    cache_delete("user:parking_lots")
    db.close()

    return jsonify({"message": "parking lot removed"})


@admin_bp.get("/parking-lots/<int:lot_id>/spots")
@admin_required
def lot_spots(lot_id):
    db = get_db()
    c = db.cursor()
    c.execute("""
        SELECT 
            ps.id,
            ps.spot_number,
            ps.status,
            
            -- user info if spot is active
            u.username,
            r.parking_in

        FROM parking_spots ps
        LEFT JOIN reservations r 
            ON ps.id = r.spot_id AND r.status = 'active'
        LEFT JOIN users u
            ON r.user_id = u.id

        WHERE ps.lot_id = ?
        ORDER BY ps.spot_number;
    """, (lot_id,))

    rows = c.fetchall()
    db.close()

    spots = []
    for r in rows:
        spots.append({
            "id": r[0],
            "spot_number": r[1],
            "status": r[2],
            "username": r[3] or None,
            "start_time": r[4] or None,
        })

    return jsonify({"spots": spots})



@admin_bp.get("/users")
@admin_required
def list_users():
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT id, username, email, phone, role, is_active
        FROM users
        ORDER BY username;
    """)

    rows = c.fetchall()
    db.close()

    users = []
    for r in rows:
        users.append({
            "id": r[0],
            "username": r[1],
            "email": r[2],
            "phone": r[3],
            "role": r[4],
            "is_active": bool(r[5]),
        })

    return jsonify({"users": users})


@admin_bp.get("/dashboard-summary")
@admin_required
def dashboard_summary():
    cache_key = "admin:dashboard_summary"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    db = get_db()
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM parking_lots;")
    total_lots = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM parking_spots;")
    total_spots = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM parking_spots WHERE status = 'O';")
    occupied_spots = c.fetchone()[0]

    available_spots = total_spots - occupied_spots

    db.close()

    summary = {
        "total_lots": total_lots,
        "total_spots": total_spots,
        "occupied_spots": occupied_spots,
        "available_spots": available_spots,
    }

    cache_set(cache_key, summary, ttl=30)

    return jsonify(summary)


@admin_bp.post("/debug/daily-reminder")
@admin_required
def run_daily_reminder():
    daily_user_reminder.delay()
    return jsonify({"status": "queued"}), 202


@admin_bp.post("/debug/monthly-report")
@admin_required
def run_monthly_report():
    monthly_report.delay()
    return jsonify({"status": "queued"}), 202
