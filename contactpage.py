from flask import Blueprint, request, jsonify, render_template
import json, re, smtplib, time, traceback
from pathlib import Path
from ipaddress import ip_address
from email.mime.text import MIMEText

contact_bp = Blueprint("contact_bp", __name__, template_folder="templates")

PRIMARY = "#2A314D"
JSON_PATH = Path("messages.json")
last_submit_by_ip = {}

# SMTP konfigurasiya
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "info@aesma.edu.az"          # Buraya öz gmail ünvanını yaz
EMAIL_PASS = "EMAIL_SIFREN_BURADA"        # Buraya Gmail App Password yaz
EMAIL_TO = "info@aesma.edu.az"   # Mesajı qəbul edən email

def init_json():
    if not JSON_PATH.exists():
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

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
    except Exception:
        print("Email göndərilərkən xəta:")
        traceback.print_exc()

@contact_bp.get("/əlaqə")
def əlaqə():
    return render_template("contact.html", primary=PRIMARY)

@contact_bp.post("/api/əlaqə")
def api_əlaqə():
    data = request.get_json(force=True, silent=True) or {}
    errors = validate_payload(data)
    if errors:
        return jsonify({"error": "; ".join(f"{k}: {v}" for k, v in errors.items())}), 400

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

@contact_bp.get("/admin/messages")
def admin_messages():
    init_json()
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        messages = json.load(f)
    return render_template("admin_messages.html", messages=messages, primary=PRIMARY)

