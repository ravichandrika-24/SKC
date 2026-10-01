from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "orders.db")

# Restaurant listings are examples.
# Confirm participation and menus before accepting real orders.
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


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'customer'
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT,
                phone TEXT,
                address TEXT,
                restaurant TEXT,
                items TEXT,
                total REAL,
                payment_method TEXT DEFAULT 'COD',
                payment_status TEXT DEFAULT 'Pending',
                status TEXT DEFAULT 'Placed'
            )
        """)

        columns = {
            row["name"]
            for row in con.execute("PRAGMA table_info(orders)")
        }

        additions = {
            "customer": "TEXT",
            "phone": "TEXT",
            "address": "TEXT",
            "restaurant": "TEXT",
            "items": "TEXT",
            "total": "REAL",
            "payment_method": "TEXT DEFAULT 'COD'",
            "payment_status": "TEXT DEFAULT 'Pending'",
            "status": "TEXT DEFAULT 'Placed'"
        }

        for name, definition in additions.items():
            if name not in columns:
                con.execute(
                    f"ALTER TABLE orders ADD COLUMN {name} {definition}"
                )

        con.commit()


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:filename>")
def pages(filename):
    allowed = {
        "index.html",
        "style.css",
        "script.js",
        "register.html",
        "login.html",
        "restaurant-detail.html",
        "checkout.html",
        "orders.html",
        "order_success.html"
    }

    if filename not in allowed:
        return jsonify(error="Page not found"), 404

    return send_from_directory(BASE_DIR, filename)


@app.route("/admin")
def admin_page():
    return send_from_directory(".", "admin.html")

@app.route("/api/admin/orders")
def admin_orders():
    try:
        with db() as con:
            rows = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()

        return jsonify([dict(row) for row in rows])

    except Exception:
        return jsonify([])
@app.route("/api/admin/orders/<int:order_id>", methods=["PATCH"])
def update_admin_order(order_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()
    allowed = {"Placed","Preparing","Ready","Out for Delivery","Delivered","Cancelled"}
    if status not in allowed:
        return jsonify(error="Invalid status"), 400
    with db() as con:
        cur = con.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        con.commit()
    if cur.rowcount == 0:
        return jsonify(error="Order not found"), 404
    return jsonify(message="Order status updated")

@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/api/restaurants")
def restaurants():
    return jsonify(RESTAURANTS)


@app.route("/api/restaurants/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    for restaurant in RESTAURANTS:
        if restaurant["id"] == restaurant_id:
            return jsonify(restaurant)

    return jsonify(error="Restaurant not found"), 404


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not name or not phone or len(password) < 8:
        return jsonify(
            error="Enter your name, phone, and a password of at least 8 characters"
        ), 400

    if not phone.isdigit() or len(phone) != 10:
        return jsonify(error="Enter a valid 10-digit phone number"), 400

    try:
        with db() as con:
            con.execute(
                """
                INSERT INTO users(name, phone, password, role)
                VALUES (?, ?, ?, 'customer')
                """,
                (name, phone, generate_password_hash(password))
            )
            con.commit()

        return jsonify(message="Account created"), 201

    except sqlite3.IntegrityError:
        return jsonify(error="Phone number already registered"), 409


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    with db() as con:
        user = con.execute(
            "SELECT * FROM users WHERE phone = ?",
            (phone,)
        ).fetchone()

    if not user or not check_password_hash(user["password"], password):
        return jsonify(error="Invalid phone number or password"), 401

    return jsonify(
        message="Login successful",
        user={
            "id": user["id"],
            "name": user["name"],
            "phone": user["phone"],
            "role": user["role"]
        }
    )


@app.route("/api/order", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}

    customer = str(data.get("customer", "")).strip()
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip()
    restaurant_id = data.get("restaurant_id")
    items = data.get("items", [])
    payment_method = str(
        data.get("payment_method", "COD")
    ).upper()

    if not customer or not phone or not address:
        return jsonify(
            error="Customer name, phone, and address are required"
        ), 400

    if not phone.isdigit() or len(phone) != 10:
        return jsonify(error="Enter a valid 10-digit phone number"), 400

    if payment_method != "COD":
        return jsonify(
            error="Only cash on delivery is currently available"
        ), 400

    if not isinstance(items, list) or not items:
        return jsonify(error="Your cart is empty"), 400

    restaurant = next(
        (r for r in RESTAURANTS if r["id"] == restaurant_id),
        None
    )

    if not restaurant:
        return jsonify(error="Restaurant not found"), 404

    menu = {
        item["name"].lower(): item["price"]
        for item in restaurant["menu"]
    }

    total = 0
    validated_items = []

    for item in items:
        if not isinstance(item, dict):
            return jsonify(error="Invalid food item"), 400

        name = str(item.get("name", "")).strip().lower()

        try:
            quantity = int(item.get("quantity", 0))
        except (ValueError, TypeError):
            return jsonify(error="Invalid quantity"), 400

        if name not in menu or quantity < 1 or quantity > 20:
            return jsonify(error="Invalid item or quantity"), 400

        price = menu[name]
        subtotal = price * quantity
        total += subtotal

        validated_items.append({
            "name": name.title(),
            "price": price,
            "quantity": quantity,
            "subtotal": subtotal
        })

    with db() as con:
        cur = con.execute(
            """
            INSERT INTO orders (
                customer, phone, address, restaurant,
                items, total, payment_method,
                payment_status, status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'COD', 'Pending', 'Placed')
            """,
            (
                customer,
                phone,
                address,
                restaurant["name"],
                json.dumps(validated_items),
                total
            )
        )
        con.commit()
        order_id = cur.lastrowid

    return jsonify(
        message="Order placed successfully",
        order_id=order_id,
        restaurant=restaurant["name"],
        total=total,
        payment_method="COD",
        status="Placed"
    ), 201


@app.route("/api/orders/<phone>")
def user_orders(phone):
    with db() as con:
        rows = con.execute(
            """
            SELECT * FROM orders
            WHERE phone = ?
            ORDER BY id DESC
            """,
            (phone,)
        ).fetchall()

    result = []
    for row in rows:
        order = dict(row)
        try:
            order["items"] = json.loads(order["items"] or "[]")
        except (ValueError, TypeError):
            order["items"] = []
        result.append(order)

    return jsonify(result)



# ---------- RIDER SYSTEM ----------
def init_rider_system():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS rider_assignments(
                order_id INTEGER PRIMARY KEY,
                rider_phone TEXT NOT NULL
            )
        """)
        con.commit()

