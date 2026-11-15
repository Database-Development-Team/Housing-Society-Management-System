
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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
