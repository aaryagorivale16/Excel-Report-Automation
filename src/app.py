"""
EduMetrics - Web Application Engine
Multi-page Flask web application providing:
1. Teacher Portal Login & Sign-up (Session-backed with password hashing)
2. Multi-Class & Division Management (Class Switcher & Auto-division detection)
3. Fresh accounts start clean without pre-loaded dummy data
4. Pre-flight file upload & CSV schema validator
5. Interactive on-screen Analytics Dashboard (Chart.js + KPI cards + Toppers + At-Risk)
6. Configurable Academic Policy & Criteria Controls
7. Sample Template Downloads & Documentation
"""

import os
import re
import sys
import datetime
from functools import wraps
import pandas as pd
from flask import Flask, request, render_template, send_file, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename

# Ensure src directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
sys.path.insert(0, BASE_DIR)

from attendance import process_attendance
from marks import process_marks
from report_generator import generate_report
from db import (
    create_teacher, authenticate_teacher, get_teacher,
    add_class_to_teacher, save_class_report, get_latest_class_report
)

app = Flask(__name__)
app.secret_key = "edumetrics_secret_key_student_suite_2026_teacher_portal"

# Directory paths
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Default institutional criteria policy
DEFAULT_POLICY = {
    "attendance_threshold": 75.0,
    "pass_percentage": 40.0,
    "grade_boundaries": {
        "A+": 90.0,
        "A": 75.0,
        "B": 60.0,
        "C": 50.0
    }
}


def sanitize_filename_part(name: str) -> str:
    """Replaces spaces and non-alphanumeric characters with clean underscores."""
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '_', name.strip())
    return cleaned.strip('_')


