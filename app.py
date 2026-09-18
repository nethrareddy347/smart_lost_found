from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory
)

from flask_cors import CORS

from werkzeug.utils import secure_filename

from database import (
    init_db,
    get_db
)



import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from ai_matching import find_ai_matches

import os
import uuid


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

init_db()


# =========================================================
# HELPER
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({

        "message":
        "Smart Lost & Found Backend is running!",

        "status":
        "success"

    })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({

        "status":
        "healthy"

    })


# =========================================================
# CREATE REPORT WITHOUT PHOTO
# =========================================================

@app.route(
    "/report",
    methods=["POST"]
)
def create_report():

    data = request.get_json()

    if not data:

        return jsonify({

            "error":
            "No data received"

        }), 400

    item_type = data.get(
        "item_type"
    )

    name = data.get(
        "name"
    )

    description = data.get(
        "description"
    )

    location = data.get(
        "location"
    )

    category = data.get(
        "category"
    )

    report_date = data.get(
        "report_date"
    )

    contact = data.get(
        "contact",
        ""
    )

    # -----------------------------------------------------
    # VALIDATE REQUIRED FIELDS
    # -----------------------------------------------------

    if not all([

        item_type,
        name,
        description,
        location,
        category,
        report_date

    ]):

        return jsonify({

            "error":
            "Please provide all required fields"

        }), 400

    # -----------------------------------------------------
    # VALIDATE ITEM TYPE
    # -----------------------------------------------------

    if item_type not in [
        "lost",
        "found"
    ]:

        return jsonify({

            "error":
            "item_type must be lost or found"

        }), 400

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    db = get_db()

    cursor = db.execute("""

        INSERT INTO reports
        (
            item_type,
            name,
            description,
            location,
            category,
            report_date,
            contact,
            photo
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        item_type,
        name,
        description,
        location,
        category,
        report_date,
        contact,
        ""

    ))

    db.commit()

    report_id = cursor.lastrowid

    db.close()

    return jsonify({

        "message":
        "Report created successfully!",

        "report_id":
        report_id

    }), 201


# =========================================================
# CREATE REPORT WITH PHOTO
# =========================================================

@app.route(
    "/report-with-photo",
    methods=["POST"]
)
def create_report_with_photo():

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

    item_type = request.form.get(
        "item_type"
    )

    name = request.form.get(
        "name"
    )

    description = request.form.get(
        "description"
    )

    location = request.form.get(
        "location"
    )

    category = request.form.get(
        "category"
    )

    report_date = request.form.get(
        "report_date"
    )

    contact = request.form.get(
        "contact",
        ""
    )

    # -----------------------------------------------------
    # VALIDATE REQUIRED FIELDS
    # -----------------------------------------------------

    if not all([

        item_type,
        name,
        description,
        location,
        category,
        report_date

    ]):

        return jsonify({

            "error":
            "Please provide all required fields"

        }), 400

    # -----------------------------------------------------
    # VALIDATE ITEM TYPE
    # -----------------------------------------------------

    if item_type not in [
        "lost",
        "found"
    ]:

        return jsonify({

            "error":
            "item_type must be lost or found"

        }), 400

    # -----------------------------------------------------
    # CHECK PHOTO
    # -----------------------------------------------------

    if "photo" not in request.files:

        return jsonify({

            "error":
            "Please upload a photo"

        }), 400

    photo = request.files["photo"]

    if photo.filename == "":

        return jsonify({

            "error":
            "No photo selected"

        }), 400

    # -----------------------------------------------------
    # VALIDATE PHOTO EXTENSION
    # -----------------------------------------------------

    if not allowed_file(
        photo.filename
    ):

        return jsonify({

            "error":
            "Only JPG, JPEG, PNG and WEBP images are allowed"

        }), 400

    # -----------------------------------------------------
    # CREATE UNIQUE PHOTO NAME
    # -----------------------------------------------------

    original_name = secure_filename(
        photo.filename
    )

    extension = original_name.rsplit(
        ".",
        1
    )[1].lower()

    unique_name = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    photo_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_name
    )

    # -----------------------------------------------------
    # SAVE PHOTO
    # -----------------------------------------------------

    photo.save(
        photo_path
    )

    # -----------------------------------------------------
    # SAVE REPORT
    # -----------------------------------------------------

    db = get_db()

    cursor = db.execute("""

        INSERT INTO reports
        (
            item_type,
            name,
            description,
            location,
            category,
            report_date,
            contact,
            photo
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        item_type,
        name,
        description,
        location,
        category,
        report_date,
        contact,
        unique_name

    ))

    db.commit()

    report_id = cursor.lastrowid

    db.close()

    return jsonify({

        "message":
        "Report with photo created successfully!",

        "report_id":
        report_id,

        "photo":
        unique_name

    }), 201


# =========================================================
# GET ALL REPORTS
# =========================================================

@app.route(
    "/reports",
    methods=["GET"]
)
def get_reports():

    db = get_db()

    rows = db.execute("""

        SELECT *
        FROM reports
        ORDER BY id DESC

    """).fetchall()

    db.close()

    reports = [

        dict(row)

        for row in rows

    ]

    return jsonify(
        reports
    )


