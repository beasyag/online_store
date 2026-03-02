from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('stripe/webhook/', views.stripe_webhook, name='stripe-webhook'),
    path('stripe/success/', views.stripe_success, name='stripe-success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe-cancel'),
]