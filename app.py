
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
from datetime import date
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


# -----------------------------------------
# HOUSE MANAGEMENT - DELETE
# -----------------------------------------

@app.route("/houses/<int:house_id>/delete", methods=["GET", "POST"])
def delete_house(house_id):

    # Create the form security token if it is missing.
    if "house_csrf_token" not in session:
        session["house_csrf_token"] = secrets.token_urlsafe(32)

    # Retrieve house details and related record counts.
    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT H.HOUSE_NO,
                       H.STREET_NUMBER,
                       H.BLOCK_NAME,
                       O.FIRST_NAME,
                       O.LAST_NAME
                FROM HOUSE H
                JOIN OWNER O
                    ON H.OWNER_ID = O.OWNER_ID
                WHERE H.HOUSE_ID = :house_id
            """, {"house_id": house_id})

            record = cursor.fetchone()

            if record is None:
                abort(404)

            house = {
                "house_no": record[0],
                "street_number": record[1],
                "block_name": record[2],
                "owner_name": f"{record[3]} {record[4]}"
            }

            cursor.execute("""
                SELECT
                    (SELECT COUNT(*)
                     FROM LEASE
                     WHERE HOUSE_ID = :house_id),

                    (SELECT COUNT(*)
                     FROM RESIDENT
                     WHERE HOUSE_ID = :house_id),

                    (SELECT COUNT(*)
                     FROM VISITOR
                     WHERE HOUSE_ID = :house_id),

                    (SELECT COUNT(*)
                     FROM MAINTENANCE_BILL
                     WHERE HOUSE_ID = :house_id),

                    (SELECT COUNT(*)
                     FROM COMPLAINT
                     WHERE HOUSE_ID = :house_id),

                    (SELECT COUNT(*)
                     FROM BOOKING
                     WHERE HOUSE_ID = :house_id)
                FROM DUAL
            """, {"house_id": house_id})

            counts = cursor.fetchone()

    dependencies = dict(zip(
        (
            "Leases",
            "Residents",
            "Visitors",
            "Maintenance Bills",
            "Complaints",
            "Bookings"
        ),
        counts
    ))

    total_dependencies = sum(dependencies.values())
    has_dependencies = total_dependencies > 0

    # GET displays the confirmation page.
    # POST performs the deletion.
    if request.method == "POST":

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["house_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        if has_dependencies:
            flash(
                "Cannot delete this house because related "
                "records exist.",
                "warning"
            )
            return redirect(url_for("houses_page"))

        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:

                    cursor.execute("""
                        DELETE FROM HOUSE
                        WHERE HOUSE_ID = :house_id
                    """, {"house_id": house_id})

                    deleted_rows = cursor.rowcount

                    if deleted_rows == 1:
                        connection.commit()

            if deleted_rows == 0:
                abort(404)

            flash("House deleted successfully!", "success")
            return redirect(url_for("houses_page"))

        except oracledb.IntegrityError as exc:

            error_code = getattr(exc.args[0], "code", None)

            if error_code == 2292:
                flash(
                    "Deletion blocked: the house has "
                    "related database records.",
                    "warning"
                )
            else:
                app.logger.exception("House deletion failed")
                flash(
                    "Could not delete the house.",
                    "danger"
                )

            return redirect(url_for("houses_page"))

        except oracledb.DatabaseError:
            app.logger.exception("House deletion failed")

            flash(
                "Database error. House was not deleted.",
                "danger"
            )

            return redirect(url_for("houses_page"))

    return render_template(
        "house_delete.html",
        house_id=house_id,
        house=house,
        dependencies=dependencies,
        has_dependencies=has_dependencies,
        csrf_token=session["house_csrf_token"]
    )


# =========================================
# RESIDENT MANAGEMENT - READ
# =========================================

def fetch_residents():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    R.RESIDENT_ID,
                    R.FULL_NAME,
                    R.RELATION_TYPE,
                    R.CONTACT_NUMBER,
                    H.HOUSE_NO,
                    H.STREET_NUMBER,
                    H.BLOCK_NAME,

                    CASE
                        WHEN R.RELATION_TYPE = 'OWNER'
                        THEN O.FIRST_NAME || ' ' || O.LAST_NAME

                        WHEN R.RELATION_TYPE = 'TENANT'
                        THEN T.FULL_NAME

                        ELSE NULL
                    END AS LINKED_PERSON,

                    TO_CHAR(R.MOVE_IN_DATE, 'YYYY-MM-DD'),
                    TO_CHAR(R.MOVE_OUT_DATE, 'YYYY-MM-DD')

                FROM RESIDENT R

                JOIN HOUSE H
                    ON R.HOUSE_ID = H.HOUSE_ID

                LEFT JOIN OWNER O
                    ON R.OWNER_ID = O.OWNER_ID

                LEFT JOIN TENANT T
                    ON R.TENANT_ID = T.TENANT_ID

                ORDER BY R.RESIDENT_ID
            """)

            records = cursor.fetchall()

    residents = []

    for record in records:

        residents.append({
            "resident_id": record[0],
            "full_name": record[1],
            "relation_type": record[2],
            "contact_number": record[3],
            "house_no": record[4],
            "street_number": record[5],
            "block_name": record[6],
            "linked_person": record[7],
            "move_in_date": record[8],
            "move_out_date": record[9]
        })

    return residents


