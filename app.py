from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import os
import json
import random
import string
import smtplib
from email.message import EmailMessage
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Products for home page
PRODUCTS = [
    {"name": "IDCODE Topup [BD SERVER]", "img": "https://i.postimg.cc/W4zZYddK/1748714434.png"},
    {"name": "Free Fire Like", "img": "https://i.postimg.cc/t4Cn7sNT/1748714728.png"},
    {"name": "E-Badge/Evo Access (Bd)", "img": "https://i.postimg.cc/Xvtr2QSG/1748714551.png"},
    {"name": "Weekly Lite", "img": "https://i.postimg.cc/WpGdnG9z/1748714560.png"},
    {"name": "Instant Top Up", "img": "https://via.placeholder.com/150?text=Instant"},
    {"name": "Diamond Pack", "img": "https://via.placeholder.com/150?text=Diamond"}
]

HOME_TEMPLATE = """
LOL TOPUP Clone LOL TOPUP Login

## FREE FIRE TOPUP

{% for p in products %}
  {{ p.name }}
{% endfor %}

🏠Home         🎥Tutorial         💎TopUp         📞Contact Us
"""

@app.route("/")
def home():
    return render_template_string(HOME_TEMPLATE, products=PRODUCTS)


# --- OAuth Setup ---
GOOGLE_CLIENT_ID = "916283515013-i03jklnbutcqg0vlortds1tu1tptvulf.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["profile", "email"],
    redirect_url="/google_login_callback"
)
app.register_blueprint(google_bp, url_prefix="/login")


# --- JSON login storage helpers ---

LOGIN_FILE = "login.json"
VERIFY_FILE = "verify_codes.json"
FORGOT_FILE = "forgot_codes.json"

