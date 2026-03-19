from django.urls import path
from . import views

app_name = 'sellers'

urlpatterns = [
    path('register/', views.seller_register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='products'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<slug:slug>/edit/', views.product_edit, name='product_edit'),
    path('products/<slug:slug>/delete/', views.product_delete, name='product_delete'),
    path('orders/', views.order_list, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('analytics/', views.analytics, name='analytics'),
    path('<slug:shop_slug>/', views.shop_page, name='shop'),
]