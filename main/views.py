from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, When, Q, BooleanField, Value, ExpressionWrapper
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, View

from .constants import ProductApprovalStatus, UserProductCategory, SellerProductCategory
from .models import UserProduct, Cart, SellerProduct, RentalRequest, Product, OrderItem
from accounts.decorators import role_required
from .forms import SellerProductForm, UserProductForm, OrderForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

from django.core.exceptions import PermissionDenied
from django.db.models import Sum, F, DecimalField
from django.db import transaction


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
    template_name = "index.html"


# Product view (show only approved products)
class ProductsView(TemplateView):
    """Show only APPROVED products with category='product'"""
    template_name = "main/products.html"

    def get_context_data(self, **kwargs):
        context = super(ProductsView, self).get_context_data(**kwargs)
        products = SellerProduct.objects.filter(
            status="Approved",
            category='Product',
        ).order_by('-created_at')

        print(products)

        context.update({
            'products': products,
        })

        return context


# Donate view
def donate_view(request):
    return render(request, 'donate.html')


# Recycle view
def recycle_view(request):
    return render(request, 'recycle.html')


# Thrift view
def thrift_view(request):
    return render(request, 'thrift.html')


# Rental pending view (shown to user after they request a rental)
def rental_pending(request):
    return render(request, 'rental_pending.html')


# User dashboard view (show pending uploads)
class UserDashboardView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = UserProduct
    template_name = "main/user_dashboard.html"
    required_roles = "user"

    def get_queryset(self):
        queryset = UserProduct.objects.all()
        return queryset


# Product page (show only approved items)
def product_page(request):
    products = UserProduct.objects.filter(status='approved')
    return render(request, 'main/products.html', {'products': products})


def admin_thrift_recycle_list(request):
    thrift_recycle_items = RentalRequest.objects.filter(status='pending')
    return render(request, 'admin_thrift_recycle_list.html', {'thrift_recycle_items': thrift_recycle_items})


# Rent item view (user submits a rental request)
@login_required
def rent_item(request, item_id):
    item = get_object_or_404(UserProduct, id=item_id)
    if item.status == 'approved' and item.is_rentable:
        rental_request = RentalRequest.objects.create(user=request.user, cloth_item=item)
        return redirect('rental_pending')  # Redirect to rental pending page
    return redirect('renting_page')  # Redirect back if item is not rentable or approved


# Seller's upload clothes for product view
@role_required(allowed_roles=['seller'])
def upload_clothes_for_product(request):
    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.status = 'pending'  # status is pending until admin approval
            product.save()
            return redirect('seller_product_list')
    else:
        form = SellerProductForm()
    return render(request, 'upload_clothes.html', {'form': form})


# Organization view for donations
@role_required(allowed_roles=['organization'])
def org_view_donations(request):
    cloth_uploads = UserProduct.objects.filter(upload_type='donation', status='pending')
    return render(request, 'donations_list.html', {'cloth_uploads': cloth_uploads})


# Admin approve clothes view
@role_required(allowed_roles=['admin'])
def admin_approve_clothes(request):
    cloth_uploads = UserProduct.objects.filter(status='pending')
    return render(request, 'approve_clothes.html', {'cloth_uploads': cloth_uploads})


# Cloth upload view (user uploads cloth for donation, recycle, etc.)
class UploadClothView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    required_roles = "user"
    model = UserProduct
    form_class = UserProductForm
    template_name = "main/upload_cloth.html"

    def dispatch(self, request, *args, **kwargs):
        self.upload_type = kwargs.get('upload_type')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        cloth = form.save(commit=False)
        cloth.user = self.request.user
        cloth.upload_type = self.upload_type
        cloth.save()
        return redirect('main:user_dashboard')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upload_type'] = self.upload_type
        return context


# Admin approval view for each cloth upload
@staff_member_required
def approve_upload(request, upload_id):
    product = get_object_or_404(UserProduct, id=upload_id)
    if request.method == 'POST':
        product.status = 'approved'
        product.save()
        return redirect('admin_product_approval')
    return render(request, 'approve_upload.html', {'product': product})


# Organization dashboard for confirming donations and recycled clothes
def organization_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'organization':
        raise PermissionDenied("You are not authorized to view this page.")
    cloth_uploads = UserProduct.objects.filter(category__in=[UserProductCategory.DONATION, UserProductCategory.RECYCLE], status='pending').order_by(
        '-created_at')
    print(cloth_uploads)
    context = {'cloth_uploads': cloth_uploads}
    return render(request, 'organization_dashboard.html', context)


# Organization confirms the donation or recycled items
def confirm_cloth_upload(request, upload_id):
    if not request.user.is_authenticated or request.user.role != 'organization':
        raise PermissionDenied("You are not authorized to perform this action.")
    cloth = get_object_or_404(UserProduct, id=upload_id)
    if request.method == 'POST':
        cloth.status = 'confirmed'
        cloth.save()
    return redirect('organization_dashboard')


