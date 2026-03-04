from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('cars/<int:pk>/', views.car_detail, name='car_detail'),
    path('conditions/', views.conditions, name='conditions'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('booking/', views.booking_quick, name='booking_quick'),
    path('order/', views.order, name='order'),
    path('order/<int:car_pk>/', views.order, name='order_car'),
    path('profile/', views.profile, name='profile'),
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('promo/check/', views.check_promo, name='check_promo'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
]