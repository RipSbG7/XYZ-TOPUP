from flask import Flask, render_template_string, request, url_for, redirect, session, flash
import random
import string

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Dummy user DB: {email: {password: ..., verified: bool, verify_code: ..., reset_code: ...}}
USERS = {}

# Dummy mail sending (replace with real mail logic)
def send_email(to_email, subject, body):
    print(f"Sending email to {to_email}\nSubject: {subject}\nBody:\n{body}\n")

PRODUCTS = [
    {"name": "IDCODE Topup [BD SERVER]", "img": "https://i.postimg.cc/W4zZYddK/1748714434.png"},
    {"name": "Free Fire Like", "img": "https://i.postimg.cc/t4Cn7sNT/1748714728.png"},
    {"name": "E-Badge/Evo Access (Bd)", "img": "https://i.postimg.cc/Xvtr2QSG/1748714551.png"},
    {"name": "Weekly Lite", "img": "https://i.postimg.cc/WpGdnG9z/1748714560.png"},
    {"name": "Instant Top Up", "img": "https://via.placeholder.com/150?text=Instant"},
    {"name": "Diamond Pack", "img": "https://via.placeholder.com/150?text=Diamond"},
]

# --- Part 1: Home and Signup templates/routes ---

HOME_TEMPLATE = """
<!doctype html>
<title>LOL TOPUP Clone - Home</title>
<h1>LOL TOPUP Clone - Home</h1>
<nav>
  <a href="{{ url_for('home') }}">🏠Home</a> |
  {% if 'email' in session %}
    Welcome, {{ session['email'] }} |
    <a href="{{ url_for('logout') }}">Logout</a>
  {% else %}
    <a href="{{ url_for('login') }}">Login</a> |
    <a href="{{ url_for('signup') }}">Sign Up</a>
  {% endif %}
</nav>
<hr>
<h2>Products</h2>
<ul>
{% for p in products %}
  <li><img src="{{ p.img }}" alt="{{ p.name }}" style="height:80px;vertical-align:middle;"> {{ p.name }}</li>
{% endfor %}
</ul>
"""

SIGNUP_TEMPLATE = """
<!doctype html>
<title>Sign Up - LOL TOPUP</title>
<h1>Sign Up</h1>
<form method="post">
  Email:<br><input type="email" name="email" required value="{{ request.form.email or '' }}"><br>
  Password:<br><input type="password" name="password" required><br>
  Confirm Password:<br><input type="password" name="confirm_password" required><br>
  <button type="submit">Sign Up</button>
</form>
<p><a href="{{ url_for('login') }}">Already have an account? Login</a></p>
{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}
"""

@app.route("/")
def home():
    return render_template_string(HOME_TEMPLATE, products=PRODUCTS)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if email in USERS:
            error = "Email already registered. Please login or use another email."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            verify_code = ''.join(random.choices(string.digits, k=6))
            USERS[email] = {
                "password": password,
                "verified": False,
                "verify_code": verify_code,
                "reset_code": None,
            }
            send_email(email, "LOL TOPUP Email Verification",
                       f"Your verification code is: {verify_code}")
            session["pending_verification_email"] = email
            return redirect(url_for("verify_email"))
    return render_template_string(SIGNUP_TEMPLATE, error=error, request=request)
  # --- Part 2: Login, Verification, Forgot Password templates and routes ---

LOGIN_TEMPLATE = """
<!doctype html>
<title>Login - LOL TOPUP</title>
<h1>Login</h1>
<form method="post">
  Email:<br><input type="email" name="email" required value="{{ request.form.email or '' }}"><br>
  Password:<br><input type="password" name="password" required><br>
  <button type="submit">Login</button>
</form>
<p><a href="{{ url_for('signup') }}">No account? Sign Up</a></p>
<p><a href="{{ url_for('forgot_password') }}">Forgot password?</a></p>
{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}
"""

VERIFY_TEMPLATE = """
<!doctype html>
<title>Email Verification - LOL TOPUP</title>
<h1>Email Verification</h1>
<p>A verification code has been sent to {{ email }}. Please enter it below:</p>
<form method="post">
  Verification Code:<br><input type="text" name="code" required><br>
  <button type="submit">Verify</button>
</form>
{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}
"""

FORGOT_PASSWORD_TEMPLATE = """
<!doctype html>
<title>Forgot Password - LOL TOPUP</title>
<h1>Forgot Password</h1>
<form method="post">
  Enter your registered email:<br>
  <input type="email" name="email" required value="{{ request.form.email or '' }}"><br>
  <button type="submit">Send Reset Code</button>
</form>
<p><a href="{{ url_for('login') }}">Back to Login</a></p>
{% if message %}
<p style="color:green;">{{ message }}</p>
{% endif %}
{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}
"""

RESET_PASSWORD_TEMPLATE = """
<!doctype html>
<title>Reset Password - LOL TOPUP</title>
<h1>Reset Password</h1>
<form method="post">
  Email:<br><input type="email" name="email" required value="{{ request.form.email or '' }}"><br>
  Reset Code:<br><input type="text" name="code" required><br>
  New Password:<br><input type="password" name="new_password" required><br>
  Confirm New Password:<br><input type="password" name="confirm_new_password" required><br>
  <button type="submit">Reset Password</button>
</form>
<p><a href="{{ url_for('login') }}">Back to Login</a></p>
{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}
"""

