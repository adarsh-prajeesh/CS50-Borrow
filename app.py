import json
from cs50 import SQL
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from pywebpush import webpush, WebPushException
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, inr, login_required

app = Flask(__name__)
app.jinja_env.filters["inr"] = inr

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///borrow.db")

# Helper function to generate or get existing VAPID keys


def get_vapid_keys():
    keys = db.execute("SELECT * FROM vapid_keys LIMIT 1;")
    if keys:
        return keys[0]["private_key"], keys[0]["public_key"]

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_key = private_key.public_key()

    # FIX HERE: Changed Encoding.X509 -> Encoding.PEM
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    db.execute("INSERT INTO vapid_keys (private_key, public_key) VALUES (?, ?);",
               private_pem, public_pem)
    return private_pem, public_pem

# Helper function to trigger notification


def send_push_notification(user_id, title, body, url="/lend"):
    subs = db.execute(
        "SELECT subscription_json FROM push_subscriptions WHERE user_id = ?;", user_id)
    private_key, public_key = get_vapid_keys()

    for sub in subs:
        try:
            webpush(
                subscription_info=json.loads(sub["subscription_json"]),
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=private_key,
                vapid_claims={"sub": "mailto:adarshprajeesh@icloud.com"}
            )
        except WebPushException as ex:
            print(f"Failed to send notification: {ex}")

# --- Push Notification Endpoints ---


@app.route("/vapid_public_key", methods=["GET"])
def vapid_public_key():
    _, public_key = get_vapid_keys()
    return jsonify({"publicKey": public_key})


@app.route("/subscribe_push", methods=["POST"])
@login_required
def subscribe_push():
    subscription_data = request.get_json()
    if subscription_data:
        sub_str = json.dumps(subscription_data)
        # Avoid duplicate subscriptions
        existing = db.execute(
            "SELECT * FROM push_subscriptions WHERE user_id = ? AND subscription_json = ?;",
            session["user_id"], sub_str
        )
        if not existing:
            db.execute(
                "INSERT INTO push_subscriptions (user_id, subscription_json) VALUES (?, ?);",
                session["user_id"], sub_str
            )
    return jsonify({"success": True})

# --- Updated Request Route with Push Notification Trigger ---


@app.route("/request", methods=["GET", "POST"])
@login_required
def request_money():
    """Request money from another user."""

    if request.method == "POST":
        lender_id = request.form.get("lender_id")
        amount = request.form.get("amount")

        if not lender_id:
            return apology("must select a lender", 400)

        try:
            amount = float(amount)
            if amount <= 0:
                return apology("amount must be greater than zero", 400)
        except (ValueError, TypeError):
            return apology("invalid amount", 400)

        if int(lender_id) == session["user_id"]:
            return apology("cannot request money from yourself", 400)

        # Insert new request into database
        db.execute(
            "INSERT INTO requests (borrower_id, lender_id, amount) VALUES (?, ?, ?);",
            session["user_id"],
            lender_id,
            amount,
        )

        # Get borrower's username to show in notification
        borrower = db.execute("SELECT username FROM users WHERE id = ?;", session["user_id"])
        borrower_name = borrower[0]["username"] if borrower else "Someone"

        # Send push notification to the targeted lender
        send_push_notification(
            user_id=int(lender_id),
            title="New Borrow Request!",
            body=f"{borrower_name} requested a loan of ₹{amount:.2f}.",
            url="/lend"
        )

        return redirect("/lend?msg=Borrow+request+sent!")

    else:
        users = db.execute(
            "SELECT id, username FROM users WHERE id != ? ORDER BY username;",
            session["user_id"],
        )
        return render_template("request.html", users=users)


# Configure application
app = Flask(__name__)

