
import os
import re
import hmac
import secrets

import oracledb
from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, jsonify, redirect,
    render_template, request, session, url_for
)

from db import get_connection

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]


def fetch_owners():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT OWNER_ID, FIRST_NAME, LAST_NAME,
                       MOBILE_NUMBER, EMAIL_ADDRESS
                FROM OWNER
                ORDER BY OWNER_ID
            """)
            records = cursor.fetchall()

    owners = []

    for record in records:
        owners.append({
            "owner_id": record[0],
            "first_name": record[1],
            "last_name": record[2],
            "mobile_number": record[3],
            "email_address": record[4]
        })

    return owners


@app.route("/")
def home():
    return jsonify({
        "application": "Housing Society Management System",
        "status": "running"
    })


@app.route("/owners")
def owners_page():
    return render_template(
        "owners.html",
        owners=fetch_owners()
    )


@app.route("/api/owners")
def owners_api():
    return jsonify(fetch_owners())


@app.route("/owners/new", methods=["GET", "POST"])
def register_owner():

    if "owner_csrf_token" not in session:
        session["owner_csrf_token"] = secrets.token_urlsafe(32)

    fields = (
        "first_name", "last_name", "cnic_number",
        "mobile_number", "email_address"
    )

    values = {
        field: request.form.get(field, "").strip()
        for field in fields
    }

    error = None

    if request.method == "POST":

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["owner_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        first_name = values["first_name"]
        last_name = values["last_name"]
        cnic = values["cnic_number"]
        mobile = values["mobile_number"]
        email = values["email_address"]

        if not first_name or not last_name or not cnic:
            error = "First name, last name and CNIC are required."

        elif len(first_name) > 50 or len(last_name) > 50:
            error = "Names must not exceed 50 characters."

        elif not re.fullmatch(
            r"(?:[0-9]{13}|[0-9]{5}-[0-9]{7}-[0-9])",
            cnic
        ):
            error = "Enter a valid 13-digit CNIC."

        elif len(mobile) > 15:
            error = "Mobile number must not exceed 15 characters."

        elif len(email) > 100 or (email and "@" not in email):
            error = "Enter a valid email address."

        else:
            # Store CNIC consistently without hyphens.
            cnic = cnic.replace("-", "")

            try:
                with get_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO OWNER (
                                OWNER_ID,
                                FIRST_NAME,
                                LAST_NAME,
                                CNIC_NUMBER,
                                MOBILE_NUMBER,
                                EMAIL_ADDRESS
                            )
                            VALUES (
                                SEQ_OWNER_ID.NEXTVAL,
                                :first_name,
                                :last_name,
                                :cnic_number,
                                :mobile_number,
                                :email_address
                            )
                        """, {
                            "first_name": first_name,
                            "last_name": last_name,
                            "cnic_number": cnic,
                            "mobile_number": mobile or None,
                            "email_address": email or None
                        })

                    connection.commit()

                flash("Owner registered successfully!", "success")
                return redirect(url_for("owners_page"))

            except oracledb.IntegrityError as exc:
                if exc.args[0].code == 1:
                    error = (
                        "A unique value already exists. "
                        "Check the CNIC or owner ID sequence."
                    )
                else:
                    app.logger.exception("Owner registration failed")
                    error = "Could not register the owner."

            except oracledb.DatabaseError:
                app.logger.exception("Owner registration failed")
                error = "Database error. Please try again."

    return render_template(
        "owner_form.html",
        values=values,
        error=error,
        csrf_token=session["owner_csrf_token"]
    )