@staff_member_required
def admin_approval(request):
    pending_rentals = RentalRequest.objects.filter(status='pending')
    if request.method == 'POST':
        rental_id = request.POST.get('rental_id')
        action = request.POST.get('action')
        if rental_id and action:
            try:
                rental_request = RentalRequest.objects.get(id=rental_id)
                if action == 'approve':
                    rental_request.status = 'approved'
                elif action == 'reject':
                    rental_request.status = 'rejected'
                rental_request.save()
                return redirect('admin_rental_approval')
            except RentalRequest.DoesNotExist:
                return redirect('admin_rental_approval')
    return render(request, 'admin_approval_list.html', {'pending_rentals': pending_rentals})


# Cart view for users
def user_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.get_total_price() for item in cart_items)
    return render(request, 'main/cart.html', {'cart_items': cart_items, 'total': total})


# Display user's uploaded products
class SellerUploadView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    template_name = "main/seller_upload_product.html"
    model = SellerProduct
    form_class = SellerProductForm
    required_roles = "seller"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = SellerProductForm()
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        form = SellerProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.state = "pending"
            product.save()
            return redirect('main:seller_product_list')
        else:
            return self.render_to_response(self.get_context_data())


# Seller's product list view
class SellerProductListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = SellerProduct
    required_roles = "seller"
    template_name = "main/seller_product_list.html"

    def get_queryset(self):
        qs = SellerProduct.objects.filter(user=self.request.user).order_by('-created_at')
        return qs


# Admin product approval view
class AdminProductApprovalView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    required_roles = "admin"
    model = SellerProduct
    template_name = "main/admin_product_approval.html"

    def get_queryset(self):
        qs = SellerProduct.objects.annotate(
            is_pending=Case(
                When(status=ProductApprovalStatus.PENDING, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('-is_pending', '-created_at')
        return qs


# Admin approves a product
class AdminConfirmProduct(LoginRequiredMixin, RoleRequiredMixin, View):
    required_roles = "admin"
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        product = get_object_or_404(SellerProduct, id=product_id)
        product.status = ProductApprovalStatus.APPROVED
        product.save()
        return redirect('main:admin_product_approval')


# Product list view for confirmed products
class ProductListView(ListView):
    model = Product


def product_list(request):
    products = UserProduct.objects.filter(
        upload_type='product',
        status='confirmed'  # or 'approved'
    ).order_by('-created_at')
    approved_products = products.filter(status='confirmed')  # Additional filtering if needed
    return render(request, 'main/products.html', {
        'products': products,
        'approved_products': approved_products
    })


# Renting list view for confirmed renting items
class ProductRentListView(ListView):
    model = Product
    template_name = "main/renting.html"

    def get_queryset(self):
        qs = SellerProduct.objects.filter(
            category=SellerProductCategory.RENTING,
            status=ProductApprovalStatus.APPROVED
        ).order_by('-created_at')
        return qs


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
                product = SellerProduct.objects.get(id=product_id)
                cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()

                messages.success(request, "Successfully added to cart")
                return redirect('main:product')

            except SellerProduct.DoesNotExist:
                messages.error(request, "Error Adding to Cart")
                return redirect('main:product')

        elif self.action == 'remove':
            cart_item = get_object_or_404(Cart, id=self.item_id, user=request.user)
            cart_item.delete()
            messages.success(request, 'Product removed from cart')
            return redirect("main:cart")

        if self.action is None:
            qs = Cart.objects.filter(user=self.request.user)
            qs = qs.annotate(
                item_total=ExpressionWrapper(
                    F('quantity') * F('product__price'),
                    output_field=DecimalField()
                )
            )
            total = qs.aggregate(total_cost=Sum('item_total'))['total_cost'] or 0
            return render(request, 'main/cart.html', {
                "object_list": qs,
                "total": total,
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
        cart_items = Cart.objects.filter(user=self.request.user)
        qs = cart_items.annotate(
            item_total=ExpressionWrapper(
                F('quantity') * F('product__price'),
                output_field=DecimalField()
            )
        )
        total = qs.aggregate(total_cost=Sum('item_total'))['total_cost'] or 0
        context['cart_items'] = cart_items
        context['total'] = total
        return context

    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST)
        cart_items = Cart.objects.filter(user=request.user)
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
                    messages.success(request, "Order successfully placed, enjoy shopping...")
                    return redirect('main:product')
            except Exception as e:
                messages.error(request, "There was an error processing your order.")
                return redirect('main:checkout')
        else:
            messages.error(request, "Invalid Order Request")
            return redirect('main:checkout')


def admin_cart_list(request):
    cart_items = Cart.objects.all()
    return render(request, 'admin_cart_list.html', {'cart_items': cart_items})
