from app import app
import sqlite3
from flask import render_template,request, redirect, url_for, session, flash
from utils.decorators import login_required, role_required

import os
from werkzeug.utils import secure_filename
from flask import current_app


def get_connection():
    connection = sqlite3.connect("placement.db")
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/student/dashboard")
@login_required
@role_required("student")
def student_dashboard():

    connection = get_connection()
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT * FROM students WHERE user_id=?",
        (user_id,)
    )

    student = cursor.fetchone()

    student_id = student["id"]

    # Application statistics
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

    # PROFILE COMPLETION SCORE
    fields = [
        student["phone"],
        student["linkedin"],
        student["portfolio"],
        student["skills"],
        student["resume_path"]
    ]

    completed = sum(1 for f in fields if f)
    profile_score = int((completed / len(fields)) * 100)

    # SMART DRIVE RECOMMENDATIONS

    cursor.execute(
        """
        SELECT placement_drives.id,
               companies.company_name,
               placement_drives.title,
               placement_drives.eligibility_cgpa,
               placement_drives.required_skills,
               placement_drives.drive_date
        FROM placement_drives
        JOIN companies
        ON placement_drives.company_id = companies.id
        WHERE placement_drives.status='approved'
        ORDER BY placement_drives.drive_date ASC
        """
    )

    drives = cursor.fetchall()

    recommended = []

    student_skills = set()

    if student["skills"]:
        student_skills = {
            s.strip().lower()
            for s in student["skills"].split(",")
        }

    for drive in drives:

        cgpa_ok = student["cgpa"] >= drive["eligibility_cgpa"]

        skill_ok = True

        if drive["required_skills"]:

            required_skills = {
                s.strip().lower()
                for s in drive["required_skills"].split(",")
            }

            # required skills must be subset of student skills
            skill_ok = required_skills.issubset(student_skills)

        if cgpa_ok and skill_ok:
            recommended.append(drive)

    # show only top 3 recommendations
    recommended = recommended[:3]

    return render_template(
        "student/dashboard.html",
        applied=applied,
        shortlisted=shortlisted,
        selected=selected,
        placed=placed,
        profile_score=profile_score,
        recommended=recommended
    )


@app.route("/student/profile", methods=["GET","POST"])
@login_required
@role_required("student")
def student_profile():

    connection = get_connection()
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

            os.makedirs(upload_folder,exist_ok=True)

            upload_path = os.path.join(upload_folder, filename)

            resume.save(upload_path)

            resume_path = filename

            cursor.execute(
                """
                UPDATE students
                SET name=?, phone=?, linkedin=?, portfolio=?, skills=?, resume_path=?
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
        flash("Profile updated successfully")

    cursor.execute(
        """
        SELECT *
        FROM students
        WHERE user_id=?
        """,
        (user_id,)
    )

    student = cursor.fetchone()

    connection.close()

    return render_template("student/profile.html", student=student)


@app.route("/student/drives")
@login_required
@role_required("student")
def student_drives():

    connection = get_connection()
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT * FROM students WHERE user_id=?",
        (user_id,)
    )

    student = cursor.fetchone()

    cursor.execute(
        """
        SELECT placement_drives.id,
               companies.company_name,
               placement_drives.title,
               placement_drives.eligibility_cgpa,
               placement_drives.eligible_branches,
               placement_drives.required_skills,
               placement_drives.drive_date,
               placement_drives.last_date_to_apply
        FROM placement_drives
        JOIN companies ON placement_drives.company_id = companies.id
        WHERE placement_drives.status='approved'
        ORDER BY placement_drives.drive_date ASC
        """
    )

    drives = cursor.fetchall()

    eligible_drives = []
    not_eligible_drives = []

    for drive in drives:

        cgpa_ok = student["cgpa"] >= drive["eligibility_cgpa"]

        branch_ok = True
        if drive["eligible_branches"]:
            branch_ok = student["branch"] in drive["eligible_branches"]

        skill_ok = True
        if drive["required_skills"] and student["skills"]:
            skill_ok = student["skills"].lower() in drive["required_skills"].lower()

        if cgpa_ok and branch_ok and skill_ok:
            eligible_drives.append(drive)
        else:
            not_eligible_drives.append(drive)

    connection.close()

    return render_template(
        "student/drives.html",
        eligible_drives=eligible_drives,
        not_eligible_drives=not_eligible_drives
    )


@app.route("/student/applications")
@login_required
@role_required("student")
def student_applications():

    connection = get_connection()
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT id FROM students WHERE user_id=?",
        (user_id,)
    )

    student_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        SELECT companies.company_name,
               placement_drives.title,
               applications.status,
               applications.applied_at
        FROM applications
        JOIN placement_drives ON applications.drive_id = placement_drives.id
        JOIN companies ON placement_drives.company_id = companies.id
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

    connection = get_connection()
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT id FROM students WHERE user_id=?",
        (user_id,)
    )

    student_id = cursor.fetchone()["id"]

    cursor.execute(
        "SELECT last_date_to_apply,status FROM placement_drives WHERE id=?",
        (drive_id,)
    )

    drive = cursor.fetchone()

    from datetime import date

    if date.today().isoformat() > drive["last_date_to_apply"]:
        flash("Application deadline has passed")
        return redirect(url_for("student_drives"))

    if drive["status"] != "approved":
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