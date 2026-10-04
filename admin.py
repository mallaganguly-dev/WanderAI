"""
WanderAI - Admin authentication and admin panel

Registered on the Flask app in web.py as the "admin" blueprint.

Default credentials come from .env:

    ADMIN_EMAIL=admin@wanderai.com
    ADMIN_PASSWORD=change-me-now
"""

import os
import sqlite3
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from werkzeug.security import check_password_hash, generate_password_hash


load_dotenv()

try:
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


DATABASE = "wanderai.db"


MAIN_ADMIN_EMAIL = os.getenv(
    "MAIN_ADMIN_EMAIL",
    "hari@gmail.com"
)

MAIN_ADMIN_PASSWORD = os.getenv(
    "MAIN_ADMIN_PASSWORD",
    "hari@1234"
)


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ==================================================
# ADMIN DATABASE
# ==================================================

def get_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def init_admin_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_access INTEGER DEFAULT 1,
            is_main_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Add is_main_admin to databases created before it existed

    cursor.execute(
        "PRAGMA table_info(admins)"
    )

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "is_main_admin" not in columns:

        cursor.execute(
            """
            ALTER TABLE admins
            ADD COLUMN is_main_admin INTEGER DEFAULT 0
            """
        )

    connection.commit()
    connection.close()


def count_admins():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM admins"
    )

    total = cursor.fetchone()[0]

    connection.close()

    return total


def count_main_admins():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM admins
        WHERE is_main_admin = 1
        """
    )

    total = cursor.fetchone()[0]

    connection.close()

    return total


def create_admin(
    email,
    password,
    full_access=1,
    is_main_admin=0
):

    email = email.strip().lower()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM admins
        WHERE email = ?
        """,
        (email,)
    )

    if cursor.fetchone():

        connection.close()

        return False

    cursor.execute(
        """
        INSERT INTO admins
        (
            email,
            password_hash,
            full_access,
            is_main_admin
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            email,
            generate_password_hash(password),
            1 if full_access else 0,
            1 if is_main_admin else 0
        )
    )

    connection.commit()
    connection.close()

    return True


def get_admin(email):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM admins
        WHERE email = ?
        """,
        (email.strip().lower(),)
    )

    admin = cursor.fetchone()

    connection.close()

    return admin


def get_admin_by_id(admin_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM admins
        WHERE id = ?
        """,
        (admin_id,)
    )

    admin = cursor.fetchone()

    connection.close()

    return admin


def get_all_admins():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            email,
            full_access,
            is_main_admin,
            created_at,
            last_login
        FROM admins
        ORDER BY is_main_admin DESC, created_at ASC
        """
    )

    admins = cursor.fetchall()

    connection.close()

    return admins


def verify_admin_credentials(email, password):

    admin = get_admin(email)

    if not admin:
        return None

    if not check_password_hash(
        admin["password_hash"],
        password
    ):
        return None

    return admin


def update_admin_login_time(admin_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE admins
        SET last_login = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (admin_id,)
    )

    connection.commit()
    connection.close()


def set_admin_full_access(admin_id, full_access):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE admins
        SET full_access = ?
        WHERE id = ?
        """,
        (1 if full_access else 0, admin_id)
    )

    connection.commit()
    connection.close()


def delete_admin(admin_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM admins
        WHERE id = ?
        AND is_main_admin = 0
        """,
        (admin_id,)
    )

    connection.commit()
    connection.close()


def ensure_main_admin():

    init_admin_database()

    if count_main_admins() > 0:
        return

    if get_admin(MAIN_ADMIN_EMAIL):

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE admins
            SET is_main_admin = 1,
                full_access = 1
            WHERE email = ?
            """,
            (MAIN_ADMIN_EMAIL.strip().lower(),)
        )

        connection.commit()
        connection.close()

        return

    create_admin(
        MAIN_ADMIN_EMAIL,
        MAIN_ADMIN_PASSWORD,
        full_access=1,
        is_main_admin=1
    )

    print(
        f"🔐 Main admin created: "
        f"{MAIN_ADMIN_EMAIL}"
    )


def update_admin_password(admin_id, new_password):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE admins
        SET password_hash = ?
        WHERE id = ?
        """,
        (
            generate_password_hash(new_password),
            admin_id
        )
    )

    connection.commit()
    connection.close()


