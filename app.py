from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "skc.db")


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT,
            phone TEXT,
            address TEXT,
            restaurant_id INTEGER,
            items TEXT,
            total REAL,
            payment_method TEXT,
            status TEXT DEFAULT 'Placed'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS rider_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            rider_name TEXT,
            status TEXT DEFAULT 'Assigned'
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- RESTAURANTS ----------------

RESTAURANTS = [
    {
        "id": 1,
        "name": "Ajwa Restaurant",
        "location": "Kurnool",
        "menu": [
            {"name": "Chicken Biryani", "price": 180},
            {"name": "Veg Biryani", "price": 140}
        ]
    },
    {
        "id": 2,
        "name": "Malik Lotus Restaurant",
        "location": "Kurnool",
        "menu": [
            {"name": "Chicken Biryani", "price": 200},
            {"name": "Fried Rice", "price": 120}
        ]
    },
    {
        "id": 3,
        "name": "The Magic Resto",
        "location": "Kurnool",
        "menu": [
            {"name": "Chicken Biryani", "price": 190},
            {"name": "Paneer Fried Rice", "price": 150}
        ]
    }
]


# ---------------- PAGES ----------------

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:filename>")
def static_pages(filename):

    allowed = {
        "index.html",
        "style.css",
        "script.js",
        "register.html",
        "login.html",
        "restaurant-detail.html",
        "checkout.html",
        "orders.html",
        "order_success.html",
        "admin.html",
        "rider.html"
    }

    if filename in allowed:
        return send_from_directory(BASE_DIR, filename)

    return "Page not found", 404


@app.route("/admin")
def admin():
    return send_from_directory(BASE_DIR, "admin.html")


@app.route("/rider")
def rider():
    return send_from_directory(BASE_DIR, "rider.html")


# ---------------- RESTAURANTS API ----------------

@app.route("/api/restaurants")
def restaurants():
    return jsonify(RESTAURANTS)


@app.route("/api/restaurants/<int:restaurant_id>")
def restaurant_details(restaurant_id):

    restaurant = next(
        (r for r in RESTAURANTS if r["id"] == restaurant_id),
        None
    )

    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    return jsonify(restaurant)


# ---------------- REGISTER ----------------

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")

    if not name or not phone or not password:
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE phone=?",
        (phone,)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({"error": "User already exists"}), 400

    hashed = generate_password_hash(password)

    conn.execute(
        "INSERT INTO users (name, phone, password) VALUES (?, ?, ?)",
        (name, phone, hashed)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Registration successful"
    })


# ---------------- LOGIN ----------------

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    phone = data.get("phone", "").strip()
    password = data.get("password", "")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE phone=?",
        (phone,)
    ).fetchone()

    conn.close()

    if not user:
        return jsonify({"error": "Invalid phone or password"}), 401

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid phone or password"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "phone": user["phone"]
        }
    })


# ---------------- PLACE ORDER ----------------

@app.route("/api/order", methods=["POST"])
def place_order():

    data = request.get_json()

    customer = data.get("customer", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    restaurant_id = data.get("restaurant_id")
    items = data.get("items", [])
    payment_method = data.get("payment_method", "COD")

    if not customer or not phone or not address:
        return jsonify({
            "error": "Customer, phone and address are required"
        }), 400

    if not items:
        return jsonify({
            "error": "Please select a food item"
        }), 400

    total = 0

    for item in items:
        price = float(item.get("price", 0))
        quantity = int(item.get("quantity", 1))
        total += price * quantity

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO orders
        (customer, phone, address, restaurant_id, items, total, payment_method, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer,
        phone,
        address,
        restaurant_id,
        json.dumps(items),
        total,
        payment_method,
        "Placed"
    ))

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order placed successfully",
        "order_id": order_id,
        "total": total
    })


# ---------------- CUSTOMER ORDER HISTORY ----------------

@app.route("/api/orders/<phone>")
def customer_orders(phone):

    conn = get_db()

    orders = conn.execute("""
        SELECT *
        FROM orders
        WHERE phone=?
        ORDER BY id DESC
    """, (phone,)).fetchall()

    conn.close()

    result = []

    for order in orders:

        result.append({
            "id": order["id"],
            "customer": order["customer"],
            "phone": order["phone"],
            "address": order["address"],
            "restaurant_id": order["restaurant_id"],
            "items": json.loads(order["items"]),
            "total": order["total"],
            "payment_method": order["payment_method"],
            "status": order["status"]
        })

    return jsonify(result)


# ---------------- ADMIN ORDERS ----------------

@app.route("/api/admin/orders")
def admin_orders():

    conn = get_db()

    orders = conn.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    result = []

    for order in orders:

        result.append({
            "id": order["id"],
            "customer": order["customer"],
            "phone": order["phone"],
            "address": order["address"],
            "restaurant_id": order["restaurant_id"],
            "items": json.loads(order["items"]),
            "total": order["total"],
            "payment_method": order["payment_method"],
            "status": order["status"]
        })

    return jsonify(result)


# ---------------- ADMIN STATUS ----------------

@app.route("/api/admin/orders/<int:order_id>", methods=["PATCH"])
def update_order(order_id):

    data = request.get_json()
    status = data.get("status")

    allowed_statuses = [
        "Placed",
        "Preparing",
        "Ready",
        "Out for Delivery",
        "Delivered",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db()

    cursor = conn.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (status, order_id)
    )

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    conn.close()

    return jsonify({
        "message": "Order status updated",
        "status": status
    })


# ---------------- RIDER ----------------

@app.route("/api/rider/orders")
def rider_orders():

    conn = get_db()

    orders = conn.execute("""
        SELECT *
        FROM orders
        WHERE status IN ('Ready', 'Out for Delivery')
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    result = []

    for order in orders:

        result.append({
            "id": order["id"],
            "customer": order["customer"],
            "phone": order["phone"],
            "address": order["address"],
            "items": json.loads(order["items"]),
            "total": order["total"],
            "status": order["status"]
        })

    return jsonify(result)


@app.route("/api/rider/orders/<int:order_id>/accept", methods=["POST"])
def rider_accept(order_id):

    conn = get_db()

    conn.execute(
        "UPDATE orders SET status=? WHERE id=?",
        ("Out for Delivery", order_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order accepted"
    })


@app.route("/api/rider/orders/<int:order_id>/status", methods=["PATCH"])
def rider_status(order_id):

    data = request.get_json()
    status = data.get("status")

    if status not in ["Out for Delivery", "Delivered"]:
        return jsonify({"error": "Invalid rider status"}), 400

    conn = get_db()

    conn.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (status, order_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Rider status updated",
        "status": status
    })


# ---------------- HEALTH ----------------

@app.route("/health")
def health():
    return jsonify({
        "status": "OK",
        "application": "SKC Food Ordering System"
    })


# ---------------- RUN ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
