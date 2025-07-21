from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)


class Customer(db.Model, UserMixin):
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True)

    def get_id(self):
        # This will be stored in the session as user_id
        return f"customer-{self.id}"

    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200))
    latitude = db.Column(db.Float)   # <-- add this
    longitude = db.Column(db.Float)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Courier(db.Model, UserMixin):
    __tablename__ = 'courier'

    id = db.Column(db.Integer, primary_key=True)

    def get_id(self):
        return f"courier-{self.id}"

    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200))
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_online = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    courier_id = db.Column(db.Integer, db.ForeignKey('courier.id'))
    restaurant_name = db.Column(db.String(100))
    delivery_address = db.Column(db.String(200))
    items = db.Column(db.Text)  # Store as JSON/text if it's a list
    note = db.Column(db.String(300))
    origin = db.Column(db.String(100))
    status = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
