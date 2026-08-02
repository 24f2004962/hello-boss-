from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from database import db
from models import User, Trek, Booking, Notification
from helpers import role_required, get_current_user, create_notification

admin_bp = Blueprint('admin', __name__)

# admin main stats dashboard
@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    pending_staff = User.query.filter_by(role='staff', status='pending').count()
    open_treks = Trek.query.filter_by(status='Open').count()

    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(8).all()

    status_counts = {}
    for s in ['Pending', 'Approved', 'Open', 'Closed', 'Completed']:
        status_counts[s] = Trek.query.filter_by(status=s).count()

    return render_template('admin/dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        pending_staff=pending_staff,
        open_treks=open_treks,
        recent_bookings=recent_bookings,
        status_counts=status_counts
    )

# list treks with filters
@admin_bp.route('/treks')
@role_required('admin')
def treks():
    q = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    query = Trek.query
    if q:
        query = query.filter(
            Trek.name.ilike('%' + q + '%') |
            Trek.location.ilike('%' + q + '%')
        )
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if status:
        query = query.filter(Trek.status == status)

    treks = query.order_by(Trek.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    approved_staff = User.query.filter_by(role='staff', status='active').all()

    return render_template('admin/treks.html',
        treks=treks,
        q=q,
        difficulty=difficulty,
        status_filter=status,
        approved_staff=approved_staff
    )

# add new trek form
@admin_bp.route('/treks/add', methods=['GET', 'POST'])
@role_required('admin')
def add_trek():
    approved_staff = User.query.filter_by(role='staff', status='active').all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty', '')
        duration = request.form.get('duration', 0)
        slots = request.form.get('slots', 0)
        status = request.form.get('status', 'Pending')
        price = request.form.get('price', 0.0)
        description = request.form.get('description', '').strip()
        highlights = request.form.get('highlights', '').strip()
        staff_id = request.form.get('staff_id') or None
        start_raw = request.form.get('start_date', '')
        end_raw = request.form.get('end_date', '')

        if not all([name, location, difficulty, duration, slots]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/trek_form.html', trek=None, staff_list=approved_staff)

        try:
            duration = int(duration)
            slots = int(slots)
            price = float(price) if price else 0.0
        except ValueError:
            flash('Duration and slots must be numbers.', 'danger')
            return render_template('admin/trek_form.html', trek=None, staff_list=approved_staff)

        start_date = datetime.strptime(start_raw, '%Y-%m-%d').date() if start_raw else None
        end_date = datetime.strptime(end_raw, '%Y-%m-%d').date() if end_raw else None

        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            total_slots=slots,
            available_slots=slots,
            status=status,
            price=price,
            description=description,
            highlights=highlights,
            staff_id=int(staff_id) if staff_id else None,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(trek)
        db.session.commit()
        flash(f'"{name}" has been created.', 'success')
        return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=None, staff_list=approved_staff)

# edit existing trek
@admin_bp.route('/treks/edit/<int:trek_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    approved_staff = User.query.filter_by(role='staff', status='active').all()

    if request.method == 'POST':
        trek.name = request.form.get('name', trek.name).strip()
        trek.location = request.form.get('location', trek.location).strip()
        trek.difficulty = request.form.get('difficulty', trek.difficulty)
        trek.description = request.form.get('description', '').strip()
        trek.highlights = request.form.get('highlights', '').strip()
        trek.status = request.form.get('status', trek.status)
        staff_id = request.form.get('staff_id') or None
        trek.staff_id = int(staff_id) if staff_id else None

        try:
            trek.duration = int(request.form.get('duration', trek.duration))
            new_total = int(request.form.get('slots', trek.total_slots))
            trek.price = float(request.form.get('price', trek.price) or 0)
        except ValueError:
            flash('Duration and slots must be numbers.', 'danger')
            return render_template('admin/trek_form.html', trek=trek, staff_list=approved_staff)

        # slot adjustment calculation
        difference = new_total - trek.total_slots
        trek.total_slots = new_total
        trek.available_slots = max(0, trek.available_slots + difference)

        start_raw = request.form.get('start_date', '')
        end_raw = request.form.get('end_date', '')
        trek.start_date = datetime.strptime(start_raw, '%Y-%m-%d').date() if start_raw else None
        trek.end_date = datetime.strptime(end_raw, '%Y-%m-%d').date() if end_raw else None

        db.session.commit()
        flash(f'"{trek.name}" has been updated.', 'success')
        return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=trek, staff_list=approved_staff)

# delete trek and cancel active bookings
@admin_bp.route('/treks/delete/<int:trek_id>', methods=['POST'])
@role_required('admin')
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    name = trek.name

    for b in trek.bookings:
        if b.status == 'Booked':
            create_notification(b.user_id, f'The trek "{name}" you booked has been cancelled by the administrator.')
        b.status = 'Cancelled'

    db.session.delete(trek)
    db.session.commit()
    flash(f'"{name}" has been deleted.', 'info')
    return redirect(url_for('admin.treks'))

# trek bookings overview
@admin_bp.route('/treks/<int:trek_id>')
@role_required('admin')
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    bookings = Booking.query.filter_by(trek_id=trek_id).order_by(Booking.booking_date.desc()).all()
    return render_template('admin/trek_detail.html', trek=trek, bookings=bookings)

# list staff members
@admin_bp.route('/staff')
@role_required('admin')
def staff():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    query = User.query.filter_by(role='staff')
    if q:
        query = query.filter(
            User.name.ilike('%' + q + '%') |
            User.email.ilike('%' + q + '%')
        )
    if status:
        query = query.filter(User.status == status)

    staff_list = query.order_by(User.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/staff.html', staff=staff_list, q=q, status_filter=status)

# approve guide account registration
@admin_bp.route('/staff/approve/<int:staff_id>', methods=['POST'])
@role_required('admin')
def approve_staff(staff_id):
    s = User.query.get_or_404(staff_id)
    s.status = 'active'
    create_notification(s.id, 'Your staff account has been approved. You can now log in.')
    db.session.commit()
    flash(f'{s.name} has been approved.', 'success')
    return redirect(url_for('admin.staff'))

# block/restore guide access
@admin_bp.route('/staff/toggle/<int:staff_id>', methods=['POST'])
@role_required('admin')
def toggle_staff(staff_id):
    s = User.query.get_or_404(staff_id)
    if s.status in ('active', 'pending'):
        s.status = 'blacklisted'
        msg = f'{s.name} has been blacklisted.'
    else:
        s.status = 'active'
        msg = f'{s.name} has been restored.'
    db.session.commit()
    flash(msg, 'info')
    return redirect(url_for('admin.staff'))

# list users list
@admin_bp.route('/users')
@role_required('admin')
def users():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    query = User.query.filter_by(role='user')
    if q:
        query = query.filter(
            User.name.ilike('%' + q + '%') |
            User.email.ilike('%' + q + '%')
        )
    if status:
        query = query.filter(User.status == status)

    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/users.html', users=users, q=q, status_filter=status)

# specific user profile view
@admin_bp.route('/users/<int:user_id>')
@role_required('admin')
def user_detail(user_id):
    u = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()
    return render_template('admin/user_detail.html', u=u, bookings=bookings)

# block or restore user account status
@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@role_required('admin')
def toggle_user(user_id):
    u = User.query.get_or_404(user_id)
    u.status = 'blacklisted' if u.status == 'active' else 'active'
    db.session.commit()
    flash(f'{u.name} status changed to {u.status}.', 'info')
    return redirect(url_for('admin.users'))

# global list of bookings
@admin_bp.route('/bookings')
@role_required('admin')
def bookings():
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    query = Booking.query
    if status:
        query = query.filter(Booking.status == status)

    bookings = query.order_by(Booking.booking_date.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/bookings.html', bookings=bookings, status_filter=status)

# show visual reports and tables
@admin_bp.route('/reports')
@role_required('admin')
def reports():
    booked_count = Booking.query.filter_by(status='Booked').count()
    cancelled_count = Booking.query.filter_by(status='Cancelled').count()
    completed_count = Booking.query.filter_by(status='Completed').count()

    popular_treks = (db.session.query(Trek, db.func.count(Booking.id).label('count'))
                     .join(Booking, Trek.id == Booking.trek_id)
                     .filter(Booking.status != 'Cancelled')
                     .group_by(Trek.id)
                     .order_by(db.desc('count'))
                     .limit(5).all())

    top_users = (db.session.query(User, db.func.count(Booking.id).label('count'))
                 .join(Booking, User.id == Booking.user_id)
                 .filter(User.role == 'user')
                 .group_by(User.id)
                 .order_by(db.desc('count'))
                 .limit(5).all())

    return render_template('admin/reports.html',
        booked_count=booked_count,
        cancelled_count=cancelled_count,
        completed_count=completed_count,
        popular_treks=popular_treks,
        top_users=top_users
    )

# search queries route
@admin_bp.route('/search')
@role_required('admin')
def search():
    q = request.args.get('q', '').strip()
    results = {'treks': [], 'users': [], 'staff': []}

    if q:
        results['treks'] = Trek.query.filter(
            Trek.name.ilike('%' + q + '%') |
            Trek.location.ilike('%' + q + '%')
        ).all()
        results['users'] = User.query.filter_by(role='user').filter(
            User.name.ilike('%' + q + '%') |
            User.email.ilike('%' + q + '%')
        ).all()
        results['staff'] = User.query.filter_by(role='staff').filter(
            User.name.ilike('%' + q + '%') |
            User.email.ilike('%' + q + '%')
        ).all()

    return render_template('admin/search.html', results=results, q=q)

# change password settings
@admin_bp.route('/settings', methods=['GET', 'POST'])
@role_required('admin')
def settings():
    user = get_current_user()

    if request.method == 'POST':
        old_pw = request.form.get('old_password', '')
        new_pw = request.form.get('new_password', '')
        confirm = request.form.get('confirm', '')

        if not check_password_hash(user.password, old_pw):
            flash('Current password is incorrect.', 'danger')
            return render_template('admin/settings.html', user=user)

        from helpers import validate_password
        err = validate_password(new_pw, confirm)
        if err:
            flash(err, 'danger')
            return render_template('admin/settings.html', user=user)

        user.password = generate_password_hash(new_pw)
        db.session.commit()
        flash('Password updated successfully.', 'success')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html', user=user)
