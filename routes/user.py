from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import db
from models import Trek, Booking, Notification
from helpers import role_required, get_current_user, create_notification, validate_password

user_bp = Blueprint('user', __name__)

# user dashboard stats and recent bookings
@user_bp.route('/dashboard')
@role_required('user')
def dashboard():
    user_id = session['user_id']
    open_treks = Trek.query.filter_by(status='Open').order_by(Trek.start_date).limit(6).all()
    my_bookings = (Booking.query
                  .filter_by(user_id=user_id)
                  .order_by(Booking.booking_date.desc())
                  .limit(5).all())
    total_completed = Booking.query.filter_by(user_id=user_id, status='Completed').count()
    total_booked = Booking.query.filter_by(user_id=user_id, status='Booked').count()

    return render_template('user/dashboard.html',
        open_treks=open_treks,
        my_bookings=my_bookings,
        total_completed=total_completed,
        total_booked=total_booked
    )

# browse/search available treks
@user_bp.route('/browse')
@role_required('user')
def browse():
    q = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '')
    location = request.args.get('location', '')
    sort = request.args.get('sort', 'date')
    page = request.args.get('page', 1, type=int)

    query = Trek.query.filter_by(status='Open')

    if q:
        query = query.filter(
            Trek.name.ilike('%' + q + '%') |
            Trek.location.ilike('%' + q + '%') |
            Trek.description.ilike('%' + q + '%')
        )
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if location:
        query = query.filter(Trek.location.ilike('%' + location + '%'))

    if sort == 'price':
        query = query.order_by(Trek.price)
    elif sort == 'duration':
        query = query.order_by(Trek.duration)
    else:
        query = query.order_by(Trek.start_date)

    treks = query.paginate(page=page, per_page=9, error_out=False)

    # select distinct locations for selector
    all_locations = [r[0] for r in db.session.query(Trek.location).distinct().all()]

    return render_template('user/browse.html',
        treks=treks,
        all_locations=all_locations,
        q=q,
        difficulty=difficulty,
        location=location,
        sort=sort
    )

# view specific trek details
@user_bp.route('/trek/<int:trek_id>')
@role_required('user')
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    user_id = session['user_id']

    # check if user already booked this trek
    existing = Booking.query.filter_by(
        user_id=user_id,
        trek_id=trek_id
    ).filter(Booking.status != 'Cancelled').first()

    related = (Trek.query
               .filter_by(difficulty=trek.difficulty, status='Open')
               .filter(Trek.id != trek_id)
               .limit(3).all())

    return render_template('user/trek_detail.html',
        trek=trek,
        existing=existing,
        related=related
    )

# book selected trek
@user_bp.route('/book/<int:trek_id>', methods=['POST'])
@role_required('user')
def book(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    user_id = session['user_id']
    notes = request.form.get('notes', '').strip()

    if trek.status != 'Open':
        flash('This trek is not open for bookings at the moment.', 'warning')
        return redirect(url_for('user.trek_detail', trek_id=trek_id))

    if trek.available_slots <= 0:
        flash('No slots are available for this trek. Please check back later.', 'danger')
        return redirect(url_for('user.trek_detail', trek_id=trek_id))

    already = Booking.query.filter_by(
        user_id=user_id, trek_id=trek_id
    ).filter(Booking.status != 'Cancelled').first()

    if already:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('user.trek_detail', trek_id=trek_id))

    booking = Booking(user_id=user_id, trek_id=trek_id, notes=notes)
    trek.available_slots -= 1
    create_notification(user_id, f'Your booking for "{trek.name}" has been confirmed.')
    db.session.add(booking)
    db.session.commit()

    flash(f'Your booking for "{trek.name}" is confirmed.', 'success')
    return redirect(url_for('user.my_bookings'))

# list user's bookings history
@user_bp.route('/bookings')
@role_required('user')
def my_bookings():
    user_id = session['user_id']
    status = request.args.get('status', '')
    query = Booking.query.filter_by(user_id=user_id)
    if status:
        query = query.filter(Booking.status == status)
    bookings = query.order_by(Booking.booking_date.desc()).all()
    return render_template('user/my_bookings.html', bookings=bookings, status_filter=status)

# cancel selected booking
@user_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@role_required('user')
def cancel(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session['user_id']:
        flash('That is not your booking.', 'danger')
        return redirect(url_for('user.my_bookings'))

    if booking.status != 'Booked':
        flash('This booking cannot be cancelled.', 'warning')
        return redirect(url_for('user.my_bookings'))

    booking.status = 'Cancelled'
    booking.trek.available_slots += 1
    create_notification(session['user_id'], f'Your booking for "{booking.trek.name}" has been cancelled.')
    db.session.commit()

    flash(f'Your booking for "{booking.trek.name}" has been cancelled. The slot has been freed.', 'info')
    return redirect(url_for('user.my_bookings'))

# view completed treks history
@user_bp.route('/history')
@role_required('user')
def history():
    user_id = session['user_id']
    bookings = (Booking.query
                 .filter_by(user_id=user_id, status='Completed')
                 .order_by(Booking.booking_date.desc()).all())
    total_days = sum(b.trek.duration for b in bookings)
    return render_template('user/history.html', bookings=bookings, total_days=total_days)

# notifications check route
@user_bp.route('/notifications')
@role_required('user')
def notifications():
    user_id = session['user_id']
    notes = (Notification.query
               .filter_by(user_id=user_id)
               .order_by(Notification.created_at.desc()).all())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('user/notifications.html', notifications=notes)

# edit user profile settings
@user_bp.route('/profile', methods=['GET', 'POST'])
@role_required('user')
def profile():
    user = get_current_user()

    if request.method == 'POST':
        user.name = request.form.get('name', user.name).strip()
        user.contact = request.form.get('contact', '').strip()
        user.address = request.form.get('address', '').strip()

        new_pw = request.form.get('new_password', '')
        if new_pw:
            old_pw = request.form.get('old_password', '')
            if not check_password_hash(user.password, old_pw):
                flash('Current password is incorrect.', 'danger')
                return render_template('user/profile.html', user=user)
            err = validate_password(new_pw, request.form.get('confirm', ''))
            if err:
                flash(err, 'danger')
                return render_template('user/profile.html', user=user)
            user.password = generate_password_hash(new_pw)

        db.session.commit()
        session['name'] = user.name
        flash('Profile updated.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html', user=user)
