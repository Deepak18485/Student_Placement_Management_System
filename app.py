
from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
import os
from werkzeug.utils import secure_filename
import bcrypt, jwt, datetime
import json

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
    cur.execute("SELECT student_id, university_roll, email, password_hash, name FROM students WHERE email = %s", (email,))
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

    return jsonify({"token": token, "name": row["name"], "email": row["email"], "student_id": row["student_id"], "university_roll": row["university_roll"]})



# ===========================
# Student Authentication
# ===========================
@app.route("/api/student/register", methods=["POST"])
def student_register():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    branch = data.get("branch")
    cgpa = data.get("cgpa")
    university_roll = data.get("university_roll")

    if not all([name, email, password, branch, cgpa, university_roll]):
        return jsonify({"error": "All fields required"}), 400

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO students (name, email, password_hash, branch, cgpa, university_roll) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, email, hashed_pw, branch, float(cgpa), university_roll)
        )
        db.commit()
        cur.close(); db.close()
        return jsonify({"message": "Student registered successfully"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email or university roll already exists"}), 409
    except Exception as e:
        print("Registration error:", e)
        return jsonify({"error": "Registration failed"}), 500

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
            "INSERT INTO PlacementOfficer (name, email, password_hash) VALUES (%s, %s, %s)",
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
    cur.execute("SELECT officer_id, email, password_hash, name FROM PlacementOfficer WHERE email = %s", (email,))
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

    return jsonify({"token": token, "name": row["name"], "email": row["email"], "officer_id": row["officer_id"]})

# ===========================
# Job Posting / Applications
# ===========================
@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        student_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        # Get jobs that student hasn't applied to yet, and filter by eligibility
        cur.execute("""
            SELECT jp.job_id, jp.title, jp.description, jp.branch_eligibility, jp.min_cgpa, jp.package_stipend, jp.deadline, jp.created_at
            FROM JobPosting jp
            LEFT JOIN Application a ON jp.job_id = a.job_id AND a.student_id = %s
            JOIN students s ON s.student_id = %s
            WHERE a.application_id IS NULL
            AND jp.deadline >= CURDATE()
            AND jp.status = 'Open'
            AND (jp.branch_eligibility = 'All' OR jp.branch_eligibility LIKE CONCAT('%%', s.branch, '%%'))
            AND jp.min_cgpa <= s.cgpa
            ORDER BY jp.created_at DESC
        """, (student_id, student_id))
        rows = cur.fetchall()
        cur.close(); db.close()
        return jsonify(rows)
    except Exception as e:
        print("Error fetching jobs:", e)
        return jsonify({"error": "Failed to fetch jobs"}), 500

@app.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
def apply_job(job_id):
    # Extract student_id from JWT token
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        student_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    resume = request.files.get("resume")
    if not resume:
        return jsonify({"error": "Resume file required"}), 400

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
# Student Management
# ===========================
@app.route("/api/students", methods=["GET"])
@app.route("/api/student/list", methods=["GET"])
def get_all_students():
    """Get all students with their details"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)

        # Query to get all student details with skills
        cur.execute("""
            SELECT s.student_id, s.university_roll, s.name, s.email, s.branch as department, s.cgpa,
                   GROUP_CONCAT(sk.skill_name) as skills, s.resume_path, s.created_at
            FROM students s
            LEFT JOIN StudentSkill ss ON s.student_id = ss.student_id
            LEFT JOIN Skill sk ON ss.skill_id = sk.skill_id
            GROUP BY s.student_id
            ORDER BY s.created_at DESC
        """)

        students = cur.fetchall()
        # Convert skills string to array
        for student in students:
            student['skills'] = student['skills'].split(',') if student['skills'] else []
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
            FROM students
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

@app.route("/api/student/profile", methods=["GET"])
def get_student_profile():
    """Get profile data for the logged-in student"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        student_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT s.student_id, s.university_roll, s.name, s.email, s.branch, s.cgpa, s.resume_path,
                   GROUP_CONCAT(sk.skill_name) as skills
            FROM students s
            LEFT JOIN StudentSkill ss ON s.student_id = ss.student_id
            LEFT JOIN Skill sk ON ss.skill_id = sk.skill_id
            WHERE s.student_id = %s
            GROUP BY s.student_id
        """, (student_id,))
        profile = cur.fetchone()
        cur.close()
        db.close()

        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        # Convert skills to list
        profile['skills'] = profile['skills'].split(',') if profile['skills'] else []
        # Check if resume exists
        profile['resume_uploaded'] = bool(profile['resume_path'] and os.path.exists(profile['resume_path']))

        return jsonify(profile)
    except Exception as e:
        print("Error fetching profile:", e)
        return jsonify({"error": "Failed to fetch profile"}), 500

@app.route("/api/student/profile", methods=["PUT"])
def update_student_profile():
    """Update profile data for the logged-in student"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        student_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data = request.form or request.json or {}
    name = data.get("name")
    email = data.get("email")
    branch = data.get("branch")
    cgpa = data.get("cgpa")
    university_roll = data.get("university_roll")

    # Handle skills - could be JSON string or comma-separated string
    skills_raw = data.get("skills", "")
    if isinstance(skills_raw, str):
        try:
            skills = json.loads(skills_raw)  # Try parsing as JSON first
        except json.JSONDecodeError:
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]  # Fallback to comma-separated
    else:
        skills = skills_raw if skills_raw else []

    resume = request.files.get("resume")

    try:
        db = get_db()
        cur = db.cursor()

        # Update basic info
        update_fields = []
        update_values = []
        if name:
            update_fields.append("name = %s")
            update_values.append(name)
        if email:
            update_fields.append("email = %s")
            update_values.append(email)
        if branch:
            update_fields.append("branch = %s")
            update_values.append(branch)
        if cgpa:
            update_fields.append("cgpa = %s")
            update_values.append(float(cgpa))
        if university_roll:
            update_fields.append("university_roll = %s")
            update_values.append(university_roll)

        if update_fields:
            update_values.append(student_id)
            cur.execute(f"UPDATE students SET {', '.join(update_fields)} WHERE student_id = %s", update_values)

        # Handle resume upload
        if resume:
            filename = secure_filename(resume.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{student_id}_{int(datetime.datetime.utcnow().timestamp())}_{filename}")
            resume.save(save_path)
            cur.execute("UPDATE students SET resume_path = %s WHERE student_id = %s", (save_path, student_id))

        # Handle skills
        if skills:
            # Remove existing skills
            cur.execute("DELETE FROM StudentSkill WHERE student_id = %s", (student_id,))
            # Add new skills
            for skill_name in skills:
                skill_name = skill_name.strip()
                if skill_name:
                    # Insert skill if not exists
                    cur.execute("INSERT IGNORE INTO Skill (skill_name) VALUES (%s)", (skill_name,))
                    cur.execute("SELECT skill_id FROM Skill WHERE skill_name = %s", (skill_name,))
                    skill_id = cur.fetchone()[0]
                    cur.execute("INSERT INTO StudentSkill (student_id, skill_id) VALUES (%s, %s)", (student_id, skill_id))

        db.commit()
        cur.close()
        db.close()
        return jsonify({"message": "Profile updated successfully"})
    except Exception as e:
        print("Error updating profile:", e)
        return jsonify({"error": "Failed to update profile"}), 500

@app.route("/api/student/applications", methods=["GET"])
def get_student_applications():
    """Get applications for the logged-in student"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        student_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT a.application_id, j.title, a.status, a.applied_on
            FROM Application a
            JOIN JobPosting j ON a.job_id = j.job_id
            WHERE a.student_id = %s
            ORDER BY a.applied_on DESC
        """, (student_id,))
        applications = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(applications)
    except Exception as e:
        print("Error fetching applications:", e)
        return jsonify({"error": "Failed to fetch applications"}), 500

@app.route("/api/student/notifications", methods=["GET"])
def get_student_notifications():
    """Get notifications for the logged-in student"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        student_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT notification_id, message, is_read, created_at
            FROM Notification
            WHERE student_id = %s
            ORDER BY created_at DESC
        """, (student_id,))
        notifications = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(notifications)
    except Exception as e:
        print("Error fetching notifications:", e)
        return jsonify({"error": "Failed to fetch notifications"}), 500

