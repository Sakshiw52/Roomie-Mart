from database.db_connection import get_db_connection
from datetime import datetime

class Item:
    @staticmethod
    def create_item(user_id, title, category, price, condition, image, description, hostel, block, address=None, latitude=None, longitude=None):
        """Create a new item listing"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO items (user_id, title, category, price, condition, image, address, latitude, longitude, description, hostel, block, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available')
        ''', (user_id, title, category, price, condition, image, address, latitude, longitude, description, hostel, block))
        
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        
        return item_id
    
    @staticmethod
    def get_item_by_id(item_id):
        """Get item by ID with seller information"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.*, u.name as seller_name, u.email as seller_email, u.phone as seller_phone,
                   u.hostel as seller_hostel, u.block as seller_block, u.room as seller_room
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE i.id = ?
        ''', (item_id,))
        
        item = cursor.fetchone()
        conn.close()
        
        return item
    
    @staticmethod
    def get_all_items(limit=None, status='available'):
        """Get all available items"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT i.*, u.name as seller_name
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE i.status = ?
            ORDER BY i.created_at DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, (status,))
        items = cursor.fetchall()
        conn.close()
        
        return items
    
    @staticmethod
    def get_user_items(user_id):
        """Get all items posted by a specific user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM items
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        return items
    
    @staticmethod
    def update_item(item_id, title, category, price, condition, image, description, address=None, latitude=None, longitude=None):
        """Update an item listing"""
        conn = get_db_connection()
        cursor = conn.cursor()
        # Build update dynamically to include optional fields
        fields = ['title = ?', 'category = ?', 'price = ?', 'condition = ?', 'description = ?']
        params = [title, category, price, condition, description]

        if image:
            # insert image before description
            fields.insert(4, 'image = ?')
            params.insert(4, image)

        if address is not None:
            fields.append('address = ?')
            params.append(address)
        if latitude is not None:
            fields.append('latitude = ?')
            params.append(latitude)
        if longitude is not None:
            fields.append('longitude = ?')
            params.append(longitude)

        params.append(item_id)
        sql = f"UPDATE items SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, tuple(params))

        conn.commit()
        conn.close()

        return True
    
    @staticmethod
    def delete_item(item_id):
        """Delete an item listing"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def mark_as_sold(item_id):
        """Mark an item as sold"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE items
            SET status = 'sold'
            WHERE id = ?
        ''', (item_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    @staticmethod
    def search_items(query, category=None, hostel=None, block=None):
        """Search for items based on various criteria"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql_query = '''
            SELECT i.*, u.name as seller_name
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE i.status = 'available'
        '''
        params = []
        
        if query:
            sql_query += " AND (i.title LIKE ? OR i.description LIKE ?)"
            params.extend([f'%{query}%', f'%{query}%'])
        
        if category:
            sql_query += " AND i.category = ?"
            params.append(category)
        
        if hostel:
            sql_query += " AND i.hostel = ?"
            params.append(hostel)
        
        if block:
            sql_query += " AND i.block = ?"
            params.append(block)
        
        sql_query += " ORDER BY i.created_at DESC"
        
        cursor.execute(sql_query, params)
        items = cursor.fetchall()
        conn.close()
        
        return items

    @staticmethod
    def get_filtered_items(category=None, condition=None, hostel=None, block=None, min_price=None, max_price=None):
        """Get items filtered by category, condition, location, and price range"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql_query = '''
            SELECT i.*, u.name as seller_name
            FROM items i
            JOIN users u ON i.user_id = u.id
            WHERE i.status = 'available'
        '''
        params = []
        
        if category:
            sql_query += " AND i.category = ?"
            params.append(category)
        
        if condition:
            sql_query += " AND i.condition = ?"
            params.append(condition)
        
        if hostel:
            sql_query += " AND i.hostel = ?"
            params.append(hostel)
        
        if block:
            sql_query += " AND i.block = ?"
            params.append(block)
        
        if min_price is not None:
            sql_query += " AND i.price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            sql_query += " AND i.price <= ?"
            params.append(max_price)
        
        sql_query += " ORDER BY i.created_at DESC"
        
        cursor.execute(sql_query, params)
        items = cursor.fetchall()
        conn.close()
        
        return items