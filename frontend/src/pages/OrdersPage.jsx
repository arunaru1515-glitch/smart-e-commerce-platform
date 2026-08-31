import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://127.0.0.1:8000";

function OrdersPage({ token }) {

    const navigate = useNavigate();

    // =========================================================
    // STATE
    // =========================================================

    const [orders, setOrders] = useState([]);
    const [products, setProducts] = useState([]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [selectedOrder, setSelectedOrder] =
        useState(null);

    const [reason, setReason] = useState("");
    const [comment, setComment] = useState("");

    const [returnLoading, setReturnLoading] =
        useState(false);

    const [returnMessage, setReturnMessage] =
        useState("");

    const [returnError, setReturnError] =
        useState("");


    // =========================================================
    // FETCH ORDERS
    // =========================================================

    const fetchOrders = async () => {

        try {

            setLoading(true);
            setError("");

            const response = await fetch(
                `${API_URL}/orders/`,
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
                    "Failed to fetch orders"
                );
            }

            const orderList =
                Array.isArray(data)
                    ? data
                    : data.orders || [];

            setOrders(orderList);

        } catch (err) {

            console.error(
                "Orders fetch error:",
                err
            );

            setError(
                err.message ||
                "Unable to load orders"
            );

        } finally {

            setLoading(false);
        }
    };


    // =========================================================
    // FETCH PRODUCTS
    //
    // Used to display actual product image/name
    // =========================================================

    const fetchProducts = async () => {

        try {

            if (!token) {
                return;
            }

            const response = await fetch(
                `${API_URL}/products/`,
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
                    "Products fetch failed:",
                    data
                );

                return;
            }

            const productList =
                Array.isArray(data)
                    ? data
                    : Array.isArray(data.products)
                        ? data.products
                        : [];

            setProducts(productList);

        } catch (err) {

            console.error(
                "Products fetch error:",
                err
            );
        }
    };


    // =========================================================
    // LOAD ORDERS + PRODUCTS
    // =========================================================

    useEffect(() => {

        if (!token) {

            setLoading(false);
            setError(
                "Authentication required"
            );

            return;
        }

        fetchOrders();
        fetchProducts();

    }, [token]);


    // =========================================================
    // PARSE ORDER PRODUCTS
    // =========================================================

    const getOrderProducts = (order) => {

        if (!order) {
            return [];
        }

        let orderProducts =
            order.products;

        // Sometimes backend returns JSON string
        if (typeof orderProducts === "string") {

            try {

                orderProducts =
                    JSON.parse(orderProducts);

            } catch (error) {

                console.error(
                    "Could not parse order products:",
                    error
                );

                return [];
            }
        }

        if (Array.isArray(orderProducts)) {
            return orderProducts;
        }

        return [];
    };


    // =========================================================
    // FIND PRODUCT FROM PRODUCTS API
    // =========================================================

    const findProduct = (orderProduct) => {

        if (!orderProduct) {
            return null;
        }

        const productId =
            orderProduct.product_id ||
            orderProduct.id ||
            orderProduct.productId;

        if (!productId) {
            return null;
        }

        return products.find(
            (product) =>
                Number(product.id) ===
                Number(productId)
        );
    };


    // =========================================================
    // GET PRODUCT NAME
    // =========================================================

    const getProductName = (orderProduct) => {

        const product =
            findProduct(orderProduct);

        return (
            orderProduct.product_name ||
            orderProduct.name ||
            orderProduct.productName ||
            product?.name ||
            product?.product_name ||
            "Product"
        );
    };


    // =========================================================
    // GET PRODUCT IMAGE
    // =========================================================

    const getProductImage = (orderProduct) => {

        const product =
            findProduct(orderProduct);

        return (
            orderProduct.image_url ||
            orderProduct.imageUrl ||
            orderProduct.product_image ||
            orderProduct.productImage ||
            orderProduct.image ||
            product?.image_url ||
            product?.imageUrl ||
            product?.product_image ||
            product?.productImage ||
            product?.image ||
            null
        );
    };


    // =========================================================
    // GET QUANTITY
    // =========================================================

    const getProductQuantity = (orderProduct) => {

        return (
            orderProduct.quantity ||
            orderProduct.qty ||
            1
        );
    };


    // =========================================================
    // GET UNIT PRICE
    // =========================================================

    const getProductPrice = (
        orderProduct,
        order
    ) => {

        const product =
            findProduct(orderProduct);

        const price =
            orderProduct.unit_price ??
            orderProduct.price ??
            product?.price ??
            null;

        if (price !== null) {
            return Number(price);
        }

        return Number(order?.total || 0);
    };


    // =========================================================
    // RETURN ELIGIBILITY
    // =========================================================

    const isReturnEligible = (order) => {

        if (
            !order ||
            order.order_status?.toLowerCase() !==
                "delivered"
        ) {
            return false;
        }

        const deliveredDate =
            order.delivered_at ||
            order.updated_at ||
            order.created_at;

        if (!deliveredDate) {
            return false;
        }

        const deliveredTime =
            new Date(
                deliveredDate
            ).getTime();

        const currentTime =
            new Date().getTime();

        const sevenDays =
            7 *
            24 *
            60 *
            60 *
            1000;

        const difference =
            currentTime -
            deliveredTime;

        return (
            difference >= 0 &&
            difference <= sevenDays
        );
    };


    // =========================================================
    // OPEN RETURN FORM
    // =========================================================

    const openReturnForm = (order) => {

        setSelectedOrder(order);

        setReason("");
        setComment("");

        setReturnMessage("");
        setReturnError("");
    };


    // =========================================================
    // CLOSE RETURN FORM
    // =========================================================

    const closeReturnForm = () => {

        if (returnLoading) {
            return;
        }

        setSelectedOrder(null);

        setReason("");
        setComment("");

        setReturnMessage("");
        setReturnError("");
    };


    // =========================================================
    // SUBMIT RETURN REQUEST
    // =========================================================

    const submitReturnRequest = async () => {

        if (!selectedOrder) {
            return;
        }

        if (!reason.trim()) {

            setReturnError(
                "Please select a return reason."
            );

            return;
        }

        try {

            setReturnLoading(true);

            setReturnError("");
            setReturnMessage("");

            const response = await fetch(
                `${API_URL}/orders/${selectedOrder.id}/return`,
                {
                    method: "POST",

                    headers: {
                        Authorization:
                            `Bearer ${token}`,

                        "Content-Type":
                            "application/json",
                    },

                    body: JSON.stringify({

                        reason:
                            reason.trim(),

                        comment:
                            comment.trim() ||
                            null,
                    }),
                }
            );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Failed to submit return request"
                );
            }

            setReturnMessage(
                data.message ||
                "Return request submitted successfully."
            );


            // Update order in UI

            setOrders(
                (previousOrders) =>
                    previousOrders.map(
                        (order) =>
                            order.id ===
                            selectedOrder.id
                                ? {
                                    ...order,

                                    order_status:
                                        data.order_status ||
                                        "return_requested",
                                }
                                : order
                    )
            );


            // Close after short delay

            setTimeout(() => {

                setSelectedOrder(null);

                setReason("");
                setComment("");

                setReturnMessage("");

            }, 1800);


        } catch (err) {

            console.error(
                "Return request error:",
                err
            );

            setReturnError(
                err.message ||
                "Unable to submit return request"
            );

        } finally {

            setReturnLoading(false);
        }
    };


    // =========================================================
    // FORMAT DATE
    // =========================================================

    const formatDate = (date) => {

        if (!date) {
            return "N/A";
        }

        return new Date(
            date
        ).toLocaleDateString(
            "en-GB",
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
            }
        );
    };


    // =========================================================
    // FORMAT CURRENCY
    // =========================================================

    const formatCurrency = (amount) => {

        const value =
            Number(amount || 0);

        return `₹${value.toLocaleString(
            "en-IN"
        )}`;
    };


    // =========================================================
    // STATUS LABEL
    // =========================================================

    const getStatusLabel = (status) => {

        if (!status) {
            return "Unknown";
        }

        return status
            .replace(/_/g, " ")
            .replace(
                /\b\w/g,
                (letter) =>
                    letter.toUpperCase()
            );
    };


    // =========================================================
    // STATUS CLASS
    // =========================================================

    const getStatusClass = (status) => {

        return (
            status
                ?.toLowerCase()
                .replace(
                    /_/g,
                    "-"
                ) ||
            "unknown"
        );
    };


    // =========================================================
    // LOADING
    // =========================================================

    if (loading) {

        return (

            <div className="orders-page">

                <div className="orders-loading">

                    <div className="orders-loading-spinner">
                    </div>

                    <h2>
                        Loading your orders
                    </h2>

                    <p>
                        Please wait while we load your purchase history.
                    </p>

                </div>

            </div>
        );
    }


    // =========================================================
    // ERROR
    // =========================================================

    if (error) {

        return (

            <div className="orders-page">

                <div className="orders-error-card">

                    <div className="orders-error-icon">
                        !
                    </div>

                    <h2>
                        Unable to load orders
                    </h2>

                    <p>
                        {error}
                    </p>

                    <button
                        type="button"
                        onClick={() =>
                            navigate("/")
                        }
                    >
                        ← Back to Home
                    </button>

                </div>

            </div>
        );
    }


    // =========================================================
    // ORDERS PAGE
    // =========================================================

    return (

        <div className="orders-page">

            <div className="orders-container">


                {/* =================================================
                    PAGE HEADER
                ================================================= */}

                <div className="orders-page-header">

                    <div className="orders-header-left">

                        <button
                            type="button"
                            className="back-home-button"
                            onClick={() =>
                                navigate("/")
                            }
                        >
                            ← Back to Home
                        </button>

                        <span className="orders-eyebrow">
                            PURCHASE HISTORY
                        </span>

                        <h1>
                            My Orders
                        </h1>

                        <p>
                            Track your purchases, payments and returns.
                        </p>

                    </div>


                    <div className="orders-total-count">

                        <strong>
                            {orders.length}
                        </strong>

                        <span>
                            {orders.length === 1
                                ? "Order"
                                : "Orders"}
                        </span>

                    </div>

                </div>


                {/* =================================================
                    EMPTY ORDERS
                ================================================= */}

                {orders.length === 0 ? (

                    <div className="empty-orders">

                        <div className="empty-orders-icon">
                            📦
                        </div>

                        <h2>
                            No orders yet
                        </h2>

                        <p>
                            You haven't placed any orders yet.
                        </p>

                        <button
                            type="button"
                            onClick={() =>
                                navigate("/")
                            }
                        >
                            Start Shopping
                        </button>

                    </div>

                ) : (

                    <div className="orders-list">

                        {orders.map((order) => {

                            const eligible =
                                isReturnEligible(
                                    order
                                );

                            const returnRequested =
                                order.order_status
                                    ?.toLowerCase() ===
                                "return_requested";


                            const orderProducts =
                                getOrderProducts(
                                    order
                                );


                            return (

                                <div
                                    className="order-card"
                                    key={order.id}
                                >


                                    {/* =================================
                                        PRODUCT IMAGE AREA
                                    ================================= */}

                                    <div className="order-image-area">

                                        {orderProducts.length > 0 &&
                                        getProductImage(
                                            orderProducts[0]
                                        ) ? (

                                            <img
                                                src={
                                                    getProductImage(
                                                        orderProducts[0]
                                                    )
                                                }
                                                alt={
                                                    getProductName(
                                                        orderProducts[0]
                                                    )
                                                }
                                                className="order-product-image"
                                                onError={(event) => {

                                                    event.currentTarget.style.display =
                                                        "none";

                                                    event.currentTarget.nextSibling.style.display =
                                                        "flex";
                                                }}
                                            />

                                        ) : null}


                                        <div
                                            className="order-image-placeholder"
                                            style={{
                                                display:
                                                    orderProducts.length > 0 &&
                                                    getProductImage(
                                                        orderProducts[0]
                                                    )
                                                        ? "none"
                                                        : "flex"
                                            }}
                                        >
                                            📦
                                        </div>

                                    </div>


                                    {/* =================================
                                        ORDER CONTENT
                                    ================================= */}

                                    <div className="order-card-content">


                                        {/* =================================
                                            ORDER TOP
                                        ================================= */}

                                        <div className="order-card-top">

                                            <div>

                                                <span className="order-label">
                                                    ORDER
                                                </span>

                                                <h2>
                                                    #{order.id}
                                                </h2>

                                            </div>


                                            <span
                                                className={`order-status-badge status-${getStatusClass(
                                                    order.order_status
                                                )}`}
                                            >
                                                {getStatusLabel(
                                                    order.order_status
                                                )}
                                            </span>

                                        </div>


                                        {/* =================================
                                            PRODUCTS
                                        ================================= */}

                                        <div className="order-products">

                                            {orderProducts.length > 0 ? (

                                                orderProducts.map(
                                                    (
                                                        orderProduct,
                                                        index
                                                    ) => {

                                                        const image =
                                                            getProductImage(
                                                                orderProduct
                                                            );

                                                        const name =
                                                            getProductName(
                                                                orderProduct
                                                            );

                                                        const quantity =
                                                            getProductQuantity(
                                                                orderProduct
                                                            );

                                                        const price =
                                                            getProductPrice(
                                                                orderProduct,
                                                                order
                                                            );

                                                        return (

                                                            <div
                                                                className="order-product"
                                                                key={`${order.id}-${index}`}
                                                            >

                                                                <div className="order-product-info">

                                                                    <h3>
                                                                        {name}
                                                                    </h3>

                                                                    <span>
                                                                        Quantity: {quantity}
                                                                    </span>

                                                                </div>

                                                                <strong>
                                                                    {formatCurrency(
                                                                        price *
                                                                        quantity
                                                                    )}
                                                                </strong>

                                                            </div>
                                                        );
                                                    }
                                                )

                                            ) : (

                                                <div className="order-product">

                                                    <div className="order-product-info">

                                                        <h3>
                                                            Order Items
                                                        </h3>

                                                        <span>
                                                            Quantity: 1
                                                        </span>

                                                    </div>

                                                    <strong>
                                                        {formatCurrency(
                                                            order.total
                                                        )}
                                                    </strong>

                                                </div>

                                            )}

                                        </div>


                                        {/* =================================
                                            DATE
                                        ================================= */}

                                        <div className="order-date">

                                            <span>
                                                🗓️
                                            </span>

                                            <span>
                                                Ordered on{" "}
                                                {formatDate(
                                                    order.created_at
                                                )}
                                            </span>

                                        </div>


                                        {/* =================================
                                            SUMMARY
                                        ================================= */}

                                        <div className="order-summary">

                                            <div>

                                                <span>
                                                    Total Amount
                                                </span>

                                                <strong>
                                                    {formatCurrency(
                                                        order.total
                                                    )}
                                                </strong>

                                            </div>


                                            <div>

                                                <span>
                                                    Payment
                                                </span>

                                                <strong
                                                    className={
                                                        order.payment_status
                                                            ?.toLowerCase() ===
                                                        "paid"
                                                            ? "payment-paid"
                                                            : ""
                                                    }
                                                >
                                                    {getStatusLabel(
                                                        order.payment_status
                                                    )}
                                                </strong>

                                            </div>

                                        </div>


                                        {/* =================================
                                            RETURN SECTION
                                        ================================= */}

                                        {returnRequested ? (

                                            <div className="return-submitted-box">

                                                <div className="return-icon">
                                                    ↩
                                                </div>

                                                <div>

                                                    <strong>
                                                        Return Request Submitted
                                                    </strong>

                                                    <p>
                                                        Your return request is currently under review.
                                                    </p>

                                                </div>

                                            </div>

                                        ) : eligible ? (

                                            <div className="return-action-box">

                                                <div>

                                                    <strong>
                                                        Need to return this item?
                                                    </strong>

                                                    <p>
                                                        Eligible within 7 days of delivery.
                                                    </p>

                                                </div>


                                                <button
                                                    type="button"
                                                    className="request-return-button"
                                                    onClick={() =>
                                                        openReturnForm(
                                                            order
                                                        )
                                                    }
                                                >
                                                    Request Return
                                                </button>

                                            </div>

                                        ) : (

                                            order.order_status
                                                ?.toLowerCase() ===
                                                "delivered" && (

                                                <div className="return-expired-box">

                                                    Return window has expired.

                                                </div>
                                            )
                                        )}

                                    </div>

                                </div>
                            );
                        })}

                    </div>
                )}

            </div>


            {/* =====================================================
                RETURN MODAL
            ===================================================== */}

            {selectedOrder && (

                <div
                    className="return-modal-overlay"
                    onClick={closeReturnForm}
                >

                    <div
                        className="return-modal"
                        onClick={(event) =>
                            event.stopPropagation()
                        }
                    >


                        {/* =============================================
                            MODAL HEADER
                        ============================================= */}

                        <div className="return-modal-header">

                            <div>

                                <span className="modal-eyebrow">
                                    RETURN REQUEST
                                </span>

                                <h2>
                                    Request Return
                                </h2>

                                <p>
                                    Order #{selectedOrder.id}
                                </p>

                            </div>


                            <button
                                type="button"
                                className="close-modal-button"
                                onClick={
                                    closeReturnForm
                                }
                                disabled={
                                    returnLoading
                                }
                            >
                                ×
                            </button>

                        </div>


                        {/* =============================================
                            ORDER PREVIEW
                        ============================================= */}

                        <div className="return-order-preview">

                            <div className="return-preview-image">

                                {getOrderProducts(
                                    selectedOrder
                                ).length > 0 &&
                                getProductImage(
                                    getOrderProducts(
                                        selectedOrder
                                    )[0]
                                ) ? (

                                    <img
                                        src={
                                            getProductImage(
                                                getOrderProducts(
                                                    selectedOrder
                                                )[0]
                                            )
                                        }
                                        alt="Product"
                                    />

                                ) : (

                                    <span>
                                        📦
                                    </span>

                                )}

                            </div>


                            <div>

                                <span>
                                    Order #{selectedOrder.id}
                                </span>

                                <strong>
                                    {getOrderProducts(
                                        selectedOrder
                                    ).length > 0
                                        ? getProductName(
                                            getOrderProducts(
                                                selectedOrder
                                            )[0]
                                        )
                                        : "Order Item"}
                                </strong>

                                <p>
                                    {formatCurrency(
                                        selectedOrder.total
                                    )}
                                </p>

                            </div>

                        </div>


                        {/* =============================================
                            SUCCESS
                        ============================================= */}

                        {returnMessage && (

                            <div className="return-success">

                                <span>
                                    ✓
                                </span>

                                <div>
                                    <strong>
                                        Return Request Submitted
                                    </strong>

                                    <p>
                                        {returnMessage}
                                    </p>
                                </div>

                            </div>
                        )}


                        {/* =============================================
                            ERROR
                        ============================================= */}

                        {returnError && (

                            <div className="return-error">

                                {returnError}

                            </div>
                        )}


                        {/* =============================================
                            FORM
                        ============================================= */}

                        {!returnMessage && (

                            <div className="return-form">


                                {/* Reason */}

                                <div className="form-group">

                                    <label>
                                        Return Reason
                                        <span>
                                            *
                                        </span>
                                    </label>

                                    <select
                                        value={reason}
                                        onChange={(event) =>
                                            setReason(
                                                event.target.value
                                            )
                                        }
                                        disabled={
                                            returnLoading
                                        }
                                    >

                                        <option value="">
                                            Select a reason
                                        </option>

                                        <option value="Product is damaged">
                                            Product is damaged
                                        </option>

                                        <option value="Wrong product received">
                                            Wrong product received
                                        </option>

                                        <option value="Product is defective">
                                            Product is defective
                                        </option>

                                        <option value="Product not as described">
                                            Product not as described
                                        </option>

                                        <option value="Changed my mind">
                                            Changed my mind
                                        </option>

                                        <option value="Other">
                                            Other
                                        </option>

                                    </select>

                                </div>


                                {/* Comment */}

                                <div className="form-group">

                                    <label>

                                        Additional Comment

                                        <span className="optional">
                                            Optional
                                        </span>

                                    </label>

                                    <textarea
                                        value={comment}
                                        onChange={(event) =>
                                            setComment(
                                                event.target.value
                                            )
                                        }
                                        placeholder="Tell us more about the reason for your return..."
                                        rows="4"
                                        disabled={
                                            returnLoading
                                        }
                                    />

                                </div>


                                {/* Buttons */}

                                <div className="return-modal-actions">

                                    <button
                                        type="button"
                                        className="cancel-return-button"
                                        onClick={
                                            closeReturnForm
                                        }
                                        disabled={
                                            returnLoading
                                        }
                                    >
                                        Cancel
                                    </button>


                                    <button
                                        type="button"
                                        className="submit-return-button"
                                        onClick={
                                            submitReturnRequest
                                        }
                                        disabled={
                                            returnLoading
                                        }
                                    >

                                        {returnLoading
                                            ? "Submitting..."
                                            : "Submit Return Request"}

                                    </button>

                                </div>

                            </div>
                        )}

                    </div>

                </div>
            )}

        </div>
    );
}

export default OrdersPage;