import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";

import { loadStripe } from "@stripe/stripe-js";

import "./Cart.css";

// =========================================================
// API
// =========================================================

const API_URL = "http://127.0.0.1:8000";

// =========================================================
// STRIPE
// =========================================================

const stripePromise = loadStripe(
  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY
);

// =========================================================
// IMAGE HELPER
// =========================================================

const getProductImage = (item) => {
  const imageName =
    item?.images ||
    item?.image ||
    item?.product_image ||
    "";

  if (!imageName) {
    return "/images/smartphone_img.jpg";
  }

  if (imageName.startsWith("http")) {
    return imageName;
  }

  return `/images/${imageName
    .replace(/^\/images\//, "")
    .trim()}`;
};

// =========================================================
// CART CONTENT
// =========================================================

function CartContent() {
  const navigate = useNavigate();

  const stripe = useStripe();
  const elements = useElements();

  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paymentLoading, setPaymentLoading] = useState(false);

  const [cardComplete, setCardComplete] = useState(false);
  const [cardError, setCardError] = useState("");

  // =========================================================
  // GET TOKEN
  // =========================================================

  const getBackendToken = () => {
    return localStorage.getItem("backendToken");
  };

  // =========================================================
  // CURRENT USER
  // =========================================================

  const getCurrentUser = async (token) => {
    const response = await fetch(
      `${API_URL}/auth/me`,
      {
        method: "GET",

        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
          "Unable to get current user"
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

      const token = getBackendToken();

      console.log(
        "Cart backend token:",
        token ? "Available" : "Missing"
      );

      if (!token) {
        setCart(null);
        return;
      }

      // -------------------------------------------------------
      // GET USER
      // -------------------------------------------------------

      const user = await getCurrentUser(token);

      console.log(
        "Cart Current User:",
        user
      );

      const userId =
        user.user_id ||
        user.id;

      if (!userId) {
        throw new Error(
          "User ID not found"
        );
      }

      // -------------------------------------------------------
      // GET CART
      // -------------------------------------------------------

      const response = await fetch(
        `${API_URL}/cart/?user_id=${userId}`,
        {
          method: "GET",

          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type":
              "application/json",
          },
        }
      );

      const data =
        await response.json();

      console.log(
        "Cart API Response:",
        data
      );

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to load cart"
        );
      }

      setCart(data);

    } catch (error) {
      console.error(
        "Cart loading error:",
        error
      );

      setCart(null);

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

  const removeFromCart = async (
    cartItemId
  ) => {
    try {
      const token =
        getBackendToken();

      if (!token) {
        alert(
          "Please authenticate with FastAPI first."
        );
        return;
      }

      const response = await fetch(
        `${API_URL}/cart/remove?cart_item_id=${cartItemId}`,
        {
          method: "DELETE",

          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type":
              "application/json",
          },
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to remove product"
        );
      }

      await fetchCart();

    } catch (error) {
      console.error(
        "Remove cart error:",
        error
      );

      alert(
        error.message ||
          "Could not remove product"
      );
    }
  };

  // =========================================================
  // UPDATE QUANTITY
  // =========================================================

  const updateQuantity = async (
    cartItemId,
    quantity
  ) => {
    try {
      if (quantity < 1) {
        return;
      }

      const token =
        getBackendToken();

      if (!token) {
        alert(
          "Please authenticate with FastAPI first."
        );
        return;
      }

      const response = await fetch(
        `${API_URL}/cart/update?cart_item_id=${cartItemId}&quantity=${quantity}`,
        {
          method: "PUT",

          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type":
              "application/json",
          },
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to update quantity"
        );
      }

      await fetchCart();

    } catch (error) {
      console.error(
        "Update quantity error:",
        error
      );

      alert(
        error.message ||
          "Could not update quantity"
      );
    }
  };

  // =========================================================
  // STRIPE CARD CHANGE
  // =========================================================

  const handleCardChange = (event) => {
    setCardComplete(
      event.complete
    );

    setCardError(
      event.error
        ? event.error.message
        : ""
    );
  };

  // =========================================================
  // CHECKOUT + PAYMENT
  // =========================================================

  const handleCheckout = async () => {
    try {
      const token =
        getBackendToken();

      if (!token) {
        alert(
          "Please authenticate with FastAPI first."
        );
        return;
      }

      if (!stripe || !elements) {
        alert(
          "Stripe is still loading. Please wait."
        );
        return;
      }

      if (
        !cart ||
        !cart.items ||
        cart.items.length === 0
      ) {
        alert(
          "Your cart is empty."
        );
        return;
      }

      const cardElement =
        elements.getElement(
          CardElement
        );

      if (!cardElement) {
        alert(
          "Please enter your card details."
        );
        return;
      }

      if (!cardComplete) {
        alert(
          "Please enter valid card number, expiry date and CVC."
        );
        return;
      }

      setPaymentLoading(true);

      // -------------------------------------------------------
      // CURRENT USER
      // -------------------------------------------------------

      const user =
        await getCurrentUser(token);

      const userId =
        user.user_id ||
        user.id;

      // -------------------------------------------------------
      // CREATE CHECKOUT
      // -------------------------------------------------------

      const response =
        await fetch(
          `${API_URL}/checkout/?user_id=${userId}`,
          {
            method: "POST",

            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type":
                "application/json",
            },
          }
        );

      const data =
        await response.json();

      console.log(
        "Checkout Response:",
        data
      );

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Checkout failed"
        );
      }

      // -------------------------------------------------------
      // CLIENT SECRET
      // -------------------------------------------------------

      const clientSecret =
        data.client_secret;

      if (!clientSecret) {
        throw new Error(
          "Payment client secret was not received."
        );
      }

      // -------------------------------------------------------
      // CONFIRM PAYMENT
      // -------------------------------------------------------

      const result =
        await stripe.confirmCardPayment(
          clientSecret,
          {
            payment_method: {
              card: cardElement,
            },
          }
        );

      if (result.error) {
        throw new Error(
          result.error.message
        );
      }

      // -------------------------------------------------------
      // SUCCESS
      // -------------------------------------------------------

      if (
        result.paymentIntent &&
        result.paymentIntent.status ===
          "succeeded"
      ) {
        const purchasedItems =
          cart.items
            .map(
              (item) =>
                `${item.product_name} × ${item.quantity}`
            )
            .join("\n");

        alert(
          `Payment Successful! 🎉\n\n` +
          `Order ID: ${data.order_id}\n\n` +
          `Products:\n${purchasedItems}\n\n` +
          `Total Amount: ₹${cart.grand_total}`
        );

        console.log(
          "Payment successful:",
          result.paymentIntent
        );

        await fetchCart();
      }

    } catch (error) {
      console.error(
        "Checkout / Payment Error:",
        error
      );

      alert(
        error.message ||
          "Payment failed"
      );
    } finally {
      setPaymentLoading(false);
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
      <div className="cart-page">
        <div className="cart-loading-card">
          <div className="loading-spinner">
            🛒
          </div>

          <h2>
            Loading Your Cart
          </h2>

          <p>
            Please wait...
          </p>
        </div>
      </div>
    );
  }

  // =========================================================
  // NOT AUTHENTICATED
  // =========================================================

  if (!getBackendToken()) {
    return (
      <div className="cart-page">
        <div className="cart-container">

          <button
            className="cart-back-button"
            onClick={() =>
              navigate("/")
            }
          >
            ← Back to Products
          </button>

          <div className="empty-cart-card">

            <div className="empty-cart-icon">
              🛒
            </div>

            <h1>
              Please Authenticate
            </h1>

            <p>
              Authenticate with FastAPI
              to access your shopping cart.
            </p>

            <button
              className="continue-shopping-button"
              onClick={() =>
                navigate("/")
              }
            >
              Continue Shopping
            </button>

          </div>

        </div>
      </div>
    );
  }

  // =========================================================
  // EMPTY CART
  // =========================================================

  if (
    !cart ||
    !cart.items ||
    cart.items.length === 0
  ) {
    return (
      <div className="cart-page">

        <div className="cart-container">

          <button
            className="cart-back-button"
            onClick={() =>
              navigate("/")
            }
          >
            ← Back to Products
          </button>

          <div className="empty-cart-card">

            <div className="empty-cart-icon">
              🛒
            </div>

            <h1>
              Your Cart is Empty
            </h1>

            <p>
              Add some products to your
              cart to continue shopping.
            </p>

            <button
              className="continue-shopping-button"
              onClick={() =>
                navigate("/")
              }
            >
              Continue Shopping
            </button>

          </div>

        </div>

      </div>
    );
  }

  // =========================================================
  // CART PAGE
  // =========================================================

  return (
    <div className="cart-page">

      <div className="cart-container">

        {/* ===================================================
            BACK BUTTON
        =================================================== */}

        <button
          className="cart-back-button"
          onClick={() =>
            navigate("/")
          }
        >
          ← Back to Products
        </button>

        {/* ===================================================
            TITLE
        =================================================== */}

        <div className="cart-heading">

          <span className="cart-heading-label">
            SHOPPING CART
          </span>

          <h1>
            Your Shopping Cart
          </h1>

          <p>
            Review your products and
            complete your payment securely.
          </p>

        </div>

        {/* ===================================================
            MAIN CART
        =================================================== */}

        <div className="cart-layout">

          {/* =================================================
              LEFT SIDE - ITEMS
          ================================================= */}

          <div className="cart-items-section">

            <div className="section-header">

              <div>
                <span className="section-label">
                  YOUR ITEMS
                </span>

                <h2>
                  Cart Items
                </h2>
              </div>

              <span className="items-count">
                {cart.items.length}{" "}
                {cart.items.length === 1
                  ? "Item"
                  : "Items"}
              </span>

            </div>

            {/* =================================================
                CART ITEMS
            ================================================= */}

            {cart.items.map(
              (item) => (
                <div
                  className="cart-item-card"
                  key={
                    item.cart_item_id
                  }
                >

                  {/* PRODUCT IMAGE */}

                  <div className="cart-image-wrapper">

                    <img
                      src={getProductImage(
                        item
                      )}
                      alt={
                        item.product_name ||
                        "Product"
                      }
                      className="cart-product-image"
                      onError={(e) => {
                        e.currentTarget.src =
                          "/images/smartphone_img.jpg";
                      }}
                    />

                  </div>

                  {/* PRODUCT DETAILS */}

                  <div className="cart-product-info">

                    <span className="product-category">
                      SMART E-COMMERCE
                    </span>

                    <h3>
                      {item.product_name}
                    </h3>

                    <p className="cart-product-description">
                      Premium quality product
                      from Smart E-Commerce.
                    </p>

                    <div className="price-row">

                      <span>
                        Unit Price
                      </span>

                      <strong>
                        ₹{item.price}
                      </strong>

                    </div>

                    <div className="item-total-row">

                      <span>
                        Item Total
                      </span>

                      <strong>
                        ₹{item.item_total}
                      </strong>

                    </div>

                  </div>

                  {/* ACTIONS */}

                  <div className="cart-item-actions">

                    <span className="quantity-label">
                      QUANTITY
                    </span>

                    <div className="quantity-controls">

                      <button
                        type="button"
                        className="quantity-button"
                        onClick={() =>
                          updateQuantity(
                            item.cart_item_id,
                            item.quantity - 1
                          )
                        }
                        disabled={
                          item.quantity <=
                          1
                        }
                      >
                        −
                      </button>

                      <span className="quantity-value">
                        {item.quantity}
                      </span>

                      <button
                        type="button"
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

                    <button
                      type="button"
                      className="remove-button"
                      onClick={() =>
                        removeFromCart(
                          item.cart_item_id
                        )
                      }
                    >
                      🗑 Remove
                    </button>

                  </div>

                </div>
              )
            )}

          </div>

          {/* =================================================
              RIGHT SIDE - SUMMARY
          ================================================= */}

          <div className="cart-summary">

            <span className="section-label">
              ORDER SUMMARY
            </span>

            <h2>
              Cart Summary
            </h2>

            {/* SUBTOTAL */}

            <div className="summary-row">

              <span>
                Subtotal
              </span>

              <strong>
                ₹{cart.cart_total}
              </strong>

            </div>

            {/* TAX */}

            <div className="summary-row">

              <span>
                Tax
              </span>

              <strong>
                ₹{cart.tax}
              </strong>

            </div>

            <div className="summary-divider"></div>

            {/* GRAND TOTAL */}

            <div className="grand-total">

              <span>
                Grand Total
              </span>

              <strong>
                ₹{cart.grand_total}
              </strong>

            </div>

            {/* =================================================
                PAYMENT
            ================================================= */}

            <div className="payment-card">

              <div className="payment-header">

                <div className="payment-icon">
                  💳
                </div>

                <div>
                  <h3>
                    Payment Details
                  </h3>

                  <p>
                    Secure card payment
                  </p>
                </div>

              </div>

              {/* CARD INPUT */}

              <div className="card-input-section">

                <label>
                  Card Details
                </label>

                <div
                  className={`stripe-card-input ${
                    cardError
                      ? "stripe-card-error"
                      : ""
                  } ${
                    cardComplete
                      ? "stripe-card-complete"
                      : ""
                  }`}
                >

                  <CardElement
                    onChange={
                      handleCardChange
                    }
                    options={{
                      hidePostalCode: true,

                      style: {
                        base: {
                          fontSize:
                            "16px",

                          fontFamily:
                            "Arial, sans-serif",

                          color:
                            "#172033",

                          lineHeight:
                            "24px",

                          fontSmoothing:
                            "antialiased",

                          "::placeholder":
                            {
                              color:
                                "#8a94a6",
                            },
                        },

                        invalid: {
                          color:
                            "#dc2626",
                          iconColor:
                            "#dc2626",
                        },

                        complete: {
                          color:
                            "#172033",
                        },
                      },
                    }}
                  />

                </div>

                {cardError && (
                  <p className="card-error">
                    ⚠ {cardError}
                  </p>
                )}

                {!cardError && (
                  <p className="card-help">
                    💳 Enter your card number,
                    expiry date and CVC
                  </p>
                )}

              </div>

              {/* PAYMENT BUTTON */}

              <button
                type="button"
                className="payment-button"
                onClick={
                  handleCheckout
                }
                disabled={
                  paymentLoading ||
                  !stripe ||
                  !elements
                }
              >

                {paymentLoading
                  ? "Processing Payment..."
                  : `🔒 Pay ₹${cart.grand_total}`}

              </button>

              {/* SECURITY */}

              <div className="payment-security">

                <span>
                  🔐
                </span>

                <p>
                  Your payment information
                  is securely processed by
                  Stripe.
                </p>

              </div>

            </div>

          </div>

        </div>

      </div>

    </div>
  );
}

// =========================================================
// STRIPE WRAPPER
// =========================================================

function Cart() {
  return (
    <Elements stripe={stripePromise}>

      <CartContent />

    </Elements>
  );
}

export default Cart;