@app.route("/residents")
def residents_page():

    residents = fetch_residents()

    return render_template(
        "residents.html",
        residents=residents
    )



# =========================================
# RESIDENT MANAGEMENT - CREATE
# =========================================

def fetch_resident_form_options():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT HOUSE_ID, HOUSE_NO,
                       STREET_NUMBER, BLOCK_NAME
                FROM HOUSE
                ORDER BY BLOCK_NAME, STREET_NUMBER, HOUSE_NO
            """)

            houses = [
                {
                    "id": row[0],
                    "label": f"{row[1]}, Street {row[2]}, {row[3]}"
                }
                for row in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT TENANT_ID, FULL_NAME
                FROM TENANT
                ORDER BY FULL_NAME
            """)

            tenants = [
                {"id": row[0], "name": row[1]}
                for row in cursor.fetchall()
            ]

    return houses, tenants


@app.route("/residents/new", methods=["GET", "POST"])
def register_resident():

    houses, tenants = fetch_resident_form_options()

    if "resident_csrf_token" not in session:
        session["resident_csrf_token"] = secrets.token_urlsafe(32)

    fields = (
        "full_name",
        "cnic_number",
        "contact_number",
        "relation_type",
        "house_id",
        "tenant_id",
        "move_in_date"
    )

    values = {
        field: request.form.get(field, "").strip()
        for field in fields
    }

    if request.method == "GET":
        values["move_in_date"] = date.today().isoformat()

    error = None

    if request.method == "POST":

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["resident_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        cnic = values["cnic_number"].replace("-", "") or None
        role = values["relation_type"]

        house_ids = {
            str(house["id"]) for house in houses
        }

        tenant_ids = {
            str(tenant["id"]) for tenant in tenants
        }

        # Validate submitted information.
        if not values["full_name"] or len(values["full_name"]) > 100:
            error = "Full name is required (maximum 100 characters)."

        elif cnic and not re.fullmatch(r"[0-9]{13}", cnic):
            error = "CNIC must contain 13 digits (hyphens are optional)."

        elif len(values["contact_number"]) > 15:
            error = "Contact number cannot exceed 15 characters."

        elif role not in {"OWNER", "TENANT", "FAMILY_MEMBER", "OTHER"}:
            error = "Choose a valid relationship type."

        elif values["house_id"] not in house_ids:
            error = "Choose a registered house."

        elif role == "TENANT" and values["tenant_id"] not in tenant_ids:
            error = "Choose a registered tenant."

        else:
            try:
                if not re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                    values["move_in_date"]
                ):
                    raise ValueError

                move_date = date.fromisoformat(values["move_in_date"])

                if move_date > date.today():
                    error = "Move-in date cannot be in the future."

            except ValueError:
                error = "Enter a valid move-in date in YYYY-MM-DD format."

        if error is None:

            try:
                with get_connection() as connection:
                    with connection.cursor() as cursor:

                        house_id = int(values["house_id"])

                        # Lock the selected house while registering.
                        cursor.execute("""
                            SELECT OWNER_ID
                            FROM HOUSE
                            WHERE HOUSE_ID = :id
                            FOR UPDATE
                        """, {"id": house_id})

                        house_row = cursor.fetchone()

                        if house_row is None:
                            error = "Selected house no longer exists."

                        else:
                            house_owner_id = house_row[0]

                            cursor.execute("""
                                SELECT COUNT(*)
                                FROM RESIDENT
                                WHERE HOUSE_ID = :id
                                  AND MOVE_OUT_DATE IS NULL
                                  AND RELATION_TYPE IN ('OWNER', 'TENANT')
                            """, {"id": house_id})

                            primary_count = cursor.fetchone()[0]

                            owner_id = None
                            tenant_id = None

                            if role in {"OWNER", "TENANT"} and primary_count:
                                error = (
                                    "This house already has an active "
                                    "primary resident."
                                )

                            elif (
                                role in {"FAMILY_MEMBER", "OTHER"}
                                and not primary_count
                            ):
                                error = (
                                    "Register an active owner or tenant "
                                    "resident first."
                                )

                            elif role == "OWNER":

                                # Owner is determined by the selected house.
                                owner_id = house_owner_id

                                cursor.execute("""
                                    SELECT FIRST_NAME || ' ' || LAST_NAME,
                                           CNIC_NUMBER
                                    FROM OWNER
                                    WHERE OWNER_ID = :id
                                """, {"id": owner_id})

                                person = cursor.fetchone()

                                # An owner must not move in during
                                # an active lease term.
                                cursor.execute("""
                                    SELECT COUNT(*)
                                    FROM LEASE
                                    WHERE HOUSE_ID = :id
                                      AND LEASE_STATUS = 'ACTIVE'
                                      AND TRUNC(SYSDATE) BETWEEN
                                          TRUNC(LEASE_START_DATE)
                                          AND TRUNC(LEASE_END_DATE)
                                """, {"id": house_id})

                                active_lease = cursor.fetchone()[0]

                                if active_lease:
                                    error = (
                                        "An active lease currently "
                                        "exists for this house."
                                    )

                                elif (
                                    person is None
                                    or not cnic
                                    or " ".join(
                                        values["full_name"].upper().split()
                                    ) != " ".join(
                                        person[0].upper().split()
                                    )
                                    or cnic != person[1].replace("-", "")
                                ):
                                    error = (
                                        "Name and CNIC must match "
                                        "the house's registered owner."
                                    )

                            elif role == "TENANT":

                                tenant_id = int(values["tenant_id"])

                                cursor.execute("""
                                    SELECT FULL_NAME, CNIC_NUMBER
                                    FROM TENANT
                                    WHERE TENANT_ID = :id
                                """, {"id": tenant_id})

                                person = cursor.fetchone()

                                cursor.execute("""
                                    SELECT COUNT(*)
                                    FROM LEASE
                                    WHERE HOUSE_ID = :house_id
                                      AND TENANT_ID = :tenant_id
                                      AND LEASE_STATUS = 'ACTIVE'
                                      AND TRUNC(SYSDATE) BETWEEN
                                          TRUNC(LEASE_START_DATE)
                                          AND TRUNC(LEASE_END_DATE)
                                """, {
                                    "house_id": house_id,
                                    "tenant_id": tenant_id
                                })

                                active_lease = cursor.fetchone()[0]

                                if not active_lease:
                                    error = (
                                        "The tenant must have a current "
                                        "ACTIVE lease for this house."
                                    )

                                elif (
                                    person is None
                                    or not cnic
                                    or " ".join(
                                        values["full_name"].upper().split()
                                    ) != " ".join(
                                        person[0].upper().split()
                                    )
                                    or cnic != person[1].replace("-", "")
                                ):
                                    error = (
                                        "Name and CNIC must match "
                                        "the selected registered tenant."
                                    )

                            if error is None:

                                cursor.execute("""
                                    INSERT INTO RESIDENT (
                                        RESIDENT_ID,
                                        FULL_NAME,
                                        CNIC_NUMBER,
                                        CONTACT_NUMBER,
                                        RELATION_TYPE,
                                        MOVE_IN_DATE,
                                        HOUSE_ID,
                                        OWNER_ID,
                                        TENANT_ID
                                    )
                                    VALUES (
                                        SEQ_RESIDENT_ID.NEXTVAL,
                                        :name,
                                        :cnic,
                                        :phone,
                                        :role,
                                        TO_DATE(:move_date, 'YYYY-MM-DD'),
                                        :house_id,
                                        :owner_id,
                                        :tenant_id
                                    )
                                """, {
                                    "name": values["full_name"],
                                    "cnic": cnic,
                                    "phone": values["contact_number"] or None,
                                    "role": role,
                                    "move_date": values["move_in_date"],
                                    "house_id": house_id,
                                    "owner_id": owner_id,
                                    "tenant_id": tenant_id
                                })

                                # Synchronize occupancy for primary residents.
                                if role in {"OWNER", "TENANT"}:

                                    status = (
                                        "OWNER-OCCUPIED"
                                        if role == "OWNER"
                                        else "TENANT-OCCUPIED"
                                    )

                                    cursor.execute("""
                                        UPDATE HOUSE
                                        SET OCCUPANCY_STATUS = :status
                                        WHERE HOUSE_ID = :house_id
                                    """, {
                                        "status": status,
                                        "house_id": house_id
                                    })

                                connection.commit()

                if error is None:
                    flash("Resident registered successfully!", "success")
                    return redirect(url_for("residents_page"))

            except oracledb.IntegrityError as exc:

                code = getattr(exc.args[0], "code", None)

                if code == 1:
                    error = (
                        "Duplicate CNIC or resident ID. "
                        "Check the existing records and sequence."
                    )

                elif code == 2291:
                    error = (
                        "A linked house, owner, or tenant "
                        "no longer exists."
                    )

                else:
                    app.logger.exception("Resident registration failed")
                    error = "Could not register the resident."

            except oracledb.DatabaseError:
                app.logger.exception("Resident registration failed")
                error = "Database error. Resident was not registered."

    return render_template(
        "resident_form.html",
        values=values,
        houses=houses,
        tenants=tenants,
        error=error,
        csrf_token=session["resident_csrf_token"]
    )


