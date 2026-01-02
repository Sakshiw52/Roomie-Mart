import sqlite3
from datetime import datetime
from database.db_connection import get_db_connection

class Message:
    @staticmethod
    def create_message(sender_id, receiver_id, item_id, content):
        """Create a new message between users regarding an item"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO messages (sender_id, receiver_id, item_id, content, created_at, is_read)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sender_id, receiver_id, item_id, content, current_time, 0))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return message_id
    
    @staticmethod
    def get_message_by_id(message_id):
        """Get a message by its ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, i.title as item_title, 
                   s.name as sender_name, r.name as receiver_name
            FROM messages m
            JOIN items i ON m.item_id = i.id
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.receiver_id = r.id
            WHERE m.id = ?
        ''', (message_id,))
        
        message = cursor.fetchone()
        conn.close()
        
        return message
    
    @staticmethod
    def get_user_messages(user_id):
        """Get all messages for a user (both sent and received)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, i.title as item_title, i.image as item_image,
                   s.name as sender_name, r.name as receiver_name,
                   CASE WHEN m.sender_id = ? THEN 'sent' ELSE 'received' END as message_type
            FROM messages m
            JOIN items i ON m.item_id = i.id
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.receiver_id = r.id
            WHERE m.sender_id = ? OR m.receiver_id = ?
            ORDER BY m.created_at DESC
        ''', (user_id, user_id, user_id))
        
        messages = cursor.fetchall()
        conn.close()
        
        return messages
    
    @staticmethod
    def get_conversation(user_id, other_user_id, item_id):
        """Get conversation between two users about a specific item"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, i.title as item_title,
                   s.name as sender_name, r.name as receiver_name,
                   CASE WHEN m.sender_id = ? THEN 'sent' ELSE 'received' END as message_type
            FROM messages m
            JOIN items i ON m.item_id = i.id
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.receiver_id = r.id
            WHERE m.item_id = ? AND 
                  ((m.sender_id = ? AND m.receiver_id = ?) OR 
                   (m.sender_id = ? AND m.receiver_id = ?))
            ORDER BY m.created_at ASC
        ''', (user_id, item_id, user_id, other_user_id, other_user_id, user_id))
        
        messages = cursor.fetchall()
        conn.close()
        
        return messages
    
    @staticmethod
    def mark_as_read(message_id):
        """Mark a message as read"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE messages
            SET is_read = 1
            WHERE id = ?
        ''', (message_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread messages for a user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM messages
            WHERE receiver_id = ? AND is_read = 0
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0