@app.route("/api/officer/postings", methods=["GET"])
def get_officer_postings():
    """Get all job postings for officer"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        officer_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT job_id, title, description, branch_eligibility, min_cgpa, package_stipend, deadline, created_at FROM JobPosting WHERE officer_id = %s ORDER BY created_at DESC", (officer_id,))
        postings = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(postings)
    except Exception as e:
        print("Error fetching postings:", e)
        return jsonify({"error": "Failed to fetch postings"}), 500

@app.route("/api/officer/postings", methods=["POST"])
def create_job_posting():
    """Create a new job posting"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        officer_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data = request.json or {}
    title = data.get("title")
    description = data.get("description")
    branch_eligibility = data.get("branch_eligibility")
    min_cgpa = data.get("min_cgpa")
    package_stipend = data.get("package_stipend")
    deadline = data.get("deadline")
    skills = data.get("skills", [])

    if not all([title, description, branch_eligibility, min_cgpa, package_stipend, deadline]):
        return jsonify({"error": "All fields required"}), 400

    try:
        db = get_db()
        cur = db.cursor()

        # Insert job posting
        cur.execute("""
            INSERT INTO JobPosting (officer_id, title, description, branch_eligibility, min_cgpa, package_stipend, deadline)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (officer_id, title, description, branch_eligibility, float(min_cgpa), float(package_stipend), deadline))

        job_id = cur.lastrowid

        # Insert skills
        if skills:
            for skill_name in skills:
                skill_name = skill_name.strip()
                if skill_name:
                    # Insert skill if not exists
                    cur.execute("INSERT IGNORE INTO Skill (skill_name) VALUES (%s)", (skill_name,))
                    cur.execute("SELECT skill_id FROM Skill WHERE skill_name = %s", (skill_name,))
                    skill_id_row = cur.fetchone()
                    if skill_id_row:
                        skill_id_val = skill_id_row[0]
                        cur.execute("INSERT INTO JobSkill (job_id, skill_id) VALUES (%s, %s)", (job_id, skill_id_val))

        db.commit()
        cur.close()
        db.close()
        return jsonify({"message": "Job posting created successfully", "job_id": job_id}), 201
    except Exception as e:
        print("Error creating job posting:", e)
        return jsonify({"error": "Failed to create job posting"}), 500

@app.route("/api/officer/student/<university_roll>", methods=["GET"])
def get_student_by_roll_number(university_roll):
    """Get student profile by university roll number"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT s.student_id, s.university_roll, s.name, s.email, s.branch, s.cgpa, s.resume_path,
                   GROUP_CONCAT(sk.skill_name) as skills
            FROM students s
            LEFT JOIN StudentSkill ss ON s.student_id = ss.student_id
            LEFT JOIN Skill sk ON ss.skill_id = sk.skill_id
            WHERE s.university_roll = %s
            GROUP BY s.student_id
        """, (university_roll,))
        student = cur.fetchone()
        cur.close()
        db.close()
        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Process skills
        student['skills'] = student['skills'].split(',') if student['skills'] else []
        student['resume_uploaded'] = bool(student['resume_path'])

        return jsonify(student)
    except Exception as e:
        print("Error fetching student:", e)
        return jsonify({"error": "Failed to fetch student"}), 500

@app.route("/api/officer/applications", methods=["GET"])
def get_officer_applications():
    """Get all applications for officer"""
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT a.application_id, a.job_id, s.name as student_name, j.title as job_title, a.status, a.applied_on
            FROM Application a
            JOIN students s ON a.student_id = s.student_id
            JOIN JobPosting j ON a.job_id = j.job_id
            ORDER BY a.applied_on DESC
        """)
        applications = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(applications)
    except Exception as e:
        print("Error fetching applications:", e)
        return jsonify({"error": "Failed to fetch applications"}), 500

