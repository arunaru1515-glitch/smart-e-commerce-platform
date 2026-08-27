import { useAuth0 } from "@auth0/auth0-react";
import { useState, useEffect, useRef } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  useNavigate,
} from "react-router-dom";

import "./App.css";
import Cart from "./Cart";

// =========================================================
// HOME / PRODUCTS PAGE
// =========================================================

function Home() {
  const {
    isAuthenticated,
    isLoading,
    user,
    loginWithRedirect,
    logout,
    getAccessTokenSilently,
  } = useAuth0();

  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

  // FastAPI JWT
  const [backendToken, setBackendToken] = useState(
    localStorage.getItem("backendToken")
  );

  // Local FastAPI login
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [backendUser, setBackendUser] = useState(null);

  // =========================================================
  // NOTIFICATIONS - ASSESSMENT 6
  // =========================================================

  const [notifications, setNotifications] = useState([]);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [loadingNotifications, setLoadingNotifications] =
    useState(false);

  const notificationRef = useRef(null);
  const websocketRef = useRef(null);

  // =========================================================
  // NORMAL EMAIL / PASSWORD LOGIN
  // =========================================================

  const handleLogin = async () => {
    if (!loginEmail || !loginPassword) {
      alert("Please enter email and password");
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/auth/login?email=${encodeURIComponent(
          loginEmail
        )}&password=${encodeURIComponent(loginPassword)}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Invalid email or password");
        return;
      }

      // Save FastAPI JWT
      setBackendToken(data.access_token);
      localStorage.setItem("backendToken", data.access_token);

      // Get current FastAPI user
      const userResponse = await fetch(
        "http://127.0.0.1:8000/auth/me",
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${data.access_token}`,
            "Content-Type": "application/json",
          },
        }
      );

      const userData = await userResponse.json();

      if (userResponse.ok) {
        setBackendUser(userData);
      }

      setLoginEmail("");
      setLoginPassword("");

    } catch (error) {
      console.error("Login error:", error);
      alert("Could not connect to backend");
    }
  };

  // =========================================================
  // GOOGLE LOGIN
  // =========================================================

  const handleGoogleLogin = async () => {
    await loginWithRedirect({
      authorizationParams: {
        connection: "google-oauth2",
        audience: "https://smart-ecommerce-api",
        scope: "openid profile email",
      },
    });
  };

  // =========================================================
  // FACEBOOK LOGIN
  // =========================================================

  const handleFacebookLogin = async () => {
    await loginWithRedirect({
      authorizationParams: {
        connection: "facebook",
        audience: "https://smart-ecommerce-api",
        scope: "openid profile email",
      },
    });
  };

  // =========================================================
  // LOGOUT
  // =========================================================

  const handleLogout = () => {
    localStorage.removeItem("backendToken");

    setBackendToken(null);
    setBackendUser(null);
    setProducts([]);
    setNotifications([]);

    // Only perform Auth0 logout when an Auth0 session exists.
    if (isAuthenticated) {
      logout({
        logoutParams: {
          returnTo: window.location.origin,
        },
      });
    }
  };

  // =========================================================
  // AUTHENTICATE AUTH0 USER WITH FASTAPI
  // =========================================================

  const authenticateWithBackend = async () => {
    try {
      const auth0Token = await getAccessTokenSilently({
        authorizationParams: {
          audience: "https://smart-ecommerce-api",
          scope: "openid profile email",
        },
      });

      console.log("Auth0 Access Token received");

      const response = await fetch(
        "http://127.0.0.1:8000/auth/auth0",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${auth0Token}`,
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      console.log("FastAPI Auth0 Response:", data);

      if (!response.ok) {
        alert(
          data.detail ||
            "Backend authentication failed"
        );

        return null;
      }

      // Save FastAPI JWT in React state
      setBackendToken(data.access_token);

      // Save FastAPI JWT in localStorage
      localStorage.setItem(
        "backendToken",
        data.access_token
      );

      console.log("FastAPI JWT received");

      return data.access_token;
    } catch (error) {
      console.error(
        "Backend authentication error:",
        error
      );

      alert("Could not connect to backend");

      return null;
    }
  };

  // =========================================================
  // AUTHENTICATE BUTTON
  // =========================================================

  const handleBackendLogin = async () => {
    const token =
      await authenticateWithBackend();

    if (token) {
      alert(
        "Successfully authenticated with FastAPI!"
      );

      await fetchProducts(token);
      await fetchNotifications(token);
    }
  };

  // =========================================================
  // FETCH PRODUCTS
  // =========================================================

  const fetchProducts = async (token) => {
    try {
      setLoadingProducts(true);

      if (!token) {
        console.error(
          "No FastAPI token available"
        );

        return;
      }

      const response = await fetch(
        "http://127.0.0.1:8000/products/",
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      console.log(
        "Products API Response:",
        data
      );

      if (!response.ok) {
        console.error(
          "Product fetch failed:",
          data
        );

        return;
      }

      setProducts(data);
    } catch (error) {
      console.error(
        "Error fetching products:",
        error
      );
    } finally {
      setLoadingProducts(false);
    }
  };

  // =========================================================
  // FETCH NOTIFICATIONS
  // =========================================================

  const fetchNotifications = async (
    token = backendToken
  ) => {
    try {
      if (!token) {
        setNotifications([]);
        return;
      }

      setLoadingNotifications(true);

      const response = await fetch(
        "http://127.0.0.1:8000/notifications/",
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      console.log(
        "Notifications API Response:",
        data
      );

      if (!response.ok) {
        console.error(
          "Notification fetch failed:",
          data
        );

        setNotifications([]);
        return;
      }

      // Supports both:
      // [...]
      // { notifications: [...] }

      const notificationList =
        Array.isArray(data)
          ? data
          : Array.isArray(data.notifications)
          ? data.notifications
          : [];

      setNotifications(notificationList);
    } catch (error) {
      console.error(
        "Notification loading error:",
        error
      );

      setNotifications([]);
    } finally {
      setLoadingNotifications(false);
    }
  };

  // =========================================================
  // MARK NOTIFICATION AS READ
  // =========================================================

  const markNotificationAsRead = async (
    notificationId
  ) => {
    try {
      if (!backendToken || !notificationId) {
        return;
      }

      const response = await fetch(
        `http://127.0.0.1:8000/notifications/read?notification_id=${notificationId}`,
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
        "Mark Notification Read Response:",
        data
      );

      if (!response.ok) {
        console.error(
          "Failed to mark notification as read:",
          data
        );

        return;
      }

      // Update notification immediately in UI
      setNotifications((previous) =>
        previous.map((notification) => {
          const currentId =
            notification.notification_id ??
            notification.id;

          if (
            String(currentId) ===
            String(notificationId)
          ) {
            return {
              ...notification,
              is_read: true,
              read: true,
              status: "read",
            };
          }

          return notification;
        })
      );
    } catch (error) {
      console.error(
        "Mark notification read error:",
        error
      );
    }
  };

  // =========================================================
  // NOTIFICATION CLICK
  // =========================================================

  const handleNotificationClick = async (
    notification
  ) => {
    const notificationId =
      notification.notification_id ??
      notification.id;

    const alreadyRead =
      notification.is_read === true ||
      notification.read === true ||
      notification.status === "read";

    if (
      !alreadyRead &&
      notificationId
    ) {
      await markNotificationAsRead(
        notificationId
      );
    }
  };

  // =========================================================
  // AUTOMATICALLY LOAD PRODUCTS + NOTIFICATIONS
  // =========================================================

  useEffect(() => {
    if (backendToken) {
      fetchProducts(backendToken);
      fetchNotifications(backendToken);
    }
  }, [backendToken]);
  

  // =========================================================
// WEBSOCKET - REAL-TIME NOTIFICATIONS
// =========================================================

useEffect(() => {
  if (!backendToken) return;

  const ws = new WebSocket(
    `ws://127.0.0.1:8000/ws/${backendUser?.user_id || backendUser?.id}`
  );

  websocketRef.current = ws;

  ws.onopen = () => {
    console.log("WebSocket connected");
  };

  ws.onmessage = (event) => {
    try {
      const notification = JSON.parse(event.data);

      setNotifications((prev) => [
        notification,
        ...prev
      ]);
    } catch (error) {
      console.error(
        "Notification parsing error:",
        error
      );
    }
  };

  ws.onclose = () => {
    console.log("WebSocket disconnected");
  };

  ws.onerror = (error) => {
    console.error(
      "WebSocket error:",
      error
    );
  };

  return () => {
    ws.close();
  };
}, [backendToken]);

  // =========================================================
  // ADD PRODUCT TO CART
  // =========================================================

  const addToCart = async (productId) => {
    try {
      if (!backendToken) {
        alert(
          "Please authenticate with FastAPI first"
        );

        return;
      }

      // =====================================================
      // STEP 1: GET CURRENT USER
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

      const userData =
        await userResponse.json();

      console.log(
        "Current User:",
        userData
      );

      if (!userResponse.ok) {
        alert(
          userData.detail ||
            "Unable to get current user"
        );

        return;
      }

      // =====================================================
      // STEP 2: ADD PRODUCT TO CART
      // Backend endpoint:
      // POST /cart/add
      // =====================================================

      const response = await fetch(
        `http://127.0.0.1:8000/cart/add?user_id=${userData.user_id}&product_id=${productId}&quantity=1`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${backendToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      const data =
        await response.json();

      console.log(
        "Add to Cart Response:",
        data
      );

      if (!response.ok) {
        alert(
          data.detail ||
            "Failed to add product to cart"
        );

        return;
      }

      alert(
        "Product added to cart successfully!"
      );
    } catch (error) {
      console.error(
        "Add to cart error:",
        error
      );

      alert(
        "Could not connect to backend"
      );
    }
  };

  // =========================================================
  // NOTIFICATION HELPERS
  // =========================================================

  const getNotificationId = (
    notification
  ) => {
    return (
      notification.notification_id ??
      notification.id
    );
  };

  const getNotificationTitle = (
    notification
  ) => {
    return (
      notification.title ||
      notification.subject ||
      "Notification"
    );
  };

  const getNotificationMessage = (
    notification
  ) => {
    return (
      notification.message ||
      notification.content ||
      notification.description ||
      "You have a new notification."
    );
  };

  const isNotificationRead = (
    notification
  ) => {
    return (
      notification.is_read === true ||
      notification.read === true ||
      notification.status === "read"
    );
  };

  const unreadCount =
    notifications.filter(
      (notification) =>
        !isNotificationRead(notification)
    ).length;

  // =========================================================
  // LOADING
  // =========================================================

  if (isLoading) {
    return (
      <div className="auth-container">
        <h2>Loading...</h2>
      </div>
    );
  }

  // =========================================================
  // LOGIN PAGE
  // =========================================================

  if (!isAuthenticated && !backendToken) {
    return (
      <div className="auth-container">

        <div className="auth-card">

          <h1>
            Smart E-Commerce Platform
          </h1>

          <p className="subtitle">
            Login with your account
          </p>

          {/* Normal Email / Password Login */}

          <input
            type="email"
            placeholder="Email"
            value={loginEmail}
            onChange={(e) => setLoginEmail(e.target.value)}
          />

          <input
            type="password"
            placeholder="Password"
            value={loginPassword}
            onChange={(e) => setLoginPassword(e.target.value)}
          />

          <button
            className="login-button"
            onClick={handleLogin}
          >
            Login
          </button>

          {/* Google Login */}

          <button
            className="google-button"
            onClick={handleGoogleLogin}
          >
            Continue with Google
          </button>

          {/* Facebook Login */}

          <button
            className="facebook-button"
            onClick={handleFacebookLogin}
          >
            Continue with Facebook
          </button>

        </div>

      </div>
    );
  }

  // =========================================================
  // MAIN PRODUCTS PAGE
  // =========================================================

  return (
    <div className="auth-container">

      <div className="auth-card">

        {/* =================================================
            HEADER
        ================================================= */}

        <h1>
          Smart E-Commerce Platform
        </h1>

        <p className="subtitle">
          Welcome to your shopping dashboard
        </p>

        {/* =================================================
            NOTIFICATIONS - ASSESSMENT 6
        ================================================= */}

        {backendToken && (
          <div
            className="notification-wrapper"
            ref={notificationRef}
          >

            <button
              type="button"
              className="notification-button"
              onClick={() => {
                setNotificationOpen(
                  (previous) => !previous
                );

                if (!notificationOpen) {
                  fetchNotifications(
                    backendToken
                  );
                }
              }}
            >
              <span className="notification-icon">
                🔔
              </span>

              {unreadCount > 0 && (
                <span className="notification-badge">
                  {unreadCount > 99
                    ? "99+"
                    : unreadCount}
                </span>
              )}
            </button>

            {notificationOpen && (
              <div className="notification-panel">

                <div className="notification-panel-header">

                  <div>
                    <h3>
                      Notifications
                    </h3>

                    <span>
                      {unreadCount > 0
                        ? `${unreadCount} unread`
                        : "No unread notifications"}
                    </span>
                  </div>

                  <button
                    type="button"
                    className="notification-refresh"
                    onClick={() =>
                      fetchNotifications(
                        backendToken
                      )
                    }
                  >
                    ↻
                  </button>

                </div>

                <div className="notification-list">

                  {loadingNotifications ? (

                    <div className="notification-empty">
                      Loading notifications...
                    </div>

                  ) : notifications.length === 0 ? (

                    <div className="notification-empty">
                      No notifications
                    </div>

                  ) : (

                    notifications.map(
                      (notification) => {

                        const notificationId =
                          getNotificationId(
                            notification
                          );

                        const read =
                          isNotificationRead(
                            notification
                          );

                        return (
                          <button
                            type="button"
                            key={
                              notificationId
                            }
                            className={`notification-item ${
                              read
                                ? "read"
                                : "unread"
                            }`}
                            onClick={() =>
                              handleNotificationClick(
                                notification
                              )
                            }
                          >

                            <span
                              className={`notification-status-dot ${
                                read
                                  ? "read"
                                  : ""
                              }`}
                            />

                            <span className="notification-item-content">

                              <span className="notification-title">
                                {getNotificationTitle(
                                  notification
                                )}
                              </span>

                              <span className="notification-message">
                                {getNotificationMessage(
                                  notification
                                )}
                              </span>

                              {notification.created_at && (
                                <span className="notification-time">
                                  {new Date(
                                    notification.created_at
                                  ).toLocaleString()}
                                </span>
                              )}

                            </span>

                            {!read && (
                              <span className="notification-new">
                                New
                              </span>
                            )}

                          </button>
                        );
                      }
                    )

                  )}

                </div>

              </div>
            )}

          </div>
        )}

        {/* =================================================
            USER PROFILE
        ================================================= */}

        <div className="profile">

          <h2>
            Welcome!
          </h2>

          {user?.picture && (
            <img
              src={user.picture}
              alt="Profile"
              className="profile-image"
            />
          )}

          <p>
            <strong>Name:</strong>{" "}
            {user?.name ||
              backendUser?.name ||
              "Not available"}
          </p>

          <p>
            <strong>Email:</strong>{" "}
            {user?.email ||
              backendUser?.email ||
              "Not available"}
          </p>

          <p>
            <strong>Auth0 ID:</strong>{" "}
            {user?.sub ||
              "Not applicable for email/password login"}
          </p>

        </div>

        {/* =================================================
            BACKEND AUTHENTICATION
        ================================================= */}

        {!backendToken && (
          <button
            className="backend-button"
            onClick={handleBackendLogin}
          >
            Authenticate with FastAPI
          </button>
        )}

        {/* =================================================
            VIEW CART
        ================================================= */}

        {backendToken && (
          <button
            className="backend-button"
            onClick={() =>
              navigate("/cart")
            }
          >
            🛒 View Cart
          </button>
        )}

        {/* =================================================
            LOGOUT
        ================================================= */}

        <button
          className="logout-button"
          onClick={handleLogout}
        >
          Logout
        </button>

        {/* =================================================
            PRODUCTS
        ================================================= */}

        <div className="products-section">

          <h2>
            Products
          </h2>

          {!backendToken ? (

            <p>
              Authenticate with FastAPI
              to view products.
            </p>

          ) : loadingProducts ? (

            <p>
              Loading products...
            </p>

          ) : products.length === 0 ? (

            <p>
              No products found.
            </p>

          ) : (

            <div className="products-grid">

              {products.map((product) => (

                <div
                  className="product-card"
                  key={product.id}
                >

                  <h3>
                    {product.name}
                  </h3>

                  <p>
                    {product.description}
                  </p>

                  <p>
                    <strong>
                      Price: ₹
                      {product.price}
                    </strong>
                  </p>

                  <p>
                    Stock:{" "}
                    {product.stock_quantity}
                  </p>

                  <button
                    onClick={() =>
                      addToCart(
                        product.id
                      )
                    }
                  >
                    Add to Cart
                  </button>

                </div>

              ))}

            </div>

          )}

        </div>

      </div>

    </div>
  );
}

// =========================================================
// APPLICATION ROUTER
// =========================================================

function App() {
  return (
    <BrowserRouter>

      <Routes>

        {/* Home / Products */}

        <Route
          path="/"
          element={<Home />}
        />

        {/* Separate Cart Page */}

        <Route
          path="/cart"
          element={<Cart />}
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;