from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('product/<slug:slug>/', views.add_product_review, name='add_product_review'),
    path('seller/<slug:shop_slug>/', views.add_seller_review, name='add_seller_review'),
    path('<int:review_id>/delete/', views.delete_review, name='delete_review'),
]