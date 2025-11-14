from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import os
import json
from datetime import datetime
import uuid  # ID üçün

rezerv = Blueprint("rezerv", __name__, template_folder="templates")

RESERV_FILE = "reservations.json"

# ---- Köməkçi funksiyalar ----
def load_reservations():
    if not os.path.exists(RESERV_FILE):
        return []
    with open(RESERV_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_reservations(reservations):
    with open(RESERV_FILE, "w", encoding="utf-8") as f:
        json.dump(reservations, f, ensure_ascii=False, indent=4)

# ---- Rezervasiya səhifəsi ----
@rezerv.route("/rezervasiya", methods=["GET", "POST"])
def reserve():
    if "user" not in session:
        flash("Zəhmət olmasa əvvəlcə daxil olun.")
        return redirect(url_for("login"))

    user_email = session["user"]

    if request.method == "POST":
        hall = request.form.get("hall")
        organization = request.form.get("organization")
        name = request.form.get("name")
        date = request.form.get("date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        # --- Boş sahə yoxlanışı ---
        if not all([hall, organization, name, date, start_time, end_time]):
            flash("Bütün sahələr doldurulmalıdır!")
            return redirect(url_for("rezerv.reserve"))

        # --- Keçmiş tarixlərin bloklanması (ƏSAS DƏYİŞİKLİK) ---
        today = datetime.now().date()
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()

        if selected_date < today:
            flash("Keçmiş tarixə rezervasiya etmək mümkün deyil!")
            return redirect(url_for("rezerv.reserve"))

        reservations = load_reservations()

        # Vaxtların datetime çevrilməsi
        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")

        # --- Başlama və bitmə vaxtı yoxlanışı ---
        if end_dt <= start_dt:
            flash("Bitmə vaxtı başlanğıc vaxtından sonra olmalıdır!")
            return redirect(url_for("rezerv.reserve"))

        # --- Eyni zal üçün vaxt üst-üstə düşməsin ---
        for r in reservations:
            if r["hall"] == hall and r["date"] == date and r.get("status") != "deleted":
                r_start = datetime.strptime(f"{r['date']} {r['start_time']}", "%Y-%m-%d %H:%M")
                r_end = datetime.strptime(f"{r['date']} {r['end_time']}", "%Y-%m-%d %H:%M")
                
                if not (end_dt <= r_start or start_dt >= r_end):
                    flash(f"{hall} zalı {date} tarixində {r['start_time']} - {r['end_time']} aralığında artıq doludur!")
                    return redirect(url_for("rezerv.reserve"))

        # --- Yeni rezerv obyekti ---
        new_rez = {
            "id": str(uuid.uuid4()),
            "hall": hall,
            "organization": organization,
            "name": name,
            "email": user_email,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "user": user_email,
            "status": "pending",
            "notification": "Rezervasiyanız göndərildi, admin təsdiqini gözləyir ⏳"
        }

        reservations.append(new_rez)
        save_reservations(reservations)

        flash(f"Rezervasiya uğurla əlavə olundu: {hall} ({date} {start_time}-{end_time})")
        return redirect(url_for("rezerv.my_reservations"))

    # GET istəyində tarix minimum üçün göndəririk
    current_date = datetime.now().strftime("%Y-%m-%d")
    return render_template("rezervasiya.html", user_email=user_email, current_date=current_date)

# ---- Öz rezervlərini görmək ----
@rezerv.route("/menim_rezervlerim")
def my_reservations():
    if "user" not in session:
        flash("Əvvəlcə daxil olun.")
        return redirect(url_for("login"))

    user_email = session["user"]
    reservations = load_reservations()

    # İstifadəçinin bütün rezervasiyaları, ləğv olunmuşlar da daxil
    user_reservations = [
        {**r} for r in reservations if r.get("user") == user_email
    ]

    return render_template("menim_rezervlerim.html", reservations=user_reservations)


# ---- Rezervasiyanı “silinmiş” kimi işarələmək ----
@rezerv.route("/rezervasiya/sil", methods=["POST"])
def delete_reservation():
    if "user" not in session:
        flash("Əvvəlcə daxil olun.")
        return redirect(url_for("login"))

    user_email = session["user"]
    hall = request.form.get("hall")
    organization = request.form.get("organization")

    reservations = load_reservations()

    for r in reservations:
        if r.get("hall") == hall and r.get("organization") == organization and r.get("user") == user_email and r.get("status") != "deleted":
            r["status"] = "deleted"
            r["notification"] = "Siz bu rezervasiyanı silmisiniz ❌"
            save_reservations(reservations)
            flash("Rezervasiya silindi (admin paneldə görünəcək).")
            return redirect(url_for("rezerv.my_reservations"))

    flash("Belə rezerv tapılmadı!")
    return redirect(url_for("rezerv.my_reservations"))

