from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.shortcuts import get_object_or_404

from .constants import ProductApprovalStatus, TransactionStatus, \
    PaymentChoices, ProductCategory, ProductDeliveryOption


# main/models.py
class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField("products/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=ProductApprovalStatus.choices,
                              default=ProductApprovalStatus.PENDING)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    available_size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=25, choices=ProductCategory.choices)
    stock_amount = models.PositiveIntegerField(default=1)

    delivery_option = models.CharField(max_length=50, blank=True, null=True, choices=ProductDeliveryOption.choices, default=ProductDeliveryOption.DROPOFF)
    pickup_address = models.CharField(max_length=255, default='Baneshwor, Kathmandu')
    pickup_phone = models.CharField(max_length=255, default="9800000000")

    def __str__(self):
        return f"{self.title} - {self.category}"

class RentalRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ProductApprovalStatus.choices, default=ProductApprovalStatus.PENDING)
    requested_date = models.DateTimeField(auto_now_add=True)
    requested_for = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.order.name} ({self.status})"


class Transaction(models.Model):
    products = models.ManyToManyField(Product, related_name='products')
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=25, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    pidx = models.CharField(max_length=100, unique=True)  # Payment ID (unique for each transaction)
    transaction_id = models.CharField(max_length=100, unique=True)  # Transaction ID (unique)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refunded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status}"

class Order(models.Model):
    name = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PaymentChoices.choices)
    is_paid = models.BooleanField(default=False)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.name:
            self.name = f"Order #{self.id}-{self.user.username}-{self.payment_method}-{self.ordered_at.strftime('%Y-%m-%d %H:%M')}"
            super().save(update_fields=['name'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey("main.Product", on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.quantity})"

    def get_total_price(self):
        return self.product.price * self.quantity
