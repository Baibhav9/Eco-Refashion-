import django_tables2 as tables
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.utils.text import Truncator
from django_tables2 import columns

from apps.main.constants import Roles, ProductApprovalStatus, ProductCategory
from apps.main.models import Order, RentalRequest, Product


class OrderTable(tables.Table):
    class Meta:
        model = Order
        template_name = "django_tables2/bootstrap5.html"


class ProductTable(tables.Table):
    actions = columns.Column(verbose_name="", empty_values=(), orderable=False)
    description = tables.Column(accessor="description", empty_values=(), orderable=False)

    def __init__(self, *args, category=None, user=None, **kwargs):
        if category in [ProductCategory.DONATION, ProductCategory.RECYCLE]:
            if "price" in kwargs.get("exclude", []) or "delivery_method" in kwargs.get("exclude", []) or "pickup_address" in kwargs.get("exclude", []) or "pickup_phone" in kwargs.get("exclude", []):
                pass
            else:
                kwargs["exclude"] = kwargs.get("exclude", []) + ["price", "delivery_method", "pickup_address", "pickup_phone"]

        super().__init__(*args, **kwargs)
        self.category = category
        self.user = user

    def render_description(self, value):
        return Truncator(value).chars(30)

    def render_actions(self, record):
        delete_url = reverse_lazy('main:product_delete', kwargs={'category': self.category, 'id': record.id})
        edit_url = reverse_lazy('main:product_edit', kwargs={'category': self.category, 'id': record.id})
        approve_url = reverse_lazy("main:product_approve", kwargs={'id': record.id})

        buttons = ""
        if (self.category == ProductCategory.DONATION or self.category == ProductCategory.RECYCLE or self.category == ProductCategory.THRIFT) and self.user.role == Roles.USER:
            buttons = f'<a href="{edit_url}" class="btn btn-sm btn-primary me-2 mb-2">Edit</a>'
            buttons += f'<a href="{delete_url}" class="btn btn-sm btn-danger">Delete</a>'

        if self.user and self.user.role != Roles.SELLER and self.user.role != Roles.USER and record.status == ProductApprovalStatus.PENDING:
            buttons += f'<a href="{approve_url}" class="btn btn-sm btn-success me-2 mb-2">Approve</a>'


        return format_html(buttons)

    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap5.html"

class RentalRequestTable(tables.Table):
    class Meta:
        model = RentalRequest
        template_name = "django_tables2/bootstrap5.html"
