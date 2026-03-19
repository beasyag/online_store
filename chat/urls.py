from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('<int:conversation_id>/', views.conversation_detail, name='detail'),
    path('start/<slug:shop_slug>/', views.start_conversation, name='start'),
    path('<int:conversation_id>/send/', views.send_message, name='send'),
]