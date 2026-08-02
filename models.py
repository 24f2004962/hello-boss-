from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(20), default='')
    address = db.Column(db.String(200), default='')
    bio = db.Column(db.Text, default='')
    role = db.Column(db.String(10), nullable=False, default='user') # role: admin/staff/user
    status = db.Column(db.String(15), nullable=False, default='active') # active/pending/blacklisted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='trekker', lazy=True, foreign_keys='Booking.user_id')


class Trek(db.Model):
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default='')
    highlights = db.Column(db.Text, default='')
    difficulty = db.Column(db.String(20), nullable=False) # Easy, Moderate, Hard
    duration = db.Column(db.Integer, nullable=False) # total days
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Approved, Open, Closed, Completed
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff = db.relationship('User', foreign_keys=[staff_id])
    bookings = db.relationship('Booking', backref='trek', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Booked') # Booked/Cancelled/Completed
    notes = db.Column(db.Text, default='')


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
