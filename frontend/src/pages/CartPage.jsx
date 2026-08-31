import React from "react";
import Cart from "../Cart";

function CartPage({ userId, token }) {
    return (
        <div className="cart-page">
            <Cart
                userId={userId}
                token={token}
            />
        </div>
    );
}

export default CartPage;