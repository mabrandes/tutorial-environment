from flask import Flask, request, render_template_string, redirect, url_for, session
import psycopg2
import os
from passlib.context import CryptContext

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To
import socket
import json


app = Flask(__name__)
app.secret_key = "your_flask_secret_key"  # Required for session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PROJECT_ROOT = os.getcwd()
with open(os.path.join(PROJECT_ROOT,'authorization.json'), 'r') as json_file:
    auth_keys = json.load(json_file)


# === DB Connection ===
def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

# === Templates ===
SIGNUP_TEMPLATE = """
<!doctype html>
<title>Sign Up</title>
<h1>Sign Up</h1>
<form action="/signup" method="post">
  Name: <input name="name" type="text"><br>
  Email: <input name="email" type="email"><br>
  Password: <input name="password" type="password"><br>
  Salary: <input name="salary" type="number" step="0.01"><br>
  <button type="submit">Sign Up</button>
</form>
<p>Already have an account? <a href="/signin">Sign In</a></p>
"""

SIGNIN_TEMPLATE = """
<!doctype html>
<title>Sign In</title>
<h1>Sign In</h1>
<form action="/signin" method="post">
  Email: <input name="email" type="email"><br>
  Password: <input name="password" type="password"><br>
  <button type="submit">Sign In</button>
</form>
<p><a href="/forgot-password">Forgot password?</a></p>
<p>Don't have an account? <a href="/signup">Sign Up</a></p>
"""

WELCOME_TEMPLATE = """
<!doctype html>
<title>Welcome</title>
<h1>Welcome, {{ user_name }}!</h1>
<p><a href="/">View Users</a> | <a href="/logout">Logout</a></p>
"""

FORGOT_TEMPLATE = """
<!doctype html>
<title>Forgot Password</title>
<h1>Forgot Password</h1>
<form action="/forgot-password" method="post">
  Enter your email: <input name="email" type="email"><br>
  <button type="submit">Reset Password</button>
</form>
<p><a href="/signin">Back to Sign In</a></p>
"""

USERS_TEMPLATE = """
<!doctype html>
<title>Users</title>
<h1>Users</h1>
<ul>
{% for user in users %}
  <li>{{ user[1] }} ({{ user[2] }}) — Salary: {{ user[4] }}</li>
{% endfor %}
</ul>
<p><a href="/signup">Sign Up</a> | <a href="/signin">Sign In</a></p>
"""

# === Routes ===
@app.route("/")
def index():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return render_template_string(USERS_TEMPLATE, users=users)
    except Exception as e:
        return f"Error accessing DB: {e}", 500

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        salary = request.form.get("salary", "0").strip()

        if not name or not email or not password:
            return "Missing name, email, or password.", 400

        hashed_password = pwd_context.hash(password)

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (name, email, password, salary) VALUES (%s, %s, %s, %s)",
                (name, email, hashed_password, salary or 0)
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("signin"))
        except Exception as e:
            return f"Error signing up: {e}", 500

    return render_template_string(SIGNUP_TEMPLATE)

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return "Missing email or password.", 400

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and pwd_context.verify(password, user[3]):
                session["user_id"] = user[0]
                session["user_name"] = user[1]
                return render_template_string(WELCOME_TEMPLATE, user_name=user[1])
            else:
                return "Invalid email or password.", 401

        except Exception as e:
            return f"Error signing in: {e}", 500

    return render_template_string(SIGNIN_TEMPLATE)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            return "Missing email.", 400

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            if not user:
                cur.close()
                conn.close()
                return "No user found with this email.", 404

            # Generate temporary password
            new_password = "NewPass" + str(socket.gethostname())[:4]  # example simple temp password
            hashed_password = pwd_context.hash(new_password)

            # Update in DB
            cur.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
            conn.commit()
            cur.close()
            conn.close()

            # Send email
            SENDGRID_API_KEY = auth_keys["sendMail"]["SENDGRID_API_KEY"]
            SRC_MAIL = auth_keys["empaMail"]

            message = Mail(
                from_email=SRC_MAIL,
                to_emails=email,
                subject=f"[Password Reset] New Password for {socket.gethostname()}",
                plain_text_content=f"Hello,\n\nYour new temporary password is: {new_password}\n\nPlease sign in and change it immediately."
            )

            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)

            return f"New password has been sent to {email}. Check your inbox.", 200

        except Exception as e:
            return f"Error resetting password: {e}", 500
        
    return render_template_string(FORGOT_TEMPLATE)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))

# === Add user (original "add" route, kept for completeness) ===
@app.route("/add", methods=["POST"])
def add_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    salary = request.form.get("salary", "0").strip()

    if not name or not email or not password:
        return "Missing name, email, or password.", 400

    hashed_password = pwd_context.hash(password)

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password, salary) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, salary or 0)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/")
    except Exception as e:
        return f"Error adding user: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
