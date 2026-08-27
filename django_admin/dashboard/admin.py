from django.contrib import admin

from .models import (
    User,
    Product,
    Cart,
    CartItem,
    Order,
    Payment,
    Notification,
)


# ============================================================
# USER ADMIN
# ============================================================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "email",
        "role",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
    )

    list_filter = (
        "role",
        "is_active",
    )

    list_editable = (
        "role",
        "is_active",
    )

    ordering = (
        "-id",
    )


# ============================================================
# PRODUCT ADMIN
# ============================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "category",
        "price",
        "stock_quantity",
        "images",
        "is_available",
        "popularity",
    )

    search_fields = (
        "name",
        "category",
        "description",
    )

    list_filter = (
        "category",
        "is_available",
    )

    ordering = (
        "-id",
    )


# ============================================================
# CART ADMIN
# ============================================================

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user_id",
    )

    search_fields = (
        "user_id",
    )


# ============================================================
# CART ITEM ADMIN
# ============================================================

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "cart_id",
        "product_id",
        "quantity",
        "price",
    )

    search_fields = (
        "cart_id",
        "product_id",
    )


# ============================================================
# ORDER ADMIN
# ============================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "total",
        "payment_status",
        "order_status",
        "created_at",
    )

    search_fields = (
        "id",
        "user",
    )

    list_filter = (
        "payment_status",
        "order_status",
    )

    ordering = (
        "-created_at",
    )


# ============================================================
# PAYMENT ADMIN
# ============================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order_id",
        "amount",
        "payment_method",
        "transaction_id",
        "status",
        "timestamp",
    )

    search_fields = (
        "order_id",
        "transaction_id",
    )

    list_filter = (
        "payment_method",
        "status",
    )

    ordering = (
        "-timestamp",
    )


# ============================================================
# NOTIFICATION ADMIN
# ============================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "type",
        "message",
        "read_status",
        "timestamp",
    )

    search_fields = (
        "user",
        "type",
        "message",
    )

    list_filter = (
        "type",
        "read_status",
    )

    ordering = (
        "-timestamp",
    )