# Register INR Jinja filter
app.jinja_env.filters["inr"] = inr

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///borrow.db")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not (request.form.get("password") and request.form.get("confirmation")):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("confirmation password wrong", 400)

        username = request.form.get("username")
        try:
            db.execute(
                "INSERT INTO users (username, hash) VALUES(?, ?)",
                username,
                generate_password_hash(request.form.get("password")),
            )
        except Exception:
            return apology("username already taken", 400)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/", methods=["GET"])
@login_required
def index():
    # Amount lent
    lent = db.execute(
        "SELECT users.username AS name, SUM(transactions.amount) AS amount "
        "FROM transactions JOIN users ON transactions.borrower_id = users.id "
        "WHERE transactions.lender_id = ? GROUP BY users.id, users.username;",
        session["user_id"],
    )

    # MUST include users.id AS id here!
    borrowed = db.execute(
        "SELECT users.id AS id, users.username AS name, SUM(transactions.amount) AS amount "
        "FROM transactions JOIN users ON transactions.lender_id = users.id "
        "WHERE transactions.borrower_id = ? GROUP BY users.id, users.username;",
        session["user_id"],
    )

    total_lent = sum(item["amount"] for item in lent)
    total_borrowed = sum(item["amount"] for item in borrowed)
    net_total = total_lent - total_borrowed

    return render_template(
        "index.html",
        borrowed=borrowed,
        lent=lent,
        total_lent=total_lent,
        total_borrowed=total_borrowed,
        net_total=net_total,
    )


@app.route("/request", methods=["GET", "POST"])
@login_required
def request_money():
    """Request money from another user."""

    if request.method == "POST":
        lender_id = request.form.get("lender_id")
        amount = request.form.get("amount")

        if not lender_id:
            return apology("must select a lender", 400)

        try:
            amount = float(amount)
            if amount <= 0:
                return apology("amount must be greater than zero", 400)
        except (ValueError, TypeError):
            return apology("invalid amount", 400)

        # Cannot request money from yourself
        if int(lender_id) == session["user_id"]:
            return apology("cannot request money from yourself", 400)

        db.execute(
            "INSERT INTO requests (borrower_id, lender_id, amount) VALUES (?, ?, ?);",
            session["user_id"],
            lender_id,
            amount,
        )

        return redirect("/lend?msg=Borrow+request+sent!")

    else:
        users = db.execute(
            "SELECT id, username FROM users WHERE id != ? ORDER BY username;",
            session["user_id"],
        )
        return render_template("request.html", users=users)


@app.route("/lend", methods=["GET"])
@login_required
def lend():
    """View pending lend requests sent to the logged-in user."""

    incoming_requests = db.execute(
        "SELECT requests.request_id, users.username AS borrower, requests.amount "
        "FROM requests "
        "JOIN users ON requests.borrower_id = users.id "
        "WHERE requests.lender_id = ?;",
        session["user_id"],
    )
    return render_template("lend.html", requests=incoming_requests)


@app.route("/handle_request", methods=["POST"])
@login_required
def handle_request():
    """Accept (tick) or reject (cross) a borrow request."""

    request_id = request.form.get("request_id")
    action = request.form.get("action")

    if not request_id or action not in ["accept", "reject"]:
        return apology("invalid action", 400)

    if action == "accept":
        # Redirect to payment page to finalize acceptance and trigger payment notification
        return redirect(f"/payment?action_type=accept_request&target_id={request_id}")

    else:
        # Fetch request details to get borrower_id and amount before deleting
        req = db.execute(
            "SELECT * FROM requests WHERE request_id = ? AND lender_id = ?;",
            request_id,
            session["user_id"],
        )

        if req:
            req = req[0]

            # Get lender's username for the message
            lender = db.execute("SELECT username FROM users WHERE id = ?;", session["user_id"])
            lender_name = lender[0]["username"] if lender else "Lender"

            # Delete the request
            db.execute(
                "DELETE FROM requests WHERE request_id = ? AND lender_id = ?;",
                request_id,
                session["user_id"],
            )

            # Send rejection notification to the borrower
            send_push_notification(
                user_id=req["borrower_id"],
                title="Request Declined ❌",
                body=f"{lender_name} declined your request for ₹{req['amount']:.2f}.",
                url="/"
            )

        return redirect("/lend?msg=Request+rejected!")


