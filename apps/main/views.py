import csv
import json
import os
from decimal import Decimal
from time import timezone

import requests
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, When, BooleanField, Value, ExpressionWrapper
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, CreateView, ListView, View, DetailView, DeleteView, UpdateView
from django_tables2 import SingleTableView

from .constants import ProductApprovalStatus, Roles, ProductCategory, PRODUCT_CATEGORY_LIST, PaymentChoices, \
    TransactionStatus, ProductDeliveryOption
from .models import Cart, RentalRequest, Product, OrderItem, Order, Transaction
from .forms import ProductForm, OrderForm

from django.core.exceptions import PermissionDenied
from django.db.models import Sum, F, DecimalField
from django.db import transaction

from .tables import OrderTable, ProductTable, RentalRequestTable
from ..accounts.models import CustomUser


class RoleRequiredMixin:
    required_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to access this page.")

        user_role = getattr(request.user, 'role', None)

        if isinstance(self.required_roles, str):
            allowed = user_role == self.required_roles
        else:
            allowed = user_role in self.required_roles

        if not allowed:
            raise PermissionDenied(f"Access denied for role: {user_role}")

        return super().dispatch(request, *args, **kwargs)


# Index view
class IndexView(TemplateView):
    template_name = "main/index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        products = Product.objects.all()
        sale_products = products.filter(category=ProductCategory.PRODUCT, status=ProductApprovalStatus.APPROVED)
        rent_products = products.filter(category=ProductCategory.RENTING, status=ProductApprovalStatus.APPROVED)
        thrifts = Product.objects.filter(category=ProductCategory.THRIFT, status=ProductApprovalStatus.APPROVED)

        context.update({
            'sale_products': sale_products,
            'rent_products': rent_products,
            'thrifts': thrifts,
        })
        return context


