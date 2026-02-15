import sqlite3
from flask import Flask,render_template,request,redirect,url_for,flash
from database import init_db
from  werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)

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

        connection = sqlite3.connect("placements.db")
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        try:
            cursor.execute(
                "INSERT INTO users (email,password,role) VALUES (?,?,?)",
                (email, hashed_passwword, role)
            )
            user_id = cursor.lastrowid
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
                
                cursor.execute(
                    "INSERT INTO students (user_id,roll_number,branch,cgpa,phone) VALUES (?,?,?,?,?)",
                    (user_id, roll_number, branch, cgpa, phone)
                )
                
            elif role == "company":
                pass

            
            connection.commit()
            flash("registration successful")
            return redirect(url_for("home"))
        
        except sqlite3.IntegrityError:
            connection.rollback()
            flash("Email or roll number already exists")
            return redirect(url_for("register"))
        
        finally:
            connection.close()

    return render_template("register.html") 

if __name__ == "__main__":
    init_db()
    app.run(debug = True)