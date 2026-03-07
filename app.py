from flask import Flask
from database import init_db
import os

app = Flask(__name__)
app.secret_key = "this is a secret key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

from routes.auth_routes import *
from routes.student_routes import *
from routes.company_routes import *
from routes.admin_routes import *

if __name__ == "__main__":
    init_db()
    app.run(debug=True)