from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum
from django.db.models.functions import TruncMonth

import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from .models import (
    Product,
    User,
    Order,
    Payment,
    Cart,
    CartItem,
    Notification,
)


# ============================================================
# DASHBOARD
# ============================================================

@staff_member_required
def dashboard(request):

    # ========================================================
    # BASIC DASHBOARD COUNTS
    # ========================================================

    total_products = Product.objects.count()
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    total_payments = Payment.objects.count()
    total_carts = Cart.objects.count()
    total_cart_items = CartItem.objects.count()
    total_notifications = Notification.objects.count()

    # ========================================================
    # ORDER STATUS COUNTS
    # ========================================================

    pending_orders = Order.objects.filter(
        order_status="pending"
    ).count()

    paid_orders = Order.objects.filter(
        order_status="paid"
    ).count()

    shipped_orders = Order.objects.filter(
        order_status="shipped"
    ).count()

    delivered_orders = Order.objects.filter(
        order_status="delivered"
    ).count()

    cancelled_orders = Order.objects.filter(
        order_status="cancelled"
    ).count()

    # ========================================================
    # PAYMENT COUNTS
    # ========================================================

    successful_payments = Payment.objects.filter(
        status="paid"
    ).count()

    pending_payments = Payment.objects.filter(
        status="pending"
    ).count()

    # ========================================================
    # ANALYTICS 1 - TOTAL SALES
    # ========================================================

    total_sales = Order.objects.filter(
        payment_status="paid"
    ).aggregate(
        total=Sum("total")
    )["total"] or 0

    # ========================================================
    # ANALYTICS 2 - REVENUE TRENDS
    # ========================================================

    revenue_data = (
        Order.objects
        .filter(payment_status="paid")
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(revenue=Sum("total"))
        .order_by("month")
    )

    revenue_labels = []
    revenue_values = []

    for item in revenue_data:

        if item["month"]:

            revenue_labels.append(
                item["month"].strftime("%b %Y")
            )

            revenue_values.append(
                float(item["revenue"] or 0)
            )

    # ========================================================
    # ANALYTICS 3 - TOP SELLING PRODUCTS
    # ========================================================

    top_products_data = (
        CartItem.objects
        .values("product_id")
        .annotate(
            total_quantity=Sum("quantity")
        )
        .order_by("-total_quantity")[:5]
    )

    top_product_labels = []
    top_product_values = []

    for item in top_products_data:

        try:

            product = Product.objects.get(
                id=item["product_id"]
            )

            top_product_labels.append(
                product.name
            )

            top_product_values.append(
                item["total_quantity"]
            )

        except Product.DoesNotExist:
            continue

    # ========================================================
    # ANALYTICS 4 - LOW STOCK PRODUCTS
    # ========================================================

    low_stock_products = Product.objects.filter(
        stock_quantity__lte=5
    ).order_by("stock_quantity")

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        # Basic counts
        "total_products": total_products,
        "total_users": total_users,
        "total_orders": total_orders,
        "total_payments": total_payments,
        "total_carts": total_carts,
        "total_cart_items": total_cart_items,
        "total_notifications": total_notifications,

        # Order status
        "pending_orders": pending_orders,
        "paid_orders": paid_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,

        # Payments
        "successful_payments": successful_payments,
        "pending_payments": pending_payments,

        # Analytics
        "total_sales": total_sales,

        "revenue_labels": revenue_labels,
        "revenue_values": revenue_values,

        "top_product_labels": top_product_labels,
        "top_product_values": top_product_values,

        "low_stock_products": low_stock_products,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )


# ============================================================
# EXPORT ORDERS - CSV
# ============================================================

@staff_member_required
def export_orders_csv(request):

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="orders_report.csv"'
    )

    writer = csv.writer(response)

    # CSV Header
    writer.writerow([
        "Order ID",
        "User ID",
        "Total",
        "Payment Status",
        "Order Status",
        "Created At",
    ])

    # Data
    orders = Order.objects.all().order_by("-created_at")

    for order in orders:

        writer.writerow([
            order.id,
            order.user,
            order.total,
            order.payment_status,
            order.order_status,
            order.created_at,
        ])

    return response


# ============================================================
# EXPORT PAYMENTS - CSV
# ============================================================

@staff_member_required
def export_payments_csv(request):

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="payments_report.csv"'
    )

    writer = csv.writer(response)

    # CSV Header
    writer.writerow([
        "Payment ID",
        "Order ID",
        "Amount",
        "Payment Method",
        "Transaction ID",
        "Status",
        "Timestamp",
    ])

    # Data
    payments = Payment.objects.all().order_by("-timestamp")

    for payment in payments:

        writer.writerow([
            payment.id,
            payment.order_id,
            payment.amount,
            payment.payment_method,
            payment.transaction_id or "-",
            payment.status,
            payment.timestamp,
        ])

    return response


# ============================================================
# EXPORT PRODUCTS - CSV
# ============================================================

