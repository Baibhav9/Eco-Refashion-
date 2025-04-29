from django.db.models import TextChoices

class Roles(TextChoices):
    SUPER_ADMIN = "super admin"
    USER = "user"
    ADMIN = "admin"
    ORGANIZATION = "organization"
    SELLER = "seller"

class ProductCategory(TextChoices):
    PRODUCT = "product", "Product"
    RENTING = "rental", "Rental"
    DONATION = "donation", "Donation"
    RECYCLE = "recycle", "Recycle"
    THRIFT = "thrift", "Thrift"

class ProductApprovalStatus(TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    DECLINED = "declined", "Declined"

class TransactionStatus(TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    CANCELED = "canceled", "User Canceled"

class PaymentChoices(TextChoices):
    COD = "cod", "Cod"
    KHALTI = "khalti", "Khalti"

class ProductDeliveryOption(TextChoices):
    PICKUP = "pickup", "Pickup"
    DROPOFF = "dropoff", "Dropoff"

PRODUCT_CATEGORY_LIST = [key for (key, value) in ProductCategory.choices]