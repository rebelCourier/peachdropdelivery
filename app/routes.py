from flask import Blueprint, render_template
from flask import request, redirect, url_for

main = Blueprint('main', __name__, static_folder='static', template_folder='templates')

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/register-courier')
def register_courier():
    return render_template('regcourier.html')



@main.route('/submit-courier-registration', methods=['POST'])
def submit_courier_registration():
    name = request.form['name']
    zone = request.form['zone']
    # save to DB or print/log it
    print(f"Courier Registered: {name}, Area: {zone}")
    return redirect(url_for('main.home'))