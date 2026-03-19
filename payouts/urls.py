from django.urls import path
from . import views

app_name = 'payouts'

urlpatterns = [
    path('', views.payout_list, name='list'),
    path('request/', views.request_payout, name='request'),
]