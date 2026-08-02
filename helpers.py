from functools import wraps
from flask import session, redirect, url_for, flash
from database import db
from models import Notification

# check login status before accessing route
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# role-based access controller
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') not in roles:
                flash('You do not have permission to view that page.', 'danger')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# fetch logged-in user
def get_current_user():
    from models import User
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

# helper to populate session
def set_session(user):
    session['user_id'] = user.id
    session['role'] = user.role
    session['name'] = user.name

# create in-app notification
def create_notification(user_id, message):
    note = Notification(user_id=user_id, message=message)
    db.session.add(note)

# count unread notices
def unread_count(user_id):
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()

# pass complexity check
def validate_password(password, confirm):
    if password != confirm:
        return 'Passwords do not match.'
    if len(password) < 6:
        return 'Password must be at least 6 characters long.'
    return None

# unique email check
def validate_email_free(email):
    from models import User
    if User.query.filter_by(email=email).first():
        return 'An account with that email address already exists.'
    return None
