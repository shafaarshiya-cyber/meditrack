import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymysql
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )

@app.route("/")
def dashboard():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM equipment")
        total = cur.fetchone()["total"]

        cur.execute("SELECT status, COUNT(*) AS count FROM equipment GROUP BY status")
        by_status = cur.fetchall()

        cur.execute("""
            SELECT e.equipment_name, e.serial_number, m.next_due_date
            FROM maintenance_logs m
            JOIN equipment e ON e.equipment_id = m.equipment_id
            WHERE m.next_due_date < %s
            ORDER BY m.next_due_date ASC
        """, (date.today(),))
        overdue = cur.fetchall()
    conn.close()
    return render_template("dashboard.html", total=total, by_status=by_status, overdue=overdue)

@app.route("/equipment")
def equipment_list():
    department = request.args.get("department")
    status = request.args.get("status")
    query = "SELECT * FROM equipment WHERE 1=1"
    params = []
    if department:
        query += " AND department = %s"
        params.append(department)
    if status:
        query += " AND status = %s"
        params.append(status)

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(query, params)
        equipment = cur.fetchall()
    conn.close()
    return render_template("equipment_list.html", equipment=equipment)

@app.route("/equipment/new", methods=["GET", "POST"])
def equipment_new():
    if request.method == "POST":
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO equipment (equipment_name, serial_number, department, purchase_date, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                request.form["equipment_name"],
                request.form["serial_number"],
                request.form["department"],
                request.form["purchase_date"],
                request.form.get("status", "Active"),
            ))
        conn.commit()
        conn.close()
        return redirect(url_for("equipment_list"))
    return render_template("equipment_form.html")

@app.route("/equipment/<int:equipment_id>")
def equipment_detail(equipment_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM equipment WHERE equipment_id = %s", (equipment_id,))
        equipment = cur.fetchone()
        cur.execute("""
            SELECT * FROM maintenance_logs
            WHERE equipment_id = %s ORDER BY maintenance_date DESC
        """, (equipment_id,))
        logs = cur.fetchall()
    conn.close()
    return render_template("equipment_detail.html", equipment=equipment, logs=logs)

@app.route("/equipment/<int:equipment_id>/status", methods=["POST"])
def equipment_update_status(equipment_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("UPDATE equipment SET status = %s WHERE equipment_id = %s",
                     (request.form["status"], equipment_id))
    conn.commit()
    conn.close()
    return redirect(url_for("equipment_detail", equipment_id=equipment_id))

@app.route("/equipment/<int:equipment_id>/log/new", methods=["GET", "POST"])
def log_new(equipment_id):
    if request.method == "POST":
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO maintenance_logs
                    (equipment_id, maintenance_date, technician_name, issue_reported, resolution_notes, next_due_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                equipment_id,
                request.form["maintenance_date"],
                request.form["technician_name"],
                request.form["issue_reported"],
                request.form["resolution_notes"],
                request.form["next_due_date"],
            ))
        conn.commit()
        conn.close()
        return redirect(url_for("equipment_detail", equipment_id=equipment_id))
    return render_template("log_form.html", equipment_id=equipment_id)

# Stretch goal: JSON feed of overdue items
@app.route("/api/overdue")
def api_overdue():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT e.equipment_id, e.equipment_name, e.serial_number, m.next_due_date
            FROM maintenance_logs m
            JOIN equipment e ON e.equipment_id = m.equipment_id
            WHERE m.next_due_date < %s
        """, (date.today(),))
        overdue = cur.fetchall()
    conn.close()
    return jsonify(overdue)

if __name__ == "__main__":
    app.run(debug=True)