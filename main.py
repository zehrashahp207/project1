from flask import Flask, request, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from user import load_users, save_users
from password import is_strong_password
from rezervasiya import rezerv, load_reservations, save_reservations
from dotenv import load_dotenv
import os
from contactpage import contact_bp  
from rezervasiya import rezerv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")
USERS_FILE = "users.json"

# Blueprint-lər
app.register_blueprint(contact_bp)
app.register_blueprint(rezerv)

# Ana səhifə
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/haqqında")
def haqqinda():
    return render_template("about.html")

@app.route("/Ana_səhifə")
def homee():
    return render_template("ana_sehife.html")

# Qeydiyyat
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

        # ✅ Qeydiyyatdan sonra dashboard-a yönləndiririk
        return redirect(url_for("dashboard"))

    return render_template("register.html")


# Giriş
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

            # ✅ İstifadəçi dashboard-a yönləndirilir
            return redirect(url_for("dashboard"))
        else:
            flash("Email və ya şifrə yanlışdır!")
            return redirect(url_for("login"))

    return render_template("login.html")

# Rezervasiya səhifəsi
@app.route("/rezervasiya", methods=["GET", "POST"])
def reserve():
    if "user" not in session:
        flash("Zəhmət olmasa əvvəlcə daxil olun.")
        return redirect(url_for("login"))

    if request.method == "POST":
        user_email = session["user"]  # istifadəçi email
        hall = request.form["hall"]
        start = request.form["start"]
        end = request.form["end"]

        # Burada overlaping yoxlaması və rezervasiyanı əlavə et

        flash("Rezervasiya uğurla tamamlandı!")
        return redirect(url_for("rezerv.reserve"))

    # GET request üçün mövcud rezervasiyaları göstər
    reservations = load_reservations()  # nümunə funksiya
    return render_template("rezervasiya.html", reservations=reservations)


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

    # Admin userləri admin səhifəsinə yönləndir
    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    return render_template("dashboard.html", user=user)


# Admin səhifəsi
@app.route("/admin")
def admin():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("dashboard"))

    users = load_users()  # bütün istifadəçiləri yüklə
    user = next((u for u in users if u["email"] == session["user"]), None)
    return render_template("admin.html", user=user, users=users)

@app.route("/admin/reservations")
def view_reservations():
    if "user" not in session or session.get("role") != "admin":
        flash("Bu səhifəyə yalnız admin girə bilər!")
        return redirect(url_for("login"))

    reservations = load_reservations()
    return render_template("admin_reservations.html", reservations=reservations)


# Çıxış
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    flash("Siz çıxış etdiniz.")
    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)