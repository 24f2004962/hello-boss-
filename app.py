from flask import Flask, session, render_template
from database import db
from config.settings import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # blue prints imports
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.staff import staff_bp
    from routes.user import user_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.context_processor
    def inject_globals():
        from helpers import unread_count
        count = 0
        if 'user_id' in session:
            count = unread_count(session['user_id'])
        return dict(unread_notifications=count, current_role=session.get('role', ''))

    # handlers for status errors
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # auto db tables initialization and seed defaults
    with app.app_context():
        db.create_all()
        seed_admin()
        seed_sample_data()

    return app

def seed_admin():
    from models import User
    from werkzeug.security import generate_password_hash
    if not User.query.filter_by(role='admin').first():
        admin = User(
            name='Admin',
            email='admin@trek.com',
            password=generate_password_hash('admin123'),
            role='admin',
            status='active'
        )
        db.session.add(admin)
        db.session.commit()
        print('seeded default admin account admin@trek.com')

def seed_sample_data():
    from models import Trek
    from datetime import date
    if Trek.query.count() > 0:
        return

    # default starting treks
    samples = [
        {
            'name': 'Everest Base Camp',
            'location': 'Nepal',
            'difficulty': 'Hard',
            'duration': 14,
            'total_slots': 20,
            'status': 'Open',
            'price': 1200.0,
            'start_date': date(2026, 9, 1),
            'end_date': date(2026, 9, 14),
            'description': 'The classic high-altitude trek through the Khumbu region to the foot of the world\'s highest mountain.',
            'highlights': 'Namche Bazaar, Tengboche Monastery, Khumbu Icefall views'
        },
        {
            'name': 'Roopkund Trek',
            'location': 'Uttarakhand, India',
            'difficulty': 'Moderate',
            'duration': 8,
            'total_slots': 15,
            'status': 'Open',
            'price': 450.0,
            'start_date': date(2026, 10, 5),
            'end_date': date(2026, 10, 12),
            'description': 'A high altitude glacial lake trek famous for its ancient skeletal remains.',
            'highlights': 'Mystery lake, Bugyal meadows, Himalayan views'
        },
        {
            'name': 'Kedarkantha Trek',
            'location': 'Uttarakhand, India',
            'difficulty': 'Easy',
            'duration': 6,
            'total_slots': 25,
            'status': 'Open',
            'price': 280.0,
            'start_date': date(2026, 12, 20),
            'end_date': date(2026, 12, 25),
            'description': 'A perfect winter trek with snow-covered trails and 360-degree summit views.',
            'highlights': 'Snow trails, pine forests, summit sunrise'
        },
        {
            'name': 'Hampta Pass',
            'location': 'Himachal Pradesh, India',
            'difficulty': 'Moderate',
            'duration': 5,
            'total_slots': 18,
            'status': 'Approved',
            'price': 320.0,
            'start_date': date(2026, 8, 10),
            'end_date': date(2026, 8, 14),
            'description': 'A crossover trek connecting two different valleys.',
            'highlights': 'Chandra Taal lake, alpine meadows, desert landscapes'
        }
    ]

    for s in samples:
        trek = Trek(
            name=s['name'],
            location=s['location'],
            difficulty=s['difficulty'],
            duration=s['duration'],
            total_slots=s['total_slots'],
            available_slots=s['total_slots'],
            status=s['status'],
            price=s['price'],
            start_date=s['start_date'],
            end_date=s['end_date'],
            description=s['description'],
            highlights=s['highlights']
        )
        db.session.add(trek)
    db.session.commit()
    print('seeded initial sample treks')

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
