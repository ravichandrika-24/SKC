let restaurants = [];

async function loadRestaurants() {
    try {
        const response = await fetch("/api/restaurants");
        restaurants = await response.json();

        const box = document.getElementById("restaurants");
        const restaurantSelect = document.getElementById("restaurant");

        if (box) {
            box.innerHTML = "";
        }

        if (restaurantSelect) {
            restaurantSelect.innerHTML =
                '<option value="">Choose restaurant</option>';
        }

        restaurants.forEach((restaurant, index) => {

            if (box) {
                const card = document.createElement("div");

                card.innerHTML = `
                    <h3>🍴 ${restaurant.name}</h3>
                    <p>📍 ${restaurant.location}</p>
                    <h4>Menu</h4>
                    <ul>
                        ${restaurant.menu.map(item => `
                            <li>
                                ${item.name} - ₹${item.price}
                            </li>
                        `).join("")}
                    </ul>
                `;

                box.appendChild(card);
            }

            if (restaurantSelect) {
                const option =
                    document.createElement("option");

                option.value = index;
                option.textContent =
                    restaurant.name;

                restaurantSelect.appendChild(option);
            }
        });

    } catch (error) {
        console.error(error);

        const box =
            document.getElementById("restaurants");

        if (box) {
            box.innerHTML =
                "<p>Unable to load restaurants.</p>";
        }
    }
}


document.addEventListener("DOMContentLoaded", () => {

    const restaurantSelect =
        document.getElementById("restaurant");

    const itemSelect =
        document.getElementById("item");

    const orderForm =
        document.getElementById("orderForm");


    if (restaurantSelect) {

        restaurantSelect.addEventListener(
            "change",
            () => {

                if (!itemSelect) return;

                itemSelect.innerHTML =
                    '<option value="">Choose food item</option>';

                const restaurant =
                    restaurants[
                        restaurantSelect.value
                    ];

                if (!restaurant) return;

                restaurant.menu.forEach(item => {

                    const option =
                        document.createElement("option");

                    option.value = item.name;

                    option.textContent =
                        `${item.name} - ₹${item.price}`;

                    itemSelect.appendChild(option);
                });
            }
        );
    }


    if (orderForm) {

        orderForm.addEventListener(
            "submit",
            async event => {

                event.preventDefault();

                const restaurant =
                    restaurants[
                        restaurantSelect.value
                    ];

                const food =
                    restaurant?.menu.find(
                        item =>
                            item.name ===
                            itemSelect.value
                    );

                const message =
                    document.getElementById("message");


                if (!restaurant || !food) {

                    if (message) {
                        message.textContent =
                            "Please choose restaurant and food.";
                    }

                    return;
                }


                const data = {
                    customer:
                        document.getElementById("customer")?.value || "",

                    phone:
                        document.getElementById("phone")?.value || "",

                    address:
                        document.getElementById("address")?.value || "",

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
                            "✅ Order placed! Order #" +
                            result.order_id;
                    }


                    orderForm.reset();

                    itemSelect.innerHTML =
                        '<option value="">Choose food item</option>';


                } catch (error) {

                    console.error(error);

                    if (message) {
                        message.textContent =
                            "❌ " + error.message;
                    }
                }
            }
        );
    }

});


loadRestaurants();