@app.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    email = session.get("pending_verification_email")
    if not email or email not in USERS:
        return redirect(url_for("signup"))
    error = None
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if code == USERS[email]["verify_code"]:
            USERS[email]["verified"] = True
            USERS[email]["verify_code"] = None
            session.pop("pending_verification_email")
            flash("Email verified! You can now login.")
            return redirect(url_for("login"))
        else:
            error = "Invalid verification code."
    return render_template_string(VERIFY_TEMPLATE, email=email, error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = USERS.get(email)
        if not user:
            error = "No account found with that email."
        elif not user["verified"]:
            error = "Email not verified. Please verify your email first."
            session["pending_verification_email"] = email
            return redirect(url_for("verify_email"))
        elif user["password"] != password:
            error = "Incorrect password."
        else:
            session["email"] = email
            flash("Logged in successfully.")
            return redirect(url_for("home"))
    return render_template_string(LOGIN_TEMPLATE, error=error, request=request)
  @app.route("/logout")
def logout():
    session.pop("email", None)
    flash("Logged out.")
    return redirect(url_for("home"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None
    message = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if email not in USERS:
            error = "No account found with that email."
        else:
            reset_code = ''.join(random.choices(string.digits, k=6))
            USERS[email]["reset_code"] = reset_code
            send_email(email, "LOL TOPUP Password Reset Code",
                       f"Your password reset code is: {reset_code}")
            message = "Reset code sent to your email."
    return render_template_string(FORGOT_PASSWORD_TEMPLATE, error=error, message=message, request=request)

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        code = request.form.get("code", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_new_password = request.form.get("confirm_new_password", "")
        user = USERS.get(email)

        if not user:
            error = "No account found with that email."
        elif user.get("reset_code") != code:
            error = "Invalid reset code."
        elif new_password != confirm_new_password:
            error = "Passwords do not match."
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters."
        else:
            user["password"] = new_password
            user["reset_code"] = None
            flash("Password reset successful. Please login.")
            return redirect(url_for("login"))
    return render_template_string(RESET_PASSWORD_TEMPLATE, error=error, request=request)

# --- Part 3 end ---
# --- Part 4: IDCODE Topup page ---

IDCODE_TEMPLATE = """
<!doctype html>
<title>IDCODE Topup [BD SERVER] - LOL TOPUP</title>
<h1>IDCODE Topup [BD SERVER]</h1>
<nav>
  <a href="{{ url_for('home') }}">Home</a> |
  <a href="{{ url_for('login') }}">Login</a>
</nav>
<hr>

{% if error %}
<p style="color:red;">{{ error|safe }}</p>
{% endif %}

<form method="post">
  <h2>1. Select Recharge</h2>
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
    <input type="radio" id="{{ val }}" name="diamond" value="{{ val }}" {% if request.form.diamond == val %}checked{% endif %}>
    <label for="{{ val }}">{{ label }} — {{ price }}</label><br>
  {% endfor %}

  <h2>2. Account Info</h2>
  <label for="player-id">Player ID (UID)</label><br>
  <input type="text" id="player-id" name="player_id" placeholder="Player ID (UID)" value="{{ request.form.player_id or '' }}"><br>

  <h2>3. Select one payment option</h2>
  <input type="radio" id="wallet-pay" name="payment" value="wallet" {% if (request.form.payment or 'wallet') == 'wallet' %}checked{% endif %}>
  <label for="wallet-pay">Wallet Pay</label><br>
  <input type="radio" id="instant-pay" name="payment" value="instant" {% if request.form.payment == 'instant' %}checked{% endif %}>
  <label for="instant-pay">Instant Pay</label><br><br>

  <button type="submit">Submit Order</button>
</form>

<p><b>Note:</b> Please double-check your Player ID. Payments once made cannot be refunded.</p>
"""

@app.route("/idcode-topup", methods=["GET", "POST"])
def idcode_topup():
    error = None
    if request.method == "POST":
        diamond = request.form.get("diamond")
        player_id = request.form.get("player_id")
        payment_method = request.form.get("payment")

        errors = []
        if not diamond:
            errors.append("Please select a diamond package.")
        if not player_id or player_id.strip() == "":
            errors.append("Please enter your Player ID (UID).")
        if not payment_method:
            errors.append("Please select a payment method.")

        if errors:
            error = "<br>".join(errors)
        else:
            return f"""
            <!DOCTYPE html>
            <html><head><title>Order Success</title>
            <style>
              body {{ font-family: Arial, sans-serif; padding: 40px; background: #f5f7fa; text-align: center; }}
              a {{ text-decoration: none; color: #b72647; font-weight: 700; }}
              h2 {{ color: #b72647; margin-bottom: 25px; }}
            </style>
            </head><body>
            <h2>Order received! {diamond} diamonds for Player ID {player_id} using {payment_method}.</h2>
            <a href="{url_for('idcode_topup')}">Make another order</a>
            </body></html>
            """
    return render_template_string(IDCODE_TEMPLATE, error=error, request=request)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
