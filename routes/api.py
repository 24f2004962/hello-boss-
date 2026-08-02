from functools import wraps
from flask import Blueprint, jsonify, session
from models import Trek, Booking, User

api_bp = Blueprint('api', __name__)

# helper check for API login
def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated

# get all open treks in JSON format
@api_bp.route('/treks')
@api_login_required
def api_treks():
    treks = Trek.query.filter_by(status='Open').all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'location': t.location,
        'difficulty': t.difficulty,
        'duration': t.duration,
        'available_slots': t.available_slots,
        'total_slots': t.total_slots,
        'price': t.price,
        'start_date': t.start_date.isoformat() if t.start_date else None,
        'end_date': t.end_date.isoformat() if t.end_date else None,
    } for t in treks])

# get specific trek info
@api_bp.route('/treks/<int:trek_id>')
@api_login_required
def api_trek_detail(trek_id):
    t = Trek.query.get_or_404(trek_id)
    return jsonify({
        'id': t.id,
        'name': t.name,
        'location': t.location,
        'difficulty': t.difficulty,
        'duration': t.duration,
        'available_slots': t.available_slots,
        'total_slots': t.total_slots,
        'price': t.price,
        'status': t.status,
        'description': t.description,
        'start_date': t.start_date.isoformat() if t.start_date else None,
        'end_date': t.end_date.isoformat() if t.end_date else None,
    })

# admin stats for charts page
@api_bp.route('/stats')
@api_login_required
def api_stats():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    return jsonify({
        'total_treks': Trek.query.count(),
        'total_users': User.query.filter_by(role='user').count(),
        'total_staff': User.query.filter_by(role='staff').count(),
        'total_bookings': Booking.query.count(),
        'booked': Booking.query.filter_by(status='Booked').count(),
        'cancelled': Booking.query.filter_by(status='Cancelled').count(),
        'completed': Booking.query.filter_by(status='Completed').count(),
        'trek_statuses': {
            s: Trek.query.filter_by(status=s).count()
            for s in ['Pending', 'Approved', 'Open', 'Closed', 'Completed']
        }
    })
