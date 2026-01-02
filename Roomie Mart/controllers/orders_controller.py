from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, make_response
from utils.authentication import login_required
from models.order_model import Order
from models.item_model import Item
from database.db_connection import get_db_connection
import io

orders_bp = Blueprint('orders_bp', __name__)


@orders_bp.route('/orders/buy/<int:item_id>', methods=['POST'])
@login_required
def create_order(item_id):
    # Legacy direct-buy endpoint — create an initial request and send buyer to payment
    buyer_id = session.get('user_id')
    item = Item.get_item_by_id(item_id)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('item_bp.marketplace'))

    seller_id = item['user_id']
    if seller_id == buyer_id:
        flash('You cannot buy your own item', 'error')
        return redirect(url_for('item_bp.item_detail', item_id=item_id))

    # sqlite3.Row doesn't implement .get(); access safely
    try:
        if item['status'] == 'sold':
            flash('Item already sold', 'error')
            return redirect(url_for('item_bp.item_detail', item_id=item_id))
    except Exception:
        # If status is missing or any error, continue (we'll handle later checks)
        pass

    # Create a request and redirect buyer to payment page (to simulate payment)
    from models.request_model import RequestModel
    req_id = RequestModel.create_request(item_id, buyer_id, seller_id, message=None, status='pending')
    # Notify seller by message
    try:
        from models.message_model import Message
        Message.create_message(buyer_id, seller_id, item_id, 'Buyer initiated purchase — pending payment.')
    except Exception as e:
        print(f"[orders_controller] notify seller failed: {e}")

    return redirect(url_for('orders_bp.pay_request', request_id=req_id))


@orders_bp.route('/orders/pay/<int:request_id>', methods=['GET', 'POST'])
@login_required
def pay_request(request_id):
    # Show a simple payment page and simulate payment completion
    from models.request_model import RequestModel
    req = RequestModel.get_request_by_id(request_id)
    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('index'))

    # Ensure buyer owns this request
    if req['requester_id'] != session.get('user_id'):
        flash('You do not have permission to pay for this request', 'error')
        return redirect(url_for('index'))

    # fetch item details for display
    try:
        item = Item.get_item_by_id(req['item_id'])
    except Exception:
        item = None

    # determine price for display (item may be a sqlite3.Row)
    amount = 0.0
    if item:
        try:
            amount = float(item['price'])
        except Exception:
            try:
                amount = float(item.get('price', 0))
            except Exception:
                amount = 0.0

    if request.method == 'POST':
        # Simulate payment success: mark request as paid and notify seller
        RequestModel.update_request_status(request_id, 'paid')
        try:
            from models.message_model import Message
            Message.create_message(req['requester_id'], req['owner_id'], req['item_id'], f'Buyer has completed payment for request #{request_id}.')
        except Exception as e:
            print(f"[orders_controller] notify seller after payment failed: {e}")

        flash('Payment successful. Seller has been notified to confirm the request.', 'success')
        return redirect(url_for('requests_bp.my_requests'))

    return render_template('pay_request.html', request_item=req, item=item, amount=amount)


@orders_bp.route('/orders/my_orders')
@login_required
def my_orders():
    buyer_id = session.get('user_id')
    rows = Order.get_orders_for_buyer(buyer_id)
    return render_template('my_orders.html', orders=rows)


@orders_bp.route('/orders/sales_history')
@login_required
def sales_history():
    seller_id = session.get('user_id')
    rows = Order.get_orders_for_seller(seller_id)
    return render_template('sales_history.html', orders=rows)


@orders_bp.route('/orders/<int:order_id>')
@login_required
def view_order(order_id):
    order = Order.get_order_by_id(order_id)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('index'))

    # Ensure only involved parties can view
    uid = session.get('user_id')
    if uid != order['buyer_id'] and uid != order['seller_id']:
        flash('You do not have permission to view this bill', 'error')
        return redirect(url_for('index'))

    return render_template('order_bill.html', order=order)


@orders_bp.route('/orders/<int:order_id>/download')
@login_required
def download_order(order_id):
    order = Order.get_order_by_id(order_id)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('index'))

    uid = session.get('user_id')
    if uid != order['buyer_id'] and uid != order['seller_id']:
        flash('You do not have permission to download this bill', 'error')
        return redirect(url_for('index'))

    rendered = render_template('order_bill.html', order=order, download=True)
    # Return as an attachment (HTML). User can save as PDF via browser.
    response = make_response(rendered)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=order_{order_id}_bill.html'
    return response
