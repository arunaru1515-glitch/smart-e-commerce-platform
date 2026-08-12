from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.core.security import get_current_user, require_roles


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# =========================================================
# GET ALL PRODUCTS
# =========================================================

@router.get("/")
def get_products(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    products = db.query(Product).all()

    return products


# =========================================================
# GET SINGLE PRODUCT
# =========================================================

@router.get("/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# =========================================================
# CREATE PRODUCT - ADMIN ONLY
# =========================================================

@router.post("/")
def create_product(
    name: str,
    description: str,
    price: float,
    stock: int,
    images: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        images=images
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return {
        "message": "Product created successfully",
        "product": product
    }


# =========================================================
# UPDATE PRODUCT - ADMIN ONLY
# =========================================================

@router.put("/{product_id}")
def update_product(
    product_id: int,
    name: str,
    description: str,
    price: float,
    stock: int,
    images: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.name = name
    product.description = description
    product.price = price
    product.stock = stock
    product.images = images

    db.commit()
    db.refresh(product)

    return {
        "message": "Product updated successfully",
        "product": product
    }


# =========================================================
# DELETE PRODUCT - ADMIN ONLY
# =========================================================

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }