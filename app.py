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

 if __name__ == "__main__":

    create_tables()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )