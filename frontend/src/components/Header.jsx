import React from "react";
import "./Header.css";
import NotificationBell from "./NotificationBell";

function Header({
    userId,
    backendToken,
    onBackendLogin,
    onViewCart,
    onLogout,
}) {
    return (
        <header className="app-header">

            {/* =================================================
                BRAND
            ================================================= */}

            <div className="header-brand">

                <div className="header-logo">
                    🛍️
                </div>

                <div className="header-brand-text">

                    <h1>
                        Smart E-Commerce
                    </h1>

                    <span>
                        Smart Shopping Platform
                    </span>

                </div>

            </div>


            {/* =================================================
                ACTIONS
            ================================================= */}

            <nav className="header-actions">


                {/* HOME */}

                <button
                    type="button"
                    className="header-nav-button"
                    onClick={() => {
                        window.location.href = "/";
                    }}
                >
                    Home
                </button>


                {/* PRODUCTS */}

                {backendToken && (
                    <button
                        type="button"
                        className="header-nav-button"
                        onClick={() => {
                            window.location.href = "/";
                        }}
                    >
                        Products
                    </button>
                )}


                {/* CART */}

                {backendToken && (
                    <button
                        type="button"
                        className="header-nav-button cart-button"
                        onClick={onViewCart}
                    >
                        🛒 Cart
                    </button>
                )}


                {/* ORDERS */}

                {backendToken && (
                    <button
                        type="button"
                        className="header-nav-button"
                        onClick={() => {
                            window.location.href = "/orders";
                        }}
                    >
                        Orders
                    </button>
                )}


                {/* NOTIFICATIONS */}

                {backendToken && (
                    <div className="header-notification">

                        <NotificationBell
                            userId={userId}
                            token={backendToken}
                        />

                    </div>
                )}


                {/* AUTHENTICATE */}

                {!backendToken && (
                    <button
                        type="button"
                        className="header-auth-button"
                        onClick={onBackendLogin}
                    >
                        Authenticate
                    </button>
                )}


                {/* LOGOUT */}

                <button
                    type="button"
                    className="header-logout-button"
                    onClick={onLogout}
                >
                    Logout
                </button>


            </nav>

        </header>
    );
}

export default Header;