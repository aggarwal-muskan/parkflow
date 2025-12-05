from backend.celery_app import celery
from backend.db import get_db
from datetime import date
from backend.emailer import send_email


@celery.task(name="daily_user_reminder")
def daily_user_reminder():
    """
    Send an email reminder to users who have not parked today.
    """
    today = date.today().isoformat()

    db = get_db()
    c = db.cursor()

    # id, username, email
    c.execute("SELECT id, username, email FROM users WHERE role = 'user';")
    users = c.fetchall()

    for user_id, username, email in users:
        if not email:
            continue  # skip users without email

        c.execute("""
            SELECT id FROM reservations
            WHERE user_id = ? AND DATE(parking_in) = ?
        """, (user_id, today))

        parked_today = c.fetchone()

        if parked_today:
            continue

        send_email(
            to=email,
            subject="Daily Parking Reminder",
            html=f"""
            <p>Hello <b>{username}</b>,</p>
            <p>You haven’t used the parking lots today.</p>
            <p>If you need parking, you can reserve a spot via the app.</p>
            """,
        )

    db.close()
    return "Daily reminders sent"
