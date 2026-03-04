from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='core.Booking')
def sync_car_status(sender, instance, created, **kwargs):
    """
    Автоматично змінює статус автомобіля залежно від статусу замовлення:
      - active / paid / awaiting_payment / pending  → 'rented'  (У прокаті)
      - completed / cancelled                       → 'free'    (Вільний)
    
    Виняток: якщо авто вже має статус 'service' або 'broken' —
    не повертаємо до 'free' при завершенні/скасуванні.
    """
    car = instance.car
    if car is None:
        return

    RENTED_STATUSES    = {'active', 'paid', 'awaiting_payment', 'pending'}
    FREE_STATUSES      = {'completed', 'cancelled'}
    PROTECTED_STATUSES = {'service', 'broken'}  # не чіпаємо

    booking_status = instance.status

    if booking_status in RENTED_STATUSES:
        if car.status != 'rented':
            car.status = 'rented'
            car.save(update_fields=['status'])

    elif booking_status in FREE_STATUSES:
        if car.status in PROTECTED_STATUSES:
            return  # авто на ТО чи несправне — не чіпаємо

        # Перевіряємо чи є інші активні замовлення на це авто
        from core.models import Booking
        has_active = Booking.objects.filter(
            car=car,
            status__in=RENTED_STATUSES,
        ).exclude(pk=instance.pk).exists()

        if not has_active and car.status != 'free':
            car.status = 'free'
            car.save(update_fields=['status'])