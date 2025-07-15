from flask import Flask, request, render_template_string, redirect
import psycopg2
import os

app = Flask(__name__)

# Template for displaying users
TEMPLATE = """
<!doctype html>
<title>Users</title>
<h1>Users</h1>
<ul>
{% for user in users %}
  <li>{{ user[1] }} ({{ user[2] }}) — Salary: {{ user[4] }}</li>
{% endfor %}
</ul>

<h2>Add new user</h2>
<form action="/add" method="post">
  Name: <input name="name" type="text"><br>
  Email: <input name="email" type="email"><br>
  Password: <input name="password" type="password"><br>
  Salary: <input name="salary" type="number" step="0.01"><br>
  <button type="submit">Add User</button>
</form>
"""

def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

@app.route("/")
def index():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return render_template_string(TEMPLATE, users=users)
    except Exception as e:
        return f"Error accessing DB: {e}", 500

@app.route("/add", methods=["POST"])
def add_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    salary = request.form.get("salary", "0").strip()

    if not name or not email or not password:
        return "Missing name, email, or password.", 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password, salary) VALUES (%s, %s, %s, %s)",
            (name, email, password, salary or 0)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/")
    except Exception as e:
        return f"Error adding user: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
