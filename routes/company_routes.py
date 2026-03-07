from app import app
import sqlite3

from flask import render_template, request, redirect, url_for, session, flash
from flask import send_from_directory,current_app
import os
from utils.decorators import login_required, role_required, company_approval_required

@app.route("/company/dashboard")
@login_required
@role_required("company")
@company_approval_required
def company_dashboard():
    return render_template("company/dashboard.html")

@app.route("/company/create_drive", methods = ['POST','GET'])
@login_required
@role_required("company")
@company_approval_required
def create_drive():

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        eligibility_cgpa = request.form["eligibility_cgpa"]
        drive_date = request.form["drive_date"]
        last_date_to_apply = request.form["last_date_to_apply"]

        connection = sqlite3.connect("placement.db")
        cursor = connection.cursor()

        user_id = session["user_id"]

        cursor.execute(
            "SELECT id FROM companies WHERE user_id = ?",
            (user_id,)
        )

        company = cursor.fetchone()
        company_id = company[0]

        cursor.execute(
            """
            INSERT INTO placement_drives
            (company_id,title, description, eligibility_cgpa, drive_date, last_date_to_apply)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (company_id,title,description,eligibility_cgpa,drive_date,last_date_to_apply)
        )
        connection.commit()
        connection.close()

        flash("placement drive created, waiting for approval")
        return redirect(url_for("company_dashboard"))

    return render_template("company/create_drive.html")

@app.route("/company/drives")
@login_required
@role_required("company")
@company_approval_required
def company_drives():

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    user_id = session["user_id"]

    cursor.execute(
        "SELECT id FROM companies WHERE user_id = ?",
        (user_id,)
    )

    company = cursor.fetchone()
    company_id = company[0]

    cursor.execute(
        """
        SELECT id, title, eligibility_cgpa, drive_date, status
        FROM placement_drives
        WHERE company_id = ?
        ORDER BY drive_date DESC
        """,
        (company_id,)
    )
    drives = cursor.fetchall()

    connection.close()

    return render_template("company/drives.html", drives = drives)

@app.route("/company/applicants/<int:drive_id>")
@login_required
@role_required("company")
@company_approval_required
def view_applicants(drive_id):

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
    """ 
    SELECT applications.id,
           students.name,
           users.email,
           students.branch,
           students.cgpa,
           students.skills,
           students.resume_path,
           applications.status
    FROM applications
    JOIN students ON applications.student_id = students.id
    JOIN users ON students.user_id = users.id
    WHERE applications.drive_id = ?
    """,
    (drive_id,)
    )

    applicants = cursor.fetchall()

    connection.close()

    return render_template("company/applicants.html",applicants = applicants)

@app.route("/company/update_application/<int:app_id>/<status>")
@login_required
@role_required("company")
@company_approval_required
def update_application(app_id, status):

    if status not in ["shortlisted", "selected", "rejected","placed"]:
        flash("Invalid status")
        return redirect(url_for("company_dashboard"))

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE applications
        SET status = ?
        WHERE id = ?
        """,
        (status, app_id)
    )

    connection.commit()
    connection.close()

    flash("Application status updated successfully")

    return redirect(request.referrer)

@app.route("/download_resume/<filename>")
@login_required
@role_required("company")
@company_approval_required
def download_resume(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    return send_from_directory(upload_folder, filename, as_attachment=True)

@app.route("/company/close_drive/<int:drive_id>")
@login_required
@role_required("company")
@company_approval_required
def close_drive(drive_id):

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE placement_drives
        SET status='closed'
        WHERE id=?
        """,
        (drive_id,)
    )

    connection.commit()
    connection.close()

    flash("Drive closed successfully")

    return redirect(url_for("company_drives"))

@app.route("/company/shortlisted/<int:drive_id>")
@login_required
@role_required("company")
@company_approval_required
def shortlisted_students(drive_id):

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT students.name,
               users.email,
               students.branch,
               students.cgpa
        FROM applications
        JOIN students
            ON applications.student_id = students.id
        JOIN users
            ON students.user_id = users.id
        WHERE applications.drive_id = ?
        AND applications.status = 'shortlisted'
        """,
        (drive_id,)
    )

    students = cursor.fetchall()

    connection.close()

    return render_template(
        "company/shortlisted.html",
        students=students
    )