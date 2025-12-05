from backend.celery_app import celery
from backend.db import get_db
from backend.emailer import send_email
from datetime import date
from collections import Counter


@celery.task(name="monthly_report")
def monthly_report():
    """
    Sends monthly activity report to all users who had activity this month.
    """
    today = date.today()
    month_str = today.strftime("%B %Y")

    db = get_db()
    c = db.cursor()

    c.execute("SELECT id, username, email FROM users WHERE role = 'user';")
    users = c.fetchall()

    for user_id, username, email in users:
        if not email:
            continue

        c.execute("""
            SELECT pl.prime_location_name, r.parking_cost
            FROM reservations r
            JOIN parking_lots pl ON r.lot_id = pl.id
            WHERE r.user_id = ?
              AND strftime('%Y-%m', r.parking_in) = strftime('%Y-%m', 'now')
        """, (user_id,))

        rows = c.fetchall()
        if not rows:
            continue

        lots = [r[0] for r in rows]
        costs = [r[1] or 0 for r in rows]

        most_used = Counter(lots).most_common(1)[0][0]
        total_spent = sum(costs)
        total_rides = len(rows)

        html = f"""
        <h2>Your Parking Report - {month_str}</h2>
        <p><b>Total visits:</b> {total_rides}</p>
        <p><b>Most used parking lot:</b> {most_used}</p>
        <p><b>Total amount spent:</b> ₹ {total_spent:.2f}</p>
        <hr>
        <p>Thank you for using the Vehicle Parking App!</p>
        """

        send_email(
            to=email,
            subject=f"Monthly Parking Report - {month_str}",
            html=html,
        )

    db.close()
    return "Monthly reports sent"
