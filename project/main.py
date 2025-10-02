from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from user import load_users, save_users
from password import is_strong_password
from dotenv import load_dotenv
import os
from pathlib import Path
from ipaddress import ip_address
import json
import re
import smtplib
from email.mime.text import MIMEText
import time
import traceback

load_dotenv()  # .env yüklənməsi app yaradılmadan əvvəl olmalıdır

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # SESSION üçün secret key

PRIMARY = "#2A314D"
JSON_PATH = Path("messages.json")
last_submit_by_ip = {}

# SMTP konfigurasiya
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "info@aesma.edu.az"
EMAIL_PASS = os.getenv("EMAIL_PASS")  # .env faylından al
EMAIL_TO = "info@aesma.edu.az"

# JSON faylını yoxla və yarat
def init_json():
    if not JSON_PATH.exists():
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

# Mesajı JSON fayla yaz
def save_message_json(first_name, last_name, email, message, ip):
    init_json()
    with open(JSON_PATH, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "message": message,
            "ip": str(ip),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()

# Validatorlar
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FIRST_NAME_RE = re.compile(r"^[A-ZƏİÖÜÇŞĞ][a-zəiöüçşğ]+$")
LAST_NAME_RE = re.compile(r"^[A-ZƏİÖÜÇŞĞ][a-zəiöüçşğ]+$")

def validate_payload(data: dict):
    errors = {}
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    hp = (data.get("hp") or "").strip()

    if not FIRST_NAME_RE.match(first_name):
        errors["first_name"] = "Ad düzgün deyil."
    if not LAST_NAME_RE.match(last_name):
        errors["last_name"] = "Soyad düzgün deyil."
    if not EMAIL_RE.match(email):
        errors["email"] = "Email düzgün deyil."
    if not (10 <= len(message) <= 2000):
        errors["message"] = "Mesaj 10–2000 simvol olmalıdır."
    if hp:
        errors["hp"] = "Bot şübhəsi (honeypot doludur)."
    return errors

# Email göndərən funksiya
def send_email(first_name, last_name, email, message):
    subject = f"Yeni mesaj: {first_name} {last_name}"
    body = f"Ad: {first_name}\nSoyad: {last_name}\nEmail: {email}\nMesaj:\n{message}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            print("Email göndərildi.")
    except Exception as e:
        print("Email göndərilərkən xəta:")
        traceback.print_exc()

# Kontakt səhifəsi
@app.get("/contact")
def contact_page():
    return render_template("contact.html", primary=PRIMARY)

# API POST — Əlaqə formu
@app.post("/api/contact")
def api_contact():
    data = request.get_json(force=True, silent=True) or {}
    errors = validate_payload(data)
    if errors:
        return jsonify({"error": "; ".join(f"{k}: {v}" for k, v in errors.items())}), 400

    # IP və Rate Limit
    try:
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
        client_ip = ip_address(client_ip)
    except Exception:
        client_ip = "0.0.0.0"

    now = time.time()
    last = last_submit_by_ip.get(client_ip)
    if last and (now - last) < 15:
        return jsonify({"error": "Çox tez-tez göndərirsiniz. 15 saniyə sonra yenidən cəhd edin."}), 429
    last_submit_by_ip[client_ip] = now

    save_message_json(
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        email=data["email"].strip(),
        message=data["message"].strip(),
        ip=client_ip
    )

    send_email(
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        email=data["email"].strip(),
        message=data["message"].strip()
    )

    return jsonify({"ok": True})

# Admin mesajlara baxış
@app.get("/admin/messages")
def admin_messages():
    init_json()
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        messages = json.load(f)
    return render_template("admin_messages.html", messages=messages, primary=PRIMARY)

USERS_FILE = "users.json"

# Ana səhifə
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/əlaqə")
def əlaqə():
    return render_template("contact.html")

@app.route("/haqqında")
def haqqinda():
    return render_template("about.html")

@app.route("/Ana_səhifə")
def homee():
    return render_template("ana_sehife.html")

# Qeydiyyat
@app.route("/qeydiyyat", methods=["GET", "POST"])
def register():
    users = load_users()
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

        if any(user["email"] == email for user in users):
            flash("Bu email artıq qeydiyyatdan keçib!")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        role = "admin" if not users else "user"

        users.append({
            "username": username,
            "surname": surname,
            "email": email,
            "password": hashed_password,
            "role": role
        })
        save_users(users)
        session["user"] = email
        session["role"] = role
        flash(f"Qeydiyyat uğurla tamamlandı! Rolunuz: {role}")
        return redirect(url_for("dashboard"))

    return render_template("register.html")

# Giriş
@app.route("/giriş", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        users = load_users()
        user = next((u for u in users if u["email"] == email), None)

        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            session["role"] = user["role"]
            flash(f"Xoş gəldiniz, {user['username']}! Rolunuz: {user['role']}")
            return redirect(url_for("dashboard"))
        else:
            flash("Email və ya şifrə yanlışdır!")
            return redirect(url_for("login"))

    return render_template("login.html")

# Dashboard
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

    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    return render_template("dashboard.html", user=user)

# Admin səhifəsi
@app.route("/admin")
def admin():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("dashboard"))

    users = load_users()
    user = next((u for u in users if u["email"] == session["user"]), None)
    return render_template("admin.html", user=user, users=users)

# Çıxış
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    flash("Siz çıxış etdiniz.")
    return redirect(url_for("login"))

# Əsas giriş nöqtəsi
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 1453))
    app.run(debug=True, host="0.0.0.0", port=PORT)
