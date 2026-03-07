import sqlite3
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("you need to login first")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") != required_role:
                flash("you are not authorized")
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
            "SELECT approval_status FROM companies WHERE user_id=?",
            (user_id,)
        )

        result = cursor.fetchone()

        if result is None or result[0] != "approved":
            flash("Company not approved yet")
            connection.close()
            return redirect(url_for("home"))

        connection.close()
        return f(*args, **kwargs)

    return wrapper