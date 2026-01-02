from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models.item_model import Item
from utils.authentication import login_required
from models.order_model import Order
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import current_app
import urllib.parse
import urllib.request
import json

item_bp = Blueprint('item_bp', __name__)

# Helper function to save uploaded image
def save_image(file):
    if file and file.filename:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        new_filename = f"{timestamp}_{filename}"
        file_path = os.path.join('static/uploads', new_filename)
        file.save(os.path.join(os.getcwd(), file_path))
        return file_path
    return None


# Helper to normalize DB rows to dicts and parse timestamp strings into datetimes
def process_items(rows):
    from datetime import datetime as _dt
    processed = []
    for r in rows:
        # sqlite3.Row is indexable and convertible to dict
        item = dict(r) if not isinstance(r, dict) else dict(r)
        for ts_field in ('created_at', 'updated_at'):
            val = item.get(ts_field)
            if isinstance(val, str) and val:
                parsed = None
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
                    try:
                        parsed = _dt.strptime(val, fmt)
                        break
                    except Exception:
                        continue
                if parsed:
                    item[ts_field] = parsed
        # Normalize image path to filename only so templates can use
        # `url_for('static', filename='uploads/' + item.image)` reliably.
        img = item.get('image')
        if img:
            try:
                item['image'] = os.path.basename(str(img).replace('\\', '/'))
            except Exception:
                pass
        processed.append(item)
    return processed

@item_bp.route('/marketplace')
def marketplace():
    # Get filter parameters from query string
    category = request.args.get('category', '').strip()
    condition = request.args.get('condition', '').strip()
    hostel = request.args.get('hostel', '').strip()
    block = request.args.get('block', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    
    # Convert prices to float if provided
    try:
        min_price = float(min_price) if min_price else None
    except ValueError:
        min_price = None
    
    try:
        max_price = float(max_price) if max_price else None
    except ValueError:
        max_price = None
    
    # Get filtered items
    items = Item.get_filtered_items(category=category, condition=condition, 
                                     hostel=hostel, block=block, 
                                     min_price=min_price, max_price=max_price)
    items = process_items(items)
    
    return render_template('marketplace.html', items=items, 
                           category=category, condition=condition, 
                           hostel=hostel, block=block, 
                           min_price=min_price, max_price=max_price)

@item_bp.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.get_item_by_id(item_id)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('item_bp.marketplace'))
    # Ensure timestamp fields are datetime objects for templates
    try:
        processed = process_items([item])
        item = processed[0] if processed else dict(item)
    except Exception:
        # Fallback to raw item if processing fails
        item = dict(item) if not isinstance(item, dict) else item
    # Normalize image path: templates expect just the filename under static/uploads/
    img = item.get('image')
    if img:
        try:
            # If DB stored a path like 'static/uploads/...', extract the basename
            item['image'] = os.path.basename(img.replace('\\', '/'))
        except Exception:
            # leave as-is if something unexpected
            pass
    # Build a seller dict expected by the template (templates use `seller.name`)
    seller = {
        'name': item.get('seller_name') or item.get('seller') or '',
        'email': item.get('seller_email') or item.get('seller_email', ''),
        'phone': item.get('seller_phone') or item.get('seller_phone', ''),
        'hostel': item.get('seller_hostel') or item.get('hostel') or '',
        'block': item.get('seller_block') or item.get('block') or '',
        'room': item.get('seller_room') or item.get('room') or ''
    }

    # If the current user is related to this item, fetch any order (bill) for quick access
    order = None
    try:
        uid = session.get('user_id')
        if uid:
            order = Order.get_order_for_item_and_user(item_id, uid)
    except Exception:
        order = None

    return render_template('product_detail.html', item=item, seller=seller, order=order)

@item_bp.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        # Collect form data with safe .get calls
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '').strip()
        condition = request.form.get('condition', '').strip()
        description = request.form.get('description', '').strip()
        # Location fields (optional)
        address = request.form.get('address', '').strip() or None
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        try:
            latitude = float(latitude) if latitude else None
        except Exception:
            latitude = None
        try:
            longitude = float(longitude) if longitude else None
        except Exception:
            longitude = None

        # Ensure user is set in session (login_required should enforce this)
        user_id = session.get('user_id')
        if not user_id:
            flash('You must be logged in to add an item', 'error')
            return redirect(url_for('auth_bp.login'))

        # Handle image upload
        image_file = request.files.get('image')
        image_path = save_image(image_file) if image_file and image_file.filename else None

        # Get user's hostel and block from the database (best-effort)
        from models.user_model import User
        user = User.get_user_by_id(user_id)
        # sqlite3.Row doesn't implement dict.get; access keys safely
        hostel = ''
        block = ''
        if user:
            try:
                hostel = user['hostel'] or ''
            except Exception:
                hostel = ''
            try:
                block = user['block'] or ''
            except Exception:
                block = ''

        # Create item and redirect on success
        try:
            item_id = Item.create_item(user_id, title, category, price, condition, image_path, description, hostel, block, address=address, latitude=latitude, longitude=longitude)
            # Log item creation for debugging
            print(f"[item_controller] Created item id={item_id} user_id={user_id} title={title}")
            flash('Item added successfully', 'success')
            return redirect(url_for('item_bp.my_items'))
        except Exception as e:
            # Don't crash; show an error and fall through to re-render the form
            print(f"[item_controller] Error creating item: {e}")
            flash('Error adding item: ' + str(e), 'error')

        # Note: server-side geocoding removed. Items will store the provided address only; no API calls are made.

    # For GET (or if POST failed), render the add/edit form
    return render_template('add_edit_item.html')