def login_required(f):
    """Decorator ensuring teacher authentication before accessing workspace pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "teacher_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_teacher_context():
    """Injects active teacher profile and registered classes into every template."""
    teacher_id = session.get("teacher_id")
    if teacher_id:
        teacher = get_teacher(teacher_id)
        if teacher:
            classes = teacher["classes"]
            active_class = session.get("active_class", classes[0] if classes else "Class 1")
            return {
                "teacher": teacher,
                "teacher_classes": classes,
                "active_class": active_class
            }
    return {
        "teacher": None,
        "teacher_classes": [],
        "active_class": None
    }


def get_active_policy():
    """Retrieve policy from session or fallback to default."""
    if "policy" in session:
        return session["policy"]
    return DEFAULT_POLICY.copy()


def compute_analytics(attendance_df: pd.DataFrame, marks_summary_df: pd.DataFrame, 
                      toppers_df: pd.DataFrame, at_risk_df: pd.DataFrame, policy: dict) -> dict:
    """
    Computes a comprehensive metrics dictionary combining attendance and marks
    with division auto-detection (Suggestion 1.2).
    """
    # Merge keys: StudentID, Name (and Division if present in both)
    merge_keys = ["StudentID", "Name"]
    if "Division" in attendance_df.columns and "Division" in marks_summary_df.columns:
        merge_keys.append("Division")

    merged = pd.merge(attendance_df, marks_summary_df, on=merge_keys, how="outer")

    # If Division is in one of them, standardize column
    if "Division" not in merged.columns:
        if "Division_x" in merged.columns:
            merged["Division"] = merged["Division_x"].fillna(merged.get("Division_y", ""))
        elif "Division_y" in merged.columns:
            merged["Division"] = merged["Division_y"]
        else:
            merged["Division"] = ""

    # Clean & fill missing columns
    merged["Total_Classes"] = merged["Total_Classes"].fillna(0).astype(int)
    merged["Classes_Attended"] = merged["Classes_Attended"].fillna(0).astype(int)
    merged["Attendance_Percent"] = merged["Attendance_Percent"].fillna(0.0).round(2)
    merged["Low_Attendance_Flag"] = merged["Attendance_Percent"] < policy.get("attendance_threshold", 75.0)

    merged["Total_Marks"] = merged["Total_Marks"].fillna(0).astype(float)
    merged["Total_MaxMarks"] = merged["Total_MaxMarks"].fillna(0).astype(float)
    merged["Overall_Percent"] = merged["Overall_Percent"].fillna(0.0).round(2)
    merged["Grade"] = merged["Grade"].fillna("F")
    merged["Final_Status"] = merged["Final_Status"].fillna("Fail")

    if "Class_Rank" not in merged.columns or merged["Class_Rank"].isnull().any():
        merged["Class_Rank"] = merged["Overall_Percent"].rank(ascending=False, method="min").astype(int)
    else:
        merged["Class_Rank"] = merged["Class_Rank"].astype(int)

    # Sort roster by rank then StudentID
    merged = merged.sort_values(by=["Class_Rank", "StudentID"]).reset_index(drop=True)

    total_students = len(merged)
    avg_marks = round(float(merged["Overall_Percent"].mean()), 1) if total_students > 0 else 0.0
    avg_attendance = round(float(merged["Attendance_Percent"].mean()), 1) if total_students > 0 else 0.0

    pass_count = int((merged["Final_Status"] == "Pass").sum())
    fail_count = int((merged["Final_Status"] == "Fail").sum())
    pass_rate = round((pass_count / total_students * 100), 1) if total_students > 0 else 0.0

    grade_distribution = {
        g: int((merged["Grade"] == g).sum()) 
        for g in ["A+", "A", "B", "C", "D", "F"]
    }

    at_risk_students = merged[
        (merged["Grade"] == "F") | (merged["Low_Attendance_Flag"] == True)
    ].to_dict(orient="records")

    toppers = merged[merged["Class_Rank"] <= 3].sort_values(by="Class_Rank").to_dict(orient="records")
    roster = merged.to_dict(orient="records")

    # Suggestion 1.2: Detect unique divisions and calculate side-by-side comparison metrics
    detected_divisions = []
    division_summary = []
    if "Division" in merged.columns:
        detected_divisions = sorted([str(d) for d in merged["Division"].dropna().unique() if str(d).strip()])
        for div in detected_divisions:
            div_students = merged[merged["Division"] == div]
            cnt = len(div_students)
            if cnt > 0:
                d_avg_marks = round(float(div_students["Overall_Percent"].mean()), 1)
                d_avg_att = round(float(div_students["Attendance_Percent"].mean()), 1)
                d_pass = int((div_students["Final_Status"] == "Pass").sum())
                d_fail = int((div_students["Final_Status"] == "Fail").sum())
                d_pass_rate = round((d_pass / cnt * 100), 1)
                division_summary.append({
                    "division": div,
                    "student_count": cnt,
                    "avg_marks": d_avg_marks,
                    "avg_attendance": d_avg_att,
                    "pass_count": d_pass,
                    "fail_count": d_fail,
                    "pass_rate": d_pass_rate
                })

    return {
        "total_students": total_students,
        "avg_marks": avg_marks,
        "avg_attendance": avg_attendance,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_rate,
        "grade_distribution": grade_distribution,
        "toppers": toppers,
        "at_risk": at_risk_students,
        "roster": roster,
        "divisions": detected_divisions,
        "division_summary": division_summary
    }


# =========================================================================
# AUTHENTICATION ROUTES
# =========================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Teacher Login Portal."""
    if "teacher_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        teacher = authenticate_teacher(username, password)
        if teacher:
            session["teacher_id"] = teacher["id"]
            session["teacher_name"] = teacher["name"]
            session["teacher_username"] = teacher["username"]
            session["active_class"] = teacher["classes"][0] if teacher["classes"] else "Class 1"
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password. Please try again.")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Teacher Account Registration with Names of Classes."""
    if "teacher_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "")
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        classes_raw = request.form.get("classes_input", "")

        if not name or not username or not password or not classes_raw:
            return render_template("signup.html", error="All fields are required to register your teacher account.")

        # Parse classes by commas
        classes_list = [c.strip() for c in classes_raw.split(",") if c.strip()]
        if not classes_list:
            classes_list = ["Class 10 - Div A"]

        teacher, err = create_teacher(name, username, password, classes_list)
        if err:
            return render_template("signup.html", error=err)

        # Log in the freshly registered teacher
        session["teacher_id"] = teacher["id"]
        session["teacher_name"] = teacher["name"]
        session["teacher_username"] = teacher["username"]
        session["active_class"] = teacher["classes"][0]

        # Redirect to Dashboard (which will cleanly show zero dummy data pre-loaded!)
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    """Logs out teacher and clears session."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/switch-class", methods=["POST"])
@login_required
def switch_class():
    """Switches the active class/division in the session."""
    chosen_class = request.form.get("active_class")
    if chosen_class:
        session["active_class"] = chosen_class
    referer = request.referrer or url_for("dashboard")
    return redirect(referer)


@app.route("/add-class", methods=["POST"])
@login_required
def add_class():
    """Dynamically adds a new class/division for the logged-in teacher."""
    new_class = request.form.get("new_class_name", "").strip()
    teacher_id = session.get("teacher_id")

    if new_class and teacher_id:
        updated = add_class_to_teacher(teacher_id, new_class)
        session["active_class"] = new_class
        return jsonify({"success": True, "classes": updated, "active_class": new_class})
    return jsonify({"success": False, "error": "Invalid class name"}), 400


# =========================================================================
# WORKSPACE ROUTES
# =========================================================================

@app.route("/", methods=["GET"])
@login_required
def index():
    """Page 1: Upload & Pre-Flight Validator Page with Class Selector."""
    policy = get_active_policy()
    teacher_id = session["teacher_id"]
    active_class = session.get("active_class", "Class 10 - Div A")

    _, active_report, _ = get_latest_class_report(teacher_id, active_class)

    return render_template(
        "upload.html",
        active_page="upload",
        policy=policy,
        active_report=active_report
    )


@app.route("/generate", methods=["POST"])
@login_required
def generate():
    """Handles file uploads, runs pipeline for selected class, and opens dashboard."""
    teacher_id = session["teacher_id"]
    selected_class = request.form.get("selected_class") or session.get("active_class", "Class 10 - Div A")
    session["active_class"] = selected_class

    policy = get_active_policy().copy()
    if "attendance_threshold" in request.form:
        policy["attendance_threshold"] = float(request.form.get("attendance_threshold", 75.0))
    if "pass_percentage" in request.form:
        policy["pass_percentage"] = float(request.form.get("pass_percentage", 40.0))
    session["policy"] = policy

    try:
        # Validate that both files were uploaded
        if 'attendance_file' not in request.files or 'marks_file' not in request.files:
            return render_template(
                "upload.html",
                active_page="upload",
                policy=policy,
                error="Both Attendance and Marks files must be provided."
            )

        att_file = request.files['attendance_file']
        marks_file = request.files['marks_file']

        if att_file.filename == '' or marks_file.filename == '':
            return render_template(
                "upload.html",
                active_page="upload",
                policy=policy,
                error="Please select valid files for both fields."
            )

        # Save files safely
        att_filename = secure_filename(att_file.filename)
        marks_filename = secure_filename(marks_file.filename)

        att_path = os.path.join(UPLOAD_FOLDER, att_filename)
        marks_path = os.path.join(UPLOAD_FOLDER, marks_filename)

        att_file.save(att_path)
        marks_file.save(marks_path)

        # Run pipeline
        att_threshold = float(policy.get("attendance_threshold", 75.0))
        pass_pct = float(policy.get("pass_percentage", 40.0))
        grade_bounds = policy.get("grade_boundaries", DEFAULT_POLICY["grade_boundaries"])

        attendance_df = process_attendance(att_path, threshold=att_threshold)
        marks_summary_df, marks_toppers_df, marks_at_risk_df = process_marks(
            marks_path, pass_percentage=pass_pct, grade_boundaries=grade_bounds
        )

        # Suggestion 1.1: Organized class-based Excel filename (e.g. Class_10_Div_A_Report_October_20261006.xlsx)
        safe_class = sanitize_filename_part(selected_class)
        month_name = datetime.datetime.now().strftime("%B")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{safe_class}_Report_{month_name}_{timestamp}.xlsx"
        report_path = os.path.join(OUTPUT_FOLDER, report_filename)

        generate_report(
            attendance_df=attendance_df,
            marks_df=marks_summary_df,
            output_path=report_path,
            toppers_df=marks_toppers_df,
            at_risk_df=marks_at_risk_df,
            attendance_threshold=att_threshold
        )

        # Compute metrics
        metrics = compute_analytics(
            attendance_df=attendance_df,
            marks_summary_df=marks_summary_df,
            toppers_df=marks_toppers_df,
            at_risk_df=marks_at_risk_df,
            policy=policy
        )

        # Persist report for this specific teacher and class
        save_class_report(teacher_id, selected_class, report_filename, metrics, policy)

        return render_template(
            "dashboard.html",
            active_page="dashboard",
            policy=policy,
            metrics=metrics,
            report_filename=report_filename,
            success=f"Report successfully generated for {selected_class}!"
        )

    except Exception as e:
        return render_template(
            "upload.html",
            active_page="upload",
            policy=policy,
            error=f"Processing error: {str(e)}"
        )


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """
    Page 2: Interactive Analytics Dashboard.
    For a fresh sign-up, NO dummy data is pre-loaded; it shows an empty state.
    """
    teacher_id = session["teacher_id"]
    active_class = session.get("active_class", "Class 10 - Div A")
    policy = get_active_policy()

    # Fetch latest report for the selected class from SQLite
    metrics, report_filename, saved_policy = get_latest_class_report(teacher_id, active_class)

    if saved_policy:
        policy = saved_policy

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        policy=policy,
        metrics=metrics,
        report_filename=report_filename
    )


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Page 3: Academic Policy & Threshold Configuration."""
    policy = get_active_policy().copy()
    teacher_id = session["teacher_id"]
    active_class = session.get("active_class", "Class 10 - Div A")
    _, active_report, _ = get_latest_class_report(teacher_id, active_class)

    if request.method == "POST":
        try:
            att_thresh = float(request.form.get("attendance_threshold", 75.0))
            pass_pct = float(request.form.get("pass_percentage", 40.0))
            
            grade_a_plus = float(request.form.get("grade_a_plus", 90.0))
            grade_a = float(request.form.get("grade_a", 75.0))
            grade_b = float(request.form.get("grade_b", 60.0))
            grade_c = float(request.form.get("grade_c", 50.0))

            updated_policy = {
                "attendance_threshold": att_thresh,
                "pass_percentage": pass_pct,
                "grade_boundaries": {
                    "A+": grade_a_plus,
                    "A": grade_a,
                    "B": grade_b,
                    "C": grade_c
                }
            }

            session["policy"] = updated_policy

            return render_template(
                "settings.html",
                active_page="settings",
                policy=updated_policy,
                active_report=active_report,
                success="Academic policies updated successfully!"
            )
        except Exception as e:
            return render_template(
                "settings.html",
                active_page="settings",
                policy=policy,
                active_report=active_report,
                error=f"Error saving settings: {str(e)}"
            )

    return render_template(
        "settings.html",
        active_page="settings",
        policy=policy,
        active_report=active_report
    )