@app.route("/api/officer/applications/<int:application_id>/status", methods=["PUT"])
def update_application_status(application_id):
    """Update application status"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        # Verify officer role
        if payload.get("role") != "officer":
            return jsonify({"error": "Officer access required"}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data = request.json or {}
    status = data.get("status")

    if not status or status not in ['Applied', 'Shortlisted', 'Selected', 'Rejected']:
        return jsonify({"error": "Valid status required"}), 400

    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE Application SET status = %s WHERE application_id = %s", (status, application_id))
        if cur.rowcount == 0:
            db.rollback()
            cur.close()
            db.close()
            return jsonify({"error": "Application not found"}), 404
        db.commit()
        cur.close()
        db.close()
        return jsonify({"message": "Application status updated successfully"})
    except Exception as e:
        print("Error updating application status:", e)
        return jsonify({"error": "Failed to update application status"}), 500

@app.route("/api/officer/notifications", methods=["POST"])
def send_notification():
    """Send notification to all students"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        # Verify officer role
        if payload.get("role") != "officer":
            return jsonify({"error": "Officer access required"}), 403
        officer_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data = request.json or {}
    message = data.get("message")

    if not message:
        return jsonify({"error": "Message required"}), 400

    try:
        db = get_db()
        cur = db.cursor()
        # Insert into SentNotifications
        cur.execute("INSERT INTO SentNotifications (officer_id, message) VALUES (%s, %s)", (officer_id, message))
        sent_id = cur.lastrowid
        # Get all student IDs
        cur.execute("SELECT student_id FROM students")
        students = cur.fetchall()
        # Insert notification for each student
        for student in students:
            cur.execute("INSERT INTO Notification (student_id, message) VALUES (%s, %s)", (student[0], message))
        db.commit()
        cur.close()
        db.close()
        return jsonify({"message": "Notification sent to all students"}), 201
    except Exception as e:
        print("Error sending notification:", e)
        return jsonify({"error": "Failed to send notification"}), 500

@app.route("/api/officer/notifications", methods=["GET"])
def get_officer_notifications():
    """Get recent notifications sent by officer (for display in dashboard)"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Authorization required"}), 401
    try:
        payload = jwt.decode(token.split(" ")[1], JWT_SECRET, algorithms=["HS256"])
        # Verify officer role
        if payload.get("role") != "officer":
            return jsonify({"error": "Officer access required"}), 403
        officer_id = payload["id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        # Get recent sent notifications by this officer (last 10)
        cur.execute("SELECT message, created_at FROM SentNotifications WHERE officer_id = %s ORDER BY created_at DESC LIMIT 10", (officer_id,))
        notifications = cur.fetchall()
        cur.close()
        db.close()
        return jsonify(notifications)
    except Exception as e:
        print("Error fetching notifications:", e)
        return jsonify({"error": "Failed to fetch notifications"}), 500
    
    
# ===========================
# Main Entry
# ===========================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
