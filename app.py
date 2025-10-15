from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
import os
from werkzeug.utils import secure_filename
import bcrypt, jwt, datetime

# ===========================
# Database & App Config
# ===========================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Ecommerce@1"),
    "database": os.getenv("DB_NAME", "student_placement_system")
}
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_secret")

app = Flask(__name__, static_folder="frontend", static_url_path="/")
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ===========================
# Database Connection
# ===========================
def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ===========================
# Serve Frontend Files
# ===========================
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

# ===========================
# Student Authentication
# ===========================
@app.route("/api/student/login", methods=["POST"])
def student_login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT student_id, email, password_hash, name FROM Student WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close(); db.close()

    if not row:
        return jsonify({"error": "Invalid credentials"}), 401

    stored = row["password_hash"].encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), stored):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({
        "id": row["student_id"],
        "role": "student",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({"token": token, "name": row["name"], "email": row["email"]})

# ===========================
# Officer Authentication
# ===========================
@app.route("/api/officer/register", methods=["POST"])
def officer_register():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all([name, email, password]):
        return jsonify({"error": "All fields required"}), 400

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO Officer (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, hashed_pw)
        )
        db.commit()
        cur.close(); db.close()
        return jsonify({"message": "Officer registered successfully"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        print("Registration error:", e)
        return jsonify({"error": "Registration failed"}), 500


@app.route("/api/officer/login", methods=["POST"])
def officer_login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT officer_id, email, password_hash, name FROM Officer WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close(); db.close()

    if not row:
        return jsonify({"error": "Invalid credentials"}), 401

    stored = row["password_hash"].encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), stored):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({
        "id": row["officer_id"],
        "role": "officer",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({"token": token, "name": row["name"], "email": row["email"]})

# ===========================
# Job Posting / Applications
# ===========================
@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT job_id, title, company, location, description, created_at FROM JobPosting ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close(); db.close()
    return jsonify(rows)

@app.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
def apply_job(job_id):
    student_id = request.form.get("student_id")
    resume = request.files.get("resume")
    if not student_id or not resume:
        return jsonify({"error": "student_id and resume required"}), 400

    filename = secure_filename(resume.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{student_id}_{int(datetime.datetime.utcnow().timestamp())}_{filename}")
    resume.save(save_path)

    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO Application (student_id, job_id, resume_path, status, applied_on) VALUES (%s, %s, %s, 'Applied', NOW())",
                (student_id, job_id, save_path))
    db.commit()
    cur.close(); db.close()
    return jsonify({"message": "Applied successfully"})

# ===========================
# Student Management (Add this section)
# ===========================
@app.route("/api/students", methods=["GET"])
def get_all_students():
    """Get all students with their details"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        # Query to get all student details
        cur.execute("""
            SELECT student_id, name, email, phone, department, year, cgpa, 
                   skills, resume_path, created_at 
            FROM Student 
            ORDER BY created_at DESC
        """)
        
        students = cur.fetchall()
        cur.close()
        db.close()
        
        return jsonify(students)
        
    except Exception as e:
        print("Error fetching students:", e)
        return jsonify({"error": "Failed to fetch students"}), 500

@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student_details(student_id):
    """Get detailed information about a specific student"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        # Query to get specific student details
        cur.execute("""
            SELECT student_id, name, email, phone, department, year, cgpa, 
                   skills, resume_path, created_at 
            FROM Student 
            WHERE student_id = %s
        """, (student_id,))
        
        student = cur.fetchone()
        cur.close()
        db.close()
        
        if not student:
            return jsonify({"error": "Student not found"}), 404
            
        return jsonify(student)
        
    except Exception as e:
        print("Error fetching student details:", e)
        return jsonify({"error": "Failed to fetch student details"}), 500
    
    
# ===========================
# Main Entry
# ===========================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
