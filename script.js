let restaurants = [];

async function loadRestaurants() {
    try {
        const response = await fetch("/api/restaurants");

        if (!response.ok) {
            throw new Error("Failed to load restaurants");
        }

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

            // Restaurant card
            if (box) {
                const card = document.createElement("div");
                card.className = "card";

                card.innerHTML = `
                    <h3>🍴 ${restaurant.name}</h3>
                    <p>📍 ${restaurant.location}</p>
                    <strong>Menu</strong>
                    <ul>
                        ${restaurant.menu.map(item => `
                            <li>${item.name} - ₹${item.price}</li>
                        `).join("")}
                    </ul>
                `;

                box.appendChild(card);
            }

            // Restaurant dropdown
            if (restaurantSelect) {
                const option = document.createElement("option");

                option.value = index;
                option.textContent = restaurant.name;

                restaurantSelect.appendChild(option);
            }
        });

    } catch (error) {
        console.error(error);

        const box = document.getElementById("restaurants");

        if (box) {
            box.innerHTML =
                "<p>❌ Could not load restaurants.</p>";
        }
    }
}


document.addEventListener("DOMContentLoaded", function () {

    const restaurantSelect =
        document.getElementById("restaurant");

    const itemSelect =
        document.getElementById("item");

    const orderForm =
        document.getElementById("orderForm");

    const message =
        document.getElementById("message");


    // Restaurant selection
    if (restaurantSelect) {

        restaurantSelect.addEventListener("change", function () {

            if (!itemSelect) return;

            itemSelect.innerHTML =
                '<option value="">Choose food item</option>';

            const restaurant =
                restaurants[restaurantSelect.value];

            if (!restaurant) return;

            restaurant.menu.forEach(function (item) {

                const option =
                    document.createElement("option");

                option.value = item.name;

                option.textContent =
                    item.name + " - ₹" + item.price;

                itemSelect.appendChild(option);
            });
        });
    }


    // Order submission
    if (orderForm) {

        orderForm.addEventListener("submit", async function (e) {

            e.preventDefault();

            const restaurant =
                restaurants[restaurantSelect.value];

            if (!restaurant) {
                if (message) {
                    message.textContent =
                        "❌ Please choose a restaurant.";
                }
                return;
            }

            const food =
                restaurant.menu.find(function (item) {
                    return item.name === itemSelect.value;
                });

            if (!food) {
                if (message) {
                    message.textContent =
                        "❌ Please choose a food item.";
                }
                return;
            }


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

                const response = await fetch("/api/order", {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(data)
                });


                const result =
                    await response.json();


                if (!response.ok) {
                    throw new Error(
                        result.error || "Order failed"
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

                console.error(error);

                if (message) {
                    message.textContent =
                        "❌ Order failed: " +
                        error.message;
                }
            }

        });
    }

});


// Start application
loadRestaurants();