# =========================================================
# GET SINGLE REPORT
# =========================================================

@app.route(
    "/reports/<int:report_id>",
    methods=["GET"]
)
def get_report(report_id):

    db = get_db()

    row = db.execute("""

        SELECT *
        FROM reports
        WHERE id = ?

    """, (

        report_id,

    )).fetchone()

    db.close()

    if row is None:

        return jsonify({

            "error":
            "Report not found"

        }), 404

    return jsonify(
        dict(row)
    )


# =========================================================
# SERVE UPLOADED PHOTOS
# =========================================================

@app.route(
    "/uploads/<filename>"
)
def uploaded_file(filename):

    return send_from_directory(

        app.config["UPLOAD_FOLDER"],

        filename

    )


# =========================================================
# GET AI MATCHES
# =========================================================

@app.route("/matches", methods=["GET"]
)
def get_matches():

    db = get_db()

    # -----------------------------------------------------
    # GET REPORTS
    # -----------------------------------------------------

    rows = db.execute("""

        SELECT *
        FROM reports
        ORDER BY id DESC

    """).fetchall()

    reports = [

        dict(row)

        for row in rows

    ]

    # -----------------------------------------------------
    # RUN AI MATCHING
    # -----------------------------------------------------

    matches = find_ai_matches(

        reports,

        app.config[
            "UPLOAD_FOLDER"
        ]

    )

    # -----------------------------------------------------
    # LOAD SAVED STATUS
    # -----------------------------------------------------

    for match in matches:

        status_row = db.execute("""

            SELECT status
            FROM match_status
            WHERE match_id = ?

        """, (

            match["id"],

        )).fetchone()

        if status_row:

            match["status"] = (
                status_row["status"]
            )

        else:

            match["status"] = "potential"

            db.execute("""

                INSERT OR IGNORE INTO
                match_status
                (
                    match_id,
                    status
                )

                VALUES (?, ?)

            """, (

                match["id"],
                "potential"

            ))

    db.commit()

    db.close()

    return jsonify(
        matches
    )


# =========================================================
# UPDATE MATCH STATUS
# =========================================================

@app.route(
    "/matches/<match_id>/status",
    methods=["PATCH"]
)
def update_match_status(match_id):

    data = request.get_json()

    if not data:

        return jsonify({

            "error":
            "Status is required"

        }), 400

    if "status" not in data:

        return jsonify({

            "error":
            "Status is required"

        }), 400

    status = data["status"]

    # -----------------------------------------------------
    # VALID STATUS VALUES
    # -----------------------------------------------------

    if status not in [
        "verified",
        "returned"
    ]:

        return jsonify({

            "error":
            "Invalid status"

        }), 400

    # -----------------------------------------------------
    # SAVE STATUS
    # -----------------------------------------------------

    db = get_db()

    db.execute("""

        INSERT INTO match_status
        (
            match_id,
            status
        )

        VALUES (?, ?)

        ON CONFLICT(match_id)
        DO UPDATE SET
            status = excluded.status

    """, (

        match_id,
        status

    ))

    db.commit()

    db.close()

    return jsonify({

        "message":
        f"Match status updated to {status}",

        "status":
        status

    })


# ==============================
# DASHBOARD STATISTICS
# ==============================

@app.route("/stats", methods=["GET"])
def get_stats():

    db = get_db()

    # ==============================
    # COUNT LOST REPORTS
    # ==============================

    lost_reports = db.execute("""
        SELECT COUNT(*)
        FROM reports
        WHERE item_type = 'lost'
    """).fetchone()[0]

    # ==============================
    # COUNT FOUND REPORTS
    # ==============================

    found_reports = db.execute("""
        SELECT COUNT(*)
        FROM reports
        WHERE item_type = 'found'
    """).fetchone()[0]

    # ==============================
    # GET ALL REPORTS
    # ==============================

    rows = db.execute("""
        SELECT *
        FROM reports
        ORDER BY id DESC
    """).fetchall()

    reports = [dict(row) for row in rows]

    # ==============================
    # AI MATCHING
    # ==============================

    matches = find_ai_matches(
        reports,
        app.config["UPLOAD_FOLDER"]
    )

    total_matches = len(matches)

    # ==============================
    # VERIFIED MATCHES
    # ==============================

    verified_matches = db.execute("""
        SELECT COUNT(*)
        FROM match_status
        WHERE status = 'verified'
    """).fetchone()[0]

    # ==============================
    # RETURNED ITEMS
    # ==============================

    returned_items = db.execute("""
        SELECT COUNT(*)
        FROM match_status
        WHERE status = 'returned'
    """).fetchone()[0]

    db.close()

    # ==============================
    # RETURN STATISTICS
    # ==============================

    return jsonify({
        "lost_reports": lost_reports,
        "found_reports": found_reports,
        "total_matches": total_matches,
        "verified_matches": verified_matches,
        "returned_items": returned_items
    })
@app.route("/dashboard.html")
def dashboard_page():
    return send_from_directory(BASE_DIR, "dashboard.html")
if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )