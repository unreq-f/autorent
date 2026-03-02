from django.contrib import admin
from .models import Car, Booking, ClientProfile, Fine, Payment, Wishlist

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['brand','model','plate','car_class','status','price_base','is_featured']
    list_filter = ['car_class','status','fuel']
    search_fields = ['brand','model','plate']
    list_editable = ['status','is_featured']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['number','user','car','date_from','date_to','status','total_price','created_at']
    list_filter = ['status','tariff']
    search_fields = ['number','user__username','car__brand']
    list_editable = ['status']

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['user','phone','segment','discount_pct','booking_count']
    list_filter = ['segment']
    search_fields = ['user__username','user__first_name','user__last_name','phone']

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['number','booking','fine_type','severity','amount','status','created_at']
    list_filter = ['status','severity','fine_type']
    list_editable = ['status']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id','booking','payment_type','method','amount','status','created_at']
    list_filter = ['status','payment_type','method']

admin.site.register(Wishlist)
