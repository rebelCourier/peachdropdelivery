from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)
from flask_login import login_required, login_user, current_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from . import db
from .models import Customer, Courier
from sqlalchemy import text
from app.models import Order

main = Blueprint("main", __name__, static_folder="static", template_folder="templates")

user = Blueprint("user", __name__)
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static/uploads"
)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        filepath = os.path.join(UPLOAD_FOLDER, unique_name)
        file.save(filepath)
        # Return path relative to "static" for correct URL use
        return f"uploads/{unique_name}"
    return None


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/order")
def order():
    return render_template("order.html")


@main.route("/couriers")
def couriers():
    return render_template("couriers.html")


@main.route("/map")
def map():
    return render_template("map.html")


# Courier Registration
@main.route("/register-courier")
def register_courier():
    return render_template("regcourier.html")


@main.route("/submit-courier-registration", methods=["POST"])
def submit_courier_registration():
    name = request.form["name"]
    nickname = request.form["nickname"]
    email = request.form["email"]
    phone = request.form["phone"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]
    file = request.files.get("profile_pic")
    filepath = save_uploaded_file(file)

    if password != confirm_password:
        return "Passwords do not match", 400

    password_hash = generate_password_hash(password)

    new_courier = Courier(
        name=name,
        nickname=nickname,
        email=email,
        phone=phone,
        password_hash=password_hash,
        profile_pic=filepath,
    )

    db.session.add(new_courier)
    db.session.commit()

    print(
        f"Courier Registered: {name}, Nickname: {nickname}, Email: {email}, Phone: {phone}, Password Hash: {password_hash}"
    )
    return redirect(url_for("main.login"))


# Customer Registration
@main.route("/register-customer")
def register_customer():
    return render_template("regcustomer.html")


@main.route("/submit-customer-registration", methods=["POST"])
def submit_customer_registration():
    name = request.form["name"]
    address = request.form["address"]
    email = request.form["email"]
    phone = request.form["phone"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]
    file = request.files.get("profile_pic")
    filepath = save_uploaded_file(file)

    if password != confirm_password:
        return "Passwords do not match", 400

    password_hash = generate_password_hash(password)

    new_customer = Customer(
        name=name,
        address=address,
        email=email,
        phone=phone,
        password_hash=password_hash,
        profile_pic=filepath,
    )

    db.session.add(new_customer)
    db.session.commit()

    print(
        f"Customer Registered: {name}, Address: {address}, Email: {email}, Phone: {phone}, Password Hash: {password_hash}"
    )
    return redirect(url_for("main.login"))


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = Customer.query.filter_by(email=email).first()
        role = "customer"

        if not user:
            user = Courier.query.filter_by(email=email).first()
            role = "courier"

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session["user_id"] = f"{role}-{user.id}"
            session["user_role"] = role
            return redirect(url_for("main.dashboard"))
        else:
            return render_template("login.html", error="Invalid email or password.")

    # For GET request, just render the login page
    return render_template("login.html")



@main.route("/dashboard")
@login_required
def dashboard():
    user_role = session.get("user_role")  # you can keep role in session or add to User model
    # Access user info from current_user directly:
    return render_template(
        "dashboard.html",
        user_type=user_role.capitalize() if user_role else "User",
        user_name=current_user.name,
        user_email=current_user.email,
        user_nickname=getattr(current_user, "nickname", ""),
        user_phone=getattr(current_user, "phone", ""),
        user_address=getattr(current_user, "address", ""),
        profile_pic=getattr(current_user, "profile_pic", None),        )


@main.route("/courier/active-delivery")
@login_required
def get_active_delivery():
    if "user_id" not in session or session.get("user_role") != "courier":
        return jsonify({"status": "unauthorized"}), 401

    courier_id = int(session["user_id"].split("-")[1])


    order = db.session.execute(
        text(
            """
            SELECT o.*, c.name AS customer_name, c.phone AS customer_phone
            FROM orders o
            JOIN customer c ON o.customer_id = c.id
            WHERE o.courier_id = :cid AND o.status = 'active'
            LIMIT 1
        """
        ),
        {"cid": courier_id},
    ).fetchone()

    if order is None:
        return jsonify({"status": "no_active_order"})

    return jsonify(
        {
            "status": "success",
            "customer_name": order["customer_name"],
            "customer_phone": order["customer_phone"],
            "delivery_address": order["delivery_address"],
            "restaurant_name": order["restaurant_name"],
            "items": order["items"],
            "note": order["note"],
        }
    )

@main.route("/courier/mark-delivered", methods=["POST"])
def mark_as_delivered():
    if "user_id" not in session or session.get("user_role") != "courier":
        return jsonify({"status": "unauthorized"}), 401

    courier_id = int(session["user_id"].split("-")[1])

    active_order = db.session.execute(
        text("""
            SELECT id FROM orders
            WHERE courier_id = :cid AND status = 'active'
            LIMIT 1
        """), {"cid": courier_id}
    ).fetchone()

    if not active_order:
        return jsonify({"status": "no_active_order"})

    # Mark the order as completed
    db.session.execute(
        text("""
            UPDATE orders
            SET status = 'completed', timestamp = CURRENT_TIMESTAMP
            WHERE id = :oid
        """), {"oid": active_order.id}
    )
    db.session.commit()

    return jsonify({"status": "success", "message": "Order marked as delivered."})


