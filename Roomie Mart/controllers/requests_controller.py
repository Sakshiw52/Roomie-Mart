from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.authentication import login_required
from models.request_model import RequestModel
from models.item_model import Item
from models.order_model import Order
from models.message_model import Message

requests_bp = Blueprint('requests_bp', __name__)


@requests_bp.route('/requests/create/<int:item_id>', methods=['POST'])
@login_required
def create_request(item_id):
    user_id = session.get('user_id')
    item = Item.get_item_by_id(item_id)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('item_bp.marketplace'))

    owner_id = item['user_id']
    if owner_id == user_id:
        flash('You cannot request your own item', 'error')
        return redirect(url_for('item_bp.item_detail', item_id=item_id))

    message = request.form.get('message', '').strip()
    from_buy = request.form.get('from_buy') == '1'

    # Create request with status 'pending' (buyer intent). If initiated via Buy, we'll redirect to payment flow.
    req_id = RequestModel.create_request(item_id, user_id, owner_id, message, status='pending')

    # Notify owner via Messages about the incoming request
    try:
        Message.create_message(user_id, owner_id, item_id, message or 'I would like to request to buy this item.')
    except Exception as e:
        print(f"[requests_controller] message notify failed: {e}")

    if from_buy:
        # Buyer initiated via Buy Now — treat this as an immediate order request (no payment step)
        flash('Order request sent to the seller. Please wait for the seller to confirm.', 'success')
        return redirect(url_for('requests_bp.my_requests'))

    flash('Request sent to the seller', 'success')
    return redirect(url_for('item_bp.item_detail', item_id=item_id))


@requests_bp.route('/requests')
@login_required
def owner_requests():
    owner_id = session.get('user_id')
    rows = RequestModel.get_requests_for_owner(owner_id)
    return render_template('requests_list.html', requests=rows)


@requests_bp.route('/requests/my_requests')
@login_required
def my_requests():
    requester_id = session.get('user_id')
    rows = RequestModel.get_requests_for_requester(requester_id)
    return render_template('requests_my.html', requests=rows)


@requests_bp.route('/requests/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    req = RequestModel.get_request_by_id(request_id)
    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('requests_bp.owner_requests'))

    owner_id = session.get('user_id')
    if owner_id != req['owner_id']:
        flash('You do not have permission to accept this request', 'error')
        return redirect(url_for('requests_bp.owner_requests'))

    # Create order and mark item sold
    item = Item.get_item_by_id(req['item_id'])
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('requests_bp.owner_requests'))

    # Prevent accepting if already sold (safe access for sqlite3.Row)
    try:
        if item['status'] == 'sold':
            RequestModel.update_request_status(request_id, 'declined')
            flash('Item already sold', 'error')
            return redirect(url_for('requests_bp.owner_requests'))
    except Exception:
        # missing status or inaccessible field — proceed to attempt create
        pass

    # Determine title and price safely
    try:
        title = item['title']
    except Exception:
        title = ''
    try:
        price = float(item['price'])
    except Exception:
        price = 0.0

    order_id = Order.create_order(req['requester_id'], req['owner_id'], req['item_id'], title, price, 1)
    try:
        Item.mark_as_sold(req['item_id'])
    except Exception as e:
        print(f"[requests_controller] failed to mark sold: {e}")

    RequestModel.update_request_status(request_id, 'accepted')

    # Notify requester
    try:
        Message.create_message(owner_id, req['requester_id'], req['item_id'], f'Your request was accepted. Order #{order_id} created.')
    except Exception as e:
        print(f"[requests_controller] notify requester failed: {e}")

    flash('Request accepted — order created', 'success')
    return redirect(url_for('orders_bp.view_order', order_id=order_id))


@requests_bp.route('/requests/decline/<int:request_id>', methods=['POST'])
@login_required
def decline_request(request_id):
    req = RequestModel.get_request_by_id(request_id)
    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('requests_bp.owner_requests'))

    owner_id = session.get('user_id')
    if owner_id != req['owner_id']:
        flash('You do not have permission to decline this request', 'error')
        return redirect(url_for('requests_bp.owner_requests'))

    RequestModel.update_request_status(request_id, 'declined')
    try:
        Message.create_message(owner_id, req['requester_id'], req['item_id'], 'Your request was declined by the seller.')
    except Exception as e:
        print(f"[requests_controller] notify decline failed: {e}")

    flash('Request declined', 'info')
    return redirect(url_for('requests_bp.owner_requests'))