# Product view (show only approved products)
class ProductsView(TemplateView):
    """Show only APPROVED products with category='product'"""
    template_name = "main/products_list.html"

    def get_context_data(self, **kwargs):
        context = super(ProductsView, self).get_context_data(**kwargs)
        category = self.kwargs['category']

        if not category in PRODUCT_CATEGORY_LIST:
            raise Http404("Category Not Found")

        products = Product.objects.filter(
            status=ProductApprovalStatus.APPROVED,
            category=category,
        ).order_by('-created_at')

        context.update({
            'title': category,
            'products': products,
        })

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/product_detail.html'
    context_object_name = 'object'

    def get_object(self, queryset=None):
        return Product.objects.get(pk=self.kwargs['id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['similar_products'] = Product.objects.filter(
            category=product.category
        ).exclude(pk=product.pk)[:6]
        return context


class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "main/dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == Roles.USER:
            total_orders = Order.objects.filter(user=self.request.user).count()
            total_donations = Product.objects.filter(user=self.request.user, category=ProductCategory.DONATION).count()
            total_thrifts = Product.objects.filter(user=self.request.user, category=ProductCategory.THRIFT).count()
            total_recycles = Product.objects.filter(user=self.request.user, category=ProductCategory.RECYCLE).count()

            context.update({
                'total_orders': total_orders,
                'total_donations': total_donations,
                'total_thrifts': total_thrifts,
                'total_recycles': total_recycles,
            })
        elif self.request.user.role == Roles.SELLER:
            total_uploads = Product.objects.filter(user=self.request.user, category__in=[ProductCategory.PRODUCT,
                                                                                         ProductCategory.RENTING]).count()
            approved_uploads = Product.objects.filter(user=self.request.user,
                                                      category__in=[ProductCategory.PRODUCT, ProductCategory.RENTING],
                                                      status=ProductApprovalStatus.APPROVED).count()
            pending_uploads = Product.objects.filter(user=self.request.user,
                                                      category__in=[ProductCategory.PRODUCT, ProductCategory.RENTING],
                                                      status=ProductApprovalStatus.PENDING).count()
            declined_uploads = Product.objects.filter(user=self.request.user,category__in=[ProductCategory.PRODUCT, ProductCategory.RENTING],
                                                      status=ProductApprovalStatus.DECLINED).count()

            context.update({
                'total_uploads': total_uploads,
                'approved_uploads': approved_uploads,
                'pending_uploads': pending_uploads,
                'declined_uploads': declined_uploads
            })
        elif self.request.user.role == Roles.ORGANIZATION:
            total_donation_received = Product.objects.filter(category=ProductCategory.DONATION).count()
            total_recycles_received = Product.objects.filter(category=ProductCategory.RECYCLE).count()
            pending_donations = Product.objects.filter(category=ProductCategory.DONATION, status=ProductApprovalStatus.PENDING).count()
            pending_recycles = Product.objects.filter(category=ProductCategory.RECYCLE, status=ProductApprovalStatus.PENDING).count()

            context.update({
                'total_donation_received': total_donation_received,
                'total_recycles_received': total_recycles_received,
                'pending_donations': pending_donations,
                'pending_recycles': pending_recycles,
            })
        else:
            total_products = Product.objects.filter(category=ProductCategory.PRODUCT).count()
            total_rentals = Product.objects.filter(category=ProductCategory.RENTING).count()
            total_thrifts_admin = Product.objects.filter(category=ProductCategory.THRIFT).count()
            total_approved_products = Product.objects.filter(category=ProductCategory.PRODUCT, status=ProductApprovalStatus.APPROVED).count()
            total_approved_rentals = Product.objects.filter(category=ProductCategory.RENTING, status=ProductApprovalStatus.APPROVED).count()
            total_approved_thrifts = Product.objects.filter(category=ProductCategory.THRIFT, status=ProductApprovalStatus.APPROVED).count()
            total_pendings = Product.objects.filter(category__in=[ProductCategory.PRODUCT, ProductCategory.RENTING, ProductCategory.THRIFT], status=ProductApprovalStatus.PENDING).count()
            total_declined= Product.objects.filter(category__in=[ProductCategory.PRODUCT, ProductCategory.RENTING, ProductCategory.THRIFT], status=ProductApprovalStatus.DECLINED).count()

            context.update({
                'total_products': total_products,
                'total_rentals': total_rentals,
                'total_thrifts_admin': total_thrifts_admin,
                'total_approved_products': total_approved_products,
                'total_approved_rentals': total_approved_rentals,
                'total_approved_thrifts': total_approved_thrifts,
                'total_pendings': total_pendings,
                'total_declined': total_declined
            })
        return context


class OrderListView(LoginRequiredMixin, SingleTableView):
    model = Order
    template_name = "main/dashboard/list_table.html"
    table_class = OrderTable

    def get_context_data(self, **kwargs: None):
        context = super().get_context_data(**kwargs)

        context.update({
            "title": "Orders"
        })

        return context


class ProductCategoryListView(LoginRequiredMixin, SingleTableView):
    model = Product
    template_name = "main/dashboard/list_table.html"
    table_class = ProductTable

    def get_queryset(self):
        category = self.kwargs['category']
        qs = Product.objects.filter(category=category)
        if self.request.user.role == Roles.USER:
            qs = qs.filter(user=self.request.user)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs: None):
        context = super().get_context_data(**kwargs)
        category = self.kwargs['category']

        if not category in PRODUCT_CATEGORY_LIST:
            raise Http404("Category Not Available")

        context.update({
            "title": category,
        })
        return context

    def get_table_kwargs(self, **kwargs):
        kwargs["category"] = self.kwargs['category']
        kwargs['user'] = self.request.user
        return kwargs

