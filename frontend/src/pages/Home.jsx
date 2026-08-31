import React from "react";

import Header from "../components/Header";
import ProductList from "../components/ProductList";
import UserProfile from "../components/UserProfile";


function Home({
    user,
    backendUser,
    backendToken,
    products,
    loadingProducts,
    addToCart,
    onBackendLogin,
    onViewCart,
    onLogout,
}) {
    return (
        <div className="home-page">


            {/* =================================================
                HEADER
            ================================================= */}

            <Header
                userId={
                    backendUser?.user_id ||
                    backendUser?.id
                }

                backendToken={
                    backendToken
                }

                onBackendLogin={
                    onBackendLogin
                }

                onViewCart={
                    onViewCart
                }

                onLogout={
                    onLogout
                }
            />


            {/* =================================================
                MAIN CONTENT
            ================================================= */}

            <main className="home-content">


                {/* =================================================
                    WELCOME SECTION
                ================================================= */}

                <section className="welcome-section">

                    <h1>
                        Welcome to Smart E-Commerce
                    </h1>

                    <p>
                        Browse products, manage your cart,
                        and track your orders easily.
                    </p>

                </section>


                {/* =================================================
                    USER PROFILE
                ================================================= */}

                <section className="profile-section">

                    <UserProfile
                        user={user}
                        backendUser={backendUser}
                    />

                </section>


                {/* =================================================
                    FASTAPI AUTHENTICATION
                ================================================= */}

                {!backendToken && (

                    <section className="backend-auth-section">

                        <button
                            type="button"
                            className="backend-button"
                            onClick={
                                onBackendLogin
                            }
                        >
                            Authenticate with FastAPI
                        </button>

                    </section>

                )}


                {/* =================================================
                    PRODUCTS
                ================================================= */}

                <section className="products-section">


                    <div className="products-heading">

                        <div>

                            <span className="section-label">
                                SHOPPING
                            </span>

                            <h2>
                                Products
                            </h2>

                            <p>
                                Discover our available products
                            </p>

                        </div>

                    </div>


                    <ProductList
                        products={
                            products
                        }

                        loadingProducts={
                            loadingProducts
                        }

                        backendToken={
                            backendToken
                        }

                        addToCart={
                            addToCart
                        }
                    />

                </section>


            </main>

        </div>
    );
}


export default Home;