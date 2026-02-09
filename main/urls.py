from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('catalog/<slug:catalog_slug>/', views.CatalogView.as_view(), name='catalog'),
    path('catalog/', views.CatalogView.as_view(), name='catalog_all'),
    path('product/<slug;slug>', views.ProductDetailView.as_view(), name='product_detail'),
]
