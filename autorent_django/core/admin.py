from django.contrib import admin
from .models import Car, CarPhoto, Booking, ClientProfile, Fine, Payment, Wishlist, PromoCode, ContactMessage

class CarPhotoInline(admin.TabularInline):
    model   = CarPhoto
    extra   = 3
    fields  = ['image', 'caption', 'order', 'is_main']
    ordering = ['order']


@admin.register(CarPhoto)
class CarPhotoAdmin(admin.ModelAdmin):
    list_display = ['car', 'caption', 'order', 'is_main']
    list_filter  = ['car', 'is_main']


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    inlines = [CarPhotoInline]
    list_display = ['brand','model','plate','car_class','status','price_base','is_featured', 'is_popular']
    list_filter = ['car_class','status','fuel']
    search_fields = ['brand','model','plate']
    list_editable = ['status','is_featured', 'is_popular']

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


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display  = ['code', 'discount_pct', 'is_active', 'valid_until', 'used_count', 'max_uses']
    list_editable = ['is_active']
    list_filter   = ['is_active']
    search_fields = ['code']
    readonly_fields = ['used_count', 'created_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter   = ['status', 'subject']
    list_editable = ['status']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['name','phone','email','subject','message','created_at']