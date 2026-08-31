import { useAuth0 } from "@auth0/auth0-react";
import { useEffect, useState } from "react";

import {
    BrowserRouter,
    Routes,
    Route,
    useNavigate,
} from "react-router-dom";

import "./App.css";

import Home from "./pages/Home";
import CartPage from "./pages/CartPage";
import OrdersPage from "./pages/OrdersPage";


/* =========================================================
   API
   ========================================================= */

const API_URL = "http://127.0.0.1:8000";


/* =========================================================
   HOME CONTAINER
   ========================================================= */

function HomeContainer() {

    const {
        isAuthenticated,
        isLoading,
        user,
        loginWithRedirect,
        logout,
        getAccessTokenSilently,
    } = useAuth0();

    const navigate = useNavigate();


    /* =====================================================
       FASTAPI TOKEN
       ===================================================== */

    const [backendToken, setBackendToken] = useState(
        localStorage.getItem("backendToken")
    );


    /* =====================================================
       BACKEND USER
       ===================================================== */

    const [backendUser, setBackendUser] = useState(null);


    /* =====================================================
       LOGIN FORM
       ===================================================== */

    const [loginEmail, setLoginEmail] = useState("");
    const [loginPassword, setLoginPassword] = useState("");


    /* =====================================================
       PRODUCTS
       ===================================================== */

    const [products, setProducts] = useState([]);

    const [loadingProducts, setLoadingProducts] =
        useState(false);


    /* =====================================================
       GET BACKEND USER
       ===================================================== */

    const fetchBackendUser = async (token) => {

        try {

            if (!token) {
                return null;
            }


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

                console.error(
                    "Failed to get backend user:",
                    data
                );

                return null;
            }


            setBackendUser(data);

            return data;

        } catch (error) {

            console.error(
                "Backend user error:",
                error
            );

            return null;
        }
    };


    /* =====================================================
       EMAIL / PASSWORD LOGIN
       ===================================================== */

    const handleLogin = async () => {

        if (!loginEmail || !loginPassword) {

            alert(
                "Please enter email and password"
            );

            return;
        }


        try {

            const response = await fetch(
                `${API_URL}/auth/login?email=${encodeURIComponent(
                    loginEmail
                )}&password=${encodeURIComponent(
                    loginPassword
                )}`,
                {
                    method: "POST",
                }
            );


            const data = await response.json();


            if (!response.ok) {

                alert(
                    data.detail ||
                    "Invalid email or password"
                );

                return;
            }


            /* Save FastAPI JWT */

            setBackendToken(
                data.access_token
            );

            localStorage.setItem(
                "backendToken",
                data.access_token
            );


            /* Get backend user */

            await fetchBackendUser(
                data.access_token
            );


            /* Clear login fields */

            setLoginEmail("");
            setLoginPassword("");


        } catch (error) {

            console.error(
                "Login error:",
                error
            );

            alert(
                "Could not connect to backend"
            );
        }
    };


    /* =====================================================
       GOOGLE LOGIN
       ===================================================== */

    const handleGoogleLogin = async () => {

        try {

            await loginWithRedirect({

                authorizationParams: {

                    connection:
                        "google-oauth2",

                    audience:
                        "https://smart-ecommerce-api",

                    scope:
                        "openid profile email",
                },

            });

        } catch (error) {

            console.error(
                "Google login error:",
                error
            );
        }
    };


    /* =====================================================
       FACEBOOK LOGIN
       ===================================================== */

    const handleFacebookLogin = async () => {

        try {

            await loginWithRedirect({

                authorizationParams: {

                    connection:
                        "facebook",

                    audience:
                        "https://smart-ecommerce-api",

                    scope:
                        "openid profile email",
                },

            });

        } catch (error) {

            console.error(
                "Facebook login error:",
                error
            );
        }
    };


    /* =====================================================
       LOGOUT
       ===================================================== */

    const handleLogout = () => {

        localStorage.removeItem(
            "backendToken"
        );


        setBackendToken(null);

        setBackendUser(null);

        setProducts([]);


        /*
         * Only logout from Auth0 when
         * an Auth0 session exists.
         */

        if (isAuthenticated) {

            logout({

                logoutParams: {

                    returnTo:
                        window.location.origin,
                },

            });

        } else {

            navigate("/");
        }
    };


    /* =====================================================
       AUTH0 → FASTAPI
       ===================================================== */

    const authenticateWithBackend = async () => {

        try {

            /*
             * Get Auth0 access token
             */

            const auth0Token =
                await getAccessTokenSilently({

                    authorizationParams: {

                        audience:
                            "https://smart-ecommerce-api",

                        scope:
                            "openid profile email",
                    },

                });


            console.log(
                "Auth0 Access Token received"
            );


            /*
             * Send Auth0 token to FastAPI
             */

            const response = await fetch(
                `${API_URL}/auth/auth0`,
                {
                    method: "POST",

                    headers: {

                        Authorization:
                            `Bearer ${auth0Token}`,

                        "Content-Type":
                            "application/json",
                    },
                }
            );


            const data =
                await response.json();


            console.log(
                "FastAPI Auth0 Response:",
                data
            );


            if (!response.ok) {

                alert(
                    data.detail ||
                    "Backend authentication failed"
                );

                return null;
            }


            /*
             * Save FastAPI JWT
             */

            setBackendToken(
                data.access_token
            );


            localStorage.setItem(
                "backendToken",
                data.access_token
            );


            console.log(
                "FastAPI JWT received"
            );


            /*
             * Get backend user
             */

            await fetchBackendUser(
                data.access_token
            );


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


    /* =====================================================
       AUTHENTICATE BUTTON
       ===================================================== */

    const handleBackendLogin = async () => {

        try {

            /*
             * If Auth0 is not logged in,
             * start Auth0 login.
             */

            if (!isAuthenticated) {

                await loginWithRedirect({

                    authorizationParams: {

                        audience:
                            "https://smart-ecommerce-api",

                        scope:
                            "openid profile email",
                    },

                });

                return;
            }


            /*
             * Auth0 already logged in.
             * Authenticate with FastAPI.
             */

            const token =
                await authenticateWithBackend();


            if (token) {

                alert(
                    "Successfully authenticated with FastAPI!"
                );
            }


        } catch (error) {

            console.error(
                "Authentication error:",
                error
            );


            alert(
                "Authentication failed. Please try again."
            );
        }
    };


    /* =====================================================
       FETCH PRODUCTS
       ===================================================== */

    const fetchProducts = async (token) => {

        try {

            setLoadingProducts(true);


            if (!token) {

                console.error(
                    "No FastAPI token available"
                );

                setProducts([]);

                return;
            }


            const response = await fetch(
                `${API_URL}/products/`,
                {
                    method: "GET",

                    headers: {

                        Authorization:
                            `Bearer ${token}`,

                        "Content-Type":
                            "application/json",
                    },
                }
            );


            const data =
                await response.json();


            console.log(
                "Products API Response:",
                data
            );


            if (!response.ok) {

                console.error(
                    "Product fetch failed:",
                    data
                );

                setProducts([]);

                return;
            }


            /*
             * Backend normally returns:
             *
             * [
             *   {...},
             *   {...}
             * ]
             *
             * Also support:
             *
             * {
             *   products: [...]
             * }
             */

            const productList =
                Array.isArray(data)
                    ? data
                    : Array.isArray(data.products)
                        ? data.products
                        : [];


            console.log(
                "Products loaded:",
                productList
            );


            setProducts(
                productList
            );


        } catch (error) {

            console.error(
                "Error fetching products:",
                error
            );


            setProducts([]);

        } finally {

            setLoadingProducts(false);
        }
    };


    /* =====================================================
       AUTOMATICALLY LOAD PRODUCTS
       ===================================================== */

    useEffect(() => {

        if (backendToken) {

            fetchProducts(
                backendToken
            );
        }

    }, [backendToken]);


    /* =====================================================
       AUTOMATICALLY LOAD BACKEND USER
       ===================================================== */

    useEffect(() => {

        if (backendToken) {

            fetchBackendUser(
                backendToken
            );
        }

    }, [backendToken]);


    /* =====================================================
       ADD PRODUCT TO CART
       ===================================================== */

    const addToCart = async (productId) => {

        try {

            if (!backendToken) {

                alert(
                    "Please authenticate with FastAPI first"
                );

                return;
            }


            /* =================================================
               STEP 1
               GET CURRENT USER
               ================================================= */

            const userResponse =
                await fetch(
                    `${API_URL}/auth/me`,
                    {
                        method: "GET",

                        headers: {

                            Authorization:
                                `Bearer ${backendToken}`,

                            "Content-Type":
                                "application/json",
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


            /* =================================================
               STEP 2
               ADD PRODUCT TO CART
               ================================================= */

            const userId =
                userData.user_id ||
                userData.id;


            const response =
                await fetch(
                    `${API_URL}/cart/add?user_id=${userId}&product_id=${productId}&quantity=1`,
                    {
                        method: "POST",

                        headers: {

                            Authorization:
                                `Bearer ${backendToken}`,

                            "Content-Type":
                                "application/json",
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


    /* =====================================================
       AUTH0 LOADING
       ===================================================== */

    if (isLoading) {

        return (
            <div className="loading-page">

                <div className="loading-card">

                    <div className="loading-spinner"></div>

                    <h2>
                        Loading...
                    </h2>

                    <p>
                        Please wait
                    </p>

                </div>

            </div>
        );
    }


    /* =====================================================
       LOGIN PAGE
       ===================================================== */

    if (
        !isAuthenticated &&
        !backendToken
    ) {

        return (

            <div className="login-page">

                {/* =================================================
                    LEFT SIDE
                ================================================= */}

                <section className="login-brand">

                    <div className="brand-content">

                        <div className="brand-logo">
                            🛍️
                        </div>


                        <p className="brand-small-title">
                            SMART SHOPPING PLATFORM
                        </p>


                        <h1>
                            Smart
                            <br />

                            <span>
                                E-Commerce
                            </span>
                        </h1>


                        <p className="brand-description">
                            Everything you need for a smarter
                            and simpler online shopping experience.
                        </p>


                        <div className="brand-features">

                            <div className="feature-item">

                                <div className="feature-icon">
                                    ✓
                                </div>

                                <div>

                                    <h3>
                                        Secure Shopping
                                    </h3>

                                    <p>
                                        Safe authentication and
                                        protected payments.
                                    </p>

                                </div>

                            </div>


                            <div className="feature-item">

                                <div className="feature-icon">
                                    🚚
                                </div>

                                <div>

                                    <h3>
                                        Fast Delivery
                                    </h3>

                                    <p>
                                        Track your orders from
                                        checkout to delivery.
                                    </p>

                                </div>

                            </div>


                            <div className="feature-item">

                                <div className="feature-icon">
                                    ★
                                </div>

                                <div>

                                    <h3>
                                        Quality Products
                                    </h3>

                                    <p>
                                        Discover products in one
                                        convenient platform.
                                    </p>

                                </div>

                            </div>

                        </div>

                    </div>

                </section>


                {/* =================================================
                    RIGHT SIDE
                ================================================= */}

                <section className="login-section">

                    <div className="login-card">

                        <div className="mobile-brand-logo">
                            🛍️
                        </div>


                        <div className="login-header">

                            <h2>
                                Welcome back
                            </h2>

                            <p>
                                Sign in to continue to your account
                            </p>

                        </div>


                        {/* EMAIL */}

                        <div className="input-group">

                            <label>
                                Email address
                            </label>

                            <input
                                type="email"
                                placeholder="Enter your email"
                                value={loginEmail}
                                onChange={(event) =>
                                    setLoginEmail(
                                        event.target.value
                                    )
                                }
                            />

                        </div>


                        {/* PASSWORD */}

                        <div className="input-group">

                            <div className="label-row">

                                <label>
                                    Password
                                </label>

                                <button
                                    type="button"
                                    className="forgot-button"
                                    onClick={() =>
                                        alert(
                                            "Password reset is not configured yet."
                                        )
                                    }
                                >
                                    Forgot password?
                                </button>

                            </div>


                            <input
                                type="password"
                                placeholder="Enter your password"
                                value={loginPassword}
                                onChange={(event) =>
                                    setLoginPassword(
                                        event.target.value
                                    )
                                }
                            />

                        </div>


                        {/* REMEMBER */}

                        <label className="remember-row">

                            <input
                                type="checkbox"
                            />

                            <span>
                                Remember me
                            </span>

                        </label>


                        {/* SIGN IN */}

                        <button
                            type="button"
                            className="login-button"
                            onClick={handleLogin}
                        >
                            Sign In
                        </button>


                        {/* DIVIDER */}

                        <div className="login-divider">

                            <span>
                                OR CONTINUE WITH
                            </span>

                        </div>


                        {/* GOOGLE */}

                        <button
                            type="button"
                            className="social-button google-button"
                            onClick={handleGoogleLogin}
                        >

                            <span className="google-icon">
                                G
                            </span>

                            <span>
                                Continue with Google
                            </span>

                        </button>


                        {/* FACEBOOK */}

                        <button
                            type="button"
                            className="social-button facebook-button"
                            onClick={handleFacebookLogin}
                        >

                            <span className="facebook-icon">
                                f
                            </span>

                            <span>
                                Continue with Facebook
                            </span>

                        </button>


                        {/* SECURITY */}

                        <p className="login-security">
                            🔒 Your account is protected with
                            secure authentication
                        </p>

                    </div>

                </section>

            </div>
        );
    }


    /* =====================================================
       MAIN HOME
       ===================================================== */

    return (

        <Home

            user={user}

            backendUser={
                backendUser
            }

            backendToken={
                backendToken
            }

            products={
                products
            }

            loadingProducts={
                loadingProducts
            }

            addToCart={
                addToCart
            }

            onBackendLogin={
                handleBackendLogin
            }

            onViewCart={() =>
                navigate("/cart")
            }

            onLogout={
                handleLogout
            }

        />
    );
}


/* =========================================================
   APPLICATION ROUTER
   ========================================================= */

function App() {

    return (

        <BrowserRouter>

            <Routes>

                {/* =================================================
                    HOME
                ================================================= */}

                <Route
                    path="/"
                    element={
                        <HomeContainer />
                    }
                />


                {/* =================================================
                    CART
                ================================================= */}

                <Route
                    path="/cart"
                    element={
                        <CartPage />
                    }
                />


                {/* =================================================
                    ORDERS
                ================================================= */}

                <Route
                    path="/orders"
                    element={
                        <OrdersPage
                            token={
                                localStorage.getItem(
                                    "backendToken"
                                )
                            }
                        />
                    }
                />

            </Routes>

        </BrowserRouter>
    );
}


export default App;