# ==================================================
# ADMIN STATISTICS
# ==================================================

def get_admin_stats():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) FROM trips
        """
    )

    total_trips = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(DISTINCT destination)
        FROM trips
        """
    )

    total_destinations = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COALESCE(SUM(budget), 0)
        FROM trips
        """
    )

    total_budget = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT destination, COUNT(*) AS trip_count
        FROM trips
        GROUP BY destination
        ORDER BY trip_count DESC
        LIMIT 5
        """
    )

    top_destinations = cursor.fetchall()

    cursor.execute(
        """
        SELECT travel_style, COUNT(*) AS style_count
        FROM trips
        WHERE travel_style IS NOT NULL
        GROUP BY travel_style
        ORDER BY style_count DESC
        """
    )

    travel_styles = cursor.fetchall()

    connection.close()

    return {
        "total_trips": total_trips,
        "total_destinations": total_destinations,
        "total_budget": round(total_budget, 2),
        "top_destinations": top_destinations,
        "travel_styles": travel_styles
    }


def get_all_trips():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            destination,
            days,
            budget,
            interests,
            travel_style,
            created_at
        FROM trips
        ORDER BY created_at DESC
        """
    )

    trips = cursor.fetchall()

    connection.close()

    return trips


def get_trip_by_id(trip_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM trips
        WHERE id = ?
        """,
        (trip_id,)
    )

    trip = cursor.fetchone()

    connection.close()

    return trip


def delete_trip(trip_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM trips
        WHERE id = ?
        """,
        (trip_id,)
    )

    deleted = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted > 0


def delete_all_trips():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM trips"
    )

    deleted = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted


# ==================================================
# ADMIN SESSION HELPERS
# ==================================================

def is_admin_logged_in():

    return bool(
        session.get("admin_id")
    )


def current_admin():

    admin_id = session.get("admin_id")

    if not admin_id:
        return None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, email, full_access, is_main_admin
        FROM admins
        WHERE id = ?
        """,
        (admin_id,)
    )

    admin = cursor.fetchone()

    connection.close()

    return admin


def is_main_admin():

    admin = current_admin()

    if not admin:
        return False

    return bool(admin["is_main_admin"])


def admin_required(view_function):

    @wraps(view_function)
    def wrapper(*args, **kwargs):

        if not is_admin_logged_in():

            return redirect(
                url_for("admin.admin_login")
            )

        return view_function(
            *args,
            **kwargs
        )

    return wrapper


def main_admin_required(view_function):

    @wraps(view_function)
    def wrapper(*args, **kwargs):

        if not is_admin_logged_in():

            return redirect(
                url_for("admin.admin_login")
            )

        if not is_main_admin():

            return render_template(
                "admin_denied.html"
            ), 403

        return view_function(
            *args,
            **kwargs
        )

    return wrapper


# ==================================================
# ADMIN ROUTES
# ==================================================

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():

    if is_admin_logged_in():

        return redirect(
            url_for("admin.admin_dashboard")
        )

    error = None

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            error = "Email and password are required."

        else:

            admin = verify_admin_credentials(
                email,
                password
            )

            if admin:

                session["admin_id"] = admin["id"]
                session["admin_email"] = admin["email"]
                session.permanent = True

                update_admin_login_time(admin["id"])

                return redirect(
                    url_for("admin.admin_dashboard")
                )

            error = "Invalid admin credentials."

    return render_template(
        "admin_login.html",
        error=error
    )


@admin_bp.route("/logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_email", None)

    return redirect(
        url_for("admin.admin_login")
    )


@admin_bp.route("/")
@admin_required
def admin_dashboard():

    return render_template(
        "admin_dashboard.html",
        admin=current_admin(),
        stats=get_admin_stats(),
        trips=get_all_trips(),
        admins=get_all_admins()
    )


@admin_bp.route("/trip/<int:trip_id>")
@admin_required
def admin_view_trip(trip_id):

    trip = get_trip_by_id(trip_id)

    if not trip:

        return "Trip not found", 404

    return render_template(
        "result.html",
        destination=trip["destination"],
        from_location="",
        days=trip["days"],
        budget=trip["budget"],
        interests=trip["interests"],
        travel_style=trip["travel_style"],
        itinerary=trip["itinerary"],
        weather=None,
        currency=None,
        admin_mode=True
    )


