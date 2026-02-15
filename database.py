import sqlite3

def init_db():
    connection = sqlite3.connect("placement.db")
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # create an users table(only once when app runs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
            )                           
    """)

    # check if admin already exists
    cursor.execute(" SELECT * FROM users WHERE role = 'admin'")
    admin = cursor.fetchone()

    # if no admin exists,insert default admin
    if admin == None:
        cursor.execute(
            "INSERT INTO users (email,password,role,is_active) VALUES (?,?,?,?)",
            ('admin1@placementportal.com','admin1','admin',1))
    
    # create students table
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            roll_number INTEGER UNIQUE NOT NULL,
            branch TEXT NOT NULL,
            cgpa REAL CHECK(cgpa >= 0 AND cgpa <= 10),
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)                        
        """)
    
    # create companies table
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            company_name TEXT UNIQUE NOT NULL,
            location TEXT NOT NULL,
            website TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)                        
        """)
    
    # create placement_drives table
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS placement_drives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            eligibility_cgpa REAL CHECK(eligibility_cgpa >= 0 AND eligibility_cgpa <= 10),
            drive_date TEXT NOT NULL,
            last_date_to_apply TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE)                        
    """)

    # create applications table
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            drive_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'applied'
                CHECK(status IN ('applied','shortlisted','rejected','selected')),
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE, 
            FOREIGN KEY(drive_id) REFERENCES placement_drives(id) ON DELETE CASCADE,
            UNIQUE(student_id,drive_id))                     
    """)

    connection.commit()
    connection.close()