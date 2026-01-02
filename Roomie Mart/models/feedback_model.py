from database.db_connection import get_db_connection
from datetime import datetime

class Feedback:
    @staticmethod
    def create_feedback(user_id, name, email, rating, comment, item_id=None, seller_id=None):
        conn = get_db_connection()
        cur = conn.cursor()
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Insert with optional item_id and seller_id columns
        cur.execute('''
            INSERT INTO feedbacks (user_id, name, email, rating, comment, item_id, seller_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, email, rating, comment, item_id, seller_id, created_at))
        fid = cur.lastrowid
        conn.commit()
        conn.close()
        return fid

    @staticmethod
    def get_all_feedbacks(limit=100):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM feedbacks ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        conn.close()
        return rows