# =========================================
# RESIDENT MANAGEMENT - UPDATE
# =========================================

def fetch_resident_for_edit(resident_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT R.FULL_NAME,
                       R.CNIC_NUMBER,
                       R.CONTACT_NUMBER,
                       R.RELATION_TYPE,
                       R.HOUSE_ID,
                       TO_CHAR(R.MOVE_IN_DATE, 'YYYY-MM-DD'),
                       TO_CHAR(R.MOVE_OUT_DATE, 'YYYY-MM-DD'),
                       H.HOUSE_NO,
                       H.STREET_NUMBER,
                       H.BLOCK_NAME
                FROM RESIDENT R
                JOIN HOUSE H ON R.HOUSE_ID = H.HOUSE_ID
                WHERE R.RESIDENT_ID = :resident_id
            """, {"resident_id": resident_id})

            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "full_name": row[0],
        "cnic_number": row[1],
        "contact_number": row[2],
        "relation_type": row[3],
        "house_id": row[4],
        "move_in_date": row[5],
        "move_out_date": row[6],
        "house_label": f"House {row[7]}, Street {row[8]}, {row[9]}"
    }


@app.route("/residents/<int:resident_id>/edit", methods=["GET", "POST"])
def edit_resident(resident_id):

    resident = fetch_resident_for_edit(resident_id)

    if resident is None:
        abort(404)

    if "resident_csrf_token" not in session:
        session["resident_csrf_token"] = secrets.token_urlsafe(32)

    editable_identity = resident["relation_type"] in {
        "FAMILY_MEMBER", "OTHER"
    }

    values = {
        "full_name": resident["full_name"],
        "cnic_number": resident["cnic_number"] or "",
        "contact_number": resident["contact_number"] or "",
        "move_out_date": resident["move_out_date"] or ""
    }

    error = None

    if request.method == "POST":

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["resident_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        values["contact_number"] = request.form.get(
            "contact_number", ""
        ).strip()

        values["move_out_date"] = request.form.get(
            "move_out_date", ""
        ).strip()

        if editable_identity:
            values["full_name"] = request.form.get(
                "full_name", ""
            ).strip()

            values["cnic_number"] = request.form.get(
                "cnic_number", ""
            ).strip()

        cnic = values["cnic_number"].replace("-", "") or None
        move_out = values["move_out_date"]

        # Validate editable fields.
        if editable_identity and not (
            1 <= len(values["full_name"]) <= 100
        ):
            error = "Full name is required (maximum 100 characters)."

        elif editable_identity and values["cnic_number"] and not re.fullmatch(
            r"(?:[0-9]{13}|[0-9]{5}-[0-9]{7}-[0-9])",
            values["cnic_number"]
        ):
            error = "CNIC must have 13 digits (optional standard hyphens)."

        elif len(values["contact_number"]) > 15:
            error = "Contact number cannot exceed 15 characters."

        elif (
            resident["move_out_date"]
            and move_out != resident["move_out_date"]
        ):
            error = "A recorded move-out date cannot be changed or cleared."

        elif move_out:
            try:
                if not re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                    move_out
                ):
                    raise ValueError("Invalid date format")

                parsed_date = date.fromisoformat(move_out)
                move_in_date = date.fromisoformat(
                    resident["move_in_date"]
                )

                if (
                    parsed_date < move_in_date
                    or parsed_date > date.today()
                ):
                    error = "Move-out must be between move-in and today."

            except ValueError:
                error = "Move-out date must be a valid YYYY-MM-DD date."

        if error is None:
            try:
                with get_connection() as connection:
                    with connection.cursor() as cursor:

                        # Use the same house lock as registration.
                        cursor.execute("""
                            SELECT HOUSE_ID
                            FROM HOUSE
                            WHERE HOUSE_ID = :house_id
                            FOR UPDATE
                        """, {"house_id": resident["house_id"]})

                        if cursor.fetchone() is None:
                            error = "The assigned house no longer exists."

                        else:
                            cursor.execute("""
                                SELECT RELATION_TYPE,
                                       HOUSE_ID,
                                       TO_CHAR(
                                           MOVE_OUT_DATE,
                                           'YYYY-MM-DD'
                                       )
                                FROM RESIDENT
                                WHERE RESIDENT_ID = :resident_id
                                FOR UPDATE
                            """, {"resident_id": resident_id})

                            current = cursor.fetchone()

                            if current is None or (
                                current[0] != resident["relation_type"]
                                or current[1] != resident["house_id"]
                                or current[2] != resident["move_out_date"]
                            ):
                                error = (
                                    "Resident details changed. "
                                    "Reload and try again."
                                )

                            new_move_out = bool(
                                move_out
                                and not resident["move_out_date"]
                            )

                            primary = resident["relation_type"] in {
                                "OWNER", "TENANT"
                            }

                            # A primary resident cannot leave active
                            # family members or others behind.
                            if error is None and new_move_out and primary:

                                cursor.execute("""
                                    SELECT COUNT(*)
                                    FROM RESIDENT
                                    WHERE HOUSE_ID = :house_id
                                      AND RESIDENT_ID <> :resident_id
                                      AND MOVE_OUT_DATE IS NULL
                                """, {
                                    "house_id": resident["house_id"],
                                    "resident_id": resident_id
                                })

                                if cursor.fetchone()[0] > 0:
                                    error = (
                                        "Move out the other active residents "
                                        "of this house first."
                                    )

                            if error is None:

                                cursor.execute("""
                                    UPDATE RESIDENT
                                    SET FULL_NAME = :full_name,
                                        CNIC_NUMBER = :cnic,
                                        CONTACT_NUMBER = :contact,
                                        MOVE_OUT_DATE = TO_DATE(
                                            :move_out, 'YYYY-MM-DD'
                                        )
                                    WHERE RESIDENT_ID = :resident_id
                                """, {
                                    "full_name": values["full_name"],
                                    "cnic": cnic,
                                    "contact":
                                        values["contact_number"] or None,
                                    "move_out": move_out or None,
                                    "resident_id": resident_id
                                })

                                # The last primary resident has moved out.
                                if primary and new_move_out:
                                    cursor.execute("""
                                        UPDATE HOUSE
                                        SET OCCUPANCY_STATUS = 'VACANT'
                                        WHERE HOUSE_ID = :house_id
                                    """, {
                                        "house_id": resident["house_id"]
                                    })

                                connection.commit()

                if error is None:
                    flash("Resident updated successfully!", "success")
                    return redirect(url_for("residents_page"))

            except oracledb.IntegrityError as exc:
                code = getattr(exc.args[0], "code", None)

                if code == 1:
                    error = "This CNIC is already used by another resident."
                else:
                    app.logger.exception("Resident update failed")
                    error = "Could not update the resident."

            except oracledb.DatabaseError:
                app.logger.exception("Resident update failed")
                error = "Database error. Resident was not updated."

    return render_template(
        "resident_edit.html",
        resident_id=resident_id,
        resident=resident,
        values=values,
        editable_identity=editable_identity,
        today=date.today().isoformat(),
        error=error,
        csrf_token=session["resident_csrf_token"]
    )


# =========================================
# RESIDENT MANAGEMENT - DELETE
# =========================================

def fetch_resident_for_delete(resident_id):

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    R.FULL_NAME,
                    R.RELATION_TYPE,
                    R.HOUSE_ID,
                    H.HOUSE_NO,
                    H.STREET_NUMBER,
                    H.BLOCK_NAME,
                    TO_CHAR(R.MOVE_OUT_DATE, 'YYYY-MM-DD'),
                    (
                        SELECT COUNT(*)
                        FROM VEHICLE V
                        WHERE V.RESIDENT_ID = R.RESIDENT_ID
                    ) AS VEHICLE_COUNT

                FROM RESIDENT R
                JOIN HOUSE H
                    ON R.HOUSE_ID = H.HOUSE_ID

                WHERE R.RESIDENT_ID = :resident_id
            """, {
                "resident_id": resident_id
            })

            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "full_name": row[0],
        "relation_type": row[1],
        "house_id": row[2],
        "house_no": row[3],
        "street_number": row[4],
        "block_name": row[5],
        "move_out_date": row[6],
        "vehicle_count": row[7]
    }


