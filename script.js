let cart = [];

async function addToCart(name, price) {
    const item = cart.find(p => p.name === name);
    if (item) {
        item.quantity++;
    } else {
        cart.push({ name, price, quantity: 1 });
    }
    updateCart();
}

function updateCart() {
    document.getElementById("cart-count").textContent =
        cart.reduce((sum, item) => sum + item.quantity, 0);

    document.getElementById("cart-total").textContent =
        cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

    const container = document.getElementById("cart-items");
    container.innerHTML = "";

    if (!cart.length) {
        container.textContent = "Your cart is empty.";
        return;
    }

    cart.forEach((item, index) => {
        const row = document.createElement("div");
        row.className = "cart-row";

        const name = document.createElement("span");
        name.textContent = `${item.name} × ${item.quantity}`;

        const price = document.createElement("strong");
        price.textContent = "₹" + item.price * item.quantity;

        const remove = document.createElement("button");
        remove.textContent = "Remove";
        remove.onclick = () => {
            cart.splice(index, 1);
            updateCart();
        };

        row.append(name, price, remove);
        container.appendChild(row);
    });
}

function showCart() {
    document.getElementById("cart-modal").style.display = "flex";
}

function closeCart() {
    document.getElementById("cart-modal").style.display = "none";
}

function checkout() {
    if (!cart.length) {
        alert("Please add food to your cart first.");
        return;
    }

    const container = document.getElementById("cart-items");
    container.innerHTML = `
        <h3>Delivery Details</h3>
        <form id="order-form">
            <input name="customer" placeholder="Full name" required>
            <input name="phone" type="tel" pattern="[0-9]{10}"
                placeholder="10-digit mobile number" required>
            <textarea name="address" placeholder="Full delivery address"
                required></textarea>
            <button type="submit" class="checkout-button">Place Order</button>
        </form>
        <p id="order-message"></p>
    `;

    document.getElementById("order-form")
        .addEventListener("submit", placeOrder);
}

async function placeOrder(event) {
    event.preventDefault();

    const form = new FormData(event.target);
    const message = document.getElementById("order-message");

    const order = {
        customer: form.get("customer").trim(),
        phone: form.get("phone").trim(),
        address: form.get("address").trim(),
        items: cart.map(item => ({
            name: item.name,
            price: item.price,
            quantity: item.quantity
        })),
        total: cart.reduce(
            (sum, item) => sum + item.price * item.quantity, 0
        )
    };

    message.textContent = "Submitting your order...";

    try {
        const response = await fetch("http://127.0.0.1:5000/api/orders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(order)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Could not place order");
        }

        message.textContent = "Order placed! Your order number is " + result.order_id;
        cart = [];
        updateCart();
    } catch (error) {
        message.textContent =
            "Could not submit order. Check that the backend is running.";
    }
}

function displayFoods() {
    const grid = document.getElementById("food-grid");
    if (!grid) return;

    const foods = [
        { name: "Chicken Biryani", price: 199, emoji: "🍛" },
        { name: "Veg Biryani", price: 149, emoji: "🍚" },
        { name: "Cheese Pizza", price: 249, emoji: "🍕" },
        { name: "Chicken Pizza", price: 349, emoji: "🍕" },
        { name: "Veg Burger", price: 129, emoji: "🍔" },
        { name: "Chicken Burger", price: 199, emoji: "🍔" },
        { name: "Veg Noodles", price: 129, emoji: "🍜" },
        { name: "Fried Rice", price: 149, emoji: "🍚" }
    ];

    const search = document.getElementById("food-search")?.value.toLowerCase() || "";
    grid.innerHTML = "";

    foods.filter(food => food.name.toLowerCase().includes(search))
        .forEach(food => {
            const card = document.createElement("div");
            card.className = "food-card";

            const image = document.createElement("div");
            image.className = "food-image";
            image.textContent = food.emoji;

            const title = document.createElement("h3");
            title.textContent = food.name;

            const bottom = document.createElement("div");
            bottom.className = "food-bottom";

            const price = document.createElement("strong");
            price.textContent = "₹" + food.price;

            const button = document.createElement("button");
            button.textContent = "Add +";
            button.onclick = () => addToCart(food.name, food.price);

            bottom.append(price, button);
            card.append(image, title, bottom);
            grid.appendChild(card);
        });
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("food-search")
        ?.addEventListener("input", displayFoods);
    displayFoods();
    updateCart();
});