@app.route("/repay", methods=["GET", "POST"])
@login_required
def repay():
    """Select a debt to repay"""

    if request.method == "POST":
        lender_id = request.form.get("lender_id")
        if not lender_id:
            return apology("must select a lender", 400)

        return redirect(f"/payment?action_type=repay&target_id={lender_id}")

    else:
        # Fetch active borrowed debts grouped by lender
        borrowed = db.execute(
            "SELECT users.username AS name, SUM(transactions.amount) AS amount, users.id AS id "
            "FROM transactions JOIN users ON transactions.lender_id = users.id "
            "WHERE transactions.borrower_id = ? GROUP BY users.id, users.username;",
            session["user_id"],
        )
        return render_template("repay.html", borrowed=borrowed)


@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    """Dummy Payment Processing Route"""

    if request.method == "POST":
        action_type = request.form.get("action_type")
        target_id = request.form.get("target_id")
        card_number = request.form.get("card_number")

        if not card_number or len(card_number.replace(" ", "")) < 13:
            return apology("invalid card number", 400)

        # 1. Processing an accepted lend request
        if action_type == "accept_request":
            req = db.execute(
                "SELECT * FROM requests WHERE request_id = ? AND lender_id = ?;",
                target_id,
                session["user_id"],
            )
            if req:
                req = req[0]

                # Insert into active transactions
                db.execute(
                    "INSERT INTO transactions (borrower_id, lender_id, amount) VALUES (?, ?, ?);",
                    req["borrower_id"],
                    req["lender_id"],
                    req["amount"],
                )

                # Delete request from pending table
                db.execute("DELETE FROM requests WHERE request_id = ?;", target_id)

                # Get lender name for the notification message
                lender = db.execute("SELECT username FROM users WHERE id = ?;", session["user_id"])
                lender_name = lender[0]["username"] if lender else "Your lender"

                # Trigger push notification to the BORROWER
                send_push_notification(
                    user_id=req["borrower_id"],
                    title="Request Accepted! 🎉",
                    body=f"{lender_name} accepted your request of ₹{req['amount']:.2f}.",
                    url="/"
                )

                msg = "Lend+request+accepted!"

        # 2. Processing a loan repayment
        elif action_type == "repay":
            # Optional: Notify lender that loan was repaid
            lender_id = target_id

            # Fetch borrower name
            borrower = db.execute("SELECT username FROM users WHERE id = ?;", session["user_id"])
            borrower_name = borrower[0]["username"] if borrower else "Borrower"

            db.execute(
                "DELETE FROM transactions WHERE borrower_id = ? AND lender_id = ?;",
                session["user_id"],
                lender_id,
            )

            # Notify the lender that they were paid back
            send_push_notification(
                user_id=int(lender_id),
                title="Loan Repaid! 💰",
                body=f"{borrower_name} has repaid their loan in full.",
                url="/"
            )

            msg = "Loan+repaid+successfully!"

        else:
            return apology("invalid payment action", 400)

        return redirect(f"/?msg={msg}")

    else:
        action_type = request.args.get("action_type")
        target_id = request.args.get("target_id")

        if not action_type or not target_id:
            return apology("missing payment details", 400)

        user = db.execute("SELECT username FROM users WHERE id = ?;", session["user_id"])
        username = user[0]["username"] if user else "User"

        return render_template(
            "payment.html",
            username=username,
            action_type=action_type,
            target_id=target_id,
        )


@app.route("/vapid_public_key", methods=["GET"])
def vapid_public_key():
    _, public_key = get_vapid_keys()
    return jsonify({"publicKey": public_key})
