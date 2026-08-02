from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User
from helpers import set_session, validate_password, validate_email_free

auth_bp = Blueprint('auth', __name__)

# default landing endpoint
@auth_bp.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'staff':
            return redirect(url_for('staff.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))

# login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter your email and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No account found with that email address.', 'danger')
            return render_template('auth/login.html')

        if not check_password_hash(user.password, password):
            flash('Incorrect password. Please try again.', 'danger')
            return render_template('auth/login.html')

        # check accounts status before logging in
        if user.status == 'blacklisted':
            flash('Your account has been suspended. Please contact the administrator.', 'danger')
            return render_template('auth/login.html')

        if user.role == 'staff' and user.status == 'pending':
            flash('Your staff account is awaiting administrator approval. You will be notified once approved.', 'warning')
            return render_template('auth/login.html')

        set_session(user)
        flash(f'Welcome back, {user.name}.', 'success')

        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))

    return render_template('auth/login.html')

# register route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        role = request.form.get('role', '')
        contact = request.form.get('contact', '').strip()

        # basic checks
        if not all([name, email, password, confirm, role]):
            flash('All fields marked with * are required.', 'danger')
            return render_template('auth/register.html')

        if role not in ('staff', 'user'):
            flash('Please select a valid role.', 'danger')
            return render_template('auth/register.html')

        err = validate_password(password, confirm)
        if err:
            flash(err, 'danger')
            return render_template('auth/register.html')

        err = validate_email_free(email)
        if err:
            flash(err, 'danger')
            return render_template('auth/register.html')

        status = 'pending' if role == 'staff' else 'active'

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            contact=contact,
            role=role,
            status=status
        )
        db.session.add(new_user)
        db.session.commit()

        if role == 'staff':
            flash('Registration submitted. Please wait for administrator approval before logging in.', 'info')
        else:
            flash('Account created successfully. You can now log in.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

# clear session on logout
@auth_bp.route('/logout')
def logout():
    name = session.get('name', '')
    session.clear()
    flash(f'You have been logged out, {name}.' if name else 'You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