@app.route("/templates", methods=["GET"])
@login_required
def templates_view():
    """Page 4: Starter Templates & Data Schema Documentation."""
    sample_att = os.path.join(DATA_FOLDER, "sample_attendance.csv")
    sample_marks = os.path.join(DATA_FOLDER, "sample_marks.csv")

    att_preview = []
    marks_preview = []

    try:
        if os.path.exists(sample_att):
            df_att = pd.read_csv(sample_att)
            att_preview = df_att.head(6).to_dict(orient="records")
        if os.path.exists(sample_marks):
            df_marks = pd.read_csv(sample_marks)
            marks_preview = df_marks.head(6).to_dict(orient="records")
    except Exception:
        pass

    teacher_id = session.get("teacher_id")
    active_class = session.get("active_class", "Class 10 - Div A")
    active_report = None
    if teacher_id:
        _, active_report, _ = get_latest_class_report(teacher_id, active_class)

    return render_template(
        "templates.html",
        active_page="templates",
        policy=get_active_policy(),
        active_report=active_report,
        sample_att_preview=att_preview,
        sample_marks_preview=marks_preview
    )


@app.route("/download-sample/<file_type>", methods=["GET"])
def download_sample(file_type):
    """Direct download endpoint for starter CSV templates."""
    if file_type == "attendance":
        file_path = os.path.join(DATA_FOLDER, "sample_attendance.csv")
        download_name = "sample_attendance.csv"
    elif file_type == "marks":
        file_path = os.path.join(DATA_FOLDER, "sample_marks.csv")
        download_name = "sample_marks.csv"
    else:
        return "Invalid template type", 400

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=download_name)
    return "Template file not found", 404


