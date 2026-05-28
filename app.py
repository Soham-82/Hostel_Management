from datetime import date
import sqlite3

from flask import Flask, redirect, render_template, request, url_for


app = Flask(__name__)
DB_NAME = "hostel.db"


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    with connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT UNIQUE NOT NULL,
                capacity INTEGER NOT NULL,
                occupied INTEGER NOT NULL DEFAULT 0,
                monthly_fee REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                guardian_name TEXT NOT NULL,
                guardian_phone TEXT NOT NULL,
                admission_date TEXT NOT NULL,
                room_id INTEGER,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                complaint_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
            """
        )


@app.template_filter("money")
def money(value):
    return f"Rs. {float(value or 0):,.2f}"


@app.route("/")
def dashboard():
    with connect_db() as conn:
        stats = conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM rooms) AS rooms,
              (SELECT COALESCE(SUM(capacity), 0) FROM rooms) AS capacity,
              (SELECT COALESCE(SUM(occupied), 0) FROM rooms) AS occupied,
              (SELECT COUNT(*) FROM students WHERE status = 'active') AS active_students,
              (SELECT COALESCE(SUM(amount), 0) FROM payments) AS payments,
              (SELECT COUNT(*) FROM complaints WHERE status = 'open') AS complaints
            """
        ).fetchone()
        recent_students = conn.execute(
            """
            SELECT students.name, students.phone, students.status,
                   COALESCE(rooms.room_number, 'Not allocated') AS room_number
            FROM students
            LEFT JOIN rooms ON students.room_id = rooms.id
            ORDER BY students.id DESC
            LIMIT 5
            """
        ).fetchall()

    return render_template("dashboard.html", stats=stats, recent_students=recent_students)


@app.route("/rooms")
def rooms():
    with connect_db() as conn:
        all_rooms = conn.execute("SELECT * FROM rooms ORDER BY room_number").fetchall()
    return render_template("rooms.html", rooms=all_rooms)


@app.route("/rooms/add", methods=["POST"])
def add_room():
    with connect_db() as conn:
        conn.execute(
            "INSERT INTO rooms (room_number, capacity, monthly_fee) VALUES (?, ?, ?)",
            (
                request.form["room_number"],
                int(request.form["capacity"]),
                float(request.form["monthly_fee"]),
            ),
        )
    return redirect(url_for("rooms"))


@app.route("/students")
def students():
    with connect_db() as conn:
        all_students = conn.execute(
            """
            SELECT students.*, COALESCE(rooms.room_number, 'Not allocated') AS room_number
            FROM students
            LEFT JOIN rooms ON students.room_id = rooms.id
            ORDER BY students.id DESC
            """
        ).fetchall()
        available_rooms = conn.execute(
            "SELECT id, room_number FROM rooms WHERE occupied < capacity ORDER BY room_number"
        ).fetchall()
    return render_template(
        "students.html",
        students=all_students,
        available_rooms=available_rooms,
    )


@app.route("/students/add", methods=["POST"])
def add_student():
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO students
            (name, phone, guardian_name, guardian_phone, admission_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                request.form["name"],
                request.form["phone"],
                request.form["guardian_name"],
                request.form["guardian_phone"],
                date.today().isoformat(),
            ),
        )
    return redirect(url_for("students"))


@app.route("/students/allocate", methods=["POST"])
def allocate_room():
    student_id = int(request.form["student_id"])
    room_id = int(request.form["room_id"])

    with connect_db() as conn:
        room = conn.execute(
            "SELECT capacity, occupied FROM rooms WHERE id = ?",
            (room_id,),
        ).fetchone()
        student = conn.execute(
            "SELECT room_id, status FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()

        if room and student and student["room_id"] is None and room["occupied"] < room["capacity"]:
            conn.execute("UPDATE students SET room_id = ? WHERE id = ?", (room_id, student_id))
            conn.execute("UPDATE rooms SET occupied = occupied + 1 WHERE id = ?", (room_id,))

    return redirect(url_for("students"))


@app.route("/students/vacate", methods=["POST"])
def vacate_room():
    student_id = int(request.form["student_id"])

    with connect_db() as conn:
        student = conn.execute(
            "SELECT room_id FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()

        if student and student["room_id"]:
            conn.execute("UPDATE rooms SET occupied = occupied - 1 WHERE id = ?", (student["room_id"],))
            conn.execute(
                "UPDATE students SET room_id = NULL, status = 'inactive' WHERE id = ?",
                (student_id,),
            )

    return redirect(url_for("students"))


@app.route("/payments")
def payments():
    with connect_db() as conn:
        active_students = conn.execute(
            "SELECT id, name FROM students WHERE status = 'active' ORDER BY name"
        ).fetchall()
        all_payments = conn.execute(
            """
            SELECT payments.*, students.name
            FROM payments
            JOIN students ON students.id = payments.student_id
            ORDER BY payments.payment_date DESC, payments.id DESC
            """
        ).fetchall()
    return render_template("payments.html", students=active_students, payments=all_payments)


@app.route("/payments/add", methods=["POST"])
def add_payment():
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO payments (student_id, amount, payment_date, note)
            VALUES (?, ?, ?, ?)
            """,
            (
                int(request.form["student_id"]),
                float(request.form["amount"]),
                date.today().isoformat(),
                request.form.get("note", ""),
            ),
        )
    return redirect(url_for("payments"))


@app.route("/complaints")
def complaints():
    with connect_db() as conn:
        active_students = conn.execute(
            "SELECT id, name FROM students WHERE status = 'active' ORDER BY name"
        ).fetchall()
        all_complaints = conn.execute(
            """
            SELECT complaints.*, students.name
            FROM complaints
            JOIN students ON students.id = complaints.student_id
            ORDER BY complaints.status, complaints.complaint_date DESC
            """
        ).fetchall()
    return render_template(
        "complaints.html",
        students=active_students,
        complaints=all_complaints,
    )


@app.route("/complaints/add", methods=["POST"])
def add_complaint():
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO complaints (student_id, description, complaint_date)
            VALUES (?, ?, ?)
            """,
            (
                int(request.form["student_id"]),
                request.form["description"],
                date.today().isoformat(),
            ),
        )
    return redirect(url_for("complaints"))


@app.route("/complaints/resolve", methods=["POST"])
def resolve_complaint():
    with connect_db() as conn:
        conn.execute(
            "UPDATE complaints SET status = 'resolved' WHERE id = ?",
            (int(request.form["complaint_id"]),),
        )
    return redirect(url_for("complaints"))


if __name__ == "__main__":
    setup_database()
    app.run(debug=True)
