import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymysql
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


# DATABASE CONNECTION
def get_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )


# CREATE TABLES AUTOMATICALLY
def create_tables():

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment(

            equipment_id INT AUTO_INCREMENT PRIMARY KEY,

            equipment_name VARCHAR(100),

            serial_number VARCHAR(50) UNIQUE,

            department VARCHAR(100),

            purchase_date DATE,

            status VARCHAR(50)

        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_logs(

            log_id INT AUTO_INCREMENT PRIMARY KEY,

            equipment_id INT,

            maintenance_date DATE,

            technician_name VARCHAR(100),

            issue_reported TEXT,

            resolution_notes TEXT,

            next_due_date DATE,

            FOREIGN KEY (equipment_id)
            REFERENCES equipment(equipment_id)

        )
        """)

    conn.commit()
    conn.close()



# DASHBOARD
@app.route("/")
def dashboard():

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute("""
        SELECT COUNT(*) total
        FROM equipment
        """)

        total = cur.fetchone()["total"]

        cur.execute("""
        SELECT status,
        COUNT(*) count
        FROM equipment
        GROUP BY status
        """)

        by_status = cur.fetchall()

        cur.execute("""
        SELECT
        e.equipment_name,
        e.serial_number,
        m.next_due_date

        FROM maintenance_logs m

        JOIN equipment e
        ON e.equipment_id=m.equipment_id

        WHERE m.next_due_date<%s
        """, (date.today(),))

        overdue = cur.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        by_status=by_status,
        overdue=overdue
    )



# EQUIPMENT LIST
@app.route("/equipment")
def equipment_list():

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute("""
        SELECT *
        FROM equipment
        """)

        equipment = cur.fetchall()

    conn.close()

    return render_template(
        "equipment_list.html",
        equipment=equipment
    )



# ADD EQUIPMENT
@app.route(
    "/equipment/new",
    methods=["GET", "POST"]
)

def equipment_new():

    if request.method == "POST":

        conn = get_db()

        with conn.cursor() as cur:

            cur.execute("""
            INSERT INTO equipment(

            equipment_name,
            serial_number,
            department,
            purchase_date,
            status

            )

            VALUES(%s,%s,%s,%s,%s)
            """,

            (

            request.form["equipment_name"],

            request.form["serial_number"],

            request.form["department"],

            request.form["purchase_date"],

            request.form["status"]

            ))

        conn.commit()

        conn.close()

        return redirect("/equipment")

    return render_template(
        "equipment_form.html"
    )



# DETAIL PAGE
@app.route("/equipment/<int:equipment_id>")

def equipment_detail(
    equipment_id
):

    conn = get_db()

    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT *
            FROM equipment

            WHERE equipment_id=%s
            """,

            (equipment_id,)
        )

        equipment = cur.fetchone()

        cur.execute(
            """
            SELECT *
            FROM maintenance_logs

            WHERE equipment_id=%s
            """,

            (equipment_id,)
        )

        logs = cur.fetchall()

    conn.close()

    return render_template(

        "equipment_detail.html",

        equipment=equipment,

        logs=logs
    )



# ADD MAINTENANCE
@app.route(
"/equipment/<int:equipment_id>/log/new",
methods=["GET","POST"]
)

def log_new(
equipment_id
):

    if request.method=="POST":

        conn=get_db()

        with conn.cursor() as cur:

            cur.execute("""

            INSERT INTO maintenance_logs(

            equipment_id,

            maintenance_date,

            technician_name,

            issue_reported,

            resolution_notes,

            next_due_date

            )

            VALUES(%s,%s,%s,%s,%s,%s)

            """,

            (

            equipment_id,

            request.form["maintenance_date"],

            request.form["technician_name"],

            request.form["issue_reported"],

            request.form["resolution_notes"],

            request.form["next_due_date"]

            ))

        conn.commit()

        conn.close()

        return redirect(
            url_for(
                "equipment_detail",
                equipment_id=equipment_id
            )
        )

    return render_template(
        "log_form.html",
        equipment_id=equipment_id
    )



# API
@app.route("/api/overdue")

def api_overdue():

    return jsonify(
        {
            "status":"ok"
        }
    )



if __name__=="__main__":

    create_tables()

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )