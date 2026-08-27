from django.urls import path

from .views import (
    dashboard,

    # Sales
    export_sales_csv,
    export_sales_pdf,

    # Orders
    export_orders_csv,
    export_orders_pdf,

    # Payments
    export_payments_csv,
    export_payments_pdf,

    # Products
    export_products_csv,

    # Users
    export_users_csv,
    export_users_pdf,
)


urlpatterns = [

    # ============================================================
    # DASHBOARD
    # ============================================================

    path(
        "",
        dashboard,
        name="dashboard"
    ),

    # ============================================================
    # EXPORT SALES
    # ============================================================

    path(
        "export/sales/csv/",
        export_sales_csv,
        name="export_sales_csv"
    ),

    path(
        "export/sales/pdf/",
        export_sales_pdf,
        name="export_sales_pdf"
    ),

    # ============================================================
    # EXPORT ORDERS
    # ============================================================

    path(
        "export/orders/csv/",
        export_orders_csv,
        name="export_orders_csv"
    ),

    path(
        "export/orders/pdf/",
        export_orders_pdf,
        name="export_orders_pdf"
    ),

    # ============================================================
    # EXPORT PAYMENTS
    # ============================================================

    path(
        "export/payments/csv/",
        export_payments_csv,
        name="export_payments_csv"
    ),

    path(
        "export/payments/pdf/",
        export_payments_pdf,
        name="export_payments_pdf"
    ),

    # ============================================================
    # EXPORT PRODUCTS
    # ============================================================

    path(
        "export/products/csv/",
        export_products_csv,
        name="export_products_csv"
    ),

    # ============================================================
    # EXPORT USERS
    # ============================================================

    path(
        "export/users/csv/",
        export_users_csv,
        name="export_users_csv"
    ),

    path(
        "export/users/pdf/",
        export_users_pdf,
        name="export_users_pdf"
    ),

]