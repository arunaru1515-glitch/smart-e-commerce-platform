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
# GET ALL PRODUCTS + FILTERS
# =========================================================

@router.get("/")
def get_products(
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    min_popularity: int = None,
    in_stock: bool = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Product)

    if category:
        query = query.filter(
            Product.category == category
        )

    if min_price is not None:
        query = query.filter(
            Product.price >= min_price
        )

    if max_price is not None:
        query = query.filter(
            Product.price <= max_price
        )

    if min_popularity is not None:
        query = query.filter(
            Product.popularity >= min_popularity
        )

    if in_stock is True:
        query = query.filter(
            Product.stock_quantity > 0
        )

    elif in_stock is False:
        query = query.filter(
            Product.stock_quantity == 0
        )

    products = query.all()

    return products


# =========================================================
# GET PRODUCTS BY CATEGORY
# =========================================================

@router.get("/category/{category}")
def get_products_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    products = db.query(Product).filter(
        Product.category == category
    ).all()

    if not products:
        raise HTTPException(
            status_code=404,
            detail="No products found in this category"
        )

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
    category: str = "General",
    popularity: int = 0,
    images: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    product = Product(
        name=name,
        description=description,
        price=price,
        category=category,
        popularity=popularity,
        stock_quantity=stock,
        is_available=stock > 0,
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
    category: str = "General",
    popularity: int = 0,
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
    product.category = category
    product.popularity = popularity
    product.stock_quantity = stock
    product.is_available = stock > 0
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