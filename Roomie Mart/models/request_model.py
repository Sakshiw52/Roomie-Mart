from database.db_connection import get_db_connection


class RequestModel:
    @staticmethod
    def count_pending_requests_for_owner(owner_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT COUNT(*) FROM requests
            WHERE owner_id = ? AND status = 'pending'
        ''', (owner_id,))
        count = cur.fetchone()[0]
        conn.close()
        return count
    @staticmethod
    def create_request(item_id, requester_id, owner_id, message=None, status='pending'):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO requests (item_id, requester_id, owner_id, message, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (item_id, requester_id, owner_id, message, status))
        conn.commit()
        req_id = cur.lastrowid
        conn.close()
        return req_id

    @staticmethod
    def get_requests_for_owner(owner_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT r.*, i.title as item_title, u.name as requester_name, u.email as requester_email
            FROM requests r
            JOIN items i ON r.item_id = i.id
            JOIN users u ON r.requester_id = u.id
            WHERE r.owner_id = ?
            ORDER BY r.created_at DESC
        ''', (owner_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_requests_for_requester(requester_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT r.*, i.title as item_title, u.name as owner_name, u.email as owner_email
            FROM requests r
            JOIN items i ON r.item_id = i.id
            JOIN users u ON r.owner_id = u.id
            WHERE r.requester_id = ?
            ORDER BY r.created_at DESC
        ''', (requester_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def update_request_status(request_id, status):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE requests SET status = ? WHERE id = ?', (status, request_id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_request_by_id(request_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM requests WHERE id = ?', (request_id,))
        row = cur.fetchone()
        conn.close()
        return row
