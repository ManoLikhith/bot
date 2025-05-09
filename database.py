import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            items TEXT,
            status TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_order(order_id, items):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (order_id, items, status, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (order_id, items, "Preparing", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False

def track_order(order_id):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT items, status, timestamp FROM orders WHERE order_id = ?", (order_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None