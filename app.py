
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
from decimal import Decimal, InvalidOperation

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

# -----------------------------------------
# HOUSE MANAGEMENT - READ
# -----------------------------------------

def fetch_houses():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    H.HOUSE_ID,
                    H.HOUSE_NO,
                    H.STREET_NUMBER,
                    H.BLOCK_NAME,
                    H.SIZE_IN_MARLA,
                    H.CONSTRUCTION_STATUS,
                    H.OCCUPANCY_STATUS,
                    O.OWNER_ID,
                    O.FIRST_NAME,
                    O.LAST_NAME
                FROM HOUSE H
                JOIN OWNER O
                    ON H.OWNER_ID = O.OWNER_ID
                ORDER BY H.HOUSE_ID
            """)

            records = cursor.fetchall()

    houses = []

    for record in records:
        houses.append({
            "house_id": record[0],
            "house_no": record[1],
            "street_number": record[2],
            "block_name": record[3],
            "size_in_marla": record[4],
            "construction_status": record[5],
            "occupancy_status": record[6],
            "owner_id": record[7],
            "owner_name": f"{record[8]} {record[9]}"
        })

    return houses


@app.route("/houses")
def houses_page():
    houses = fetch_houses()

    return render_template(
        "houses.html",
        houses=houses
    )


# -----------------------------------------
# HOUSE MANAGEMENT - CREATE
# -----------------------------------------

@app.route("/houses/new", methods=["GET", "POST"])
def register_house():

    owners = fetch_owners()

    if "house_csrf_token" not in session:
        session["house_csrf_token"] = secrets.token_urlsafe(32)

    fields = (
        "house_no",
        "street_number",
        "block_name",
        "size_in_marla",
        "construction_status",
        "owner_id"
    )

    values = {
        field: request.form.get(field, "").strip()
        for field in fields
    }

    if request.method == "GET":
        values["construction_status"] = "COMPLETED"

    error = None

    if request.method == "POST":

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["house_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        # Normalize location values before saving.
        values["house_no"] = values["house_no"].upper()
        values["street_number"] = values["street_number"].upper()
        values["block_name"] = values["block_name"].upper()

        valid_owner_ids = {
            str(owner["owner_id"]) for owner in owners
        }

        allowed_statuses = {
            "COMPLETED",
            "UNDER_CONSTRUCTION",
            "RENOVATING"
        }

        if any(not values[field] for field in fields):
            error = "All fields are required."

        elif (
            len(values["house_no"]) > 20
            or len(values["street_number"]) > 20
            or len(values["block_name"]) > 50
        ):
            error = "House location information is too long."

        elif values["owner_id"] not in valid_owner_ids:
            error = "Please select a registered owner."

        elif values["construction_status"] not in allowed_statuses:
            error = "Invalid construction status."

        else:
            try:
                size = Decimal(values["size_in_marla"])

                if (
                    not size.is_finite()
                    or size <= 0
                    or size > Decimal("9999.99")
                    or size.as_tuple().exponent < -2
                ):
                    error = (
                        "House size must be positive, at most "
                        "9999.99, with up to two decimal places."
                    )

            except InvalidOperation:
                error = "Enter a valid numeric house size."

        if error is None:
            try:
                with get_connection() as connection:
                    with connection.cursor() as cursor:

                        cursor.execute("""
                            INSERT INTO HOUSE (
                                HOUSE_ID,
                                HOUSE_NO,
                                STREET_NUMBER,
                                BLOCK_NAME,
                                SIZE_IN_MARLA,
                                CONSTRUCTION_STATUS,
                                OCCUPANCY_STATUS,
                                OWNER_ID
                            )
                            VALUES (
                                SEQ_HOUSE_ID.NEXTVAL,
                                :house_no,
                                :street_number,
                                :block_name,
                                :size_in_marla,
                                :construction_status,
                                'VACANT',
                                :owner_id
                            )
                        """, {
                            "house_no": values["house_no"],
                            "street_number": values["street_number"],
                            "block_name": values["block_name"],
                            "size_in_marla": size,
                            "construction_status":
                                values["construction_status"],
                            "owner_id": int(values["owner_id"])
                        })

                    connection.commit()

                flash("House registered successfully!", "success")
                return redirect(url_for("houses_page"))

            except oracledb.IntegrityError as exc:
                error_code = getattr(exc.args[0], "code", None)

                if error_code == 1:
                    error = (
                        "This property location already exists, "
                        "or its generated ID conflicts with a record."
                    )

                elif error_code == 2291:
                    error = "The selected owner no longer exists."

                else:
                    app.logger.exception("House registration failed")
                    error = "Could not register the house."

            except oracledb.DatabaseError:
                app.logger.exception("House registration failed")
                error = "Database error. House was not registered."

    return render_template(
        "house_form.html",
        owners=owners,
        values=values,
        error=error,
        csrf_token=session["house_csrf_token"]
    )


# -----------------------------------------
# HOUSE MANAGEMENT - UPDATE
# -----------------------------------------

@app.route("/houses/<int:house_id>/edit", methods=["GET", "POST"])
def edit_house(house_id):

    owners = fetch_owners()

    # Fetch the existing house details.
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT HOUSE_NO,
                       STREET_NUMBER,
                       BLOCK_NAME,
                       SIZE_IN_MARLA,
                       CONSTRUCTION_STATUS,
                       OCCUPANCY_STATUS,
                       OWNER_ID
                FROM HOUSE
                WHERE HOUSE_ID = :house_id
            """, {"house_id": house_id})

            house = cursor.fetchone()

    if house is None:
        abort(404)

    original_owner_id = house[6]

    if "house_csrf_token" not in session:
        session["house_csrf_token"] = secrets.token_urlsafe(32)

    values = {
        "house_no": house[0],
        "street_number": house[1],
        "block_name": house[2],
        "size_in_marla": str(house[3]),
        "construction_status": house[4],
        "occupancy_status": house[5],
        "owner_id": str(house[6])
    }

    error = None

    if request.method == "POST":

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["house_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        for field in (
            "house_no",
            "street_number",
            "block_name",
            "size_in_marla",
            "construction_status",
            "owner_id"
        ):
            values[field] = request.form.get(field, "").strip()

        values["house_no"] = values["house_no"].upper()
        values["street_number"] = values["street_number"].upper()
        values["block_name"] = values["block_name"].upper()

        valid_owner_ids = {
            str(owner["owner_id"]) for owner in owners
        }

        valid_statuses = {
            "COMPLETED",
            "UNDER_CONSTRUCTION",
            "RENOVATING"
        }

        if any(not values[field] for field in (
            "house_no",
            "street_number",
            "block_name",
            "size_in_marla",
            "construction_status",
            "owner_id"
        )):
            error = "All fields are required."

        elif (
            len(values["house_no"]) > 20
            or len(values["street_number"]) > 20
            or len(values["block_name"]) > 50
        ):
            error = "Property location information is too long."

        elif values["construction_status"] not in valid_statuses:
            error = "Invalid construction status."

        elif values["owner_id"] not in valid_owner_ids:
            error = "Please select a registered owner."

        else:
            try:
                size = Decimal(values["size_in_marla"])

                if (
                    not size.is_finite()
                    or size <= 0
                    or size > Decimal("9999.99")
                    or size.as_tuple().exponent < -2
                ):
                    error = "Enter a valid size up to 9999.99 marla."

            except InvalidOperation:
                error = "House size must be numeric."

        if error is None:

            try:
                with get_connection() as connection:
                    with connection.cursor() as cursor:

                        # Prevent changing the owner while
                        # resident or lease records exist.
                        if int(values["owner_id"]) != original_owner_id:

                            cursor.execute("""
                                SELECT
                                    (SELECT COUNT(*)
                                     FROM RESIDENT
                                     WHERE HOUSE_ID = :house_id)
                                    +
                                    (SELECT COUNT(*)
                                     FROM LEASE
                                     WHERE HOUSE_ID = :house_id)
                                FROM DUAL
                            """, {"house_id": house_id})

                            dependencies = cursor.fetchone()[0]

                            if dependencies > 0:
                                error = (
                                    "Cannot change the owner while "
                                    "resident or lease records exist."
                                )

                        if error is None:
                            cursor.execute("""
                                UPDATE HOUSE
                                SET HOUSE_NO = :house_no,
                                    STREET_NUMBER = :street_number,
                                    BLOCK_NAME = :block_name,
                                    SIZE_IN_MARLA = :size_in_marla,
                                    CONSTRUCTION_STATUS =
                                        :construction_status,
                                    OWNER_ID = :owner_id
                                WHERE HOUSE_ID = :house_id
                            """, {
                                "house_no": values["house_no"],
                                "street_number": values["street_number"],
                                "block_name": values["block_name"],
                                "size_in_marla": size,
                                "construction_status":
                                    values["construction_status"],
                                "owner_id": int(values["owner_id"]),
                                "house_id": house_id
                            })

                            updated_rows = cursor.rowcount

                            if updated_rows == 1:
                                connection.commit()

                if error is None:
                    if updated_rows == 0:
                        abort(404)

                    flash("House updated successfully!", "success")
                    return redirect(url_for("houses_page"))

            except oracledb.IntegrityError as exc:

                code = getattr(exc.args[0], "code", None)

                if code == 1:
                    error = (
                        "Another house already uses this "
                        "block, street and house number."
                    )

                elif code == 2291:
                    error = "Selected owner no longer exists."

                else:
                    app.logger.exception("House update failed")
                    error = "Could not update the house."

            except oracledb.DatabaseError:
                app.logger.exception("House update failed")
                error = "Database error. House was not updated."

    return render_template(
        "house_edit.html",
        house_id=house_id,
        owners=owners,
        values=values,
        error=error,
        csrf_token=session["house_csrf_token"]
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
