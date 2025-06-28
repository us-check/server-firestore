from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('query/', views.process_query, name='query'),
    path('qr/', views.view_qr, name='qr'),
    path('business/', views.view_business, name='business'),
    
]