@app.route(
    "/residents/<int:resident_id>/delete",
    methods=["GET", "POST"]
)
def delete_resident(resident_id):

    resident = fetch_resident_for_delete(resident_id)

    if resident is None:
        abort(404)

    if "resident_csrf_token" not in session:
        session["resident_csrf_token"] = secrets.token_urlsafe(32)

    # GET: Display the confirmation page.
    if request.method == "GET":

        can_delete = (
            resident["move_out_date"] is not None
            and resident["vehicle_count"] == 0
        )

        return render_template(
            "resident_delete.html",
            resident_id=resident_id,
            resident=resident,
            can_delete=can_delete,
            csrf_token=session["resident_csrf_token"]
        )

    # POST: Validate the form security token.
    submitted_token = request.form.get("_csrf_token", "")

    if not hmac.compare_digest(
        session["resident_csrf_token"],
        submitted_token
    ):
        abort(400, "Invalid form security token.")

    error = None
    deleted_rows = 0

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:

                # First, identify the resident's house.
                cursor.execute("""
                    SELECT HOUSE_ID
                    FROM RESIDENT
                    WHERE RESIDENT_ID = :resident_id
                """, {
                    "resident_id": resident_id
                })

                house_row = cursor.fetchone()

                if house_row is None:
                    abort(404)

                house_id = house_row[0]

                # Lock the house first, consistent with
                # our Resident CREATE and UPDATE routes.
                cursor.execute("""
                    SELECT HOUSE_ID
                    FROM HOUSE
                    WHERE HOUSE_ID = :house_id
                    FOR UPDATE
                """, {
                    "house_id": house_id
                })

                if cursor.fetchone() is None:
                    abort(404)

                # Lock the resident and recheck move-out.
                cursor.execute("""
                    SELECT MOVE_OUT_DATE
                    FROM RESIDENT
                    WHERE RESIDENT_ID = :resident_id
                    FOR UPDATE
                """, {
                    "resident_id": resident_id
                })

                current = cursor.fetchone()

                if current is None:
                    abort(404)

                # Repeat the dependency check at POST time.
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM VEHICLE
                    WHERE RESIDENT_ID = :resident_id
                """, {
                    "resident_id": resident_id
                })

                vehicle_count = cursor.fetchone()[0]

                if current[0] is None:
                    error = (
                        "This resident is still active. "
                        "Record a move-out date before deletion."
                    )

                elif vehicle_count > 0:
                    error = (
                        "Cannot delete this resident because "
                        "registered vehicles are linked to them."
                    )

                else:
                    cursor.execute("""
                        DELETE FROM RESIDENT
                        WHERE RESIDENT_ID = :resident_id
                          AND MOVE_OUT_DATE IS NOT NULL
                    """, {
                        "resident_id": resident_id
                    })

                    deleted_rows = cursor.rowcount

                    if deleted_rows == 1:
                        connection.commit()

    except oracledb.IntegrityError as exc:

        error_code = getattr(exc.args[0], "code", None)

        if error_code == 2292:
            error = (
                "Deletion blocked because another database "
                "record references this resident."
            )
        else:
            app.logger.exception("Resident deletion failed")
            error = "Could not delete the resident."

    except oracledb.DatabaseError:

        app.logger.exception("Resident deletion failed")
        error = "Database error. Resident was not deleted."

    if error is not None:
        flash(error, "warning")
        return redirect(url_for("residents_page"))

    if deleted_rows == 0:
        abort(404)

    flash("Resident deleted successfully!", "success")
    return redirect(url_for("residents_page"))


# =========================================
# TENANT MANAGEMENT - READ
# =========================================

def fetch_tenants():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    T.TENANT_ID,
                    T.FULL_NAME,
                    T.CONTACT_NUMBER,
                    NVL(T.FAMILY_MEMBERS_COUNT, 0),
                    TO_CHAR(
                        T.REGISTRATION_DATE,
                        'YYYY-MM-DD'
                    ),

                    (
                        SELECT COUNT(*)
                        FROM LEASE L
                        WHERE L.TENANT_ID = T.TENANT_ID
                    ) AS LEASE_COUNT

                FROM TENANT T

                ORDER BY T.TENANT_ID
            """)

            records = cursor.fetchall()

    tenants = []

    for record in records:

        tenants.append({
            "tenant_id": record[0],
            "full_name": record[1],
            "contact_number": record[2],
            "family_members_count": record[3],
            "registration_date": record[4],
            "lease_count": record[5]
        })

    return tenants


