let restaurants = [];

async function loadRestaurants() {
    const box = document.getElementById("restaurants");
    const select = document.getElementById("restaurant");

    try {
        const response = await fetch("/api/restaurants");

        if (!response.ok) {
            throw new Error("Failed to load restaurants");
        }

        restaurants = await response.json();

        if (box) {
            box.innerHTML = "";
        }

        if (select) {
            select.innerHTML =
                '<option value="">Choose restaurant</option>';
        }

        restaurants.forEach((restaurant, index) => {

            if (box) {

                const card = document.createElement("div");
                card.className = "card";

                const title = document.createElement("h3");
                title.textContent =
                    "🍴 " + restaurant.name;

                const location = document.createElement("p");
                location.textContent =
                    "📍 " + restaurant.location;

                const menuTitle =
                    document.createElement("strong");

                menuTitle.textContent = "Menu";

                const menu =
                    document.createElement("ul");

                restaurant.menu.forEach(item => {

                    const li =
                        document.createElement("li");

                    li.textContent =
                        item.name +
                        " - ₹" +
                        item.price;

                    menu.appendChild(li);
                });

                card.appendChild(title);
                card.appendChild(location);
                card.appendChild(menuTitle);
                card.appendChild(menu);

                box.appendChild(card);
            }

            if (select) {

                const option =
                    document.createElement("option");

                option.value = index;
                option.textContent =
                    restaurant.name;

                select.appendChild(option);
            }
        });

    } catch (error) {

        console.error("Restaurant error:", error);

        if (box) {
            box.innerHTML =
                "<p>Unable to load restaurants.</p>";
        }
    }
}


const restaurantSelect =
    document.getElementById("restaurant");

if (restaurantSelect) {

    restaurantSelect.addEventListener(
        "change",
        function () {

            const itemSelect =
                document.getElementById("item");

            if (!itemSelect) return;

            itemSelect.innerHTML =
                '<option value="">Choose food item</option>';

            const restaurant =
                restaurants[this.value];

            if (!restaurant) return;

            restaurant.menu.forEach(item => {

                const option =
                    document.createElement("option");

                option.value = item.name;

                option.textContent =
                    item.name +
                    " - ₹" +
                    item.price;

                itemSelect.appendChild(option);
            });
        }
    );
}


const orderForm =
    document.getElementById("orderForm");

if (orderForm) {

    orderForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const restaurantSelect =
                document.getElementById("restaurant");

            const itemSelect =
                document.getElementById("item");

            const message =
                document.getElementById("message");

            const restaurant =
                restaurants[
                    restaurantSelect.value
                ];

            const foodName =
                itemSelect.value;

            if (!restaurant || !foodName) {

                if (message) {
                    message.textContent =
                        "Please choose a restaurant and food item.";
                }

                return;
            }

            const food =
                restaurant.menu.find(
                    item => item.name === foodName
                );

            const data = {

                customer:
                    document.getElementById("customer").value.trim(),

                phone:
                    document.getElementById("phone").value.trim(),

                address:
                    document.getElementById("address").value.trim(),

                restaurant_id:
                    restaurant.id,

                items: [
                    {
                        name: food.name,
                        price: food.price,
                        quantity: 1
                    }
                ],

                payment_method: "COD"
            };

            try {

                const response =
                    await fetch(
                        "/api/order",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(data)
                        }
                    );

                const result =
                    await response.json();

                if (!response.ok) {

                    throw new Error(
                        result.error ||
                        "Order failed"
                    );
                }

                if (message) {

                    message.textContent =
                        "✅ Order placed successfully! Order #" +
                        result.order_id;
                }

                orderForm.reset();

                itemSelect.innerHTML =
                    '<option value="">Choose food item</option>';

            } catch (error) {

                console.error(
                    "Order error:",
                    error
                );

                if (message) {

                    message.textContent =
                        "❌ Order failed: " +
                        error.message;
                }
            }
        }
    );
}


loadRestaurants();
