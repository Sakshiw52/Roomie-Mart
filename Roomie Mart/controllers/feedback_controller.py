from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.feedback_model import Feedback
from models.order_model import Order

feedback_bp = Blueprint('feedback_bp', __name__)


@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    # Generic site feedback (not tied to an order)
    if request.method == 'POST':
        user_id = session.get('user_id')
        name = request.form.get('name') if not user_id else session.get('user_name')
        email = request.form.get('email') if not user_id else session.get('user_email')
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        try:
            rating_val = int(rating) if rating else None
        except ValueError:
            rating_val = None

        if not (rating_val and 1 <= rating_val <= 5):
            flash('Please provide a rating between 1 and 5', 'error')
            return render_template('feedback.html', name=name, email=email, rating=rating, comment=comment)

        Feedback.create_feedback(user_id, name, email, rating_val, comment)
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('index'))

    return render_template('feedback.html')


@feedback_bp.route('/feedback/order/<int:order_id>', methods=['GET', 'POST'])
def feedback_for_order(order_id):
    # Allow buyer to submit feedback tied to a completed order
    order = Order.get_order_by_id(order_id)
    # sqlite3.Row doesn't support .get(); normalize to dict for safe access
    if order and not isinstance(order, dict):
        try:
            order = dict(order)
        except Exception:
            pass
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    # Only buyer can submit feedback for their order
    # Safe access to buyer id
    buyer_id = order.get('buyer_id') if isinstance(order, dict) else None

    if not user_id or user_id != buyer_id:
        flash('You are not authorized to provide feedback for this order', 'error')
        return redirect(url_for('index'))

    item_title = order.get('item_title')
    item_id = order.get('item_id')
    seller_id = order.get('seller_id')
    seller_name = order.get('seller_name')

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        try:
            rating_val = int(rating) if rating else None
        except ValueError:
            rating_val = None

        if not (rating_val and 1 <= rating_val <= 5):
            flash('Please select a rating between 1 and 5', 'error')
            return render_template('feedback_order.html', item_title=item_title, seller_name=seller_name, rating=rating, comment=comment)

        # Use session user details if present
        uid = session.get('user_id')
        name = session.get('user_name') if uid else request.form.get('name')
        email = session.get('user_email') if uid else request.form.get('email')

        Feedback.create_feedback(uid, name, email, rating_val, comment, item_id=item_id, seller_id=seller_id)
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('item_bp.item_detail', item_id=item_id))

    return render_template('feedback_order.html', item_title=item_title, seller_name=seller_name)
