from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cart import Cart

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.post("/")
def add_to_cart(
    user_id: int,
    product_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db)
):
    cart_item = Cart(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity
    )

    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return {
        "message": "Product added to cart successfully",
        "cart_id": cart_item.id,
        "user_id": cart_item.user_id,
        "product_id": cart_item.product_id,
        "quantity": cart_item.quantity
    }


@router.get("/")
def get_cart(
    user_id: int,
    db: Session = Depends(get_db)
):
    cart_items = db.query(Cart).filter(
        Cart.user_id == user_id
    ).all()

    return cart_items


@router.delete("/{cart_id}")
def remove_from_cart(
    cart_id: int,
    db: Session = Depends(get_db)
):
    cart_item = db.query(Cart).filter(
        Cart.id == cart_id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Product removed from cart successfully"
    }