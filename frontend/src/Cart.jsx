import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";

import { loadStripe } from "@stripe/stripe-js";


// =========================================================
// STRIPE SETUP
// =========================================================

const stripePromise = loadStripe(
  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY
);


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


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Failed to load cart"
        );
      }


      console.log(
        "Cart API Response:",
        data
      );


      setCart(data);

    }

    catch (error) {

      console.error(
        "Cart loading error:",
        error
      );

      alert(
        error.message ||
        "Could not load cart"
      );

    }

    finally {

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

    }

    catch (error) {

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


      if (!response.ok) {

        alert(
          data.detail ||
          "Failed to update quantity"
        );

        return;
      }


      await fetchCart();

    }

    catch (error) {

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
  // CHECKOUT + STRIPE PAYMENT
  // =========================================================

  const handleCheckout = async () => {

    try {

      if (!stripe || !elements) {

        alert(
          "Stripe is still loading. Please try again."
        );

        return;
      }


      if (!cart || !cart.items || cart.items.length === 0) {

        alert(
          "Your cart is empty."
        );

        return;
      }


      setPaymentLoading(true);


      // =====================================================
      // GET CURRENT USER
      // =====================================================

      const user = await getCurrentUser();

      const userId = user.user_id;


      // =====================================================
      // CREATE CHECKOUT + PAYMENT INTENT
      // =====================================================

      const response = await fetch(
        `http://127.0.0.1:8000/checkout/?user_id=${userId}`,
        {
          method: "POST",

          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );


      const data = await response.json();


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


      // =====================================================
      // GET CLIENT SECRET
      // =====================================================

      const clientSecret =
        data.client_secret;


      if (!clientSecret) {

        throw new Error(
          "Payment client secret was not received."
        );
      }


      // =====================================================
      // GET CARD ELEMENT
      // =====================================================

      const cardElement =
        elements.getElement(CardElement);


      if (!cardElement) {

        throw new Error(
          "Card details are required."
        );
      }


      // =====================================================
      // CONFIRM PAYMENT
      // =====================================================

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


      // =====================================================
      // PAYMENT SUCCESS
      // =====================================================

      if (
        result.paymentIntent &&
        result.paymentIntent.status === "succeeded"
      ) {

        alert(
          `Payment successful!\n\nOrder ID: ${data.order_id}`
        );

        console.log(
          "Payment successful:",
          result.paymentIntent
        );


        // Refresh cart

        await fetchCart();
      }

    }

    catch (error) {

      console.error(
        "Checkout / Payment Error:",
        error
      );

      alert(
        error.message ||
        "Payment failed"
      );

    }

    finally {

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


              {/* =================================================
                  CARD PAYMENT
              ================================================= */}

              <div
                style={{
                  marginTop: "25px",
                  padding: "20px",
                  border: "1px solid #ddd",
                  borderRadius: "8px",
                  background: "#fff"
                }}
              >

                <h3>
                  Payment Details
                </h3>


                <div
                  style={{
                    padding: "15px",
                    border: "1px solid #ccc",
                    borderRadius: "6px",
                    marginTop: "15px"
                  }}
                >

                  <CardElement
                    options={{
                      style: {
                        base: {
                          fontSize: "16px",
                          color: "#32325d",
                          "::placeholder": {
                            color: "#aab7c4",
                          },
                        },

                        invalid: {
                          color: "#fa755a",
                        },
                      },
                    }}
                  />

                </div>


                <button
                  className="checkout-button"
                  onClick={handleCheckout}
                  disabled={
                    paymentLoading ||
                    !stripe ||
                    !elements
                  }
                  style={{
                    marginTop: "20px",
                    width: "100%",
                    padding: "14px",
                    cursor:
                      paymentLoading
                        ? "not-allowed"
                        : "pointer"
                  }}
                >

                  {paymentLoading
                    ? "Processing Payment..."
                    : `Pay ₹${cart.grand_total}`
                  }

                </button>

              </div>

            </div>

          </div>
        )}

      </div>

    </div>
  );
}


// =========================================================
// CART COMPONENT WITH STRIPE ELEMENTS
// =========================================================

function Cart() {

  return (

    <Elements stripe={stripePromise}>

      <CartContent />

    </Elements>
  );
}


export default Cart;