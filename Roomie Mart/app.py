from flask import Flask, render_template, flash, redirect, url_for, session, request
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from types import SimpleNamespace

# Import controllers
from controllers.auth_controller import auth_bp
from controllers.item_controller import item_bp
from controllers.message_controller import message_bp
from controllers.feedback_controller import feedback_bp
from controllers.reports_controller import reports_bp
from controllers.orders_controller import orders_bp
from controllers.requests_controller import requests_bp


# Import database connection
from database.db_connection import get_db_connection


app = Flask(__name__)
app.secret_key = 'roomie_mart_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Inject pending requests count for seller into all templates (must be after app is defined)
from models.request_model import RequestModel
@app.context_processor
def inject_pending_request_count():
    user_id = session.get('user_id')
    pending_requests_count = 0
    if user_id:
        try:
            pending_requests_count = RequestModel.count_pending_requests_for_owner(user_id)
        except Exception:
            pending_requests_count = 0
    return dict(pending_requests_count=pending_requests_count)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(item_bp)
app.register_blueprint(message_bp, url_prefix='/message')
app.register_blueprint(feedback_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(requests_bp)



# Inject a simple `current_user` into templates so code that expects
# `current_user.is_authenticated` works without Flask-Login.
@app.context_processor
def inject_current_user():
    if 'user_id' in session:
        user = SimpleNamespace(
            is_authenticated=True,
            id=session.get('user_id'),
            name=session.get('user_name'),
            email=session.get('user_email'),
            hostel=session.get('hostel'),
            block=session.get('block')
        )
    else:
        user = SimpleNamespace(is_authenticated=False)
    return {'current_user': user}


# Note: Google Maps API key support removed. Templates will display address text instead of maps.


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# Home route
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.*, u.name as seller_name, u.hostel, u.block
        FROM items i
        JOIN users u ON i.user_id = u.id
        WHERE i.status = 'available'
        ORDER BY i.created_at DESC
        LIMIT 12
    ''')
    items = cursor.fetchall()
    conn.close()
    return render_template('index.html', items=items)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# Debug helper: return current session user info (development only)
@app.route('/_whoami')
def whoami():
    return {
        'user_id': session.get('user_id'),
        'user_name': session.get('user_name'),
        'user_email': session.get('user_email'),
        'hostel': session.get('hostel'),
        'block': session.get('block')
    }


@app.route('/_my_items')
def my_items_debug():
    """Debug endpoint: return current user's items as JSON (development only)."""
    if 'user_id' not in session:
        return ({'error': 'not_logged_in'}, 401)
    from models.item_model import Item
    items = Item.get_user_items(session['user_id'])
    # convert sqlite Row objects to dicts
    out = [dict(i) for i in items]
    return {'items': out}

if __name__ == '__main__':
    app.run(debug=True)