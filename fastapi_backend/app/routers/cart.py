from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


# =========================================================
# ADD PRODUCT TO CART
# POST /cart/add
# =========================================================

@router.post("/add")
def add_to_cart(
    user_id: int,
    product_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db)
):

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    # Check product
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check stock
    if product.stock_quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient product stock"
        )

    # Find user's cart
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    # Create cart if user does not have one
    if not cart:
        cart = Cart(
            user_id=user_id
        )

        db.add(cart)
        db.commit()
        db.refresh(cart)

    # Check whether product already exists in cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id
    ).first()

    if existing_item:

        new_quantity = existing_item.quantity + quantity

        if product.stock_quantity < new_quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient product stock"
            )

        existing_item.quantity = new_quantity
        existing_item.price = product.price

        db.commit()
        db.refresh(existing_item)

        return {
            "message": "Cart quantity updated successfully",
            "cart_id": cart.id,
            "cart_item_id": existing_item.id,
            "user_id": user_id,
            "product_id": product_id,
            "quantity": existing_item.quantity,
            "price": product.price
        }

    # Create new CartItem
    cart_item = CartItem(
        cart_id=cart.id,
        product_id=product_id,
        quantity=quantity,
        price=product.price
    )

    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return {
        "message": "Product added to cart successfully",
        "cart_id": cart.id,
        "cart_item_id": cart_item.id,
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity,
        "price": product.price
    }


# =========================================================
# UPDATE CART QUANTITY
# PUT /cart/update
# =========================================================

@router.put("/update")
def update_cart(
    cart_item_id: int,
    quantity: int,
    db: Session = Depends(get_db)
):

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    # Find cart item
    cart_item = db.query(CartItem).filter(
        CartItem.id == cart_item_id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    # Find product
    product = db.query(Product).filter(
        Product.id == cart_item.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check stock
    if product.stock_quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient product stock"
        )

    cart_item.quantity = quantity
    cart_item.price = product.price

    db.commit()
    db.refresh(cart_item)

    return {
        "message": "Cart quantity updated successfully",
        "cart_id": cart_item.cart_id,
        "cart_item_id": cart_item.id,
        "product_id": cart_item.product_id,
        "quantity": cart_item.quantity,
        "price": cart_item.price
    }


# =========================================================
# REMOVE PRODUCT FROM CART
# DELETE /cart/remove
# =========================================================

@router.delete("/remove")
def remove_from_cart(
    cart_item_id: int,
    db: Session = Depends(get_db)
):

    cart_item = db.query(CartItem).filter(
        CartItem.id == cart_item_id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    cart_id = cart_item.cart_id

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Product removed from cart successfully",
        "cart_id": cart_id,
        "cart_item_id": cart_item_id
    }


# =========================================================
# VIEW CART WITH CALCULATIONS
# GET /cart/
# =========================================================

@router.get("/")
def get_cart(
    user_id: int,
    db: Session = Depends(get_db)
):

    # Find user's cart
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    # User has no cart
    if not cart:
        return {
            "user_id": user_id,
            "cart_id": None,
            "items": [],
            "cart_total": 0.0,
            "tax": 0.0,
            "grand_total": 0.0
        }

    # Get cart items
    cart_items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).all()

    items = []
    cart_total = 0.0

    for cart_item in cart_items:

        # Find product
        product = db.query(Product).filter(
            Product.id == cart_item.product_id
        ).first()

        if not product:
            continue

        # Item total
        item_total = product.price * cart_item.quantity

        # Cart total
        cart_total += item_total

        items.append({
            "cart_item_id": cart_item.id,
            "product_id": product.id,
            "product_name": product.name,
            "price": product.price,
            "quantity": cart_item.quantity,
            "item_total": item_total
        })

    # Tax is optional
    tax = 0.0

    # Grand total
    grand_total = cart_total + tax

    return {
        "user_id": user_id,
        "cart_id": cart.id,
        "items": items,
        "cart_total": cart_total,
        "tax": tax,
        "grand_total": grand_total
    }