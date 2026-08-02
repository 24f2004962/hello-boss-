from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import db
from models import Trek, Booking, User
from helpers import role_required, get_current_user, create_notification, validate_password

staff_bp = Blueprint('staff', __name__)

# staff main landing route
@staff_bp.route('/dashboard')
@role_required('staff')
def dashboard():
    staff_id = session['user_id']
    my_treks = Trek.query.filter_by(staff_id=staff_id).all()

    total_participants = 0
    open_count = 0
    completed_count = 0
    for t in my_treks:
        total_participants += Booking.query.filter_by(trek_id=t.id, status='Booked').count()
        if t.status == 'Open':
            open_count += 1
        if t.status == 'Completed':
            completed_count += 1

    return render_template('staff/dashboard.html',
        treks=my_treks,
        total_participants=total_participants,
        open_count=open_count,
        completed_count=completed_count
    )

# view list of bookings for assigned trek
@staff_bp.route('/trek/<int:trek_id>')
@role_required('staff')
def manage_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.staff_id != session['user_id']:
        flash('You are not assigned to that trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    bookings = (Booking.query
                .filter_by(trek_id=trek_id)
                .order_by(Booking.booking_date.desc()).all())

    booked_count = sum(1 for b in bookings if b.status == 'Booked')
    cancelled_count = sum(1 for b in bookings if b.status == 'Cancelled')

    return render_template('staff/manage_trek.html',
        trek=trek,
        bookings=bookings,
        booked_count=booked_count,
        cancelled_count=cancelled_count
    )

# update trek info by guide
@staff_bp.route('/trek/<int:trek_id>/update', methods=['POST'])
@role_required('staff')
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.staff_id != session['user_id']:
        flash('You are not assigned to that trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    slots = request.form.get('available_slots')
    status = request.form.get('status')

    if slots is not None:
        try:
            trek.available_slots = max(0, int(slots))
        except ValueError:
            flash('Slots must be a number.', 'danger')
            return redirect(url_for('staff.manage_trek', trek_id=trek_id))

    if status:
        old_status = trek.status
        trek.status = status
        # alert users of status changes
        if old_status != status:
            for b in trek.bookings:
                if b.status == 'Booked':
                    create_notification(b.user_id, f'The status of "{trek.name}" has changed to {status}.')

    db.session.commit()
    flash('Trek updated.', 'success')
    return redirect(url_for('staff.manage_trek', trek_id=trek_id))

# complete active trek status
@staff_bp.route('/trek/<int:trek_id>/complete', methods=['POST'])
@role_required('staff')
def complete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.staff_id != session['user_id']:
        flash('You are not assigned to that trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    trek.status = 'Completed'
    for b in trek.bookings:
        if b.status == 'Booked':
            b.status = 'Completed'
            create_notification(b.user_id, f'Your trek "{trek.name}" has been completed. Thank you for joining!')

    db.session.commit()
    flash(f'"{trek.name}" marked as completed.', 'success')
    return redirect(url_for('staff.manage_trek', trek_id=trek_id))

# check all guides participants list
@staff_bp.route('/participants')
@role_required('staff')
def participants():
    staff_id = session['user_id']
    my_treks = Trek.query.filter_by(staff_id=staff_id).all()
    trek_ids = [t.id for t in my_treks]

    all_bookings = []
    if trek_ids:
        all_bookings = (Booking.query
                        .filter(Booking.trek_id.in_(trek_ids))
                        .order_by(Booking.booking_date.desc()).all())

    return render_template('staff/participants.html',
        bookings=all_bookings,
        treks=my_treks
    )

# edit guide profile info
@staff_bp.route('/profile', methods=['GET', 'POST'])
@role_required('staff')
def profile():
    user = get_current_user()

    if request.method == 'POST':
        user.name = request.form.get('name', user.name).strip()
        user.contact = request.form.get('contact', '').strip()
        user.bio = request.form.get('bio', '').strip()

        new_pw = request.form.get('new_password', '')
        if new_pw:
            old_pw = request.form.get('old_password', '')
            if not check_password_hash(user.password, old_pw):
                flash('Current password is incorrect.', 'danger')
                return render_template('staff/profile.html', user=user)
            err = validate_password(new_pw, request.form.get('confirm', ''))
            if err:
                flash(err, 'danger')
                return render_template('staff/profile.html', user=user)
            user.password = generate_password_hash(new_pw)

        db.session.commit()
        session['name'] = user.name
        flash('Profile updated.', 'success')
        return redirect(url_for('staff.profile'))

    return render_template('staff/profile.html', user=user)