@main.route("/courier/completed-deliveries")
@login_required
def completed_deliveries():
    if "user_id" not in session or session.get("user_role") != "courier":
        return jsonify({"status": "unauthorized"}), 401

    courier_id = int(session["user_id"].split("-")[1])

    deliveries = db.session.execute(
        text("""
            SELECT o.id, o.delivery_address, o.restaurant_name, o.items, o.note, c.name AS customer_name, o.updated_at
            FROM orders o
            JOIN customer c ON o.customer_id = c.id
            WHERE o.courier_id = :cid AND o.status = 'completed'
            ORDER BY o.updated_at DESC
        """),
        {"cid": courier_id}
    ).mappings().all()

    result = []
    for d in deliveries:
        result.append({
            "order_id": d["id"],
            "customer_name": d["customer_name"],
            "delivery_address": d["delivery_address"],
            "restaurant_name": d["restaurant_name"],
            "items": d["items"],
            "note": d["note"],
            "completed_at": d["updated_at"].isoformat() if d["updated_at"] else None,
        })

    return jsonify({"status": "success", "deliveries": result})

@main.route("/customer/active-couriers")
@login_required
def get_active_couriers():
    if session.get("user_role") != "customer":
        return jsonify({"status": "unauthorized"}), 401

    couriers = Courier.query.filter_by(is_online=True).all()

    courier_data = []
    for courier in couriers:
        if courier.latitude is not None and courier.longitude is not None:
            courier_data.append({
                "id": courier.id,
                "lat": courier.latitude,
                "lng": courier.longitude
            })

    return jsonify({
        "status": "success",
        "couriers": courier_data
    })

@main.route("/update-location", methods=["POST"])
def update_location():
    if "user_id" not in session or session.get("user_role") != "courier":
        return jsonify({"status": "unauthorized"}), 401

    data = request.json
    lat = data.get("lat")
    lng = data.get("lng")
    courier_id = int(session["user_id"].split("-")[1])  # FIXED

    print(f"Courier ID {courier_id} location: ({lat}, {lng})")

    courier = Courier.query.get(courier_id)
    if courier:
        courier.latitude = lat
        courier.longitude = lng
        courier.is_online = True
        db.session.commit()

    active_order = db.session.execute(
        text("""
            SELECT o.id, o.customer_id
            FROM orders o
            WHERE o.courier_id = :cid AND o.status = 'active'
            LIMIT 1
        """),
        {"cid": courier_id},
    ).fetchone()

    if active_order:
        customer = Customer.query.get(active_order.customer_id)
        return jsonify({
            "status": "success",
            "customer": {
                "lat": customer.latitude or 0,
                "lng": customer.longitude or 0
            }
        })

    return jsonify({"status": "no_active_order"})


@main.route("/customer/active-order")
@login_required  # if you're using Flask-Login
def get_active_order():
    customer_id = int(session["user_id"].split("-")[1])

    order = Order.query.filter_by(customer_id=customer_id, status="in_progress").first()

    if not order:
        return jsonify(status="none")

    courier = Courier.query.get(order.courier_id)

    return jsonify(
        status="success",
        courier_name=courier.name,
        courier_phone=courier.phone,
        restaurant_name=order.origin,
        items=order.items,  # assuming this is a list or string
        note=order.note or ""
    )




@main.route("/customer/courier-location")
@login_required
def get_courier_location():
    order = Order.query.filter_by(customer_id=current_user.id, status="in_progress").first()
    if order and order.courier:
        return jsonify({
            "status": "success",
            "lat": order.courier.latitude,
            "lng": order.courier.longitude
        })
    return jsonify({"status": "error", "message": "No active courier"})

@main.route("/logout")
@login_required
def logout():
    # Check if the user is a courier (and has the is_online field)
    if hasattr(current_user, 'is_online'):
        current_user.is_online = False
        db.session.commit()

    logout_user()
    return redirect(url_for("main.login"))

@main.route("/delete-user/<email>")
def delete_user(email):
    customer = Customer.query.filter_by(email=email).first()
    courier = Courier.query.filter_by(email=email).first()

    user = customer or courier

    if user:
        if user.profile_pic:
            relative_path = user.profile_pic
            full_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "static",
                relative_path.replace("uploads/", "uploads/"),
            )

            print(f"Attempting to delete profile image at: {full_path}")

            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    print(f"Deleted: {full_path}")
                except Exception as e:
                    print(f"Error deleting file: {e}")
            else:
                print(f"File not found: {full_path}")

        db.session.delete(user)
        db.session.commit()
        user_type = "Customer" if customer else "Courier"
        return f"{user_type} with email {email} deleted."

    return f"No user with email {email} found."