class ImportCSVView(View):
    model_mapping = {
        'product': Product,
        'rental': Product,
    }

    def post(self, request, title, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, "No file uploaded.")
            return redirect(request.META.get('HTTP_REFERER'))

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Uploaded file is not a CSV.")
            return redirect(request.META.get('HTTP_REFERER'))

        model = self.model_mapping.get(title)
        if not model:
            messages.error(request, "Invalid import category.")
            return redirect(request.META.get('HTTP_REFERER'))

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            for row in reader:
                obj = model.objects.create(
                    title=row.get('title'),
                    description=row.get('description'),
                    price=row.get('price') or 0,
                    user=request.user,
                    available_size=row.get('available_size') or 'L',
                    stock_amount=row.get('stock_amount') or 0,
                    color=row.get('color'),
                    category=title,
                )
            messages.success(request, "CSV imported successfully.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

        return redirect(request.META.get('HTTP_REFERER'))

class ProductCategoryDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "main/dashboard/dashboard_product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        category = self.kwargs.get('category')
        return Product.objects.filter(category=category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProductCategoryCreateView(LoginRequiredMixin, CreateView):
    model = Product
    template_name = "main/dashboard/create_product.html"
    form_class = ProductForm

    def get_success_url(self):
        messages.success(self.request, f"Product successfully created.")
        return reverse('main:product_by_category', kwargs={'category': self.kwargs['category']})

    def get_context_data(self, **kwargs: None):
        context = super().get_context_data(**kwargs)
        category = self.kwargs['category']

        if not category in PRODUCT_CATEGORY_LIST:
            raise Http404("Category Not Available")

        context.update({
            "title": category,
        })
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["category"] = self.kwargs['category']
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ProductCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    template_name = "main/dashboard/edit_product.html"
    form_class = ProductForm

    def get_object(self, queryset=None):
        category = self.kwargs['category']
        product_id = self.kwargs['id']
        return get_object_or_404(Product, category=category, pk=product_id)

    def get_success_url(self):
        messages.success(self.request, f"Product with id {self.object.id} successfully updated.")
        return reverse('main:product_by_category', kwargs={'category': self.kwargs['category']})

    def get_context_data(self, **kwargs: None):
        context = super().get_context_data(**kwargs)
        category = self.kwargs['category']

        if not category in PRODUCT_CATEGORY_LIST:
            raise Http404("Category Not Available")

        context.update({
            "title": category,
        })
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["category"] = self.kwargs['category']
        return kwargs


class RentalRequestListView(LoginRequiredMixin, SingleTableView):
    model = RentalRequest
    template_name = "main/dashboard/list_table.html"
    table_class = RentalRequestTable


class ProductCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = "main/dashboard/delete_product.html"

    def get_object(self, queryset=None):
        category = self.kwargs['category']
        product_id = self.kwargs['id']
        return get_object_or_404(Product, category=category, pk=product_id)

    def get_success_url(self):
        messages.success(self.request, f"Product with id {self.object.id} successfully deleted.")
        return reverse_lazy("main:product_by_category", kwargs={'category': self.kwargs['category']})


class ProductApproveView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        product_id = self.kwargs['id']
        product = get_object_or_404(Product, id=product_id)
        product.status = ProductApprovalStatus.APPROVED
        product.save()
        messages.success(request, f"Product with id {product.id} successfully approved.")
        return redirect("main:product_by_category", category=product.category)

class ProductRejectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        product_id = self.kwargs['id']
        product = get_object_or_404(Product, id=product_id)
        product.status = ProductApprovalStatus.DECLINED
        product.save()
        messages.success(request, f"Product with id {product.id} successfully declined.")
        return redirect("main:product_by_category", category=product.category)

class RentalRequestView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    required_roles = Roles.USER
    template_name = "main/rental_request.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items = Cart.objects.prefetch_related("product").filter(user=self.request.user,
                                                                     product__category=ProductCategory.RENTING)

        context.update({
            "cart_items": cart_items,
        })

        return context

    def post(self, request, *args, **kwargs):
        requested_for = request.POST.get("requested_for")
        total_amount = request.POST.get("total_amount")
        rental_duration = request.POST.get("rental_duration")

        rental = RentalRequest.objects.create(
            requested_for=requested_for,
            user=request.user,
        )
        checkout_url = reverse("main:checkout", kwargs={'category': ProductCategory.RENTING})
        return redirect(
            f"{checkout_url}?total_amount={total_amount}&rental_request_id={rental.id}&rental_duration={rental_duration}")


# Cart
class CartView(LoginRequiredMixin, RoleRequiredMixin, View):
    required_roles = "user"

    def dispatch(self, request, *args, **kwargs):
        self.action = kwargs.get('action')
        self.item_id = kwargs.get('item_id')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.action == 'add':
            product_id = self.item_id
            try:
                product = Product.objects.get(id=product_id)
                cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()

                messages.success(request, "Successfully added to cart")
                return redirect('main:products', category=product.category)

            except Product.DoesNotExist:
                messages.error(request, "Error Adding to Cart")
                return redirect('main:products', category=ProductCategory.PRODUCT)

        elif self.action == 'remove':
            cart_item = get_object_or_404(Cart, id=self.item_id, user=request.user)
            cart_item.delete()
            messages.success(request, 'Product removed from cart')
            return redirect("main:cart")

        if self.action is None:
            qs = Cart.objects.filter(user=self.request.user).prefetch_related("product")

            sale_products = qs.filter(product__category__in=[ProductCategory.PRODUCT, ProductCategory.THRIFT]).annotate(
                item_total=ExpressionWrapper(
                    F('quantity') * F('product__price'),
                    output_field=DecimalField()
                )
            )

            rental_products = qs.filter(product__category=ProductCategory.RENTING).annotate(
                item_total=ExpressionWrapper(
                    F('quantity') * F('product__price'),
                    output_field=DecimalField()
                )
            )

            sale_products_total = sale_products.aggregate(total_cost=Sum('item_total'))['total_cost'] or 0
            rental_products_total = rental_products.aggregate(total_cost=Sum('item_total'))['total_cost'] or 0

            return render(request, 'main/cart.html', {
                "sale_products_total": sale_products_total,
                "rental_products_total": rental_products_total,
                "sale_products": sale_products,
                "rental_products": rental_products,
            })
        messages.error(request, "Error Adding to Cart")
        return redirect('main:cart')

    def post(self, request, *args, **kwargs):
        if self.action == 'update':
            cart_item = get_object_or_404(Cart, id=self.item_id, user=request.user)
            new_quantity = int(request.POST.get('quantity', 1))
            if new_quantity > 0:
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                cart_item.delete()
            messages.success(request, "Cart Successfully updated")
            return redirect('main:cart')
        messages.error(request, "Cart Operation Failed")
        return redirect('main:cart')


class CheckoutView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    required_roles = "user"
    template_name = "main/checkout.html"

    def get_context_data(self, **kwargs):
        context = super(CheckoutView, self).get_context_data(**kwargs)
        category = self.kwargs.get('category')
        cart_items = Cart.objects.filter(user=self.request.user, product__category=category)

        if category == ProductCategory.PRODUCT:
            qs = cart_items.annotate(
                item_total=ExpressionWrapper(
                    F('quantity') * F('product__price'),
                    output_field=DecimalField()
                )
            )
            total = qs.aggregate(total_cost=Sum('item_total'))['total_cost'] or 0
        else:
            total = self.request.GET.get('total_amount', 0)

        context['cart_items'] = cart_items
        context['total'] = total
        return context

    def post(self, request, *args, **kwargs):
        category = self.kwargs.get('category')
        print(request.POST)
        form = OrderForm(request.POST)
        cart_items = Cart.objects.filter(user=request.user, product__category=category)

        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    order.user = request.user
                    order.save()

                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.price
                        )

                    cart_items.delete()

                    if category == ProductCategory.RENTING:
                        rental = get_object_or_404(RentalRequest, id=self.request.GET.get('rental_request_id'))
                        rental.order = order
                        rental.save()

                    if order.payment_method == PaymentChoices.KHALTI:
                        khalti_initiate_url = f'{os.getenv("KHALTI_API_ENDPOINT")}epayment/initiate/'
                        user = self.request.user

                        current_user = get_object_or_404(CustomUser, id=user.id)
                        if self.request.user.is_authenticated:
                            payload = json.dumps({
                                "return_url": f'http://localhost:8000{reverse("main:checkout_success")}',
                                "website_url": "http://localhost:800",
                                "amount": f"{order.total_amount}",
                                "purchase_order_id": order.id or "Order1",
                                "purchase_order_name": order.name or "Order 1",
                                "customer_info": {
                                    "name": current_user.get_full_name,
                                    "email": current_user.email or "test@khalti.com",
                                    "phone": current_user.phone or "9800000001"
                                }
                            })

                            headers = {
                                'Authorization': f'key {os.getenv("KHALTI_LIVE_SECRET_KEY")}',
                                'Content-Type': 'application/json',
                            }

                            response = requests.request("POST", khalti_initiate_url, headers=headers, data=payload)
                            data = response.json()

                            messages.success(request, "Order successfully placed, enjoy shopping...")
                            return redirect(data["payment_url"])

                    messages.success(request, "Order successfully placed, enjoy shopping...")
                    return redirect(f"{reverse('main:checkout_success')}?order_id={order.id}")
            except Exception as e:
                messages.error(request, "There was an error processing your order.")
                return redirect('main:checkout', category)
        else:
            messages.error(request, "Invalid Order Request")
            return redirect('main:checkout', category)


class CheckoutSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "main/success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pidx = self.request.GET.get('pidx')

        if pidx:
            transaction_id = self.request.GET.get('transaction_id')
            transaction_amount = self.request.GET.get('total_amount')
            status = self.request.GET.get('status')
            order_id = self.request.GET.get('purchase_order_id')
            order = get_object_or_404(Order, id=order_id)

            if status and status.lower() == TransactionStatus.COMPLETED:
                order.is_paid = True
            else:
                order.is_paid = False
            order.save()

            try:
                Transaction.objects.create(
                    transaction_id=transaction_id,
                    status=status.lower() if status else '',
                    total_amount=Decimal(transaction_amount),
                    order=order,
                    pidx=pidx,
                )
            except Exception as e:
                print(f"Transaction save error: {e}")
        else:
            order_id = self.request.GET.get('order_id')
            order = get_object_or_404(Order, id=order_id)

        context.update({
            "order": order,
        })
        return context

# Errors
def error_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)
