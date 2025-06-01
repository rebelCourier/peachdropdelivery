from flask import Blueprint, render_template
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
import uuid

main = Blueprint('main', __name__, static_folder='static', template_folder='templates')

user = Blueprint('user', __name__)
UPLOAD_FOLDER = 'static/uploads'
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
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return filepath
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
    print(f"Customer Registered: {name}, Address: {address}, Email: {email}, Phone: {phone}, Password Hash: {password_hash}")
    return redirect(url_for('main.login'))

@main.route('/login')
def login():
    return render_template('login.html')