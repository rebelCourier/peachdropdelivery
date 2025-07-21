# reset.py
from app.app import create_app
from app.initialize_functions import db

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database has been reset.")
