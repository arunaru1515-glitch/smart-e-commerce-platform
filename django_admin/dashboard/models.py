from django.db import models


# ============================================================
# USER
# Existing FastAPI table: users
# ============================================================

class User(models.Model):
    id = models.IntegerField(
        primary_key=True
    )

    name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        max_length=255,
        unique=True
    )

    password = models.CharField(
        max_length=255
    )

    role = models.CharField(
        max_length=20,
        choices=[
            ("admin", "Admin"),
            ("staff", "Staff"),
            ("customer", "Customer"),
        ],
        default="customer",
    )

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        managed = False
        db_table = "users"

    def __str__(self):
        return f"{self.name} ({self.email})"


# ============================================================
# PRODUCT
# Existing FastAPI table: products
# ============================================================

class Product(models.Model):
    id = models.IntegerField(
        primary_key=True
    )

    name = models.CharField(
        max_length=255
    )

    description = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    price = models.FloatField()

    category = models.CharField(
        max_length=100
    )

    popularity = models.IntegerField(
        default=0
    )

    stock_quantity = models.IntegerField(
        default=0
    )

    images = models.ImageField(
        upload_to="products/",
        null=True,
        blank=True
    )

    is_available = models.BooleanField(
        default=True
    )

    class Meta:
        managed = False
        db_table = "products"

    def __str__(self):
        return self.name


# ============================================================
# CART
# Existing FastAPI table: carts
# ============================================================

class Cart(models.Model):
    id = models.IntegerField(
        primary_key=True
    )

    user_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "carts"

    def __str__(self):
        return f"Cart #{self.id}"


# ============================================================
# CART ITEM
# Existing FastAPI table: cart_items
# ============================================================

class CartItem(models.Model):
    id = models.IntegerField(
        primary_key=True
    )

    cart_id = models.IntegerField()

    product_id = models.IntegerField()

    quantity = models.IntegerField(
        default=1
    )

    price = models.FloatField()

    class Meta:
        managed = False
        db_table = "cart_items"

    def __str__(self):
        return f"Cart Item #{self.id}"


# ============================================================
# ORDER
# Existing FastAPI table: orders
# ============================================================

class Order(models.Model):
    id = models.IntegerField(
        primary_key=True
    )

    user = models.IntegerField()

    products = models.JSONField()

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_status = models.CharField(
        max_length=50,
        default="pending"
    )

    order_status = models.CharField(
        max_length=20,
        default="pending"
    )

    created_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = "orders"

    def __str__(self):
        return f"Order #{self.id}"


# ============================================================
# PAYMENT
# Existing FastAPI table: payments
# ============================================================

class Payment(models.Model):
    id = models.IntegerField(
        primary_key=True
    )

    order_id = models.IntegerField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=50
    )

    transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=50,
        default="pending"
    )

    timestamp = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = "payments"

    def __str__(self):
        return f"Payment #{self.id}"


# ============================================================
# NOTIFICATION
# Existing FastAPI table: notifications
# ============================================================

class Notification(models.Model):
    id = models.IntegerField(
        primary_key=True
    )

    user = models.IntegerField()

    type = models.CharField(
        max_length=100
    )

    message = models.CharField(
        max_length=500
    )

    read_status = models.CharField(
        max_length=20,
        default="unread"
    )

    timestamp = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = "notifications"

    def __str__(self):
        return f"Notification #{self.id}"