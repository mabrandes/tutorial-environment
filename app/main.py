from flask import Flask, request, render_template_string, redirect
import random
import hashlib
import requests
import json
import time

app = Flask(__name__)

# Example database endpoints (could be real URLs)
databases = [
    "http://db1.example.com",
    "http://db2.example.com"
]

# Template string (could also use a separate .html file)
TEMPLATE = """
<!doctype html>
<title>Links</title>
<h1>Links</h1>
<ul>
{% for link in links %}
  <li>#{{ link.rank }} - <a href="{{ link.url }}">{{ link.title }}</a> (Points: {{ link.points }})</li>
{% endfor %}
</ul>

<h2>Post a new link</h2>
<form action="/post" method="post">
  URL: <input name="url" type="text"><br>
  Title: <input name="title" type="text"><br>
  <button type="submit">Post</button>
</form>
"""

@app.route("/")
def index():
    db = random.choice(databases)
    try:
        response = requests.get(db)
        response.raise_for_status()
        links = response.json().get("Links", [])
        for i, link in enumerate(links):
            link["rank"] = i + 1
        return render_template_string(TEMPLATE, links=links)
    except Exception as e:
        return f"Error contacting DB: {e}", 500

@app.route("/post", methods=["POST"])
def post_link():
    url_input = request.form.get("url", "").strip()
    title = request.form.get("title", "").strip()

    if not url_input or not title:
        return "Missing URL or Title", 400

    # Create an ID using sha1
    id_hash = hashlib.sha1(url_input.encode()).hexdigest()
    link_id = int(id_hash[:4], 16)  # Just a short ID example

    payload = {
        "ID": link_id,
        "URL": url_input,
        "Title": title
    }

    db = random.choice(databases)
    try:
        res = requests.post(f"{db}/post", json=payload)
        res.raise_for_status()
    except Exception as e:
        return f"Error posting to DB: {e}", 500

    return redirect("/")

@app.route("/vote", methods=["POST"])
def vote():
    link_id = request.form.get("id")
    if not link_id:
        return "Missing ID", 400

    payload = {"ID": int(link_id)}

    db = random.choice(databases)
    try:
        res = requests.post(f"{db}/vote", json=payload)
        res.raise_for_status()
    except Exception as e:
        return f"Error voting: {e}", 500

    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
