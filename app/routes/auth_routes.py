from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from app.db import get_db
from app.models import get_user_by_username, log_activity
from functools import wraps

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            user_role = session.get("role")
            if user_role not in roles and "System Administrator" not in user_role:
                flash(f"Access denied. Required role: {', '.join(roles)}", "danger")
                return redirect(url_for("disaster.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["full_name"] = user["full_name"]

            log_activity(user["id"], user["username"], user["role"], "LOGIN", "User logged into emergency system")
            flash(f"Welcome back, {user['full_name']} ({user['role']})!", "success")
            return redirect(url_for("disaster.dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    if "user_id" in session:
        log_activity(session["user_id"], session["username"], session["role"], "LOGOUT", "User logged out")
        session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