@staff_member_required
def export_products_csv(request):

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="products_report.csv"'
    )

    writer = csv.writer(response)

    # CSV Header
    writer.writerow([
        "Product ID",
        "Name",
        "Category",
        "Price",
        "Stock Quantity",
        "Is Available",
        "Popularity",
    ])

    # Data
    products = Product.objects.all().order_by("-id")

    for product in products:

        writer.writerow([
            product.id,
            product.name,
            product.category,
            product.price,
            product.stock_quantity,
            "Yes" if product.is_available else "No",
            product.popularity,
        ])

    return response



# ============================================================
# EXPORT SALES - CSV
# ============================================================

@staff_member_required
def export_sales_csv(request):

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="sales_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Sale ID",
        "Order ID",
        "User ID",
        "Amount",
        "Payment Status",
        "Order Status",
        "Created At",
    ])

    orders = Order.objects.filter(
        payment_status="paid"
    ).order_by("-created_at")

    for order in orders:
        writer.writerow([
            order.id,
            order.id,
            order.user,
            order.total,
            order.payment_status,
            order.order_status,
            order.created_at,
        ])

    return response

# ============================================================
# EXPORT SALES - PDF
# ============================================================

@staff_member_required
def export_sales_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="sales_report.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=A4
    )

    elements = []

    styles = getSampleStyleSheet()

    title = Paragraph(
        "Sales Report",
        styles["Title"]
    )

    elements.append(title)
    elements.append(Spacer(1, 15))

    orders = Order.objects.filter(
        payment_status="paid"
    ).order_by("-created_at")

    data = [
        [
            "Sale ID",
            "Order ID",
            "User ID",
            "Amount",
            "Payment Status",
            "Order Status",
            "Created At"
        ]
    ]

    for order in orders:
        data.append([
            str(order.id),
            str(order.id),
            str(order.user),
            str(order.total),
            str(order.payment_status),
            str(order.order_status),
            str(order.created_at),
        ])

    table = Table(data)

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1f2937")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                colors.HexColor("#f2f2f2")
            ),
        ])
    )

    elements.append(table)

    document.build(elements)

    return response

# ============================================================
# EXPORT ORDERS - PDF
# ============================================================

@staff_member_required
def export_orders_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="orders_report.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(
        Paragraph(
            "Smart E-Commerce - Orders Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    # Table Header
    data = [[
        "Order ID",
        "User",
        "Total",
        "Payment",
        "Order Status",
        "Created At",
    ]]

    orders = Order.objects.all().order_by("-created_at")

    for order in orders:

        created_at = (
            order.created_at.strftime("%Y-%m-%d %H:%M")
            if order.created_at
            else "-"
        )

        data.append([
            str(order.id),
            str(order.user),
            str(order.total),
            str(order.payment_status),
            str(order.order_status),
            created_at,
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            55,
            50,
            65,
            75,
            80,
            100,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#2c3e50"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f2f2f2"),
                ],
            ),
        ])
    )

    elements.append(table)

    document.build(elements)

    return response


# ============================================================
# EXPORT PAYMENTS - PDF
# ============================================================

@staff_member_required
def export_payments_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="payments_report.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "Smart E-Commerce - Payments Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    data = [[
        "Payment ID",
        "Order ID",
        "Amount",
        "Method",
        "Status",
        "Timestamp",
    ]]

    payments = Payment.objects.all().order_by("-timestamp")

    for payment in payments:

        timestamp = (
            payment.timestamp.strftime("%Y-%m-%d %H:%M")
            if payment.timestamp
            else "-"
        )

        data.append([
            str(payment.id),
            str(payment.order_id),
            str(payment.amount),
            str(payment.payment_method),
            str(payment.status),
            timestamp,
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            60,
            60,
            70,
            75,
            65,
            110,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#2c3e50"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f2f2f2"),
                ],
            ),
        ])
    )

    elements.append(table)

    document.build(elements)

    return response

# ============================================================
# EXPORT USERS - CSV
# ============================================================

@staff_member_required
def export_users_csv(request):

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="users_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "User ID",
        "Name",
        "Email",
        "Role",
        "Is Active",
        "Created At",
    ])

    users = User.objects.all().order_by("-id")

    for user in users:
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.role,
            "Yes" if user.is_active else "No",
            user.created_at,
        ])

    return response


# ============================================================
# EXPORT USERS - PDF
# ============================================================

@staff_member_required
def export_users_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="users_report.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "Smart E-Commerce - Users Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    data = [[
        "User ID",
        "Name",
        "Email",
        "Role",
        "Active",
        "Created At",
    ]]

    users = User.objects.all().order_by("-id")

    for user in users:

        created_at = (
            user.created_at.strftime("%Y-%m-%d %H:%M")
            if user.created_at
            else "-"
        )

        data.append([
            str(user.id),
            str(user.name),
            str(user.email),
            str(user.role),
            "Yes" if user.is_active else "No",
            created_at,
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            50,
            80,
            150,
            60,
            50,
            100,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#2c3e50"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f2f2f2"),
                ],
            ),
        ])
    )

    elements.append(table)

    document.build(elements)

    return response