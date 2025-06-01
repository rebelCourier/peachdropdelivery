from flask import Flask
import os


def create_app():
    app = Flask(__name__)
    
    from app.routes import main, user
    app.register_blueprint(main)
    app.register_blueprint(user)
    
    return app