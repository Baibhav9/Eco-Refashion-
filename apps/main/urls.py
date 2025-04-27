from django.urls import path, include

from . import views
from .constants import ProductCategory
from .views import IndexView, ProductsView, UserDashboardView, CartView, CheckoutView, RentalRequestView, \
    ProductDetailView, OrderListView, \
    ProductCategoryListView, ProductCategoryCreateView, ProductCategoryDeleteView, ProductCategoryUpdateView, \
    ProductApproveView, CheckoutSuccessView, RentalRequestListView

app_name = 'main'

product_paths = [
    path('products/<str:category>/', ProductsView.as_view(), name='products'),
    path("products/detail/<int:id>", ProductDetailView.as_view(), name='product_detail'),
    path("products/<str:category>/delete/<int:id>", ProductCategoryDeleteView.as_view(), name='product_delete'),
    path("products/<str:category>/edit/<int:id>", ProductCategoryUpdateView.as_view(), name='product_edit'),
]

dashboard_paths = [
    path('dashboard', UserDashboardView.as_view(), name='dashboard'),
    path("dashboard/orders", OrderListView.as_view(), name='orders'),
    path("dashboard/create/<str:category>", ProductCategoryCreateView.as_view(), name='create'),
    path("dashboard/<str:category>/", ProductCategoryListView.as_view(), name="product_by_category"),
    path("dashboard/product/approve/<int:id>", ProductApproveView.as_view(), name='product_approve'),
    path("dashboard/rental-requests", RentalRequestListView.as_view(), name='user_rental_requests'),
]

cart_paths = [
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/<str:action>/', CartView.as_view(), name='cart_action'),
    path('cart/<str:action>/<int:item_id>/', CartView.as_view(), name='cart_action_with_id'),
    path('checkout/<str:category>', CheckoutView.as_view(), name='checkout'),
    path('order/checkout/success', CheckoutSuccessView.as_view(), name='checkout_success'),
]

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('accounts/', include('apps.accounts.urls')),
    path('rental/request', RentalRequestView.as_view(), name='rental_request'),
]

urlpatterns += product_paths
urlpatterns += dashboard_paths
urlpatterns += cart_paths