from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os, uuid
from . import db
from .models import Customer, Courier

main = Blueprint('main', __name__, static_folder='static', template_folder='templates')

user = Blueprint('user', __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/order')
def order():
    return render_template('order.html')

@main.route('/couriers')
def couriers():
    return render_template('couriers.html')

@main.route('/map')
def map():
    return render_template('map.html')

# Courier Registration
@main.route('/register-courier')
def register_courier():
    return render_template('regcourier.html')

@main.route('/submit-courier-registration', methods=['POST'])
def submit_courier_registration():
    name = request.form['name']
    nickname = request.form['nickname']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    file = request.files.get('profile_pic')
    filepath = save_uploaded_file(file)
    
    if password != confirm_password:
        return "Passwords do not match", 400
    
    password_hash = generate_password_hash(password)
    
    # save to DB or print/log it
    new_courier = Courier(
        name=name,
        nickname=nickname,
        email=email,
        phone=phone,
        password_hash=password_hash,
        profile_pic=filepath
    )

    db.session.add(new_courier)
    db.session.commit()
    
    print(f"Courier Registered: {name}, Nickname: {nickname}, Email: {email}, Phone: {phone}, Password Hash: {password_hash}")
    return redirect(url_for('main.login'))

# Customer Registration
@main.route('/register-customer')
def register_customer():
    return render_template('regcustomer.html')

@main.route('/submit-customer-registration', methods=['POST'])
def submit_customer_registration():
    name = request.form['name']
    address = request.form['address']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    file = request.files.get('profile_pic')
    filepath = save_uploaded_file(file)
    
    if password != confirm_password:
        return "Passwords do not match", 400
    
    password_hash = generate_password_hash(password)
    
    # save to DB or print/log it
    new_customer = Customer(
        name=name,
        address=address,
        email=email,
        phone=phone,
        password_hash=password_hash,
        profile_pic=filepath
    )

    db.session.add(new_customer)
    db.session.commit()
    
    print(f"Customer Registered: {name}, Address: {address}, Email: {email}, Phone: {phone}, Password Hash: {password_hash}")
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Try Customer login first
        user = Customer.query.filter_by(email=email).first()
        role = 'customer'

        if not user:
            # Try Courier if not found as Customer
            user = Courier.query.filter_by(email=email).first()
            role = 'courier'

        if user and check_password_hash(user.password_hash, password):
            # Store user session (optional: user.id, role, etc.)
            session['user_id'] = user.id
            session['user_role'] = role
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_nickname'] = user.nickname
            session['user_phone'] = user.phone
            session['profile_pic'] = user.profile_pic
            return redirect(url_for('main.dashboard'))  # You'll define this page
        else:
            return render_template('login.html', error="Invalid email or password.")
    
    return render_template('login.html')

@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user_role = session.get('user_role')  # could be 'customer' or 'courier'
    user_name = session.get('user_name')
    user_email = session.get('user_email')
    user_nickname = session.get('user_nickname')
    user_phone = session.get('user_phone')
    profile_pic = session.get('profile_pic')

    if user_role in ['customer', 'courier']:
        return render_template(
        'dashboard.html',
        user_type=user_role.capitalize(),
        user_name=user_name,
        user_email=user_email, user_nickname=user_nickname, user_phone=user_phone,
        profile_pic=profile_pic
    )
    else:
        return redirect(url_for('main.login'))
    
@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main.route('/delete-user/<email>')
def delete_user(email):
    customer = Customer.query.filter_by(email=email).first()
    courier = Courier.query.filter_by(email=email).first()
    
    user = customer or courier

    if user:
        # Construct full path
        if user.profile_pic:
            relative_path = user.profile_pic
            full_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'static',
                relative_path.replace('uploads/', 'uploads/')
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
