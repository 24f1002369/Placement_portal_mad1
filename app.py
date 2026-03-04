import sqlite3
from flask import Flask,render_template,request,redirect,url_for,flash,session
from database import init_db
from  werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # check logic here
        if "user_id" not in session:
            flash("you need to login first")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            
            if  session.get("role") != required_role:
                flash("you are not authorized to access this page")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return wrapper
    return decorator

def company_approval_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")

        connection = sqlite3.connect("placement.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT approval_status FROM companies WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()

        if result is None or result[0] != "approved":
            flash("Your company account is not approved yet")
            connection.close()
            return redirect(url_for("home"))
        connection.close()
        return f(*args, **kwargs)
    return wrapper




app.secret_key = "this is a secret key"

@app.route("/")
def home():
    portal_name = "Placement portal MAD 1"
    return render_template("home.html", name = portal_name)

@app.route("/register",methods = ['GET','POST'])
def register():
    if request.method == "POST":

        # extract the fields from post
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        role = request.form["role"].strip()

        # validate them and flash error msg
        if not email or not password or not role:
            flash("ALL fields are required")
            return redirect(url_for("register"))
        
        if role not in ["student","company"]:
            flash("Allowed roles are student and company only")
            return redirect(url_for("register"))
        
        if len(password) <6:
            flash("password should be atleast 6 characters or more") 
            return redirect(url_for("register"))

        hashed_passwword = generate_password_hash(password)

    
        if role == "student":
            # extract student fields
            roll_number = request.form["roll_number"].strip()
            branch = request.form["branch"].strip()
            cgpa_raw = request.form["cgpa"].strip()
            phone = request.form["phone"]

            try:
                cgpa = float(cgpa_raw)
            except ValueError:
                flash("CGPA must be a valid number")
                return redirect(url_for("register"))
            if not (0 <= cgpa <= 10):
                flash("CGPA must be between 0 and 10")
                return redirect(url_for("register"))
            
            if not roll_number or not branch or not cgpa_raw or not phone:
                flash("All student fields are required")
                return redirect(url_for("register"))
                
                
                
        elif role == "company":
            # extract company fields
            company_name = request.form["company_name"].strip()
            location = request.form["location"].strip()
            website = request.form["website"].strip()
            description = request.form["description"].strip()

            if not company_name or not location:
                flash("company name and location are required")
                return redirect(url_for("register"))
                
        connection = sqlite3.connect("placement.db")
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        try:
            cursor.execute(
                "INSERT INTO users (email,password,role) VALUES (?,?,?)",
                (email, hashed_passwword, role)
            )
            user_id = cursor.lastrowid

            if role == "student":
                cursor.execute(
                    "INSERT INTO students (user_id,roll_number,branch,cgpa,phone) VALUES (?,?,?,?,?)",
                    (user_id, roll_number, branch, cgpa, phone)
                )
            
            elif role == "company":
                cursor.execute(
                    "INSERT INTO companies (user_id, company_name, location, website, description) VALUES (?,?,?,?,?)",
                    (user_id, company_name, location, website, description)
                )
            connection.commit()


            if role == "student":
                flash("student registration successful, you will be rediredted to login page")
            else:
                flash("company registration successful, you will be rediredted to login page after admin approval")

            return redirect(url_for("login"))
        
        except sqlite3.IntegrityError:
            connection.rollback()
            flash("Email or roll number already exists")
            return redirect(url_for("register"))
 
        finally:
            connection.close()

    return render_template("register.html")

@app.route("/login",methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        if not email or not password:
            flash("All the fields are required")
            return redirect(url_for("login"))
        
        connection = sqlite3.connect("placement.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id,password,role FROM users WHERE email = ?",
            (email,)
        )
        user = cursor.fetchone()

        if user == None:
            flash("Invalid credentials")
            connection.close()
            return redirect(url_for("login"))
        
        user_id = user[0]
        hashed_password = user[1]
        role = user[2]

        if not check_password_hash(hashed_password, password):
            flash("Invalid credentials")
            connection.close()
            return redirect(url_for("login"))
        
        session["user_id"] = user_id
        session["role"] = role

        connection.close()

        if role == "student":
            return redirect(url_for("student_dashboard"))
        elif role == "company":
            return redirect(url_for("company_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))                    
    return render_template("login.html")
    
@app.route("/student/dashboard")
@login_required
@role_required("student")
def student_dashboard():
    return render_template("student/dashboard.html")

@app.route("/company/dashboard")
@login_required
@role_required("company")
@company_approval_required
def company_dashboard():
    return render_template("company/dashboard.html")

@app.route("/admin/dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    connection = sqlite3.connect("placement.db")

    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, company_name, location FROM companies WHERE approval_status = 'pending'"
    )
    companies = cursor.fetchall()
    connection.close()

    return render_template("admin/dashboard.html",companies = companies)

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug = True)