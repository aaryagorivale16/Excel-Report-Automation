"""
Database Module for EduMetrics
SQLite-backed persistent storage for Teacher accounts, registered classes, and generated reports.
"""

import os
import json
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edumetrics.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Teachers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            classes_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Class Reports Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            report_filename TEXT NOT NULL,
            metrics_json TEXT NOT NULL,
            policy_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id)
        )
    """)

    conn.commit()
    conn.close()


def create_teacher(name: str, username: str, password: str, classes_list: list) -> tuple:
    """
    Creates a new teacher account. Returns (teacher_dict, None) on success or (None, error_msg).
    """
    conn = get_db()
    cursor = conn.cursor()

    username = username.strip().lower()
    name = name.strip()

    # Clean classes list
    cleaned_classes = [c.strip() for c in classes_list if c.strip()]
    if not cleaned_classes:
        cleaned_classes = ["Class 10 - Div A"]

    password_hash = generate_password_hash(password)
    classes_json = json.dumps(cleaned_classes)

    try:
        cursor.execute("""
            INSERT INTO teachers (name, username, password_hash, classes_json)
            VALUES (?, ?, ?, ?)
        """, (name, username, password_hash, classes_json))
        conn.commit()
        teacher_id = cursor.lastrowid
        conn.close()

        return {
            "id": teacher_id,
            "name": name,
            "username": username,
            "classes": cleaned_classes
        }, None
    except sqlite3.IntegrityError:
        conn.close()
        return None, "A teacher with this username already exists. Please choose another username or log in."
    except Exception as e:
        conn.close()
        return None, f"Database error: {str(e)}"


def authenticate_teacher(username: str, password: str):
    """
    Validates username and password. Returns teacher_dict on success or None.
    """
    conn = get_db()
    cursor = conn.cursor()
    username = username.strip().lower()

    cursor.execute("SELECT * FROM teachers WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row["password_hash"], password):
        try:
            classes = json.loads(row["classes_json"])
        except Exception:
            classes = ["Class 10 - Div A"]
        return {
            "id": row["id"],
            "name": row["name"],
            "username": row["username"],
            "classes": classes
        }
    return None


def get_teacher(teacher_id: int):
    """
    Fetches teacher by ID.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        try:
            classes = json.loads(row["classes_json"])
        except Exception:
            classes = ["Class 10 - Div A"]
        return {
            "id": row["id"],
            "name": row["name"],
            "username": row["username"],
            "classes": classes
        }
    return None


def add_class_to_teacher(teacher_id: int, new_class_name: str) -> list:
    """
    Adds a new class/division to the teacher's profile. Returns updated classes list.
    """
    teacher = get_teacher(teacher_id)
    if not teacher:
        return []

    classes = teacher["classes"]
    new_class_name = new_class_name.strip()
    if new_class_name and new_class_name not in classes:
        classes.append(new_class_name)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE teachers SET classes_json = ? WHERE id = ?", (json.dumps(classes), teacher_id))
        conn.commit()
        conn.close()

    return classes


def save_class_report(teacher_id: int, class_name: str, report_filename: str, metrics: dict, policy: dict):
    """
    Saves a generated report and analytics metrics for a specific teacher and class.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO class_reports (teacher_id, class_name, report_filename, metrics_json, policy_json)
        VALUES (?, ?, ?, ?, ?)
    """, (
        teacher_id,
        class_name,
        report_filename,
        json.dumps(metrics),
        json.dumps(policy)
    ))

    conn.commit()
    conn.close()


def get_latest_class_report(teacher_id: int, class_name: str):
    """
    Retrieves the most recent report for a teacher's specific class. Returns (metrics, filename, policy) or (None, None, None).
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM class_reports 
        WHERE teacher_id = ? AND class_name = ?
        ORDER BY id DESC LIMIT 1
    """, (teacher_id, class_name))
    row = cursor.fetchone()
    conn.close()

    if row:
        metrics = json.loads(row["metrics_json"])
        policy = json.loads(row["policy_json"])
        filename = row["report_filename"]
        return metrics, filename, policy
    return None, None, None


# Initialize on import
init_db()
