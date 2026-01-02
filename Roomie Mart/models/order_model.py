from database.db_connection import get_db_connection
import uuid

class Order:
    @staticmethod
    def create_order(buyer_id, seller_id, item_id, item_title, price, quantity=1, total=None, transaction_ref=None):
        conn = get_db_connection()
        cur = conn.cursor()
        if total is None:
            total = float(price) * int(quantity)
        if not transaction_ref:
            transaction_ref = str(uuid.uuid4())
        cur.execute('''
            INSERT INTO orders (buyer_id, seller_id, item_id, item_title, price, quantity, total, transaction_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (buyer_id, seller_id, item_id, item_title, price, quantity, total, transaction_ref))
        conn.commit()
        order_id = cur.lastrowid
        conn.close()
        return order_id

    @staticmethod
    def get_orders_for_buyer(buyer_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT o.*, u.name as seller_name, u.email as seller_email
            FROM orders o
            JOIN users u ON o.seller_id = u.id
            WHERE o.buyer_id = ?
            ORDER BY o.created_at DESC
        ''', (buyer_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_orders_for_seller(seller_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT o.*, u.name as buyer_name, u.email as buyer_email
            FROM orders o
            JOIN users u ON o.buyer_id = u.id
            WHERE o.seller_id = ?
            ORDER BY o.created_at DESC
        ''', (seller_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_order_by_id(order_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT o.*, b.name as buyer_name, b.email as buyer_email, s.name as seller_name, s.email as seller_email FROM orders o JOIN users b ON o.buyer_id = b.id JOIN users s ON o.seller_id = s.id WHERE o.id = ?', (order_id,))
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def get_order_for_item_and_user(item_id, user_id):
        """Return an order for the given item where user_id is buyer or seller (latest)."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT o.*, b.name as buyer_name, b.email as buyer_email, s.name as seller_name, s.email as seller_email
            FROM orders o
            JOIN users b ON o.buyer_id = b.id
            JOIN users s ON o.seller_id = s.id
            WHERE o.item_id = ? AND (o.buyer_id = ? OR o.seller_id = ?)
            ORDER BY o.created_at DESC
            LIMIT 1
        ''', (item_id, user_id, user_id))
        row = cur.fetchone()
        conn.close()
        return row