@app.route("/rider")
def rider_page():
    return send_from_directory(".", "rider.html")

@app.route("/api/rider/test")
def rider_test():
    try:
        with db() as con:
            con.execute("SELECT 1").fetchone()
        return jsonify(status="OK", database="OK")
    except Exception as e:
        return jsonify(status="ERROR", error=str(e), error_type=type(e).__name__), 500
@app.route("/api/rider/test")
def rider_test():
    try:
        with db() as con:
            con.execute("SELECT 1").fetchone()
        return jsonify(status="OK", database="OK")
    except Exception as e:
        return jsonify(status="ERROR", error=str(e), error_type=type(e).__name__), 500
@app.route("/api/rider/orders")
def rider_orders():
    phone = str(request.args.get("phone", "")).strip()

    if not phone:
        return jsonify(error="Rider phone is required"), 400

    with db() as con:
        rows = con.execute("""
            SELECT
                o.id,
                o.phone,
                o.items,
                o.total,
                o.status,
                ra.rider_phone
            FROM orders o
            LEFT JOIN rider_assignments ra ON o.id = ra.order_id
            WHERE o.status NOT IN ('Delivered','Cancelled')
            ORDER BY o.id DESC
        """).fetchall()

    return jsonify([dict(row) for row in rows])

@app.route("/api/rider/orders/<int:order_id>/accept", methods=["PATCH"])
def rider_accept_order(order_id):
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()

    if not phone:
        return jsonify(error="Rider phone is required"), 400

    with db() as con:
        order = con.execute(
            "SELECT id,status FROM orders WHERE id=?",
            (order_id,)
        ).fetchone()

        if not order:
            return jsonify(error="Order not found"), 404

        existing = con.execute(
            "SELECT rider_phone FROM rider_assignments WHERE order_id=?",
            (order_id,)
        ).fetchone()

        if existing and existing["rider_phone"] != phone:
            return jsonify(error="Order is already assigned to another rider"), 409

        con.execute("""
            INSERT OR REPLACE INTO rider_assignments(order_id,rider_phone)
            VALUES(?,?)
        """, (order_id, phone))

        con.execute(
            "UPDATE orders SET status=? WHERE id=?",
            ("Out for Delivery", order_id)
        )

        con.commit()

    return jsonify(message="Delivery accepted")

@app.route("/api/rider/orders/<int:order_id>/status", methods=["PATCH"])
def rider_update_status(order_id):
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    status = str(data.get("status", "")).strip()

    if not phone:
        return jsonify(error="Rider phone is required"), 400

    if status not in ("Out for Delivery", "Delivered"):
        return jsonify(error="Invalid delivery status"), 400

    with db() as con:
        assignment = con.execute(
            "SELECT rider_phone FROM rider_assignments WHERE order_id=?",
            (order_id,)
        ).fetchone()

        if not assignment:
            return jsonify(error="Order is not assigned to a rider"), 400

        if assignment["rider_phone"] != phone:
            return jsonify(error="This order belongs to another rider"), 403

        con.execute(
            "UPDATE orders SET status=? WHERE id=?",
            (status, order_id)
        )
        con.commit()

    return jsonify(message="Delivery status updated")

init_db()
init_rider_system()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)














