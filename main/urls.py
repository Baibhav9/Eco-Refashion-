from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index_view, name='index'),
    path('products/', views.product_view, name='product'), 
    path('donate/', views.donate_view, name='donate'),
    path('recycle/', views.recycle_view, name='recycle'),
    path('thrift/', views.thrift_view, name='thrift'),
    path('renting/', views.renting_view, name='renting'),
    path('cart/', views.cart_view, name='cart'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('accounts/', include('accounts.urls')),
    path('rent/<int:item_id>/', views.rent_item, name='rent_item'),
    path('cart/', views.user_cart, name='user_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('user/upload/recycle/', views.upload_cloth, {'upload_type': 'recycle'}, name='user_upload_recycle'),
    path('user/upload/thrift/', views.upload_cloth, {'upload_type': 'thrift'}, name='user_upload_thrift'),
    path('user/upload/donate/', views.upload_cloth, {'upload_type': 'donation'}, name='user_upload_donate'),
    path('rent_item/<int:item_id>/', views.rent_item, name='rent_item'),
    path('rental_pending/', views.rental_pending, name='rental_pending'),
    
    # Organization Dashboard URLs
    path('org/dashboard/', views.organization_dashboard, name='organization_dashboard'),
    path('org/confirm/<int:upload_id>/', views.confirm_cloth_upload, name='confirm_cloth_upload'),

    # Seller Dashboard URLs
    path('seller/upload/', views.seller_upload_product, name='seller_upload_product'),
    path('seller/products/', views.seller_product_list, name='seller_product_list'),

    # Admin Dashboard URLs (removed duplicate confirm path)
    path('admin-dashboard/product-approval/', views.admin_product_approval, name='admin_product_approval'),
    path('admin-dashboard/confirm/<int:product_id>/', views.confirm_product, name='confirm_product'),
    path('admin-dashboard/cart-list/', views.admin_cart_list, name='admin_cart_list'),    
    path('rental-approval/', views.admin_approval, name='admin_rental_approval'),  
      
    # Public product list and renting views (available to all users)
    path('products/', views.product_list, name='product_list'),
    path('renting/', views.renting_list, name='renting_list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)