"""
Web App Entry Point

This file replaces gui.py's role for the web-deployable version of the 
Student Performance & Attendance Automation Suite.

The underlying backend modules (attendance.py, marks.py, report_generator.py) 
remain exactly as built by Members 1, 2, and 3. No changes were made to their logic; 
this file simply handles taking inputs via a web form and serving the generated Excel 
file back as a direct download.
"""

import os
import datetime
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename

# Import backend modules safely
from attendance import process_attendance
from marks import process_marks
from report_generator import generate_report

app = Flask(__name__)

# Configure upload and output directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    """Renders the main upload form."""
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    """Handles file uploads, processes them through the pipeline, and generates the report."""
    try:
        # Validate that both files were uploaded
        if 'attendance_file' not in request.files or 'marks_file' not in request.files:
            return render_template("index.html", error="Both Attendance and Marks files must be provided.")
            
        att_file = request.files['attendance_file']
        marks_file = request.files['marks_file']
        
        if att_file.filename == '' or marks_file.filename == '':
            return render_template("index.html", error="Please select valid files for both fields.")
            
        # Secure the filenames and save them
        att_filename = secure_filename(att_file.filename)
        marks_filename = secure_filename(marks_file.filename)
        
        att_path = os.path.join(UPLOAD_FOLDER, att_filename)
        marks_path = os.path.join(UPLOAD_FOLDER, marks_filename)
        
        att_file.save(att_path)
        marks_file.save(marks_path)
        
        # 1. Process Attendance (Member 1)
        attendance_df = process_attendance(att_path)
        
        # 2. Process Marks (Member 2)
        # Unpacking the tuple exactly like gui.py does to get the summary DataFrame
        marks_summary_df, marks_toppers_df, marks_at_risk_df = process_marks(marks_path)
        
        # 3. Generate Report (Member 3)
        # Use a timestamped filename to prevent overlap issues
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"Class_Report_{timestamp}.xlsx"
        report_path = os.path.join(OUTPUT_FOLDER, report_filename)
        
        generate_report(attendance_df, marks_summary_df, report_path)
        
        # Re-render with success message and download link
        return render_template("index.html", success="Report successfully generated!", download_link=report_filename)
        
    except Exception as e:
        # Catch and surface any errors gracefully to the UI
        return render_template("index.html", error=f"An error occurred during processing: {str(e)}")

@app.route("/download/<filename>")
def download(filename):
    """Serves the generated file back to the user."""
    # Security check to prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return "Invalid filename", 400
        
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
