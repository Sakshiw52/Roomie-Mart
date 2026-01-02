from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.message_model import Message
from models.item_model import Item
from models.user_model import User
from utils.authentication import login_required

message_bp = Blueprint('message_bp', __name__)

@message_bp.route('/messages')
@login_required
def messages():
    """Display all messages for the current user"""
    user_id = session.get('user_id')
    messages = Message.get_user_messages(user_id)
    
    # Group messages by conversation (item + other user)
    conversations = {}
    for msg in messages:
        other_user_id = msg['sender_id'] if msg['sender_id'] != user_id else msg['receiver_id']
        other_user_name = msg['sender_name'] if msg['sender_id'] != user_id else msg['receiver_name']
        
        key = f"{msg['item_id']}_{other_user_id}"
        if key not in conversations:
            conversations[key] = {
                'item_id': msg['item_id'],
                'item_title': msg['item_title'],
                'item_image': msg['item_image'],
                'other_user_id': other_user_id,
                'other_user_name': other_user_name,
                'last_message': msg['content'],
                'last_message_time': msg['created_at'],
                'unread': 1 if msg['is_read'] == 0 and msg['receiver_id'] == user_id else 0
            }
        else:
            # Update only if this message is newer
            if msg['created_at'] > conversations[key]['last_message_time']:
                conversations[key]['last_message'] = msg['content']
                conversations[key]['last_message_time'] = msg['created_at']
            
            # Count unread messages
            if msg['is_read'] == 0 and msg['receiver_id'] == user_id:
                conversations[key]['unread'] += 1
    
    # Convert to list and sort by last message time (newest first)
    conversation_list = list(conversations.values())
    conversation_list.sort(key=lambda x: x['last_message_time'], reverse=True)
    
    return render_template('messages.html', conversations=conversation_list)

@message_bp.route('/conversation/<int:item_id>/<int:other_user_id>')
@login_required
def conversation(item_id, other_user_id):
    """Display conversation between current user and another user about a specific item"""
    user_id = session.get('user_id')
    
    # Get item and other user details
    item = Item.get_item_by_id(item_id)
    other_user = User.get_user_by_id(other_user_id)
    
    if not item or not other_user:
        flash('Conversation not found', 'danger')
        return redirect(url_for('message_bp.messages'))
    
    # Get messages in this conversation
    messages = Message.get_conversation(user_id, other_user_id, item_id)
    
    # Mark all received messages as read
    for msg in messages:
        if msg['receiver_id'] == user_id and msg['is_read'] == 0:
            Message.mark_as_read(msg['id'])
    
    return render_template('conversation.html', 
                          messages=messages, 
                          item=item, 
                          other_user=other_user,
                          user_id=user_id)

@message_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """Send a new message in a conversation"""
    user_id = session.get('user_id')
    receiver_id = request.form.get('receiver_id')
    item_id = request.form.get('item_id')
    content = request.form.get('content')
    
    if not all([receiver_id, item_id, content]):
        flash('All fields are required', 'danger')
        return redirect(request.referrer)
    
    # Create the message
    message_id = Message.create_message(user_id, receiver_id, item_id, content)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # If AJAX request, return JSON response
        return jsonify({
            'success': True,
            'message_id': message_id
        })
    else:
        # Otherwise redirect back to conversation
        flash('Message sent successfully', 'success')
        return redirect(url_for('message_bp.conversation', item_id=item_id, other_user_id=receiver_id))

@message_bp.route('/unread_count')
@login_required
def unread_count():
    """Get count of unread messages for the current user (for navbar badge)"""
    user_id = session.get('user_id')
    count = Message.get_unread_count(user_id)
    
    return jsonify({
        'count': count
    })