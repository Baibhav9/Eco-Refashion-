from django.urls import path, include
from . import views
from .views import IndexView, ProductsView, SellerUploadView, SellerProductListView, AdminProductApprovalView, \
    AdminConfirmProduct, UploadClothView, UserDashboardView, CartView, ProductRentListView, CheckoutView

app_name = 'main'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('products/', ProductsView.as_view(), name='product'),
    path('donate/', views.donate_view, name='donate'),
    path('recycle/', views.recycle_view, name='recycle'),
    path('thrift/', views.thrift_view, name='thrift'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/<str:action>/', CartView.as_view(), name='cart_action'),
    path('cart/<str:action>/<int:item_id>/', CartView.as_view(), name='cart_action_with_id'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('user/dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    path('accounts/', include('accounts.urls')),
    path('rent/<int:item_id>/', views.rent_item, name='rent_item'),
    path('user/upload/recycle/', UploadClothView.as_view(), {'upload_type': 'recycle'}, name='user_upload_recycle'),
    path('user/upload/thrift/', UploadClothView.as_view(), {'upload_type': 'thrift'}, name='user_upload_thrift'),
    path('user/upload/donate/', UploadClothView.as_view(), {'upload_type': 'donation'}, name='user_upload_donate'),
    path('rent_item/<int:item_id>/', views.rent_item, name='rent_item'),
    path('rental_pending/', views.rental_pending, name='rental_pending'),
    
    # Organization Dashboard URLs
    path('org/dashboard/', views.organization_dashboard, name='organization_dashboard'),
    path('org/confirm/<int:upload_id>/', views.confirm_cloth_upload, name='confirm_cloth_upload'),

    # Seller Dashboard URLs
    path('seller/upload/', SellerUploadView.as_view(), name='seller_upload_product'),
    path('seller/products/', SellerProductListView.as_view(), name='seller_product_list'),

    # Admin Dashboard URLs (removed duplicate confirm path)
    path('admin-dashboard/product-approval/', AdminProductApprovalView.as_view(), name='admin_product_approval'),
    path('admin-dashboard/confirm/<int:product_id>/', AdminConfirmProduct.as_view(), name='confirm_product'),
    path('admin-dashboard/cart-list/', views.admin_cart_list, name='admin_cart_list'),    
    path('rental-approval/', views.admin_approval, name='admin_rental_approval'),  
      
    # Public product list and renting views (available to all users)
    path('products/', views.product_list, name='product_list'),
    path('renting/', ProductRentListView.as_view(), name='renting'),
]