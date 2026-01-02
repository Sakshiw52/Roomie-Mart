from database.db_connection import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    @staticmethod
    def create_user(name, email, password, phone, hostel, block, room):
        """Create a new user in the database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO users (name, email, password, phone, hostel, block, room)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, hashed_password, phone, hostel, block, room))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return user_id
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return user
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        conn.close()
        return user
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        """Verify the password"""
        return check_password_hash(stored_password, provided_password)
    
    @staticmethod
    def update_user(user_id, name, phone, hostel, block, room):
        """Update user profile"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET name = ?, phone = ?, hostel = ?, block = ?, room = ?
            WHERE id = ?
        ''', (name, phone, hostel, block, room, user_id))
        
        conn.commit()
        conn.close()
        
        return True