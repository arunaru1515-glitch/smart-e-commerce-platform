import { useAuth0 } from "@auth0/auth0-react";
import { useState, useEffect } from "react";
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

  // =========================================================
  // Normal Auth0 Login
  // =========================================================

  const handleLogin = async () => {
    await loginWithRedirect({
      authorizationParams: {
        audience: "https://smart-ecommerce-api",
        scope: "openid profile email",
      },
    });
  };

  // =========================================================
  // Google Login
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
  // Facebook Login
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
  // Logout
  // =========================================================

  const handleLogout = () => {
    localStorage.removeItem("backendToken");

    setBackendToken(null);
    setProducts([]);

    logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  };

  // =========================================================
  // Authenticate Auth0 User with FastAPI
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

      alert(
        "Could not connect to backend"
      );

      return null;
    }
  };

  // =========================================================
  // Authenticate Button
  // =========================================================

  const handleBackendLogin = async () => {
    const token =
      await authenticateWithBackend();

    if (token) {
      alert(
        "Successfully authenticated with FastAPI!"
      );

      await fetchProducts(token);
    }
  };

  // =========================================================
  // Fetch Products
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
  // Automatically Load Products
  // =========================================================

  useEffect(() => {
    if (backendToken) {
      fetchProducts(backendToken);
    }
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

      // -----------------------------------------------------
      // STEP 1:
      // Get the currently logged-in user
      // -----------------------------------------------------

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

      // This is the REAL logged-in user's ID
      const userId = userData.user_id;

      console.log(
        "Adding product for User ID:",
        userId
      );

      // -----------------------------------------------------
      // STEP 2:
      // Add product to THAT user's cart
      // -----------------------------------------------------

      const response = await fetch(
        `http://127.0.0.1:8000/cart/?user_id=${userId}&product_id=${productId}&quantity=1`,
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
  // Loading
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

  if (!isAuthenticated) {
    return (
      <div className="auth-container">

        <div className="auth-card">

          <h1>
            Smart E-Commerce Platform
          </h1>

          <p className="subtitle">
            Authentication using Auth0
          </p>

          {/* Normal Login */}

          <button
            className="login-button"
            onClick={handleLogin}
          >
            Login with Auth0
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
            Header
        ================================================= */}

        <h1>
          Smart E-Commerce Platform
        </h1>

        <p className="subtitle">
          Welcome to your shopping dashboard
        </p>

        {/* =================================================
            User Profile
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
              "Not available"}
          </p>

          <p>
            <strong>Email:</strong>{" "}
            {user?.email ||
              "Not available"}
          </p>

          <p>
            <strong>Auth0 ID:</strong>{" "}
            {user?.sub ||
              "Not available"}
          </p>

        </div>

        {/* =================================================
            Backend Authentication
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
            View Cart
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
            Logout
        ================================================= */}

        <button
          className="logout-button"
          onClick={handleLogout}
        >
          Logout
        </button>

        {/* =================================================
            Products
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
                    {product.stock}
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