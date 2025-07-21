from flask import Flask, session
from app import db
from flask_migrate import Migrate
from flask_login import LoginManager
from .models import Customer, Courier
import os
from .models import User
from app.routes import main, user  # Assuming Blueprints are here

migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Basic Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'S3c@!qL#2vZ8pT0$Km7^uMdxBn!eFr91')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///peachdrop.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    @login_manager.user_loader
    def load_user(user_id):
        # user_id can be stored as "role-id" in session
        # For example "customer-3" or "courier-7"
        if "-" in user_id:
            role, id_str = user_id.split("-", 1)
            try:
                uid = int(id_str)
            except ValueError:
                return None

            if role == "customer":
                return Customer.query.get(uid)
            elif role == "courier":
                return Courier.query.get(uid)
            else:
                return None
        else:
            # fallback for old user_id format
            user = Customer.query.get(int(user_id))
            if user:
                return user
            return Courier.query.get(int(user_id))

    # Load user

    # Register Blueprints
    app.register_blueprint(main)
    app.register_blueprint(user)

    # Template Context Globals
    @app.context_processor
    def inject_user():
        return {
            'user_role': session.get('user_role'),
            'user_name': session.get('user_name')
        }
    
    @app.template_filter('phone')
    def format_phone(phone_str):
        # Strip anything that isn't a digit
        digits = ''.join(filter(str.isdigit, phone_str))
        if len(digits) == 10:
            return f"({digits[:3]}){digits[3:6]}-{digits[6:]}"
        
        return phone_str  # fallback


    return app
