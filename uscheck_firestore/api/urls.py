from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('query/', views.process_query, name='query'),
    path('business/', views.view_business, name='business'),
    path('qr/generate/', views.qr_generate_request, name='qr_generate_request'),
    path('qr/generate/pubsub/', views.qr_get_url, name='generate_qr_pubsub'),
]
