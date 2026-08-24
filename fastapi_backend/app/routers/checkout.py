from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.order import Order
from app.models.payment import Payment

from app.core.stripe_service import create_payment_intent


# =========================================================
# CHECKOUT ROUTER
# =========================================================

router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"]
)


# =========================================================
# CHECKOUT
# POST /checkout/
# =========================================================

@router.post("/")
def checkout(
    user_id: int,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. FIND USER CART
    # =====================================================

    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    # =====================================================
    # 2. GET CART ITEMS
    # =====================================================

    cart_items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    # =====================================================
    # 3. VALIDATE PRODUCTS AND STOCK
    # =====================================================

    order_items = []

    total = Decimal("0.00")

    for cart_item in cart_items:

        product = db.query(Product).filter(
            Product.id == cart_item.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {cart_item.product_id} not found"
            )

        if product.stock_quantity < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}"
            )

        # Calculate item total

        item_total = (
            Decimal(str(product.price))
            * cart_item.quantity
        )

        total += item_total

        order_items.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": cart_item.quantity,
            "price": float(product.price),
            "item_total": float(item_total)
        })

    # =====================================================
    # 4. CREATE ORDER
    # =====================================================

    order = Order(
        user=user_id,
        products=order_items,
        total=total,
        payment_status="pending",
        order_status="pending"
    )

    db.add(order)

    # Flush to generate order.id
    # without committing yet

    db.flush()

    # =====================================================
    # 5. CREATE STRIPE PAYMENT INTENT
    # =====================================================

    try:

        payment_intent = create_payment_intent(
            amount=total,
            order_id=order.id
        )

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Stripe payment creation failed: {str(e)}"
        )

    # =====================================================
    # 6. CREATE PAYMENT RECORD
    # =====================================================

    payment = Payment(
        order_id=order.id,
        amount=total,
        payment_method="stripe",
        transaction_id=payment_intent.id,
        status="pending"
    )

    db.add(payment)

    # =====================================================
    # 7. SAVE ORDER + PAYMENT
    # =====================================================

    try:

        db.commit()

        db.refresh(order)
        db.refresh(payment)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error during checkout: {str(e)}"
        )

    # =====================================================
    # 8. RETURN CHECKOUT RESPONSE
    # =====================================================

    return {
        "message": "Checkout created successfully",

        "order_id": order.id,

        "payment_id": payment.id,

        "user_id": user_id,

        "items": order_items,

        "total": float(total),

        "payment_status": payment.status,

        "order_status": order.order_status,

        "stripe_payment_intent_id": payment_intent.id,

        "client_secret": payment_intent.client_secret
    }