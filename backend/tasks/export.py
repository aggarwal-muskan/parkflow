from backend.celery_app import celery
from backend.db import get_db
import csv
import os


@celery.task(name="backend.tasks.export.generate_csv")
def generate_csv(export_id, user_id):
    """
    Celery task that generates a CSV file of all reservations
    for a given user and returns the file path.
    """
    db = get_db()
    c = db.cursor()

    c.execute("""
        SELECT r.id, pl.prime_location_name, ps.spot_number,
               r.parking_in, r.parking_out, r.parking_cost, r.status
        FROM reservations r
        JOIN parking_lots pl ON r.lot_id = pl.id
        JOIN parking_spots ps ON r.spot_id = ps.id
        WHERE r.user_id = ?
        ORDER BY r.parking_in;
    """, (user_id,))

    rows = c.fetchall()
    db.close()

    export_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(export_dir, f"export_{export_id}.csv")

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Lot", "Spot", "Start", "End", "Cost", "Status"])
        for r in rows:
            writer.writerow(r)

    print(f"[EXPORT] CSV generated for user {user_id}: {file_path}")
    return file_path
