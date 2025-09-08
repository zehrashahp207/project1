from flask import Flask, request, render_template, redirect, url_for, flash, session
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import re
app = Flask(__name__)
app.secret_key = "supersecretkey"
USERS_FILE = "users.json"
# JSON fayl yoxdursa yaradılır
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)
# İstifadəçiləri yüklə və yadda saxla
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)
# Şifrənin güclülüyünü yoxla
def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True
# İlk açılışda login səhifəsi
@app.route("/")
def home():
    users = load_users()
    if not users:
        flash("İlk öncə qeydiyyatdan keçin.")
        return redirect(url_for("register"))
    return redirect(url_for("login"))
# Register səhifəsi
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        surname = request.form["surname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm"]
        if password != confirm:
            flash("Şifrələr eyni deyil!")
            return redirect(url_for("register"))
        if not is_strong_password(password):
            flash("Şifrə zəifdir! Ən az 8 simvol, böyük/kiçik hərf, rəqəm və xüsusi simvol olmalıdır.")
            return redirect(url_for("register"))
        users = load_users()
        if any(user["email"] == email for user in users):
            flash("Bu email artıq qeydiyyatdan keçib!")
            return redirect(url_for("register"))
        hashed_password = generate_password_hash(password)
        users.append({
            "username": username,
            "surname": surname,
            "email": email,
            "password": hashed_password
        })
        save_users(users)
        flash("Qeydiyyat uğurla tamamlandı!")
        session["user"] = email  # Avtomatik login
        return redirect(url_for("dashboard"))
    return render_template("register.html")
# Login səhifəsi
@app.route("/login", methods=["GET", "POST"])
def login():
    users = load_users()
    if not users:
        flash("İlk öncə qeydiyyatdan keçin.")
        return redirect(url_for("register"))
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = next((u for u in users if u["email"] == email), None)
        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            flash(f"Xoş gəldiniz, {user['username']}!")
            return redirect(url_for("dashboard"))
        else:
            flash("Email və ya şifrə yanlışdır!")
            return redirect(url_for("login"))
    return render_template("login.html")
# Dashboard səhifəsi
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Zəhmət olmasa əvvəlcə daxil olun.")
        return redirect(url_for("login"))
    users = load_users()
    user = next((u for u in users if u["email"] == session["user"]), None)
    if not user:
        flash("İstifadəçi tapılmadı!")
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=user)
# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Siz çıxış etdiniz.")
    return redirect(url_for("login"))
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",port=1453)