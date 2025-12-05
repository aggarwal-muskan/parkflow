from flask import Blueprint, request, jsonify, g
from functools import wraps
from datetime import datetime

from backend.db import get_db
from backend.models import find_first_available_spot
from backend.tasks.export import generate_csv
from backend.cache import cache_get, cache_set

user_bp = Blueprint("user", __name__)


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if not user or user.get("role") != "user":
            return jsonify({"error": "user access required"}), 403
        return view(*args, **kwargs)
    return wrapped

@user_bp.get("/parking-lots")
@user_required
def list_lots_for_user():
    cache_key = "user:parking_lots"
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"lots": cached})

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
            "total_spots": total,
            "occupied_spots": occupied,
            "available_spots": total - occupied,
        })

    cache_set(cache_key, lots, ttl=20)

    return jsonify({"lots": lots})


@user_bp.post("/reservations")
@user_required
def create_reservation():
    data = request.get_json(force=True) or {}
    lot_id = data.get("lot_id")
    user = g.current_user

    if not lot_id:
        return jsonify({"error": "lot_id is required"}), 400

    try:
        lot_id = int(lot_id)
    except ValueError:
        return jsonify({"error": "lot_id must be integer"}), 400

    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT id FROM reservations
        WHERE user_id = ? AND status = 'active'
        LIMIT 1;
    """, (user["id"],))
    existing = c.fetchone()
    if existing:
        db.close()
        return jsonify({"error": "you already have an active reservation"}), 400

    spot_row = find_first_available_spot(lot_id)
    if not spot_row:
        db.close()
        return jsonify({"error": "no available spot in this lot"}), 400

    spot_id, _, spot_number, _ = spot_row
    now = datetime.utcnow().isoformat()

    c.execute("""
        INSERT INTO reservations (user_id, lot_id, spot_id, parking_in, status)
        VALUES (?, ?, ?, ?, 'active');
    """, (user["id"], lot_id, spot_id, now))

    reservation_id = c.lastrowid

    c.execute("""
        UPDATE parking_spots
        SET status = 'O'
        WHERE id = ?;
    """, (spot_id,))

    db.commit()
    db.close()

    return jsonify({
        "id": reservation_id,
        "lot_id": lot_id,
        "spot_id": spot_id,
        "spot_number": spot_number,
        "parking_in": now,
        "status": "active",
    }), 201


@user_bp.put("/reservations/<int:reservation_id>/release")
@user_required
def release_reservation(reservation_id):
    user = g.current_user
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT r.id, r.spot_id, r.parking_in, pl.price_per_hour
        FROM reservations r
        JOIN parking_lots pl ON r.lot_id = pl.id
        WHERE r.id = ? AND r.user_id = ? AND r.status = 'active';
    """, (reservation_id, user["id"]))

    row = c.fetchone()
    if not row:
        db.close()
        return jsonify({"error": "active reservation not found"}), 404

    res_id, spot_id, parking_in_str, price_per_hour = row

    try:
        start_time = datetime.fromisoformat(parking_in_str)
    except ValueError:
        start_time = datetime.utcnow()

    end_time = datetime.utcnow()
    duration_seconds = (end_time - start_time).total_seconds()
    hours = duration_seconds / 3600.0
    if hours < 0:
        hours = 0

    cost = round(hours * float(price_per_hour), 2)

    c.execute("""
        UPDATE reservations
        SET parking_out = ?, parking_cost = ?, status = 'completed'
        WHERE id = ?;
    """, (end_time.isoformat(), cost, res_id))

    c.execute("""
        UPDATE parking_spots
        SET status = 'A'
        WHERE id = ?;
    """, (spot_id,))

    db.commit()
    db.close()

    return jsonify({
        "id": res_id,
        "parking_out": end_time.isoformat(),
        "parking_cost": cost,
        "status": "completed",
    })


@user_bp.get("/reservations/current")
@user_required
def current_reservation():
    user = g.current_user
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT r.id, pl.prime_location_name, ps.spot_number,
               r.parking_in, r.status
        FROM reservations r
        JOIN parking_lots pl ON r.lot_id = pl.id
        JOIN parking_spots ps ON r.spot_id = ps.id
        WHERE r.user_id = ? AND r.status = 'active'
        ORDER BY r.parking_in DESC
        LIMIT 1;
    """, (user["id"],))

    row = c.fetchone()
    db.close()

    if not row:
        return jsonify({"reservation": None})

    res_id, lot_name, spot_number, parking_in, status = row

    return jsonify({
        "reservation": {
            "id": res_id,
            "lot_name": lot_name,
            "spot_number": spot_number,
            "parking_in": parking_in,
            "status": status,
        }
    })


@user_bp.get("/reservations/history")
@user_required
def reservation_history():
    user = g.current_user
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT r.id, pl.prime_location_name, ps.spot_number,
               r.parking_in, r.parking_out, r.parking_cost, r.status
        FROM reservations r
        JOIN parking_lots pl ON r.lot_id = pl.id
        JOIN parking_spots ps ON r.spot_id = ps.id
        WHERE r.user_id = ?
        ORDER BY r.parking_in DESC;
    """, (user["id"],))

    rows = c.fetchall()
    db.close()

    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "lot_name": r[1],
            "spot_number": r[2],
            "parking_in": r[3],
            "parking_out": r[4],
            "parking_cost": r[5],
            "status": r[6],
        })

    return jsonify({"reservations": items})

@user_bp.post("/export-csv")
@user_required
def export_csv():
    user = g.current_user

    db = get_db()
    c = db.cursor()

    c.execute("""
        INSERT INTO exports (user_id, status, created_at)
        VALUES (?, 'pending', datetime('now'));
    """, (user["id"],))

    export_id = c.lastrowid
    db.commit()
    db.close()

    generate_csv.delay(export_id, user["id"])

    return jsonify({
        "export_id": export_id,
        "status": "processing"
    }), 202
