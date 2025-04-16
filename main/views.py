from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from .models import ClothUpload, Cart, SellerProduct, RentalRequest, CartItem
from accounts.decorators import role_required
from .forms import SellerProductForm, ClothUploadForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

# Index view
def index_view(request):
    return render(request, 'index.html') 

# Product view (show only approved products)
def product_view(request):
    """Show only APPROVED products with category='product'"""
    products = SellerProduct.objects.filter(
        status='approved',
        category='product'  # Only show normal products
    ).order_by('-created_at')
    return render(request, 'product.html', {'products': products})

# Donate view
def donate_view(request):
    return render(request, 'donate.html')

# Recycle view
def recycle_view(request):
    return render(request, 'recycle.html')

# Thrift view
def thrift_view(request):
    return render(request, 'thrift.html')

# Renting view (show only approved rentable items)
def renting_view(request):
    """Show only APPROVED products with category='renting'"""
    rent_items = SellerProduct.objects.filter(
        status='approved',
        category='renting'  # Only show rental items
    ).order_by('-created_at')
    return render(request, 'renting.html', {'rent_items': rent_items})

# Rental pending view (shown to user after they request a rental)
def rental_pending(request):
    return render(request, 'rental_pending.html')

# Cart view
def cart_view(request):
    return render(request, 'cart.html')

# User dashboard view (show pending uploads)
def user_dashboard(request):
    uploads = ClothUpload.objects.filter(user=request.user, status='pending')
    return render(request, 'user_dashboard.html', {'uploads': uploads})

# Product page (show only approved items)
def product_page(request):
    products = ClothUpload.objects.filter(status='approved') 
    return render(request, 'products.html', {'products': products})

def admin_thrift_recycle_list(request):
    thrift_recycle_items = RentalRequest.objects.filter(status='pending')
    return render(request, 'admin_thrift_recycle_list.html', {'thrift_recycle_items': thrift_recycle_items})

# Rent item view (user submits a rental request)
@login_required
def rent_item(request, item_id):
    item = get_object_or_404(ClothUpload, id=item_id)
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
    cloth_uploads = ClothUpload.objects.filter(upload_type='donation', status='pending')
    return render(request, 'donations_list.html', {'cloth_uploads': cloth_uploads})

# Admin approve clothes view
@role_required(allowed_roles=['admin'])
def admin_approve_clothes(request):
    cloth_uploads = ClothUpload.objects.filter(status='pending')
    return render(request, 'approve_clothes.html', {'cloth_uploads': cloth_uploads})

# Cloth upload view (user uploads cloth for donation, recycle, etc.)
def upload_cloth(request, upload_type):
    if request.method == 'POST':
        form = ClothUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cloth = form.save(commit=False)
            cloth.user = request.user
            cloth.upload_type = upload_type
            cloth.save()
            return redirect('user_dashboard') 
    else:
        form = ClothUploadForm()
    return render(request, 'upload_cloth.html', {'form': form, 'upload_type': upload_type})

# Admin approval view for each cloth upload
@staff_member_required
def approve_upload(request, upload_id):
    product = get_object_or_404(ClothUpload, id=upload_id)
    if request.method == 'POST':
        product.status = 'approved'
        product.save()
        return redirect('admin_product_approval')  
    return render(request, 'approve_upload.html', {'product': product})

# Organization dashboard for confirming donations and recycled clothes
def organization_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'organization':
        raise PermissionDenied("You are not authorized to view this page.")
    cloth_uploads = ClothUpload.objects.filter(upload_type__in=['donation', 'recycle'], status='pending').order_by('-created_at')
    context = {'cloth_uploads': cloth_uploads}
    return render(request, 'organization_dashboard.html', context)

# Organization confirms the donation or recycled items
def confirm_cloth_upload(request, upload_id):
    if not request.user.is_authenticated or request.user.role != 'organization':
        raise PermissionDenied("You are not authorized to perform this action.")
    cloth = get_object_or_404(ClothUpload, id=upload_id)
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
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

# Remove item from the cart
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    cart_item.delete() 
    return redirect('user_cart')

# Update cart quantity
def update_cart_quantity(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    if request.method == 'POST':
        new_quantity = int(request.POST['quantity'])
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('user_cart')

# Display user's uploaded products
def seller_upload_product(request):
    if not request.user.is_authenticated or request.user.role != 'seller':
        raise PermissionDenied("Only sellers can upload products.")
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
    return render(request, 'seller_upload_product.html', {'form': form})

# Seller's product list view
def seller_product_list(request):
    if not request.user.is_authenticated or request.user.role != 'seller':
        raise PermissionDenied("Only sellers can view this page.")
    products = SellerProduct.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'seller_product_list.html', {'products': products})

# Admin product approval view
@staff_member_required
def admin_product_approval(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        raise PermissionDenied("Only admins can access this page.")
    pending_products = SellerProduct.objects.filter(status='pending').order_by('-created_at')
    context = {'pending_products': pending_products}
    return render(request, 'admin_product_approval.html', context)

# Admin approves a product
def confirm_product(request, product_id):
    product = get_object_or_404(SellerProduct, id=product_id)
    if request.method == 'POST':
        product.status = 'confirmed'  # Change to match the filter in product_list()
        product.save()
    return redirect('admin_product_approval')

# Product list view for confirmed products
def product_list(request):
    products = ClothUpload.objects.filter(
        upload_type='product',
        status='confirmed'  # or 'approved'
    ).order_by('-created_at')
    approved_products = products.filter(status='confirmed')  # Additional filtering if needed
    return render(request, 'product.html', {
        'products': products,
        'approved_products': approved_products
    })

# Renting list view for confirmed renting items
def renting_list(request):
    approved_rents = ClothUpload.objects.filter(
        upload_type='renting', 
        status='confirmed'
    ).order_by('-created_at')
    context = {'rent_items': approved_rents}
    return render(request, 'renting.html', context)

# Add item to cart for users
def add_to_cart(request, product_id):
    product = get_object_or_404(ClothUpload, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('user_cart')

def admin_cart_list(request):
    cart_items = CartItem.objects.all()  
    return render(request, 'admin_cart_list.html', {'cart_items': cart_items})