@admin_bp.route("/trip/<int:trip_id>/delete", methods=["POST"])
@admin_required
def admin_delete_trip(trip_id):

    delete_trip(trip_id)

    flash("Trip deleted.", "success")

    return redirect(
        url_for("admin.admin_dashboard")
    )


@admin_bp.route("/trips/delete-all", methods=["POST"])
@admin_required
def admin_delete_all_trips():

    deleted = delete_all_trips()

    flash(
        f"{deleted} trips deleted.",
        "success"
    )

    return redirect(
        url_for("admin.admin_dashboard")
    )


@admin_bp.route("/admins/add", methods=["POST"])
@main_admin_required
def admin_add_admin():

    email = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    if not email or not password:

        flash(
            "Email and password are required.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    if len(password) < 6:

        flash(
            "Password must be at least 6 characters.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    if create_admin(email, password):

        flash(
            f"Admin {email} added.",
            "success"
        )

    else:

        flash(
            "That admin already exists.",
            "error"
        )

    return redirect(
        url_for("admin.admin_dashboard")
    )


@admin_bp.route(
    "/admins/<int:admin_id>/access",
    methods=["POST"]
)
@main_admin_required
def admin_toggle_access(admin_id):

    actor = current_admin()

    if not actor:
        return redirect(
            url_for("admin.admin_dashboard")
        )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT full_access, is_main_admin
        FROM admins
        WHERE id = ?
        """,
        (admin_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if not row:

        flash("Admin not found.", "error")

        return redirect(
            url_for("admin.admin_dashboard")
        )

    if row["is_main_admin"]:

        flash(
            "The main admin always keeps full access.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    if admin_id == actor["id"] and row["full_access"]:

        flash(
            "You cannot remove your own full access.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    set_admin_full_access(
        admin_id,
        not row["full_access"]
    )

    flash(
        "Full access updated.",
        "success"
    )

    return redirect(
        url_for("admin.admin_dashboard")
    )


@admin_bp.route(
    "/admins/<int:admin_id>/delete",
    methods=["POST"]
)
@main_admin_required
def admin_delete_admin(admin_id):

    actor = current_admin()

    if not actor:
        return redirect(
            url_for("admin.admin_dashboard")
        )

    if admin_id == actor["id"]:

        flash(
            "You cannot delete your own account.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    delete_admin(admin_id)

    flash("Admin deleted.", "success")

    return redirect(
        url_for("admin.admin_dashboard")
    )


@admin_bp.route(
    "/admins/<int:admin_id>/password",
    methods=["POST"]
)
@admin_required
def admin_change_password(admin_id):

    actor = current_admin()

    if not actor:
        return redirect(
            url_for("admin.admin_dashboard")
        )

    target = get_admin_by_id(admin_id)

    if not target:

        flash(
            "Admin not found.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    # Only the main admin can change another admin's password

    if (
        target["id"] != actor["id"]
        and not actor["is_main_admin"]
    ):

        flash(
            "Only the main admin can change "
            "another admin's password.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    new_password = request.form.get(
        "new_password",
        ""
    )

    if len(new_password) < 6:

        flash(
            "Password must be at least 6 characters.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    update_admin_password(
        admin_id,
        new_password
    )

    flash("Password updated.", "success")

    return redirect(
        url_for("admin.admin_dashboard")
    )


@admin_bp.route("/admins/my-password", methods=["POST"])
@admin_required
def admin_change_own_password():

    admin = current_admin()

    if not admin:
        return redirect(
            url_for("admin.admin_login")
        )

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirmed_password = request.form.get(
        "confirm_password",
        ""
    )

    existing = get_admin_by_id(admin["id"])

    if not check_password_hash(
        existing["password_hash"],
        current_password
    ):

        flash(
            "Current password is incorrect.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    if len(new_password) < 6:

        flash(
            "New password must be at least "
            "6 characters.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    if new_password != confirmed_password:

        flash(
            "New passwords do not match.",
            "error"
        )

        return redirect(
            url_for("admin.admin_dashboard")
        )

    update_admin_password(
        admin["id"],
        new_password
    )

    flash(
        "Your password has been updated.",
        "success"
    )

    return redirect(
        url_for("admin.admin_dashboard")
    )