@item_bp.route('/my_items')
@login_required
def my_items():
    user_id = session['user_id']
    rows = Item.get_user_items(user_id)
    processed = process_items(rows)

    # Split items into active (available) and sold lists for the template
    active_items = [item for item in processed if item.get('status') == 'available']
    sold_items = [item for item in processed if item.get('status') == 'sold']

    # Fetch purchases (orders where the current user is the buyer)
    purchases = []
    try:
        order_rows = Order.get_orders_for_buyer(user_id)
        for r in order_rows:
            o = dict(r) if not isinstance(r, dict) else r
            # created_at may be a string in DB; format a readable string for the template
            ca = o.get('created_at')
            created_str = None
            if isinstance(ca, str) and ca:
                from datetime import datetime as _dt
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
                    try:
                        created_str = _dt.strptime(ca, fmt).strftime('%d %b %Y')
                        break
                    except Exception:
                        continue
            elif hasattr(ca, 'strftime'):
                try:
                    created_str = ca.strftime('%d %b %Y')
                except Exception:
                    created_str = str(ca)
            else:
                created_str = str(ca) if ca is not None else ''

            o['created_at_str'] = created_str
            purchases.append(o)
    except Exception:
        purchases = []

    return render_template('my_items.html', active_items=active_items, sold_items=sold_items, purchases=purchases)

@item_bp.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.get_item_by_id(item_id)
    
    # Check if item exists and belongs to the current user
    if not item or item['user_id'] != session['user_id']:
        flash('You do not have permission to edit this item', 'error')
        return redirect(url_for('item_bp.my_items'))
    
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        price = request.form['price']
        condition = request.form['condition']
        description = request.form['description']
        # Handle image upload
        image_file = request.files.get('image')
        image_path = save_image(image_file) if image_file and image_file.filename else None

        # Location fields (optional)
        address = request.form.get('address', '').strip() or None
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        try:
            latitude = float(latitude) if latitude else None
        except Exception:
            latitude = None
        try:
            longitude = float(longitude) if longitude else None
        except Exception:
            longitude = None

        # Update item
        Item.update_item(item_id, title, category, price, condition, image_path, description, address=address, latitude=latitude, longitude=longitude)

        flash('Item updated successfully', 'success')
        return redirect(url_for('item_bp.my_items'))

    return render_template('add_edit_item.html', item=item, edit_mode=True)

@item_bp.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.get_item_by_id(item_id)
    
    # Check if item exists and belongs to the current user
    if not item or item['user_id'] != session['user_id']:
        flash('You do not have permission to delete this item', 'error')
        return redirect(url_for('item_bp.my_items'))
    
    # Delete item
    Item.delete_item(item_id)
    
    flash('Item deleted successfully', 'success')
    return redirect(url_for('item_bp.my_items'))

@item_bp.route('/mark_as_sold/<int:item_id>', methods=['POST'])
@login_required
def mark_as_sold(item_id):
    item = Item.get_item_by_id(item_id)
    
    # Check if item exists and belongs to the current user
    if not item or item['user_id'] != session['user_id']:
        flash('You do not have permission to update this item', 'error')
        return redirect(url_for('item_bp.my_items'))
    
    # Mark item as sold
    Item.mark_as_sold(item_id)
    
    flash('Item marked as sold', 'success')
    return redirect(url_for('item_bp.my_items'))

@item_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    hostel = request.args.get('hostel', '')
    block = request.args.get('block', '')
    
    items = Item.search_items(query, category, hostel, block)
    items = process_items(items)

    return render_template('marketplace.html', items=items, search=True,
                           query=query, category=category, hostel=hostel, block=block)


@item_bp.route('/send_request/<int:item_id>', methods=['POST'])
@login_required
def send_request(item_id):
    """Handle the contact-seller form on the product detail page.
    Creates a Message from current user to the item's owner and redirects to the conversation.
    """
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to contact the seller', 'error')
        return redirect(url_for('auth_bp.login'))

    content = request.form.get('message', '').strip()
    # Fetch the item to get owner info
    item = Item.get_item_by_id(item_id)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('item_bp.marketplace'))

    owner_id = item['user_id']
    if owner_id == user_id:
        flash('You cannot contact yourself about your own item', 'info')
        return redirect(url_for('item_bp.item_detail', item_id=item_id))

    # Create a message to the owner (also serves as a contact/request)
    try:
        from models.message_model import Message
        Message.create_message(user_id, owner_id, item_id, content or 'Hi, I am interested in this item.')
        flash('Message sent to the seller', 'success')
    except Exception as e:
        print(f"[item_controller] Error sending message: {e}")
        flash('Failed to send message: ' + str(e), 'error')

    # Redirect to the conversation view for this item between the two users
    return redirect(url_for('message_bp.conversation', item_id=item_id, other_user_id=owner_id))