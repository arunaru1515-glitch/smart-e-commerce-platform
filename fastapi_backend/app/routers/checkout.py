from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user

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
# GET AUTHENTICATED USER ID
# =========================================================

def get_user_id(current_user):

    if isinstance(current_user, dict):

        user_id = (
            current_user.get("id")
            or current_user.get("user_id")
        )

    else:

        user_id = getattr(
            current_user,
            "id",
            None
        )

        if user_id is None:

            user_id = getattr(
                current_user,
                "user_id",
                None
            )

    if user_id is None:

        raise HTTPException(
            status_code=401,
            detail="Unable to identify authenticated user"
        )

    return int(user_id)


# =========================================================
# CHECKOUT
# POST /checkout/
# =========================================================

@router.post("/")
def checkout(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # =====================================================
    # 1. GET LOGGED-IN USER
    # =====================================================

    user_id = get_user_id(current_user)


    # =====================================================
    # 2. FIND USER CART
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
    # 3. GET CART ITEMS
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
    # 4. VALIDATE PRODUCTS AND STOCK
    # =====================================================

    order_items = []

    total = Decimal("0.00")


    for cart_item in cart_items:

        product = db.query(Product).filter(
            Product.id == cart_item.product_id
        ).first()


        # -------------------------------------------------
        # Product must exist
        # -------------------------------------------------

        if not product:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Product {cart_item.product_id} "
                    "not found"
                )
            )


        # -------------------------------------------------
        # Product must be available
        # -------------------------------------------------

        if not product.is_available:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Product {product.name} "
                    "is not available"
                )
            )


        # -------------------------------------------------
        # Validate quantity
        # -------------------------------------------------

        if cart_item.quantity <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid quantity for "
                    f"{product.name}"
                )
            )


        # -------------------------------------------------
        # Validate stock
        # -------------------------------------------------

        if product.stock_quantity < cart_item.quantity:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient stock for "
                    f"{product.name}"
                )
            )


        # -------------------------------------------------
        # Calculate item total
        # -------------------------------------------------

        item_total = (
            Decimal(str(product.price))
            * cart_item.quantity
        )

        total += item_total


        # -------------------------------------------------
        # Add item to order
        # -------------------------------------------------

        order_items.append({

            "product_id": product.id,

            "product_name": product.name,

            "quantity": cart_item.quantity,

            "price": float(product.price),

            "item_total": float(item_total)

        })


    # =====================================================
    # 5. VALIDATE TOTAL
    # =====================================================

    if total <= Decimal("0.00"):

        raise HTTPException(
            status_code=400,
            detail="Invalid checkout total"
        )


    # =====================================================
    # 6. CREATE ORDER
    # =====================================================

    order = Order(

        user=user_id,

        products=order_items,

        total=total,

        payment_status="pending",

        order_status="pending"

    )

    db.add(order)


    # -----------------------------------------------------
    # Generate order ID before Stripe request
    # -----------------------------------------------------

    db.flush()


    # =====================================================
    # 7. CREATE STRIPE PAYMENT INTENT
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

            detail=(
                "Stripe payment creation failed: "
                f"{str(e)}"
            )

        )


    # =====================================================
    # 8. CREATE PAYMENT RECORD
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
    # 9. SAVE ORDER + PAYMENT
    # =====================================================

    try:

        db.commit()

        db.refresh(order)

        db.refresh(payment)

    except Exception as e:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=(
                "Database error during checkout: "
                f"{str(e)}"
            )

        )


    # =====================================================
    # 10. RETURN CHECKOUT RESPONSE
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