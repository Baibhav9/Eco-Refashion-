from django.db.models import TextChoices

class Roles(TextChoices):
    USER = "user"
    ADMIN = "admin"
    ORGANIZATION = "organization"
    SELLER = "seller"

class SellerProductCategory(TextChoices):
    PRODUCT = "product", "Product"
    RENTING = "renting", "Renting"


class UserProductCategory(TextChoices):
    DONATION = "donation", "Donation"
    RECYCLE = "recycle", "Recycle"
    THRIFT = "thrift", "Thrift"


class ProductApprovalStatus(TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    DECLINED = "declined", "Declined"

class TransactionStatus(TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    CANCELED = "canceled", "Canceled"

class PaymentChoices(TextChoices):
    COD = "cod", "Cod"
    KHALTI = "khalti", "Khalti"
