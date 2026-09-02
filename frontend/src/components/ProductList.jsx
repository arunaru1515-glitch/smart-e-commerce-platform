import React from "react";
import "./ProductList.css";

function ProductList({
    products,
    loadingProducts,
    backendToken,
    addToCart,
}) {

    // =========================================================
    // PRODUCT IMAGE
    // =========================================================

    const getProductImage = (product) => {
        if (!product.images) {
            return null;
        }

        // If backend already gives a full URL
        if (product.images.startsWith("http")) {
            return product.images;
        }

        // Load product images from Django media
        return `http://127.0.0.1:8001/media/${product.images}`;
    };


    // =========================================================
    // NOT AUTHENTICATED
    // =========================================================

    if (!backendToken) {
        return (
            <section className="products-section">

                <div className="products-header">
                    <div>
                        <span className="section-label">
                            SHOPPING
                        </span>

                        <h2>Our Products</h2>

                        <p>
                            Authenticate to browse and purchase
                            our products.
                        </p>
                    </div>
                </div>

                <div className="products-empty">

                    <div className="empty-icon">
                        🛍️
                    </div>

                    <h3>Authentication Required</h3>

                    <p>
                        Please authenticate with FastAPI
                        to view available products.
                    </p>

                </div>

            </section>
        );
    }


    // =========================================================
    // LOADING
    // =========================================================

    if (loadingProducts) {
        return (
            <section className="products-section">

                <div className="products-header">
                    <div>

                        <span className="section-label">
                            SHOPPING
                        </span>

                        <h2>Our Products</h2>

                        <p>
                            Browse our latest products
                        </p>

                    </div>
                </div>

                <div className="products-loading">

                    <div className="loading-spinner"></div>

                    <h3>Loading products...</h3>

                    <p>
                        Please wait while we load
                        the products.
                    </p>

                </div>

            </section>
        );
    }


    // =========================================================
    // NO PRODUCTS
    // =========================================================

    if (!Array.isArray(products) || products.length === 0) {
        return (
            <section className="products-section">

                <div className="products-header">

                    <div>

                        <span className="section-label">
                            SHOPPING
                        </span>

                        <h2>Our Products</h2>

                        <p>
                            Browse our available products
                        </p>

                    </div>

                    <span className="product-count">
                        0 Products
                    </span>

                </div>

                <div className="products-empty">

                    <div className="empty-icon">
                        📦
                    </div>

                    <h3>No Products Found</h3>

                    <p>
                        There are currently no products
                        available to display.
                    </p>

                </div>

            </section>
        );
    }


    // =========================================================
    // PRODUCTS
    // =========================================================

    return (
        <section className="products-section">

            {/* =================================================
                PRODUCTS HEADER
            ================================================= */}

            <div className="products-header">

                <div>

                    <span className="section-label">
                        SHOPPING
                    </span>

                    <h2>Explore Our Products</h2>

                    <p>
                        Find the right products for your needs
                    </p>

                </div>

                <div className="product-count">
                    {products.length}{" "}
                    {products.length === 1
                        ? "Product"
                        : "Products"}
                </div>

            </div>


            {/* =================================================
                PRODUCT GRID
            ================================================= */}

            <div className="products-grid">

                {products.map((product) => {

                    const stock =
                        Number(product.stock_quantity ?? 0);

                    const isOutOfStock =
                        stock <= 0;

                    const productImage =
                        getProductImage(product);


                    return (
                        <article
                            className="product-card"
                            key={product.id}
                        >

                            {/* =================================================
                                PRODUCT IMAGE
                            ================================================= */}

                            <div className="product-image">

                                {productImage ? (

                                    <img
                                        src={productImage}
                                        alt={
                                            product.name ||
                                            "Product"
                                        }
                                        onError={(event) => {
                                            event.currentTarget.style.display =
                                                "none";
                                        }}
                                    />

                                ) : (

                                    <div className="image-placeholder">
                                        🛍️
                                    </div>

                                )}

                            </div>


                            {/* =================================================
                                PRODUCT INFORMATION
                            ================================================= */}

                            <div className="product-content">

                                {/* Category + Popularity */}

                                <div className="product-top-row">

                                    <span className="product-category">
                                        {product.category ||
                                            "General"}
                                    </span>

                                    {product.popularity !==
                                        undefined && (

                                        <span className="product-popularity">
                                            ⭐{" "}
                                            {product.popularity}
                                        </span>

                                    )}

                                </div>


                                {/* Product Name */}

                                <h3 className="product-name">
                                    {product.name ||
                                        "Unnamed Product"}
                                </h3>


                                {/* Description */}

                                <p className="product-description">
                                    {product.description ||
                                        "No description available for this product."}
                                </p>


                                {/* Price + Stock */}

                                <div className="product-info-row">

                                    <div>

                                        <span className="price-label">
                                            PRICE
                                        </span>

                                        <div className="product-price">
                                            ₹
                                            {Number(
                                                product.price || 0
                                            ).toLocaleString(
                                                "en-IN"
                                            )}
                                        </div>

                                    </div>


                                    <div className="stock-container">

                                        <span className="price-label">
                                            STOCK
                                        </span>

                                        <span
                                            className={
                                                isOutOfStock
                                                    ? "stock out"
                                                    : "stock"
                                            }
                                        >
                                            {isOutOfStock
                                                ? "Out of Stock"
                                                : `${stock} available`}
                                        </span>

                                    </div>

                                </div>


                                {/* Add To Cart */}

                                <button
                                    type="button"
                                    className="add-cart-button"
                                    onClick={() =>
                                        addToCart(
                                            product.id
                                        )
                                    }
                                    disabled={
                                        isOutOfStock
                                    }
                                >

                                    {isOutOfStock ? (
                                        <>
                                            <span>
                                                ✕
                                            </span>

                                            Out of Stock
                                        </>
                                    ) : (
                                        <>
                                            <span>
                                                🛒
                                            </span>

                                            Add to Cart
                                        </>
                                    )}

                                </button>

                            </div>

                        </article>
                    );
                })}

            </div>

        </section>
    );
}

export default ProductList;