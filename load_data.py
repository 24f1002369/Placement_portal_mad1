import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("placement.db")
cursor = conn.cursor()

# Sample students
students = [
("student1@demo.com","student","CSE",8.5,"Python,SQL,Flask"),
("student2@demo.com","student","ECE",7.8,"Java,SQL"),
]

for email,role,branch,cgpa,skills in students:

    cursor.execute(
        "INSERT INTO users (email,password,role) VALUES (?,?,?)",
        (email,generate_password_hash("1234"),role)
    )

    user_id = cursor.lastrowid

    cursor.execute(
        """INSERT INTO students
        (user_id,name,roll_number,branch,cgpa,skills)
        VALUES (?,?,?,?,?,?)""",
        (user_id,email.split("@")[0],100+user_id,branch,cgpa,skills)
    )

# Sample company
cursor.execute(
    "INSERT INTO users (email,password,role) VALUES (?,?,?)",
    ("company@demo.com",generate_password_hash("1234"),"company")
)

company_user = cursor.lastrowid

cursor.execute(
"""
INSERT INTO companies
(user_id,company_name,location,approval_status)
VALUES (?,?,?,?)
""",
(company_user,"TechCorp","Bangalore","approved")
)

company_id = cursor.lastrowid

# Sample drive
cursor.execute(
"""
INSERT INTO placement_drives
(company_id,title,eligibility_cgpa,eligible_branches,required_skills,drive_date,last_date_to_apply,status)
VALUES (?,?,?,?,?,?,?,?)
""",
(company_id,"Software Engineer",7,"CSE,ECE","Python,SQL","2026-04-10","2026-04-01","approved")
)

conn.commit()
conn.close()

print("Sample data loaded successfully")