from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard, name='manager_dashboard'),
    path('bookings/', views.bookings, name='manager_bookings'),
    path('bookings/<int:pk>/edit/', views.booking_edit, name='manager_booking_edit'),
    path('bookings/<int:pk>/status/', views.booking_status_update, name='manager_booking_status'),
    path('cars/', views.cars, name='manager_cars'),
    path('cars/add/', views.car_edit, name='manager_car_add'),
    path('cars/<int:pk>/edit/', views.car_edit, name='manager_car_edit'),
    path('clients/', views.clients, name='manager_clients'),
    path('clients/<int:pk>/edit/', views.client_edit, name='manager_client_edit'),
    path('payments/', views.payments, name='manager_payments'),
    path('fines/', views.fines, name='manager_fines'),
    path('fines/add/', views.fine_edit, name='manager_fine_add'),
    path('fines/<int:pk>/edit/', views.fine_edit, name='manager_fine_edit'),
    path('reports/', views.reports, name='manager_reports'),
]
