from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user_model import User
from utils.authentication import login_required

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        hostel = request.form.get('hostel')
        block = request.form.get('block')
        room = request.form.get('room')

        # Validate form data - only name/email/password are required at registration
        if not all([name, email, password, confirm_password]):
            flash('Name, email and password are required', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        # Check if user already exists
        existing_user = User.get_user_by_email(email)
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('register.html')

        # Create new user (optional fields may be empty)
        phone = phone or ''
        hostel = hostel or ''
        block = block or ''
        room = room or ''

        user_id = User.create_user(name, email, password, phone, hostel, block, room)

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth_bp.login'))

    # GET -> render registration form
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate form data
        if not all([email, password]):
            flash('Email and password are required', 'error')
            return render_template('login.html')

        # Check if user exists
        user = User.get_user_by_email(email)
        if not user:
            flash('Invalid email or password', 'error')
            return render_template('login.html')

        # Verify password
        if not User.verify_password(user['password'], password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')

        # Set session on successful login
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        # store hostel/block to prefill item form
        session['hostel'] = user['hostel']
        session['block'] = user['block']

        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('index'))

    # GET -> render login form
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        hostel = request.form['hostel']
        block = request.form['block']
        room = request.form['room']
        
        # Validate form data
        if not all([name, phone, hostel, block, room]):
            flash('All fields are required', 'error')
            return render_template('profile.html', user=user)
        
        # Update user profile
        User.update_user(session['user_id'], name, phone, hostel, block, room)

        # Update session
        session['user_name'] = name

        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth_bp.profile'))

    return render_template('profile.html', user=user)