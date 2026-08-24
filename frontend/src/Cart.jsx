import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function Cart() {
  const navigate = useNavigate();

  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);

  const backendToken =
    localStorage.getItem("backendToken");

  // =========================================================
  // GET CURRENT USER
  // =========================================================

  const getCurrentUser = async () => {
    const response = await fetch(
      "http://127.0.0.1:8000/auth/me",
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${backendToken}`,
          "Content-Type": "application/json",
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Unable to get current user"
      );
    }

    return data;
  };

  // =========================================================
  // GET CART
  // =========================================================

  const fetchCart = async () => {
    try {
      setLoading(true);

      if (!backendToken) {
        alert("Please login first");
        navigate("/");
        return;
      }

      const user = await getCurrentUser();

      const userId = user.user_id;

      const response = await fetch(
        `http://127.0.0.1:8000/cart/?user_id=${userId}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      console.log("Cart API Response:", data);

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to load cart"
        );
      }

      setCart(data);

    } catch (error) {
      console.error(
        "Cart loading error:",
        error
      );

      alert(
        error.message ||
          "Could not load cart"
      );

    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // REMOVE FROM CART
  // =========================================================

  const removeFromCart = async (cartItemId) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/cart/remove?cart_item_id=${cartItemId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      console.log(
        "Remove Cart Response:",
        data
      );

      if (!response.ok) {
        alert(
          data.detail ||
            "Failed to remove product"
        );
        return;
      }

      alert(
        "Product removed from cart successfully!"
      );

      await fetchCart();

    } catch (error) {
      console.error(
        "Remove cart error:",
        error
      );

      alert(
        "Could not connect to backend"
      );
    }
  };

  // =========================================================
  // UPDATE CART QUANTITY
  // =========================================================

  const updateQuantity = async (
    cartItemId,
    quantity
  ) => {
    try {
      if (quantity <= 0) {
        return;
      }

      const response = await fetch(
        `http://127.0.0.1:8000/cart/update?cart_item_id=${cartItemId}&quantity=${quantity}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      console.log(
        "Update Cart Response:",
        data
      );

      if (!response.ok) {
        alert(
          data.detail ||
            "Failed to update quantity"
        );
        return;
      }

      await fetchCart();

    } catch (error) {
      console.error(
        "Update quantity error:",
        error
      );

      alert(
        "Could not connect to backend"
      );
    }
  };

  // =========================================================
  // LOAD CART
  // =========================================================

  useEffect(() => {
    fetchCart();
  }, []);

  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <div className="cart-loading">
        Loading cart...
      </div>
    );
  }

  // =========================================================
  // CART PAGE
  // =========================================================

  return (
    <div className="cart-page">

      <div className="cart-container">

        {/* =================================================
            BACK BUTTON
        ================================================= */}

        <button
          className="cart-back-button"
          onClick={() => navigate("/")}
        >
          ← Back to Products
        </button>

        {/* =================================================
            PAGE TITLE
        ================================================= */}

        <h1 className="cart-title">
          Shopping Cart
        </h1>

        {/* =================================================
            EMPTY CART
        ================================================= */}

        {(!cart ||
          !cart.items ||
          cart.items.length === 0) && (

          <div className="empty-cart">

            <h2>
              Your cart is empty
            </h2>

            <p>
              Add some products to your cart.
            </p>

            <button
              className="continue-shopping-button"
              onClick={() => navigate("/")}
            >
              Continue Shopping
            </button>

          </div>
        )}

        {/* =================================================
            CART ITEMS
        ================================================= */}

        {cart &&
          cart.items &&
          cart.items.length > 0 && (

          <div className="cart-items">

            {cart.items.map((item) => (

              <div
                className="cart-item"
                key={item.cart_item_id}
              >

                {/* =================================================
                    PRODUCT DETAILS
                ================================================= */}

                <div className="cart-product-details">

                  <h2 className="cart-product-name">
                    {item.product_name}
                  </h2>

                  <p>
                    Price:{" "}
                    <strong>
                      ₹{item.price}
                    </strong>
                  </p>

                  <p>
                    Quantity:{" "}
                    <strong>
                      {item.quantity}
                    </strong>
                  </p>

                  <p className="item-total">
                    Item Total: ₹
                    {item.item_total}
                  </p>

                </div>

                {/* =================================================
                    ACTIONS
                ================================================= */}

                <div className="cart-actions">

                  {/* Quantity Controls */}

                  <div className="quantity-controls">

                    <button
                      className="quantity-button"
                      onClick={() =>
                        updateQuantity(
                          item.cart_item_id,
                          item.quantity - 1
                        )
                      }
                      disabled={
                        item.quantity <= 1
                      }
                    >
                      −
                    </button>

                    <span className="quantity-value">
                      {item.quantity}
                    </span>

                    <button
                      className="quantity-button"
                      onClick={() =>
                        updateQuantity(
                          item.cart_item_id,
                          item.quantity + 1
                        )
                      }
                    >
                      +
                    </button>

                  </div>

                  {/* Remove */}

                  <button
                    className="remove-button"
                    onClick={() =>
                      removeFromCart(
                        item.cart_item_id
                      )
                    }
                  >
                    Remove
                  </button>

                </div>

              </div>

            ))}

            {/* =================================================
                CART SUMMARY
            ================================================= */}

            <div className="cart-summary">

              <h2>
                Cart Summary
              </h2>

              <div className="summary-row">
                <span>
                  Cart Total
                </span>

                <strong>
                  ₹{cart.cart_total}
                </strong>
              </div>

              <div className="summary-row">
                <span>
                  Tax
                </span>

                <strong>
                  ₹{cart.tax}
                </strong>
              </div>

              <hr className="summary-divider" />

              <div className="grand-total">

                <strong>
                  Grand Total
                </strong>

                <strong>
                  ₹{cart.grand_total}
                </strong>

              </div>

            </div>

          </div>
        )}

      </div>

    </div>
  );
}

export default Cart;