def load_json_file(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("{}")
    with open(filename, "r") as f:
        return json.load(f)

def save_json_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def load_logins():
    return load_json_file(LOGIN_FILE)

def save_logins(data):
    save_json_file(LOGIN_FILE, data)

def load_verify_codes():
    return load_json_file(VERIFY_FILE)

def save_verify_codes(data):
    save_json_file(VERIFY_FILE, data)

def load_forgot_codes():
    return load_json_file(FORGOT_FILE)

def save_forgot_codes(data):
    save_json_file(FORGOT_FILE, data)


# --- Email sending helper (using SMTP) ---
def send_email(to_email, subject, content):
    # NOTE: Replace with your SMTP server details and credentials
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "youremail@gmail.com"
    SMTP_PASS = "yourapppassword"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(content)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Failed to send email:", e)
        return False

#paste the next code here
# --- Signup route ---
SIGNUP_TEMPLATE = """
<h2>Sign Up</h2>
<form method="post">
  Email:<br>
  <input type="email" name="email" required value="{{ request.form.email or '' }}"><br>
  Username:<br>
  <input type="text" name="username" required value="{{ request.form.username or '' }}"><br>
  Password:<br>
  <input type="password" name="password" required><br>
  Confirm Password:<br>
  <input type="password" name="confirm_password" required><br>
  <button type="submit">Sign Up</button>
</form>
<p style="color:red">{{ error or '' }}</p>
"""

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not username or not password or not confirm_password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            users = load_logins()
            # Check if email or username already exists
            if any(u.get("email") == email for u in users.values()):
                error = "Email already registered."
            elif any(u.get("username") == username for u in users.values()):
                error = "Username already taken."
            else:
                # Create verification code
                code = ''.join(random.choices(string.digits, k=6))
                verify_codes = load_verify_codes()
                verify_codes[email] = {
                    "code": code,
                    "username": username,
                    "password": password  # store plaintext only temporarily until verified
                }
                save_verify_codes(verify_codes)

                # Send verification code by email
                subject = "LOL TOPUP Signup Verification Code"
                content = f"Your verification code is: {code}\nEnter this code on the verification page to activate your account."
                if send_email(email, subject, content):
                    session["pending_email"] = email
                    return redirect(url_for("verify_code"))
                else:
                    error = "Failed to send verification email. Please try again later."

    return render_template_string(SIGNUP_TEMPLATE, error=error, request=request)


# --- Verification code route ---
VERIFY_TEMPLATE = """
<h2>Verify Your Email</h2>
<p>A verification code was sent to {{ email }}.</p>
<form method="post">
  Enter Code:<br>
  <input type="text" name="code" required><br>
  <button type="submit">Verify</button>
</form>
<p style="color:red">{{ error or '' }}</p>
"""

@app.route("/verify", methods=["GET", "POST"])
def verify_code():
    email = session.get("pending_email")
    if not email:
        return redirect(url_for("signup"))
    error = None
    if request.method == "POST":
        entered_code = request.form.get("code", "").strip()
        verify_codes = load_verify_codes()
        data = verify_codes.get(email)
        if not data:
            error = "No verification code found. Please sign up again."
        elif entered_code == data["code"]:
            # Create user account
            users = load_logins()
            new_id = str(max([int(k) for k in users.keys()] + [0]) + 1)  # numeric user_id
            users[new_id] = {
                "email": email,
                "username": data["username"],
                "password": data["password"],  # store plaintext password (for demo; you should hash it!)
                "name": data["username"],     # default name
                "profile_pic": None
            }
            save_logins(users)

            # Remove verification code
            verify_codes.pop(email)
            save_verify_codes(verify_codes)

            session.pop("pending_email")
            flash("Account verified! You can now log in.")
            return redirect(url_for("login"))
        else:
            error = "Incorrect verification code."

    return render_template_string(VERIFY_TEMPLATE, email=email, error=error)


# --- Login route (email/username + password) ---
LOGIN_TEMPLATE = """
<h2>Login</h2>
<form method="post">
  Email or Username:<br>
  <input type="text" name="login_id" required value="{{ request.form.login_id or '' }}"><br>
  Password:<br>
  <input type="password" name="password" required><br>
  <button type="submit">Login</button>
</form>
<p>
  <a href="{{ url_for('signup') }}">Sign Up</a> | <a href="{{ url_for('forgot_password') }}">Forgot Password?</a> | <a href="{{ url_for('login') }}?google=1">Login with Google</a>
</p>
<p style="color:red">{{ error or '' }}</p>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    # If query param google=1, redirect to google oauth
    if request.args.get("google") == "1":
        if google.authorized and session.get("user_id"):
            return redirect(url_for("profile"))
        return redirect(url_for("google.login"))

    error = None
    if request.method == "POST":
        login_id = request.form.get("login_id", "").strip().lower()
        password = request.form.get("password", "")
        users = load_logins()

        # Search user by email or username
        user = None
        for uid, u in users.items():
            if u.get("email", "").lower() == login_id or u.get("username", "").lower() == login_id:
                user = (uid, u)
                break

        if not user:
            error = "User not found."
        elif user[1].get("password") != password:
            error = "Incorrect password."
        else:
            session["user_id"] = user[0]
            return redirect(url_for("profile"))

    return render_template_string(LOGIN_TEMPLATE, error=error, request=request)


# --- Google OAuth callback ---

@app.route("/google_login_callback")
def google_login_callback():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info from Google.", 500
    user_info = resp.json()
    email = user_info["email"]
    user_id = user_info["id"]

    users = load_logins()
    # Save or update user info
    users[user_id] = {
        "email": email,
        "name": user_info.get("name"),
        "profile_pic": user_info.get("picture"),
        "username": email.split("@")[0],  # default username as email prefix
        "password": None
    }
    save_logins(users)

    session["user_id"] = user_id
    return redirect(url_for("profile"))


# --- Profile route ---
PROFILE_TEMPLATE = """
<h2>Profile - LOL TOPUP</h2>
{% if user %}
  <img src="{{ user.profile_pic or 'https://via.placeholder.com/150' }}" alt="Profile Picture" width="150"><br>
  <b>{{ user.name or user.username }}</b><br>
  Email: {{ user.email }}<br>
  <a href="{{ url_for('logout') }}">Logout</a>
{% else %}
  You are not logged in. <a href="{{ url_for('login') }}">Login here</a>
{% endif %}
"""

@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    users = load_logins()
    user = users.get(user_id)
    return render_template_string(PROFILE_TEMPLATE, user=user)


# --- Logout route ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

#paste the next code here
# --- Forgot password route ---
FORGOT_TEMPLATE = """
<h2>Forgot Password</h2>
<form method="post">
  Enter your registered email:<br>
  <input type="email" name="email" required value="{{ request.form.email or '' }}"><br>
  <button type="submit">Send Reset Code</button>
</form>
<p style="color:red">{{ error or '' }}</p>
"""

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        users = load_logins()
        # Find user by email
        user_id = None
        for uid, u in users.items():
            if u.get("email", "").lower() == email:
                user_id = uid
                break
        if not user_id:
            error = "Email not found."
        else:
            # Create reset code and save it
            code = ''.join(random.choices(string.digits, k=6))
            forgot_codes = load_forgot_codes()
            forgot_codes[email] = {
                "code": code,
                "user_id": user_id
            }
            save_forgot_codes(forgot_codes)

            # Send reset code email
            subject = "LOL TOPUP Password Reset Code"
            content = f"Your password reset code is: {code}\nEnter this code on the reset page to change your password."
            if send_email(email, subject, content):
                session["forgot_email"] = email
                return redirect(url_for("reset_password"))
            else:
                error = "Failed to send reset email. Please try again later."

    return render_template_string(FORGOT_TEMPLATE, error=error, request=request)


# --- Reset password route ---
RESET_TEMPLATE = """
<h2>Reset Password</h2>
<p>A reset code was sent to {{ email }}.</p>
<form method="post">
  Enter Reset Code:<br>
  <input type="text" name="code" required><br>
  New Password:<br>
  <input type="password" name="new_password" required><br>
  Confirm Password:<br>
  <input type="password" name="confirm_password" required><br>
  <button type="submit">Reset Password</button>
</form>
<p style="color:red">{{ error or '' }}</p>
"""

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("forgot_email")
    if not email:
        return redirect(url_for("forgot_password"))
    error = None
    if request.method == "POST":
        entered_code = request.form.get("code", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            error = "Passwords do not match."
        else:
            forgot_codes = load_forgot_codes()
            data = forgot_codes.get(email)
            if not data:
                error = "No reset code found. Please try forgot password again."
            elif entered_code != data["code"]:
                error = "Incorrect reset code."
            else:
                # Update password
                users = load_logins()
                user_id = data["user_id"]
                if user_id in users:
                    users[user_id]["password"] = new_password
                    save_logins(users)
                    # Remove reset code
                    forgot_codes.pop(email)
                    save_forgot_codes(forgot_codes)
                    session.pop("forgot_email")
                    flash("Password reset successful! Please login.")
                    return redirect(url_for("login"))
                else:
                    error = "User not found."

    return render_template_string(RESET_TEMPLATE, email=email, error=error)


# --- IDCODE Topup route (existing) ---
IDCODE_TEMPLATE = """
<h2>IDCODE Topup [BD SERVER]</h2>
<a href="{{ url_for('home') }}">LOL TOPUP Home</a> | <a href="{{ url_for('logout') }}">Logout</a>

{% if error %}
  <p style="color:red">{{ error|safe }}</p>
{% endif %}

<form method="post">
  <h3>1. Select Recharge</h3>
  {% for val, label, price in [
      ('25','25 Diamond','24 TK'),
      ('50','50 Diamond','40 TK'),
      ('115','115 Diamond','80 TK'),
      ('240','240 Diamond','159 TK'),
      ('355','355 Diamond','240 TK'),
      ('480','480 Diamond','318 TK'),
      ('505','505 Diamond','349 TK'),
      ('610','610 Diamond','407 TK'),
      ('850','850 Diamond','563 TK'),
      ('1090','1090 Diamond','735 TK'),
      ('1240','1240 Diamond','803 TK'),
      ('2530','2530 Diamond','1606 TK'),
      ('5060','5060 Diamond','3213 TK'),
      ('10120','10120 Diamond','6427 TK'),
      ('weekly','Weekly','158 TK'),
      ('monthly','Monthly','785 TK'),
      ('weekly-lite','Weekly Lite','40 TK')
      ] %}
    <input type="radio" name="diamond" value="{{ val }}" id="d{{ loop.index }}"
    {% if (request.form.diamond or '') == val %}checked{% endif %}>
    <label for="d{{ loop.index }}">{{ label }} - {{ price }}</label><br>
  {% endfor %}

  <h3>2. Account Info</h3>
  Player ID (UID): <input type="text" name="player_id" value="{{ request.form.player_id or '' }}" required><br>

  <h3>3. Select Payment Option</h3>
  <input type="radio" name="payment" value="wallet" id="wallet"
  {% if (request.form.payment or 'wallet') == 'wallet' %}checked{% endif %}>
  <label for="wallet">Wallet Pay</label>

  <input type="radio" name="payment" value="instant" id="instant"
  {% if request.form.payment == 'instant' %}checked{% endif %}>
  <label for="instant">Instant Pay</label><br><br>

  <button type="submit">Order</button>
</form>

<div><b>Note:</b> Please double-check your
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
