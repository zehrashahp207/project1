from flask import Flask, request, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from user import load_users, save_users
from password import is_strong_password
from rezervasiya import rezerv, load_reservations, save_reservations
from dotenv import load_dotenv
import os
from contactpage import contact_bp  

# --- Yükləmələr və ayarlar ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")
USERS_FILE = "users.json"

# --- Blueprint-lər ---
app.register_blueprint(contact_bp)
app.register_blueprint(rezerv)
from admin_panel import admin_bp
app.register_blueprint(admin_bp)

from flask import Flask, request, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from user import load_users, save_users
from password import is_strong_password
from rezervasiya import rezerv, load_reservations, save_reservations
from dotenv import load_dotenv
import os
from contactpage import contact_bp  

# --- Yükləmələr və ayarlar ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")
USERS_FILE = "users.json"

# --- Blueprint-lər ---
app.register_blueprint(contact_bp)
app.register_blueprint(rezerv)

# --- Ana səhifələr ---
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/haqqında")
def haqqinda():
    return render_template("about.html")

@app.route("/Ana_səhifə")
def homee():
    return render_template("ana_sehife.html")


# --- Qeydiyyat ---
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
        flash(f"Qeydiyyat uğurla tamamlandı! Xoş gəldiniz, {username}!")

        return redirect(url_for("dashboard"))

    return render_template("register.html")


# --- Giriş ---
@app.route("/giriş", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        users = load_users()
        user = next((u for u in users if u["email"] == email), None)

        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            session["role"] = user["role"]
            flash(f"Xoş gəldiniz, {user['username']}!")
            return redirect(url_for("dashboard"))
        else:
            flash("Email və ya şifrə yanlışdır!")
            return redirect(url_for("login"))

    return render_template("login.html")


# --- Dashboard ---
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


# --- Admin səhifəsi ---
@app.route("/admin")
def admin():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("dashboard"))

    users = load_users()
    user = next((u for u in users if u["email"] == session["user"]), None)
    return render_template("admin.html", user=user, users=users)


# --- Admin rezervasiyalar səhifəsi ---
@app.route("/admin/reservations")
def view_reservations():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()

    pending_reservations = [r for r in reservations if r.get("status") in (None, "pending")]
    active_reservations = [r for r in reservations if r.get("status") == "active"]
    deleted_reservations = [r for r in reservations if r.get("status") == "deleted"]

    return render_template(
        "admin_rezervasiya.html",
        pending_reservations=pending_reservations,
        active_reservations=active_reservations,
        deleted_reservations=deleted_reservations
    )


# --- Rezervasiyanın təsdiqi ---
@app.route("/admin/reservations/approve/<res_id>", methods=["POST"])
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
        flash("Rezerv tapılmadı!")

    return redirect(url_for("view_reservations"))


# --- Rezervasiyanın ləğvi ---
@app.route("/admin/reservations/delete/<res_id>", methods=["POST"])
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

    return redirect(url_for("view_reservations"))


# --- Çıxış ---
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    flash("Siz çıxış etdiniz.")
    return redirect(url_for("home"))


# --- Əsas giriş nöqtəsi ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
# --- Ana səhifələr ---
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/haqqında")
def haqqinda():
    return render_template("about.html")

@app.route("/Ana_səhifə")
def homee():
    return render_template("ana_sehife.html")


# --- Qeydiyyat ---
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
        flash(f"Qeydiyyat uğurla tamamlandı! Xoş gəldiniz, {username}!")

        return redirect(url_for("dashboard"))

    return render_template("register.html")


# --- Giriş ---
@app.route("/giriş", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        users = load_users()
        user = next((u for u in users if u["email"] == email), None)

        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            session["role"] = user["role"]
            flash(f"Xoş gəldiniz, {user['username']}!")
            return redirect(url_for("dashboard"))
        else:
            flash("Email və ya şifrə yanlışdır!")
            return redirect(url_for("login"))

    return render_template("login.html")


# --- Dashboard ---
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


# --- Admin səhifəsi ---
@app.route("/admin")
def admin():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("dashboard"))

    users = load_users()
    user = next((u for u in users if u["email"] == session["user"]), None)
    return render_template("admin.html", user=user, users=users)


# --- Admin rezervasiyalar səhifəsi ---
@app.route("/admin/reservations")
def view_reservations():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()
    pending_reservations = [r for r in reservations if r.get("status") in (None, "pending")]
    active_reservations = [r for r in reservations if r.get("status") == "active"]
    deleted_reservations = [r for r in reservations if r.get("status") == "deleted"]

    return render_template(
        "admin_reservations.html",
        pending_reservations=pending_reservations,
        active_reservations=active_reservations,
        deleted_reservations=deleted_reservations
    )


# --- Admin tərəfindən rezervasiyanın təsdiqi ---
@app.route("/admin/reservations/approve", methods=["POST"])
def approve_reservation():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu əməliyyatı yalnız admin edə bilər!")
        return redirect(url_for("login"))

    hall = request.form["hall"]
    organization = request.form["organization"]
    email = request.form["email"]
    date = request.form["date"]

    reservations = load_reservations()
    updated = False
    for r in reservations:
        if r["hall"] == hall and r["organization"] == organization and r["email"] == email and r["date"] == date:
            r["status"] = "active"
            updated = True
            break

    if updated:
        save_reservations(reservations)
        flash("Rezervasiya təsdiqləndi ✅")
    else:
        flash("Rezervasiya tapılmadı!")

    return redirect(url_for("view_reservations"))


@app.route("/admin/reservations/delete", methods=["POST"])
def delete_reservation():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu əməliyyatı yalnız admin edə bilər!")
        return redirect(url_for("login"))

    hall = request.form["hall"]
    organization = request.form["organization"]
    email = request.form["email"]
    date = request.form["date"]

    reservations = load_reservations()
    updated = False
    for r in reservations:
        if r["hall"] == hall and r["organization"] == organization and r["email"] == email and r["date"] == date:
            r["status"] = "deleted"
            updated = True
            break

    if updated:
        save_reservations(reservations)
        flash("Rezervasiya ləğv edildi ❌")
    else:
        flash("Rezervasiya tapılmadı!")

    return redirect(url_for("view_reservations"))


# --- Çıxış ---
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    flash("Siz çıxış etdiniz.")
    return redirect(url_for("home"))


# --- Əsas giriş nöqtəsi ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)