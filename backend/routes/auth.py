from flask import Blueprint, request, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash

from backend.db import get_db

auth_bp = Blueprint("auth", __name__)


def load_user(user_id):
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT id, username, role, email, phone, is_active
        FROM users
        WHERE id = ?;
    """, (user_id,))

    row = c.fetchone()
    db.close()

    if not row:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "role": row[2],
        "email": row[3],
        "phone": row[4],
        "is_active": bool(row[5]),
    }


@auth_bp.before_app_request
def attach_current_user():
    user_id = session.get("user_id")
    if not user_id:
        g.current_user = None
        return

    user = load_user(user_id)
    g.current_user = user


@auth_bp.post("/register")
def register():
    data = request.get_json(force=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    if len(username) < 3:
        return jsonify({"error": "username must be at least 3 characters"}), 400

    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400

    db = get_db()
    c = db.cursor()

    c.execute("SELECT id FROM users WHERE username = ?;", (username,))
    existing = c.fetchone()
    if existing:
        db.close()
        return jsonify({"error": "username is already taken"}), 400

    password_hash = generate_password_hash(password)

    c.execute("""
        INSERT INTO users (username, password_hash, role, email, phone, is_active)
        VALUES (?, ?, 'user', ?, ?, 1);
    """, (username, password_hash, email, phone))

    db.commit()
    db.close()

    return jsonify({"message": "user registered successfully"}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT id, username, password_hash, role, is_active
        FROM users
        WHERE username = ?;
    """, (username,))

    row = c.fetchone()
    db.close()

    if not row:
        return jsonify({"error": "invalid username or password"}), 401

    user_id, uname, pwd_hash, role, is_active = row

    if not is_active:
        return jsonify({"error": "account is disabled"}), 403

    if not check_password_hash(pwd_hash, password):
        return jsonify({"error": "invalid username or password"}), 401

    session["user_id"] = user_id

    return jsonify({
        "message": "login successful",
        "username": uname,
        "role": role,
    })


@auth_bp.post("/logout")
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "logged out"})


@auth_bp.get("/me")
def me():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"user": None}), 200

    return jsonify({
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "email": user["email"],
            "phone": user["phone"],
            "is_active": user["is_active"],
        }
    })
