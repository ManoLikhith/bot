import sqlite3

conn = sqlite3.connect('orders.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM orders")
orders = cursor.fetchall()
for order in orders:
    print(f"Order ID: {order[0]}")
    print(f"Items: {order[1]}")
    print(f"Status: {order[2]}")
    print(f"Timestamp: {order[3]}\n")
conn.close()