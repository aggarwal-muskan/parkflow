# Vehicle Parking App – Backend Design Notes

This document explains the current backend structure and logic in plain language.
It is meant for understanding and viva, not for the users of the app.

---

## 1. Overall Backend Structure

Python package: `backend/`

- `db.py` – helper to open and close SQLite connections.
- `models.py` – database schema and core helper functions.
- `routes/admin.py` – APIs that only the admin can use.
- `routes/auth.py` – login, registration, logout (to be implemented).
- `routes/user.py` – APIs for normal users (to be implemented).
- `config.py` – configuration (database path, redis url, secret key, etc.).
- `app.py` – creates the Flask app and registers blueprints.

The backend exposes REST APIs under `/api/...` and is meant to be used by a Vue.js frontend.

---

## 2. Database Schema (from models.py)

The database uses SQLite. Tables are created programmatically by `init_db()` in `models.py`.

### 2.1 `users` table

Stores both the single admin and all normal users.

Columns:
- `id` – primary key.
- `username` – unique login name.
- `password_hash` – password stored as a hash.
- `role` – either `"admin"` or `"user"`.
- `email` – optional contact.
- `phone` – optional contact.
- `is_active` – integer flag, 1 means active, 0 means blocked/deactivated.

A default admin is created if no admin exists:
- username: `admin`
- password: `admin123`
- email: `admin@parkingapp.com`

---

### 2.2 `parking_lots` table

Represents a physical parking lot.

Columns:
- `id` – primary key.
- `prime_location_name` – display name, e.g. "Mall Parking".
- `address` – address text.
- `pin_code` – postal code.
- `price_per_hour` – cost charged per hour.
- `number_of_spots` – total spots in this lot.
- `is_active` – 1 = usable, 0 = disabled.

Whenever a lot is created, the corresponding spots are inserted into `parking_spots`.

---

### 2.3 `parking_spots` table

Represents an individual parking spot inside a lot.

Columns:
- `id` – primary key.
- `lot_id` – foreign key to `parking_lots`.
- `spot_number` – numeric label like 1, 2, 3 within a lot.
- `status` – `'A'` for available, `'O'` for occupied.
- `level` – optional (e.g., basement level, floor).
- `remarks` – optional notes.

Constraint:
- Unique index on `(lot_id, spot_number)` so the same spot number in the same lot cannot be duplicated.

---

### 2.4 `reservations` table

Stores each parking session for a user.

Columns:
- `id` – primary key.
- `user_id` – foreign key to `users`.
- `lot_id` – foreign key to `parking_lots`.
- `spot_id` – foreign key to `parking_spots`.
- `parking_in` – start time as ISO string.
- `parking_out` – end time as ISO string (can be `NULL` while active).
- `parking_cost` – final cost for the session.
- `status` – `"active"`, `"completed"`, or `"cancelled"`.

Used for:
- user history,
- monthly reports,
- CSV exports.

---

### 2.5 `task_status` table

General-purpose table to track long-running background tasks such as CSV exports or monthly reports.

Columns:
- `id` – primary key.
- `user_id` – foreign key to `users`.
- `task_id` – Celery task ID or some async job reference.
- `task_type` – e.g. `"csv_export"`, `"monthly_report"`.
- `status` – `"pending"`, `"running"`, `"done"`, `"failed"`.
- `file_path` – where the generated file is stored (if any).
- `created_at` – timestamp of when the task row was created.

---

### 2.6 `exports` table

Keeps history of generated export files for a user.

Columns:
- `id` – primary key.
- `user_id` – foreign key to `users`.
- `file_path` – file path of the export.
- `status` – `"pending"`, `"ready"`, or `"failed"`.
- `created_at` – timestamp.

---

## 3. Core Functions in models.py

These functions encapsulate common database operations so that route files do not need to write raw SQL everywhere.

### 3.1 `init_db()`

- Opens a database connection.
- Creates all required tables if they do not exist.
- Ensures a default admin user is present.
- Commits changes and closes the connection.
- Intended to be called once at application start-up.

