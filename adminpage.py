from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from rezervasiya import load_reservations, save_reservations

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

# --- Admin rezervasiyalar səhifəsi ---
@admin_bp.route("/reservations")
def view_reservations():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()

    # Statuslara görə ayırırıq
    pending = [r for r in reservations if r.get("status") in (None, "pending")]
    approved = [r for r in reservations if r.get("status") == "active"]
    deleted = [r for r in reservations if r.get("status") == "deleted"]

    return render_template(
        "admin_rezervasiya.html",
        pending_reservations=pending,
        active_reservations=approved,
        deleted_reservations=deleted
    )
# --- Rezervasiyanın təsdiqi ---
@admin_bp.route("/reservations/approve/<res_id>", methods=["POST"])
def approve_reservation(res_id):
    if "user" not in session or session.get("role") != "admin":
        flash("Bu əməliyyatı yalnız admin edə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()
    for r in reservations:
        if str(r.get("id")) == res_id or str(reservations.index(r)) == res_id:
            r["status"] = "active"
            save_reservations(reservations)
            flash("Rezervasiya təsdiqləndi ✅")
            break
    else:
        flash("Rezervasiya tapılmadı!")

    return redirect(url_for("admin_bp.view_reservations"))


# --- Rezervasiyanın ləğvi ---
@admin_bp.route("/reservations/delete/<res_id>", methods=["POST"])
def delete_reservation(res_id):
    if "user" not in session or session.get("role") != "admin":
        flash("Bu əməliyyatı yalnız admin edə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()
    for r in reservations:
        if str(r.get("id")) == res_id or str(reservations.index(r)) == res_id:
            r["status"] = "deleted"
            save_reservations(reservations)
            flash("Rezervasiya ləğv edildi ❌")
            break
    else:
        flash("Rezerv tapılmadı!")

    return redirect(url_for("admin_bp.view_reservations"))