@app.route("/owners/<int:owner_id>/edit", methods=["GET", "POST"])
def edit_owner(owner_id):

    # Retrieve the existing owner.
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT FIRST_NAME, LAST_NAME, CNIC_NUMBER,
                       MOBILE_NUMBER, EMAIL_ADDRESS
                FROM OWNER
                WHERE OWNER_ID = :owner_id
            """, {"owner_id": owner_id})

            owner = cursor.fetchone()

    if owner is None:
        abort(404)

    # Reuse the form security token.
    if "owner_csrf_token" not in session:
        session["owner_csrf_token"] = secrets.token_urlsafe(32)

    values = {
        "first_name": owner[0],
        "last_name": owner[1],
        "cnic_number": owner[2],
        "mobile_number": owner[3] or "",
        "email_address": owner[4] or ""
    }

    error = None

    if request.method == "POST":

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["owner_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        for field in (
            "first_name", "last_name",
            "mobile_number", "email_address"
        ):
            values[field] = request.form.get(field, "").strip()

        if not values["first_name"] or not values["last_name"]:
            error = "First and last names are required."

        elif (
            len(values["first_name"]) > 50
            or len(values["last_name"]) > 50
        ):
            error = "Names cannot exceed 50 characters."

        elif len(values["mobile_number"]) > 15:
            error = "Mobile number is too long."

        elif (
            len(values["email_address"]) > 100
            or (
                values["email_address"]
                and "@" not in values["email_address"]
            )
        ):
            error = "Enter a valid email address."

        else:
            try:
                with get_connection() as connection:
                    with connection.cursor() as cursor:

                        cursor.execute("""
                            UPDATE OWNER
                            SET FIRST_NAME = :first_name,
                                LAST_NAME = :last_name,
                                MOBILE_NUMBER = :mobile_number,
                                EMAIL_ADDRESS = :email_address
                            WHERE OWNER_ID = :owner_id
                        """, {
                            "first_name": values["first_name"],
                            "last_name": values["last_name"],
                            "mobile_number": values["mobile_number"] or None,
                            "email_address": values["email_address"] or None,
                            "owner_id": owner_id
                        })

                        if cursor.rowcount == 0:
                            abort(404)

                    connection.commit()

                flash("Owner updated successfully!", "success")
                return redirect(url_for("owners_page"))

            except oracledb.DatabaseError:
                app.logger.exception("Owner update failed")
                error = "Database error. Owner was not updated."

    return render_template(
        "owner_edit.html",
        owner_id=owner_id,
        values=values,
        error=error,
        csrf_token=session["owner_csrf_token"]
    )

@app.route("/owners/<int:owner_id>/delete", methods=["GET", "POST"])
def delete_owner(owner_id):

    # Create a security token for the confirmation form.
    if "owner_csrf_token" not in session:
        session["owner_csrf_token"] = secrets.token_urlsafe(32)

    # Find the owner and check related records.
    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT FIRST_NAME, LAST_NAME
                FROM OWNER
                WHERE OWNER_ID = :owner_id
            """, {"owner_id": owner_id})

            owner = cursor.fetchone()

            if owner is None:
                abort(404)

            cursor.execute("""
                SELECT COUNT(*)
                FROM HOUSE
                WHERE OWNER_ID = :owner_id
            """, {"owner_id": owner_id})

            house_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM RESIDENT
                WHERE OWNER_ID = :owner_id
            """, {"owner_id": owner_id})

            resident_count = cursor.fetchone()[0]

    has_dependencies = house_count > 0 or resident_count > 0

    if request.method == "POST":

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["owner_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        if has_dependencies:
            flash(
                "Cannot delete this owner because related "
                "house or resident records exist.",
                "warning"
            )
            return redirect(url_for("owners_page"))

        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:

                    cursor.execute("""
                        DELETE FROM OWNER
                        WHERE OWNER_ID = :owner_id
                    """, {"owner_id": owner_id})

                    deleted_rows = cursor.rowcount

                if deleted_rows == 1:
                    connection.commit()

            if deleted_rows == 0:
                abort(404)

            flash("Owner deleted successfully!", "success")
            return redirect(url_for("owners_page"))

        except oracledb.DatabaseError as exc:

            error_code = getattr(exc.args[0], "code", None)

            if error_code == 2292:
                flash(
                    "Deletion blocked: related records exist.",
                    "warning"
                )
            else:
                app.logger.exception("Owner deletion failed")
                flash(
                    "Database error. Owner was not deleted.",
                    "danger"
                )

            return redirect(url_for("owners_page"))

    return render_template(
        "owner_delete.html",
        owner_id=owner_id,
        owner=owner,
        house_count=house_count,
        resident_count=resident_count,
        has_dependencies=has_dependencies,
        csrf_token=session["owner_csrf_token"]
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