### 3.2 `create_parking_lot(name, address, pin_code, price, spot_count)`

- Inserts a new row into `parking_lots` with the given information.
- Automatically inserts `spot_count` rows into `parking_spots` for that lot with spot numbers from 1 to `spot_count`.
- Returns the `id` of the newly created lot.

Used by admin routes when the admin adds a new parking lot.

---

### 3.3 `get_lot_summary()`

- For each active parking lot, computes:
  - total number of spots (from `number_of_spots`),
  - number of occupied spots,
  - number of available spots.
- Returns a list of dictionaries, each representing a lot and its current usage.

Useful for the admin dashboard overview.

---

### 3.4 `find_first_available_spot(lot_id)`

- Looks up the first spot in `parking_spots` for a given `lot_id` where `status = 'A'`.
- Returns one row (id, lot_id, spot_number, status) or `None` if no free spot exists.

Used by user routes when a user requests to reserve a parking space.

---

### 3.5 `mark_spot_status(spot_id, status)`

- Updates the `status` field in `parking_spots` for the given `spot_id`.
- Typical statuses:
  - `'O'` when a reservation starts (occupied),
  - `'A'` when a reservation ends (available).

---

## 4. Admin API Endpoints (routes/admin.py)

Blueprint name: `admin_bp`  
Base prefix (in app.py): `/api/admin`

Authorization:
- All endpoints use the `admin_required` decorator.
- The decorator expects `g.current_user` to be set with at least a `"role"` field.
- If the user is not an admin, the API returns HTTP 403.

### 4.1 `GET /api/admin/parking-lots/summary`

- Uses `get_lot_summary()` from `models.py`.
- Response: list of lots with occupancy and availability.
- Purpose: feed data to admin dashboard (cards + table).

---

### 4.2 `GET /api/admin/parking-lots`

- Returns basic information for all parking lots:
  - id, name, address, pin code, price per hour, total spots, active flag.
- Sorted by `prime_location_name`.

Used for admin lot management screens.

---

### 4.3 `POST /api/admin/parking-lots`

Request body (JSON):
- `prime_location_name` (required)
- `address` (optional)
- `pin_code` (optional)
- `price_per_hour` (required, numeric)
- `number_of_spots` (required, positive integer)

Behaviour:
- Validates required fields and their types.
- Calls `create_parking_lot(...)`.
- Returns the new lot id and a success message.

Used when the admin creates a new parking lot.

---

### 4.4 `PUT /api/admin/parking-lots/<lot_id>`

Request body can contain any of:
- `prime_location_name`
- `address`
- `pin_code`
- `price_per_hour`
- `is_active` (boolean)

Behaviour:
- Builds an `UPDATE` statement only for fields that are present.
- Updates the corresponding row in `parking_lots`.

Used when admin edits an existing parking lot.

---

### 4.5 `DELETE /api/admin/parking-lots/<lot_id>`

Behaviour:
- Checks if any spot in the lot has `status = 'O'`.
- If yes, returns error saying the lot cannot be deleted while spots are occupied.
- If all spots are free:
  - deletes rows from `parking_spots` for that lot,
  - deletes the row from `parking_lots`.

Used when admin wants to fully remove a parking lot.

---

### 4.6 `GET /api/admin/parking-lots/<lot_id>/spots`

- Lists all spots in a given lot:
  - id, spot number, status, level, remarks.
- Sorted by spot number.

Used for a detailed view of a single parking lot.

---

### 4.7 `GET /api/admin/users`

- Lists all users (not only admins):
  - id, username, email, phone, role, active flag.
- Sorted by username.

Used for admin to review who is using the system.

---

### 4.8 `GET /api/admin/dashboard-summary`

- Returns aggregate numbers:
  - total_lots
  - total_spots
  - occupied_spots
  - available_spots
  - total_users (only users with `role = 'user'`)

This is another convenient endpoint for the admin home dashboard.

---
