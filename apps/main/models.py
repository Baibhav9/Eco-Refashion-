from django.db import models
from django.conf import settings

from .constants import ProductApprovalStatus, SellerProductCategory, UserProductCategory, TransactionStatus, \
    PaymentChoices


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

    class Meta:
        abstract = True


class SellerProduct(Product):
    category = models.CharField(max_length=25, choices=SellerProductCategory.choices)

    def __str__(self):
        return f"{self.title} - {self.category}"


class UserProduct(Product):
    category = models.CharField(max_length=25, choices=UserProductCategory.choices)

    def __str__(self):
        return f"{self.title} - {self.category}"


class RentalRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cloth_item = models.ForeignKey('UserProduct', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.cloth_item.title} ({self.status})"


class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    products = models.ManyToManyField(SellerProduct, related_name='products')
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=25, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_date}"

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PaymentChoices.choices)
    is_paid = models.BooleanField(default=False)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(SellerProduct, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey("main.SellerProduct", on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.quantity})"

    def get_total_price(self):
        return self.product.price * self.quantity
