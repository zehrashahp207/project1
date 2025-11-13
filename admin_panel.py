from flask import Blueprint, render_template, redirect, url_for, flash, session, request
import json, os

admin_bp = Blueprint("admin_bp", __name__, template_folder="templates")

RESERV_FILE = "reservations.json"


# ======== Köməkçi funksiyalar ========
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


# ======== ADMIN PANEL ========
@admin_bp.route("/admin-panel")
def admin_panel():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()

    pending = [r for r in reservations if r.get("status") in (None, "pending")]
    approved = [r for r in reservations if r.get("status") == "active"]
    rejected = [r for r in reservations if r.get("status") == "rejected"]

    return render_template(
        "admin_panel.html",
        pending=pending,
        approved=approved,
        rejected=rejected
    )


# ======== REZERVASİYANIN TƏSDİQİ ========
@admin_bp.route("/admin-panel/approve/<int:index>", methods=["POST"])
def approve_reservation(index):
    if "user" not in session or session.get("role") != "admin":
        flash("Yalnız admin təsdiqləyə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()
    if 0 <= index < len(reservations):
        reservations[index]["status"] = "active"
        save_reservations(reservations)
        flash("Rezervasiya təsdiqləndi ✅")
    else:
        flash("Rezerv tapılmadı!")

    return redirect(url_for("admin_bp.admin_panel"))


# ======== REZERVASİYANIN RƏDD EDİLMƏSİ ========
@admin_bp.route("/admin-panel/reject/<int:index>", methods=["POST"])
def reject_reservation(index):
    if "user" not in session or session.get("role") != "admin":
        flash("Yalnız admin rədd edə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()
    if 0 <= index < len(reservations):
        reservations[index]["status"] = "rejected"
        save_reservations(reservations)
        flash("Rezervasiya rədd edildi ❌")
    else:
        flash("Rezerv tapılmadı!")

    return redirect(url_for("admin_bp.admin_panel"))
