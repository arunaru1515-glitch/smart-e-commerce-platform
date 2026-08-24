from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# =========================================================
# Database Models
# =========================================================

from app.models.user import User
from app.models.product import Product
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.payment import Payment


# =========================================================
# Routers
# =========================================================

from app.routers.auth import router as auth_router
from app.routers.product import router as product_router
from app.routers.cart import router as cart_router
from app.routers.checkout import router as checkout_router
from app.routers.webhook import router as webhook_router


# =========================================================
# Create Database Tables
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# Create FastAPI Application
# =========================================================

app = FastAPI(
    title="Smart E-Commerce Platform",
    description="Backend API for the Smart E-Commerce Platform",
    version="1.0.0"
)


# =========================================================
# CORS Configuration
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Include Authentication Routes
# =========================================================

app.include_router(auth_router)


# =========================================================
# Include Product Routes
# =========================================================

app.include_router(product_router)


# =========================================================
# Include Cart Routes
# =========================================================

app.include_router(cart_router)


# =========================================================
# Include Checkout Routes
# =========================================================

app.include_router(checkout_router)


# =========================================================
# Include Stripe Webhook Routes
# =========================================================

app.include_router(webhook_router)


# =========================================================
# Root Endpoint
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Smart E-Commerce Platform API is running"
    }