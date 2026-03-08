from app import app
import sqlite3
from flask import render_template,request, redirect, url_for, session, flash
from utils.decorators import login_required, role_required

import os
from werkzeug.utils import secure_filename
from flask import current_app

@app.route("/student/dashboard")
@login_required
@role_required("student")
def student_dashboard():

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT id FROM students WHERE user_id=?",
        (user_id,)
    )
    student_id = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id=?",
        (student_id,)
    )
    applied = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id=? AND status='shortlisted'",
        (student_id,)
    )
    shortlisted = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id=? AND status='selected'",
        (student_id,)
    )
    selected = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id=? AND status='placed'",
        (student_id,)
    )
    placed = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "student/dashboard.html",
        applied=applied,
        shortlisted=shortlisted,
        selected=selected,
        placed=placed
    )

@app.route("/student/profile", methods = ["GET","POST"])
@login_required
@role_required("student")
def student_profile():
    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    user_id = session["user_id"]

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        linkedin = request.form["linkedin"]
        portfolio = request.form["portfolio"]
        skills = request.form["skills"]

        resume = request.files.get("resume")
        resume_path = None

        if resume and resume.filename != "":

            filename = secure_filename(resume.filename)

            upload_folder = current_app.config["UPLOAD_FOLDER"]

            os.makedirs(upload_folder,exist_ok = True)

            upload_path = os.path.join(upload_folder, filename)

            resume.save(upload_path)

            resume_path = filename

            cursor.execute(
                """ 
                UPDATE students
                SET name=?, phone=?,linkedin=?,portfolio=?,skills=?,resume_path=?
                WHERE user_id=?
                """,
                (name, phone, linkedin, portfolio, skills, resume_path, user_id)
            )
        else:
            cursor.execute(
            """
            UPDATE students
            SET name=?, phone=?, linkedin=?, portfolio=?, skills=?
            WHERE user_id=?
            """,
            (name, phone, linkedin, portfolio, skills, user_id)
        )
    
        connection.commit()
        flash("profile updated successfully")

    cursor.execute(
        """ 
        SELECT name, roll_number, branch, cgpa, phone, linkedin, portfolio, skills
        FROM students
        WHERE user_id=?
        """,
        (user_id,)
    )
    student = cursor.fetchone()

    connection.close()

    return render_template("student/profile.html", student = student)

@app.route("/student/drives")
@login_required
@role_required("student")
def student_drives():

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        """ 
        SELECT placement_drives.id,
               companies.company_name,
               placement_drives.title,
               placement_drives.eligibility_cgpa,
               placement_drives.drive_date,
               placement_drives.last_date_to_apply
        FROM placement_drives JOIN companies
        ON placement_drives.company_id = companies.id
        JOIN students ON students.user_id = ?
        WHERE placement_drives.status = 'approved'
        AND placement_drives.last_date_to_apply >= DATE('now')
        AND students.cgpa >= placement_drives.eligibility_cgpa
        ORDER BY placement_drives.drive_date ASC
        """,
        (user_id,)
    )

    drives = cursor.fetchall()

    connection.close()

    return render_template("student/drives.html", drives = drives)

@app.route("/student/applications")
@login_required
@role_required("student")
def student_applications():

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT id FROM students WHERE user_id=?",
        (user_id,)
    )

    student_id = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT companies.company_name,
               placement_drives.title,
               applications.status,
               applications.applied_at
        FROM applications
        JOIN placement_drives
            ON applications.drive_id = placement_drives.id
        JOIN companies
            ON placement_drives.company_id = companies.id
        WHERE applications.student_id = ?
        ORDER BY applications.applied_at DESC
        """,
        (student_id,)
    )

    applications = cursor.fetchall()

    connection.close()

    return render_template(
        "student/applications.html",
        applications=applications
    )

@app.route("/student/apply/<int:drive_id>")
@login_required
@role_required("student")
def apply_drive(drive_id):

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT id FROM students WHERE user_id=?",
        (user_id,)
    )
    student_id = cursor.fetchone()[0]

    # Check drive status
    cursor.execute(
        """
        SELECT status
        FROM placement_drives
        WHERE id=?
        """,
        (drive_id,)
    )

    drive = cursor.fetchone()

    cursor.execute(
    "SELECT last_date_to_apply FROM placement_drives WHERE id=?",
    (drive_id,)
    )

    last_date = cursor.fetchone()[0]

    from datetime import date

    if date.today().isoformat() > last_date:
        flash("Application deadline has passed")
        return redirect(url_for("student_drives"))

    if drive is None:
        flash("Drive not found")
        return redirect(url_for("student_drives"))

    if drive[0] != "approved":
        flash("Drive not open for applications")
        return redirect(url_for("student_drives"))

    try:
        cursor.execute(
            """
            INSERT INTO applications (student_id, drive_id, status)
            VALUES (?, ?, 'applied')
            """,
            (student_id, drive_id)
        )

        flash("Successfully applied for the drive")

    except sqlite3.IntegrityError:
        flash("You have already applied for this drive")

    connection.commit()
    connection.close()

    return redirect(url_for("student_drives"))