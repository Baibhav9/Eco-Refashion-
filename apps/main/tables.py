import django_tables2 as tables
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.utils.text import Truncator
from django_tables2 import columns

from apps.main.constants import Roles, ProductApprovalStatus, ProductCategory
from apps.main.models import Order, RentalRequest, Product


class OrderTable(tables.Table):
    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.get("exclude", [])
        exclude_fields += ["id"]
        kwargs["exclude"] = list(set(exclude_fields))
        super().__init__(*args, **kwargs)

    class Meta:
        model = Order
        template_name = "django_tables2/bootstrap5.html"


class ProductTable(tables.Table):
    actions = columns.Column(verbose_name="", empty_values=(), orderable=False)
    description = tables.Column(accessor="description", empty_values=(), orderable=False)

    def __init__(self, *args, category=None, user=None, **kwargs):
        exclude_fields = kwargs.get("exclude", [])

        if category in [ProductCategory.DONATION, ProductCategory.RECYCLE, ProductCategory.THRIFT]:
            exclude_fields += ["id", "price"]
            if user.role == Roles.USER:
                exclude_fields += ["user"]
        elif category in [ProductCategory.PRODUCT, ProductCategory.RENTING]:
            exclude_fields += ["id", "delivery_option", "pickup_address", "pickup_phone"]
            if user.role == Roles.SELLER:
                exclude_fields += ["user"]
            exclude_fields += ["product"]

        exclude_fields += ["updated_at", "created_at"]

        kwargs["exclude"] = list(set(exclude_fields))

        super().__init__(*args, **kwargs)
        self.category = category
        self.user = user

    def render_description(self, value):
        return Truncator(value).chars(30)

    def can_edit(self, record):
        if self.category in [ProductCategory.DONATION, ProductCategory.RECYCLE, ProductCategory.THRIFT] and self.user.role == Roles.USER:
            return record.status == ProductApprovalStatus.PENDING
        if self.category in [ProductCategory.PRODUCT, ProductCategory.RENTING] and self.user.role == Roles.SELLER:
            return record.status == ProductApprovalStatus.PENDING
        return False

    def can_delete(self, record):
        if self.category in [ProductCategory.DONATION, ProductCategory.RECYCLE, ProductCategory.THRIFT] and self.user.role == Roles.USER:
            return True
        if self.category in [ProductCategory.PRODUCT, ProductCategory.RENTING] and self.user.role == Roles.SELLER:
            return True
        return False

    def can_approve_or_reject(self, record):
        return self.user and self.user.role not in [Roles.SELLER, Roles.USER] and record.status == ProductApprovalStatus.PENDING

    def render_actions(self, record):
        delete_url = reverse_lazy('main:product_delete', kwargs={'category': self.category, 'id': record.id})
        edit_url = reverse_lazy('main:product_edit', kwargs={'category': self.category, 'id': record.id})
        approve_url = reverse_lazy('main:product_approve', kwargs={'id': record.id})
        reject_url = reverse_lazy('main:product_reject', kwargs={'id': record.id})
        view_url = reverse_lazy('main:dashboard_product_detail', kwargs={'category': self.category, 'pk': record.id})

        buttons = f'<a href="{view_url}" class="btn btn-sm btn-info me-2 mb-2">View</a>'

        if self.can_edit(record):
            buttons += f'<a href="{edit_url}" class="btn btn-sm btn-primary me-2 mb-2">Edit</a>'

        if self.can_delete(record):
            buttons += f'<a href="{delete_url}" class="btn btn-sm btn-danger me-2 mb-2">Delete</a>'

        if self.can_approve_or_reject(record):
            buttons += f'<a href="{approve_url}" class="btn btn-sm btn-success me-2 mb-2">Approve</a>'
            buttons += f'<a href="{reject_url}" class="btn btn-sm btn-warning mb-2">Reject</a>'

        return format_html(buttons)

    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap5.html"


class RentalRequestTable(tables.Table):
    def __init__(self, *args, **kwargs):
        exclude_fields = ['id', 'order', "status"]
        kwargs['exclude'] = kwargs.get('exclude', []) + exclude_fields
        super().__init__(*args, **kwargs)

    class Meta:
        model = RentalRequest
        template_name = "django_tables2/bootstrap5.html"
