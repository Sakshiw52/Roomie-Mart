import sqlite3
import os
from sqlite3 import Error

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'hosteltrade.db')

def get_db_connection():
    """Create a database connection to the SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Error as e:
        print(e)
    
    return conn

def init_db():
    """Initialize the database with tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        hostel TEXT,
        block TEXT,
        room TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        condition TEXT NOT NULL,
        image TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        description TEXT,
        hostel TEXT,
        block TEXT,
        status TEXT DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Ensure new geolocation columns exist for older DBs: add columns if missing
    try:
        cursor.execute('ALTER TABLE items ADD COLUMN address TEXT')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE items ADD COLUMN latitude REAL')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE items ADD COLUMN longitude REAL')
    except Exception:
        pass
    
    # Create requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        requester_id INTEGER NOT NULL,
        owner_id INTEGER NOT NULL,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES items (id),
        FOREIGN KEY (requester_id) REFERENCES users (id),
        FOREIGN KEY (owner_id) REFERENCES users (id)
    )
    ''')
    
    # Create messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users (id),
        FOREIGN KEY (receiver_id) REFERENCES users (id),
        FOREIGN KEY (item_id) REFERENCES items (id)
    )
    ''')
    
    conn.commit()
    conn.close()

    # Create orders table
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        item_title TEXT,
        price REAL,
        quantity INTEGER DEFAULT 1,
        total REAL,
        transaction_ref TEXT,
        status TEXT DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (buyer_id) REFERENCES users (id),
        FOREIGN KEY (seller_id) REFERENCES users (id),
        FOREIGN KEY (item_id) REFERENCES items (id)
    )
    ''')
    conn.commit()
    conn.close()

    # Create feedbacks table
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        email TEXT,
        rating INTEGER,
        comment TEXT,
        item_id INTEGER,
        seller_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (item_id) REFERENCES items (id),
        FOREIGN KEY (seller_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    conn.close()
    # Backfill/add columns for older databases that may lack them
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE feedbacks ADD COLUMN item_id INTEGER')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE feedbacks ADD COLUMN seller_id INTEGER')
    except Exception:
        pass
    conn.commit()
    conn.close()

# Initialize database when module is imported
init_db()