from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect

import requests

from jose import jwt

from .models import (
    User,
    Product,
    Cart,
    CartItem,
    Order,
    Payment,
    Notification,
    ReturnRequest,
)


# ============================================================
# FASTAPI JWT CONFIGURATION
# Must match fastapi_backend/app/core/security.py
# ============================================================

FASTAPI_SECRET_KEY = "smart-ecommerce-secret-key"
FASTAPI_ALGORITHM = "HS256"


# ============================================================
# CREATE FASTAPI ACCESS TOKEN FOR DJANGO ADMIN
# ============================================================

def create_fastapi_admin_token(admin_user):
    """
    Create a JWT access token compatible with FastAPI.

    The Django admin user email is matched with the
    FastAPI users table to get the correct FastAPI user ID.
    """

    if not admin_user.is_authenticated:
        raise Exception("Django admin user is not authenticated.")

    # --------------------------------------------------------
    # Find the same user in FastAPI's users table
    # --------------------------------------------------------

    fastapi_user = (
        User.objects
        .filter(email=admin_user.email)
        .first()
    )

    if not fastapi_user:
        raise Exception(
            "Admin user was not found in the FastAPI users table."
        )

    # --------------------------------------------------------
    # Make sure the FastAPI user is actually an admin
    # --------------------------------------------------------

    if fastapi_user.role != "admin":
        raise Exception(
            "The FastAPI user does not have admin role."
        )

    # --------------------------------------------------------
    # Create JWT payload
    # Same structure as FastAPI create_access_token()
    # --------------------------------------------------------

    from datetime import datetime, timedelta, timezone

    expire = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    payload = {
        "sub": str(fastapi_user.id),
        "type": "access",
        "exp": expire,
    }

    # --------------------------------------------------------
    # Encode token
    # --------------------------------------------------------

    token = jwt.encode(
        payload,
        FASTAPI_SECRET_KEY,
        algorithm=FASTAPI_ALGORITHM,
    )

    return token


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
        "image_preview",
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

    list_editable = (
        "price",
        "stock_quantity",
        "is_available",
        "popularity",
    )

    ordering = (
        "-id",
    )

    def image_preview(self, obj):

        if obj.images:
            return format_html(
                '<img src="{}" width="80" height="80" '
                'style="object-fit: contain; border-radius: 8px;" />',
                obj.images.url,
            )

        return "No Image"

    image_preview.short_description = "Image"


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

    ordering = (
        "-id",
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

    ordering = (
        "-id",
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


# ============================================================
# RETURN REQUEST ADMIN
# ============================================================

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order_id",
        "user_id",
        "reason",
        "status",
        "created_at",
        "admin_actions",
    )

    search_fields = (
        "order_id",
        "user_id",
        "reason",
    )

    list_filter = (
        "status",
        "reason",
    )

    ordering = (
        "-created_at",
    )

    # ========================================================
    # CUSTOM ADMIN URLS
    # ========================================================

    def get_urls(self):

        urls = super().get_urls()

        custom_urls = [
            path(
                "<int:return_id>/approve/",
                self.admin_site.admin_view(
                    self.approve_return
                ),
                name="approve_return",
            ),

            path(
                "<int:return_id>/reject/",
                self.admin_site.admin_view(
                    self.reject_return
                ),
                name="reject_return",
            ),
        ]

        return custom_urls + urls

    # ========================================================
    # APPROVE RETURN
    # ========================================================

    def approve_return(self, request, return_id):

        if request.method != "GET":

            messages.error(
                request,
                "Invalid request method."
            )

            return redirect(
                "admin:dashboard_returnrequest_changelist"
            )

        try:

            # ------------------------------------------------
            # CREATE FASTAPI JWT
            # ------------------------------------------------

            access_token = create_fastapi_admin_token(
                request.user
            )

            # ------------------------------------------------
            # CALL FASTAPI APPROVE API
            # ------------------------------------------------

            response = requests.post(
                f"http://127.0.0.1:8000/admin/returns/"
                f"{return_id}/approve",

                headers={
                    "Authorization": f"Bearer {access_token}"
                },

                timeout=30,
            )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if response.status_code in (200, 201):

                messages.success(
                    request,
                    f"Return request #{return_id} "
                    f"approved successfully."
                )

            # ------------------------------------------------
            # FASTAPI ERROR
            # ------------------------------------------------

            else:

                try:
                    error_detail = response.json().get(
                        "detail",
                        "Unknown error"
                    )
                except Exception:
                    error_detail = response.text

                messages.error(
                    request,
                    f"Failed to approve return request "
                    f"#{return_id}. "
                    f"FastAPI returned "
                    f"{response.status_code}: "
                    f"{error_detail}"
                )

        except requests.RequestException as error:

            messages.error(
                request,
                f"Could not connect to FastAPI: {error}"
            )

        except Exception as error:

            messages.error(
                request,
                f"Error while approving return request "
                f"#{return_id}: {error}"
            )

        return redirect(
            "admin:dashboard_returnrequest_changelist"
        )

    # ========================================================
    # REJECT RETURN
    # ========================================================

    def reject_return(self, request, return_id):

        if request.method != "GET":

            messages.error(
                request,
                "Invalid request method."
            )

            return redirect(
                "admin:dashboard_returnrequest_changelist"
            )

        try:

            # ------------------------------------------------
            # CREATE FASTAPI JWT
            # ------------------------------------------------

            access_token = create_fastapi_admin_token(
                request.user
            )

            # ------------------------------------------------
            # CALL FASTAPI REJECT API
            # ------------------------------------------------

            response = requests.post(
                f"http://127.0.0.1:8000/admin/returns/"
                f"{return_id}/reject",

                headers={
                    "Authorization": f"Bearer {access_token}"
                },

                timeout=30,
            )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if response.status_code in (200, 201):

                messages.success(
                    request,
                    f"Return request #{return_id} "
                    f"rejected successfully."
                )

            # ------------------------------------------------
            # FASTAPI ERROR
            # ------------------------------------------------

            else:

                try:
                    error_detail = response.json().get(
                        "detail",
                        "Unknown error"
                    )
                except Exception:
                    error_detail = response.text

                messages.error(
                    request,
                    f"Failed to reject return request "
                    f"#{return_id}. "
                    f"FastAPI returned "
                    f"{response.status_code}: "
                    f"{error_detail}"
                )

        except requests.RequestException as error:

            messages.error(
                request,
                f"Could not connect to FastAPI: {error}"
            )

        except Exception as error:

            messages.error(
                request,
                f"Error while rejecting return request "
                f"#{return_id}: {error}"
            )

        return redirect(
            "admin:dashboard_returnrequest_changelist"
        )

    # ========================================================
    # ACTION BUTTONS
    # ========================================================

    def admin_actions(self, obj):

        if obj.status == "pending":

            approve_url = (
                f"/admin/dashboard/returnrequest/"
                f"{obj.id}/approve/"
            )

            reject_url = (
                f"/admin/dashboard/returnrequest/"
                f"{obj.id}/reject/"
            )

            return format_html(
                '<a href="{}" '
                'style="background:#28a745;'
                'color:white;padding:6px 10px;'
                'border-radius:4px;'
                'text-decoration:none;'
                'margin-right:5px;">'
                'Approve'
                '</a>'

                '<a href="{}" '
                'style="background:#dc3545;'
                'color:white;padding:6px 10px;'
                'border-radius:4px;'
                'text-decoration:none;">'
                'Reject'
                '</a>',

                approve_url,
                reject_url,
            )

        return format_html(
            '<span style="color:#777;">'
            'No action'
            '</span>'
        )

    admin_actions.short_description = "Actions"