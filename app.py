from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

DB = Path(__file__).resolve().parent / "orders.db"

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            menu TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            restaurant TEXT NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'New',
            rider TEXT DEFAULT ''
        )""")

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/restaurant")
def restaurant_page():
    return send_from_directory(".", "restaurant.html")

@app.route("/register")
def register_page():
    return send_from_directory(".", "register.html")

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))
    role = str(data.get("role", "customer")).strip()

    if not name or not phone or len(password) < 8:
        return jsonify(error="Enter your name, phone, and a password of at least 8 characters"), 400
    if role not in ("customer", "rider"):
        return jsonify(error="Invalid account type"), 400

    try:
        with db() as con:
            con.execute(
                "INSERT INTO users(name, phone, password, role) VALUES(?,?,?,?)",
                (name, phone, generate_password_hash(password), role)
            )
        return jsonify(message="Account created")
    except sqlite3.IntegrityError:
        return jsonify(error="Phone number already registered"), 409

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    with db() as con:
        user = con.execute(
            "SELECT * FROM users WHERE phone=?",
            (str(data.get("phone", "")).strip(),)
        ).fetchone()

    if not user or not check_password_hash(user["password"], str(data.get("password", ""))):
        return jsonify(error="Invalid phone or password"), 401
    return jsonify(message="Login successful", user={
        "id": user["id"], "name": user["name"], "role": user["role"]
    })

@app.route("/api/restaurants", methods=["GET", "POST"])
def restaurants():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        fields = ["restaurant", "owner", "phone", "address", "menu"]
        values = [str(data.get(k, "")).strip() for k in fields]
        if not all(values):
            return jsonify(error="Please fill in all fields"), 400
        with db() as con:
            con.execute(
                "INSERT INTO restaurants(name,owner,phone,address,menu) VALUES(?,?,?,?,?)",
                values
            )
        return jsonify(message="Restaurant registered"), 201

    with db() as con:
        rows = con.execute(
            "SELECT id,name AS restaurant,address,menu FROM restaurants ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/orders", methods=["GET", "POST"])
def orders():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        customer = str(data.get("customer_name", data.get("customer", ""))).strip()
        phone = str(data.get("phone", "")).strip()
        address = str(data.get("address", "")).strip()
        restaurant = str(data.get("restaurant", "")).strip()
        items = data.get("items", [])

        if not customer or not phone or not address or not restaurant:
            return jsonify(error="Please complete the order form"), 400
        if not isinstance(items, list) or not items:
            return jsonify(error="Select at least one item"), 400

        with db() as con:
            restaurant_row = con.execute(
                "SELECT menu FROM restaurants WHERE name=?", (restaurant,)
            ).fetchone()
            if not restaurant_row:
                return jsonify(error="Restaurant not found"), 404

            allowed_items = [x.strip() for x in restaurant_row["menu"].split(",")]
            if any(str(item) not in allowed_items for item in items):
                return jsonify(error="Selected item is not on the restaurant menu"), 400

            # Prices are not configured yet; no real payment is collected.
            cur = con.execute(
                """INSERT INTO orders(customer,phone,address,restaurant,items,total,status)
                   VALUES(?,?,?,?,?,0,'New')""",
                (customer, phone, address, restaurant, ", ".join(map(str, items)))
            )
            order_id = cur.lastrowid
        return jsonify(message="Order placed", order_id=order_id), 201

    with db() as con:
        rows = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/orders/<int:order_id>/status", methods=["PATCH"])
def update_status(order_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()
    allowed = ["New", "Accepted", "Preparing", "Ready", "Picked up", "Delivered", "Cancelled"]
    if status not in allowed:
        return jsonify(error="Invalid order status"), 400
    with db() as con:
        cur = con.execute(
            "UPDATE orders SET status=? WHERE id=?", (status, order_id)
        )
        if cur.rowcount == 0:
            return jsonify(error="Order not found"), 404
    return jsonify(message="Status updated")

@app.route("/api/orders/<int:order_id>", methods=["GET"])
def track_order(order_id):
    with db() as con:
        row = con.execute(
            "SELECT id,restaurant,items,total,status FROM orders WHERE id=?",
            (order_id,)
        ).fetchone()
    if not row:
        return jsonify(error="Order not found"), 404
    return jsonify(dict(row))

@app.route("/api/orders/<int:order_id>/rider", methods=["PATCH"])
def assign_rider(order_id):
    data = request.get_json(silent=True) or {}
    rider = str(data.get("rider", "")).strip()
    if not rider:
        return jsonify(error="Enter rider name"), 400
    with db() as con:
        cur = con.execute(
            "UPDATE orders SET rider=? WHERE id=?", (rider, order_id)
        )
        if cur.rowcount == 0:
            return jsonify(error="Order not found"), 404
    return jsonify(message="Rider assigned")

@app.route("/api/earnings")
def earnings():
    with db() as con:
        row = con.execute(
            "SELECT COUNT(*) AS order_count, COALESCE(SUM(total),0) AS total FROM orders"
        ).fetchone()
    return jsonify(dict(row))

@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/login")
def login_page():
    return send_from_directory(".", "login.html")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