@app.route("/download/<filename>", methods=["GET"])
@login_required
def download(filename):
    """Serves generated Excel report files."""
    if ".." in filename or "/" in filename or "\\" in filename:
        return "Invalid filename", 400

    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return "File not found", 404


@app.route("/quick-demo", methods=["POST"])
@login_required
def quick_demo():
    """Runs a demonstration using sample templates for the active class upon explicit request."""
    teacher_id = session["teacher_id"]
    active_class = session.get("active_class", "Class 10 - Div A")
    policy = get_active_policy().copy()
    att_path = os.path.join(DATA_FOLDER, "sample_attendance.csv")
    marks_path = os.path.join(DATA_FOLDER, "sample_marks.csv")

    try:
        att_threshold = float(policy.get("attendance_threshold", 75.0))
        pass_pct = float(policy.get("pass_percentage", 40.0))
        grade_bounds = policy.get("grade_boundaries", DEFAULT_POLICY["grade_boundaries"])

        attendance_df = process_attendance(att_path, threshold=att_threshold)
        marks_summary_df, marks_toppers_df, marks_at_risk_df = process_marks(
            marks_path, pass_percentage=pass_pct, grade_boundaries=grade_bounds
        )

        safe_class = sanitize_filename_part(active_class)
        month_name = datetime.datetime.now().strftime("%B")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{safe_class}_Report_{month_name}_{timestamp}.xlsx"
        report_path = os.path.join(OUTPUT_FOLDER, report_filename)

        generate_report(
            attendance_df=attendance_df,
            marks_df=marks_summary_df,
            output_path=report_path,
            toppers_df=marks_toppers_df,
            at_risk_df=marks_at_risk_df,
            attendance_threshold=att_threshold
        )

        metrics = compute_analytics(
            attendance_df=attendance_df,
            marks_summary_df=marks_summary_df,
            toppers_df=marks_toppers_df,
            at_risk_df=marks_at_risk_df,
            policy=policy
        )

        save_class_report(teacher_id, active_class, report_filename, metrics, policy)
        return redirect(url_for("dashboard"))
    except Exception as e:
        return redirect(url_for("templates_view"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
