from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import os
import json

rezerv = Blueprint("rezerv", __name__, template_folder="templates")

RESERV_FILE = "reservations.json"

# Rezervasiyaları yüklə
def load_reservations():
    if not os.path.exists(RESERV_FILE):
        return []
    with open(RESERV_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# Rezervasiyaları yadda saxla
def save_reservations(reservations):
    with open(RESERV_FILE, "w", encoding="utf-8") as f:
        json.dump(reservations, f, ensure_ascii=False, indent=4)

# Rezervasiya səhifəsi
@rezerv.route("/rezervasiya", methods=["GET", "POST"])
def reserve():
    if "user" not in session:
        flash("Zəhmət olmasa əvvəlcə daxil olun.")
        return redirect(url_for("login"))

    if request.method == "POST":
        hall = request.form.get("hall")
        date = request.form.get("date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        user_email = session["user"]

        if not hall or not date or not start_time or not end_time:
            flash("Bütün sahələr doldurulmalıdır!")
            return redirect(url_for("rezerv.reserve"))

        reservations = load_reservations()

        # Üst-üstə düşmə yoxlanışı
        for r in reservations:
            if r["hall"] == hall and r["date"] == date:
                if not (end_time <= r["start_time"] or start_time >= r["end_time"]):
                    flash(f"Bu vaxt aralığı artıq rezerv olunub! ({r['start_time']} - {r['end_time']})")
                    return redirect(url_for("rezerv.reserve"))

        # Yeni rezervi əlavə et
        reservations.append({
            "hall": hall,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "user": user_email
        })
        save_reservations(reservations)
        flash(f"Rezervasiya uğurla əlavə olundu: {date} {start_time}-{end_time}")
        return redirect(url_for("rezerv.reserve"))

    reservations = load_reservations()
    return render_template("rezervasiya.html", reservations=reservations)