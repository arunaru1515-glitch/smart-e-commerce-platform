import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";

function Cart() {
  const navigate = useNavigate();

  const [cartItems, setCartItems] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Get FastAPI JWT
  const backendToken = localStorage.getItem("backendToken");

  // =========================================================
  // Load Cart + Products
  // =========================================================

  const loadCart = async () => {
    try {
      setLoading(true);

      if (!backendToken) {
        console.error("FastAPI token not found");
        setCartItems([]);
        return;
      }

      // =====================================================
      // 1. Get Current User
      // =====================================================

      const userResponse = await fetch(
        "http://127.0.0.1:8000/auth/me",
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      const userData = await userResponse.json();

      console.log("Current User Response:", userData);

      if (!userResponse.ok) {
        console.error("Unable to get current user:", userData);
        setCartItems([]);
        return;
      }

      const userId = userData.user_id;

      console.log("Current User ID:", userId);

      // =====================================================
      // 2. Get Cart for Current User
      // =====================================================

      const cartResponse = await fetch(
        `http://127.0.0.1:8000/cart/?user_id=${userId}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      const cartData = await cartResponse.json();

      console.log("Cart API Response:", cartData);

      if (!cartResponse.ok) {
        console.error("Cart loading failed:", cartData);
        setCartItems([]);
        return;
      }

      // =====================================================
      // 3. Get All Products
      // =====================================================

      const productsResponse = await fetch(
        "http://127.0.0.1:8000/products/",
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      const productsData = await productsResponse.json();

      console.log("Products API Response:", productsData);

      if (!productsResponse.ok) {
        console.error(
          "Products loading failed:",
          productsData
        );

        setProducts([]);
      } else {
        setProducts(productsData);
      }

      // =====================================================
      // 4. Store User-Specific Cart
      // =====================================================

      setCartItems(cartData);

    } catch (error) {
      console.error("Cart loading error:", error);
      setCartItems([]);
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // Load Cart when Page Opens
  // =========================================================

  useEffect(() => {
    loadCart();
  }, []);

  // =========================================================
  // Remove Product From Cart
  // =========================================================

  const removeFromCart = async (cartId) => {
    try {
      if (!backendToken) {
        alert("Authentication token not found");
        return;
      }

      const response = await fetch(
        `http://127.0.0.1:8000/cart/${cartId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      console.log("Remove Cart Response:", data);

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

      // Reload cart after removing
      await loadCart();

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
  // Back to Products
  // =========================================================

  const goBackToProducts = () => {
    navigate("/");
  };

  // =========================================================
  // Find Product Details
  // =========================================================

  const getProduct = (productId) => {
    return products.find(
      (product) => product.id === productId
    );
  };

  // =========================================================
  // Calculate Total
  // =========================================================

  const getCartTotal = () => {
    return cartItems.reduce(
      (total, item) => {
        const product = getProduct(item.product_id);

        if (!product) {
          return total;
        }

        return (
          total +
          Number(product.price) *
            Number(item.quantity)
        );
      },
      0
    );
  };

  // =========================================================
  // Loading Screen
  // =========================================================

  if (loading) {
    return (
      <div className="auth-container">

        <div className="auth-card">

          <h1>
            Shopping Cart
          </h1>

          <p>
            Loading your cart...
          </p>

        </div>

      </div>
    );
  }

  // =========================================================
  // Cart Page
  // =========================================================

  return (
    <div className="auth-container">

      <div className="auth-card">

        {/* Header */}

        <h1>
          🛒 Shopping Cart
        </h1>

        <p className="subtitle">
          Review your selected products
        </p>

        {/* Back to Products */}

        <button
          className="backend-button"
          onClick={goBackToProducts}
        >
          ← Back to Products
        </button>

        {/* =================================================
            Empty Cart
        ================================================= */}

        {cartItems.length === 0 ? (

          <div className="products-section">

            <h2>
              Your Cart is Empty
            </h2>

            <p>
              You haven't added any products yet.
            </p>

            <button
              className="backend-button"
              onClick={goBackToProducts}
            >
              Continue Shopping
            </button>

          </div>

        ) : (

          /* =================================================
             Cart Items
          ================================================= */

          <div className="products-section">

            <h2>
              Cart Items
            </h2>

            <div className="products-grid">

              {cartItems.map((item) => {

                const product = getProduct(
                  item.product_id
                );

                return (

                  <div
                    className="product-card"
                    key={item.id}
                  >

                    {product ? (

                      <>
                        <h3>
                          {product.name}
                        </h3>

                        <p>
                          {product.description}
                        </p>

                        <p>
                          <strong>
                            Price: ₹
                            {Number(
                              product.price
                            ).toLocaleString("en-IN")}
                          </strong>
                        </p>

                        <p>
                          Quantity:{" "}
                          {item.quantity}
                        </p>

                        <p>
                          <strong>
                            Item Total: ₹
                            {(
                              Number(
                                product.price
                              ) *
                              Number(
                                item.quantity
                              )
                            ).toLocaleString("en-IN")}
                          </strong>
                        </p>

                        <button
                          className="logout-button"
                          onClick={() =>
                            removeFromCart(
                              item.id
                            )
                          }
                        >
                          Remove
                        </button>
                      </>

                    ) : (

                      <>
                        <h3>
                          Product ID:{" "}
                          {item.product_id}
                        </h3>

                        <p>
                          Product details
                          unavailable.
                        </p>

                        <p>
                          Quantity:{" "}
                          {item.quantity}
                        </p>

                        <button
                          className="logout-button"
                          onClick={() =>
                            removeFromCart(
                              item.id
                            )
                          }
                        >
                          Remove
                        </button>
                      </>

                    )}

                  </div>

                );
              })}

            </div>

            {/* =================================================
                Cart Summary
            ================================================= */}

            <div className="cart-summary">

              <h2>
                Order Summary
              </h2>

              <p>
                Total Items:{" "}
                <strong>
                  {cartItems.reduce(
                    (total, item) =>
                      total +
                      Number(item.quantity),
                    0
                  )}
                </strong>
              </p>

              <h2>
                Grand Total: ₹
                {getCartTotal().toLocaleString(
                  "en-IN"
                )}
              </h2>

              <button
                className="backend-button"
                onClick={goBackToProducts}
              >
                Continue Shopping
              </button>

              <button
                className="google-button"
                onClick={() =>
                  alert(
                    "Checkout feature will be implemented next."
                  )
                }
              >
                Proceed to Checkout
              </button>

            </div>

          </div>

        )}

      </div>

    </div>
  );
}

export default Cart;