@app.route("/tenants")
def tenants_page():

    tenants = fetch_tenants()

    return render_template(
        "tenants.html",
        tenants=tenants
    )


# =========================================
# TENANT MANAGEMENT - CREATE
# =========================================

@app.route("/tenants/new", methods=["GET", "POST"])
def register_tenant():

    # Generate a security token for this form.
    if "tenant_csrf_token" not in session:
        session["tenant_csrf_token"] = secrets.token_urlsafe(32)

    fields = (
        "full_name",
        "cnic_number",
        "contact_number",
        "family_members_count",
        "address_proof"
    )

    values = {
        field: request.form.get(field, "").strip()
        for field in fields
    }

    if request.method == "GET":
        values["family_members_count"] = "0"

    error = None

    if request.method == "POST":

        # ---------------------------------
        # CSRF VALIDATION
        # ---------------------------------

        submitted_token = request.form.get("_csrf_token", "")

        if not hmac.compare_digest(
            session["tenant_csrf_token"],
            submitted_token
        ):
            abort(400, "Invalid form security token.")

        # Normalize CNIC before storing.
        cnic = values["cnic_number"].replace("-", "")

        # ---------------------------------
        # INPUT VALIDATION
        # ---------------------------------

        if not values["full_name"]:
            error = "Full name is required."

        elif len(values["full_name"]) > 100:
            error = "Full name cannot exceed 100 characters."

        elif not re.fullmatch(
            r"(?:[0-9]{13}|[0-9]{5}-[0-9]{7}-[0-9])",
            values["cnic_number"]
        ):
            error = (
                "Enter a valid 13-digit CNIC, "
                "with or without standard hyphens."
            )

        elif len(values["contact_number"]) > 15:
            error = "Contact number cannot exceed 15 characters."

        elif not re.fullmatch(
            r"[0-9]{1,3}",
            values["family_members_count"]
        ):
            error = (
                "Family members count must be "
                "a whole number from 0 to 999."
            )

        elif len(values["address_proof"]) > 255:
            error = "Address proof reference is too long."

        # ---------------------------------
        # DATABASE INSERT
        # ---------------------------------

        if error is None:

            try:

                with get_connection() as connection:
                    with connection.cursor() as cursor:

                        # Check existing CNIC values,
                        # including previously stored
                        # hyphenated CNIC numbers.
                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM TENANT
                            WHERE REPLACE(
                                CNIC_NUMBER, '-', ''
                            ) = :cnic
                        """, {
                            "cnic": cnic
                        })

                        existing_count = cursor.fetchone()[0]

                        if existing_count > 0:
                            error = (
                                "A tenant with this CNIC "
                                "is already registered."
                            )

                        else:

                            cursor.execute("""
                                INSERT INTO TENANT (
                                    TENANT_ID,
                                    FULL_NAME,
                                    CNIC_NUMBER,
                                    CONTACT_NUMBER,
                                    FAMILY_MEMBERS_COUNT,
                                    ADDRESS_PROOF
                                )
                                VALUES (
                                    SEQ_TENANT_ID.NEXTVAL,
                                    :full_name,
                                    :cnic_number,
                                    :contact_number,
                                    :family_count,
                                    :address_proof
                                )
                            """, {
                                "full_name": values["full_name"],
                                "cnic_number": cnic,
                                "contact_number":
                                    values["contact_number"] or None,
                                "family_count":
                                    int(values["family_members_count"]),
                                "address_proof":
                                    values["address_proof"] or None
                            })

                            connection.commit()

                if error is None:

                    flash(
                        "Tenant registered successfully!",
                        "success"
                    )

                    return redirect(url_for("tenants_page"))

            except oracledb.IntegrityError as exc:

                error_code = getattr(exc.args[0], "code", None)

                if error_code == 1:
                    error = (
                        "Duplicate CNIC or tenant ID. "
                        "Check existing records and the sequence."
                    )

                else:
                    app.logger.exception(
                        "Tenant registration failed"
                    )
                    error = "Could not register the tenant."

            except oracledb.DatabaseError:

                app.logger.exception(
                    "Tenant registration failed"
                )

                error = (
                    "Database error. "
                    "Tenant was not registered."
                )

    return render_template(
        "tenant_form.html",
        values=values,
        error=error,
        csrf_token=session["tenant_csrf_token"]
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
