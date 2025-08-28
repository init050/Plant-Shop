from django.urls import path
from . import views


app_name = 'product_module'


urlpatterns = [
    # Product URLs
    path('', views.product_list, name='product_list'),
    path('search/', views.search_products, name='search_products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),

    # Cart URLs
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),

    # Order URLs
    path('checkout/', views.checkout, name='checkout'),
    path('order/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_history, name='order_history'),

    # Admin URLs
    path('admin/discount/create/<int:product_id>/', views.admin_discount_create, name='admin_discount_create'),

    # AJAX URLs
    path('ajax/add-to-cart/', views.ajax_add_to_cart, name='ajax_add_to_cart'),
    path('ajax/cart-count/', views.ajax_cart_count, name='ajax_cart_count'),
]