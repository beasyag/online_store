from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('account-details/', views.account_details, name='account_details'),
    path('edit-account-details/', views.edit_account_details, name='edit_account_details'),
    path('update-account-details/', views.update_account_details, name='update_account_details'),
    path('order-history/', views.order_history, name='order_history'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('logout/', views.logout_view, name='logout'),
    path('orders/', views.order_history, name='order_history'),
    path('change-password/', views.change_password, name='change_password'),  # ← новое
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('addresses/', views.addresses_view, name='addresses'),  # ← новое
    path('addresses/add/', views.address_add, name='address_add'),  # ← новое
    path('addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),  # ← новое
    path('addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
]