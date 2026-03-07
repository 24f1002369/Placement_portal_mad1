from app import app
import sqlite3

from flask import render_template, redirect, request,  url_for, flash

from utils.decorators import login_required, role_required

@app.route("/admin/dashboard")
@login_required
@role_required("admin")
def admin_dashboard():

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    # Pending companies
    cursor.execute(
        "SELECT id, company_name, location FROM companies WHERE approval_status='pending'"
    )
    companies = cursor.fetchall()

    # Pending placement drives
    cursor.execute(
        """
        SELECT placement_drives.id,
               companies.company_name,
               placement_drives.title,
               placement_drives.drive_date
        FROM placement_drives
        JOIN companies
            ON placement_drives.company_id = companies.id
        WHERE placement_drives.status='pending'
        """
    )
    pending_drives = cursor.fetchall()

    # Statistics
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM placement_drives")
    total_drives = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "admin/dashboard.html",
        companies=companies,
        pending_drives=pending_drives,
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications
    )

@app.route("/admin/manage")
@login_required
@role_required("admin")
def admin_manage():

    search = request.args.get("search")

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    if search:

        cursor.execute(
            """
            SELECT students.name,
                   students.roll_number,
                   students.branch,
                   students.cgpa,
                   students.phone
            FROM students
            WHERE name LIKE ? OR roll_number LIKE ? OR phone LIKE ?
            """,
            (f"%{search}%", f"%{search}%", f"%{search}%")
        )
        students = cursor.fetchall()

        cursor.execute(
            """
            SELECT company_name, location, approval_status
            FROM companies
            WHERE company_name LIKE ?
            """,
            (f"%{search}%",)
        )
        companies = cursor.fetchall()

    else:
        students = []
        companies = []

    connection.close()

    return render_template(
        "admin/manage.html",
        students=students,
        companies=companies
    )

@app.route("/approve_company/<int:company_id>")
@login_required
@role_required("admin")
def approve_company(company_id):
    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE companies SET approval_status = 'approved' WHERE id = ?",
        (company_id,)
    )
    connection.commit()
    connection.close()

    flash("company approved successfully")

    return redirect(url_for("admin_dashboard"))

@app.route("/reject_company/<int:company_id>")
@login_required
@role_required("admin")
def reject_company(company_id):
    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE companies SET approval_status = 'rejected' WHERE id = ?",
        (company_id,)
    )
    connection.commit()
    connection.close()

    flash("company rejected")

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/approve_drive/<int:drive_id>")
@login_required
@role_required("admin")
def approve_drive(drive_id):

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE placement_drives SET status='approved' WHERE id=?",
        (drive_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject_drive/<int:drive_id>")
@login_required
@role_required("admin")
def reject_drive(drive_id):

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE placement_drives SET status='rejected' WHERE id=?",
        (drive_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/placements")
@login_required
@role_required("admin")
def admin_placements():

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT students.name,
               companies.company_name,
               placement_drives.title,
               applications.status,
               applications.applied_at
        FROM applications
        JOIN students
            ON applications.student_id = students.id
        JOIN placement_drives
            ON applications.drive_id = placement_drives.id
        JOIN companies
            ON placement_drives.company_id = companies.id
        WHERE applications.status = 'placed'
        ORDER BY applications.applied_at DESC
        """
    )

    placements = cursor.fetchall()

    connection.close()

    return render_template(
        "admin/placements.html",
        placements=placements
    )

@app.route("/admin/analytics")
@login_required
@role_required("admin")
def admin_analytics():

    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()

    # Applications per company
    cursor.execute(
        """
        SELECT companies.company_name, COUNT(applications.id)
        FROM applications
        JOIN placement_drives
            ON applications.drive_id = placement_drives.id
        JOIN companies
            ON placement_drives.company_id = companies.id
        GROUP BY companies.company_name
        """
    )
    company_data = cursor.fetchall()

    company_names = [row[0] for row in company_data]
    application_counts = [row[1] for row in company_data]

    # Placement status distribution
    cursor.execute(
        """
        SELECT status, COUNT(*)
        FROM applications
        GROUP BY status
        """
    )

    status_data = cursor.fetchall()

    statuses = [row[0] for row in status_data]
    status_counts = [row[1] for row in status_data]

    connection.close()

    return render_template(
        "admin/analytics.html",
        company_names=company_names,
        application_counts=application_counts,
        statuses=statuses,
        status_counts=status_counts
    )