from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register(), name='register'),
    path('login/', views.login_view(), name='login'),
    path('logout/', views.logout_view(), name='logout'),
    path('profile/', views.profile_view(), name='profile'),
    path('accounts-details/', views.account_details(), name='account_details'),
    path('edit-accounts-details/', views.edit_account_details(), name='edit_account_details'),
    path('update-accounts-details/', views.update_account_details(), name='update_account_details'),

]