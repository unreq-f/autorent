from django.db import models
from django.contrib.auth.models import User
import random, string

def gen_id(prefix, length=4):
    return f"{prefix}-{''.join(random.choices(string.digits, k=length))}"

class Car(models.Model):
    CAR_CLASSES = [('economy','Економ'),('comfort','Комфорт'),('business','Бізнес'),('vip','VIP'),('crossover','Кросовер'),('minivan','Мінівен'),('electric','Електро')]
    FUELS = [('petrol','Бензин'),('diesel','Дизель'),('electric','Електро'),('hybrid','Гібрид')]
    STATUSES = [('free','Вільний'),('rented','У прокаті'),('service','На ТО'),('broken','Несправний')]

    brand = models.CharField('Марка', max_length=50)
    model = models.CharField('Модель', max_length=100)
    year = models.IntegerField('Рік', default=2023)
    car_class = models.CharField('Клас', max_length=20, choices=CAR_CLASSES, default='comfort')
    fuel = models.CharField('Паливо', max_length=20, choices=FUELS, default='petrol')
    transmission = models.CharField('КПП', max_length=30, default='Автомат')
    seats = models.IntegerField('Місць', default=5)
    engine = models.CharField('Двигун', max_length=40, blank=True)
    drive = models.CharField('Привід', max_length=20, default='Передній')
    color = models.CharField('Колір', max_length=30, default='Чорний')
    plate = models.CharField('Держ. номер', max_length=20, unique=True)
    mileage = models.IntegerField('Пробіг км', default=0)
    price_base = models.DecimalField('Base USD/доба', max_digits=8, decimal_places=2, default=50)
    price_prime = models.DecimalField('Prime USD/доба', max_digits=8, decimal_places=2, default=70)
    deposit = models.DecimalField('Застава USD', max_digits=8, decimal_places=2, default=1500)
    status = models.CharField('Статус', max_length=20, choices=STATUSES, default='free')
    next_service = models.DateField('Наступне ТО', null=True, blank=True)
    description = models.TextField('Опис', blank=True)
    features = models.TextField('Особливості (через кому)', blank=True)
    image = models.ImageField('Фото', upload_to='cars/', blank=True, null=True)
    emoji = models.CharField('Емодзі', max_length=8, default='🚗')
    is_featured = models.BooleanField('На головній', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Автомобіль'
        verbose_name_plural = 'Автомобілі'
        ordering = ['car_class', 'brand']

    def __str__(self): return f'{self.brand} {self.model} ({self.plate})'

    @property
    def full_name(self): return f'{self.brand} {self.model}'

    @property
    def features_list(self): return [f.strip() for f in self.features.split(',') if f.strip()]

    @property
    def is_available(self): return self.status == 'free'

    def get_class_display_custom(self):
        return dict(self.CAR_CLASSES).get(self.car_class, self.car_class)

    def get_status_display_custom(self):
        return dict(self.STATUSES).get(self.status, self.status)


class ClientProfile(models.Model):
    SEGMENTS = [('new','Новий'),('regular','Постійний'),('vip','VIP'),('blocked','Заблокований')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    birth_date = models.DateField('Дата народження', null=True, blank=True)
    city = models.CharField('Місто', max_length=100, blank=True)
    address = models.CharField('Адреса', max_length=200, blank=True)
    driver_license = models.CharField('ВП', max_length=20, blank=True)
    experience_years = models.IntegerField('Стаж (років)', default=0)
    segment = models.CharField('Сегмент', max_length=10, choices=SEGMENTS, default='new')
    discount_pct = models.IntegerField('Знижка %', default=0)
    manager_note = models.TextField('Нотатка менеджера', blank=True)

    def __str__(self): return f'Профіль: {self.user}'

    @property
    def initials(self):
        fn, ln = self.user.first_name, self.user.last_name
        return f'{fn[:1]}{ln[:1]}'.upper() if fn and ln else self.user.username[:2].upper()

    @property
    def total_spent(self):
        return sum(float(b.total_price) for b in self.user.bookings.filter(status='completed'))

    @property
    def booking_count(self):
        return self.user.bookings.count()

    def get_segment_display_custom(self):
        return dict(self.SEGMENTS).get(self.segment, self.segment)


class Booking(models.Model):
    STATUSES = [('pending','Очікує'),('active','Активне'),('completed','Завершено'),('cancelled','Скасовано')]
    TARIFFS = [('base','Base (зі заставою)'),('prime','Prime (без застави)')]
    PAYMENTS = [('card','Картка'),('cash','Готівка'),('bank','Безготівковий')]
    PICKUPS = [('office','Офіс, вул. Клочківська, 94а'),('airport','Аеропорт «Харків»'),('station','Залізничний вокзал'),('delivery','Доставка по місту')]

    number = models.CharField('Номер', max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    date_from = models.DateField('Від')
    date_to = models.DateField('До')
    time_from = models.TimeField('Час', default='10:00')
    pickup_location = models.CharField('Місце', max_length=10, choices=PICKUPS, default='office')
    tariff = models.CharField('Тариф', max_length=10, choices=TARIFFS, default='base')
    payment_method = models.CharField('Оплата', max_length=10, choices=PAYMENTS, default='card')
    status = models.CharField('Статус', max_length=20, choices=STATUSES, default='pending')
    extra_gps = models.BooleanField('GPS', default=False)
    extra_child_seat = models.BooleanField('Дитяче крісло', default=False)
    extra_wifi = models.BooleanField('Wi-Fi', default=False)
    extra_driver = models.BooleanField('Доп. водій', default=False)
    extra_tire = models.BooleanField('Захист шин', default=False)
    extra_green_card = models.BooleanField('Зелена картка', default=False)
    total_price = models.DecimalField('Сума USD', max_digits=10, decimal_places=2, default=0)
    deposit_amount = models.DecimalField('Застава USD', max_digits=10, decimal_places=2, default=0)
    manager_note = models.TextField('Нотатка', blank=True)
    promo_code = models.CharField('Промокод', max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']

    def __str__(self): return f'{self.number}'

    @property
    def days(self):
        d = (self.date_to - self.date_from).days
        return max(d, 1)

    def calculate_price(self):
        daily = float(self.car.price_prime if self.tariff == 'prime' else self.car.price_base)
        total = daily * self.days
        if self.extra_gps: total += 5 * self.days
        if self.extra_child_seat: total += 5 * self.days
        if self.extra_wifi: total += 8 * self.days
        if self.extra_tire: total += 10 * self.days
        if self.extra_green_card: total += 15
        return round(total, 2)

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = f'AR-2025-{random.randint(1000,9999)}'
        if not self.total_price:
            self.total_price = self.calculate_price()
        if self.tariff == 'base' and not self.deposit_amount:
            self.deposit_amount = self.car.deposit
        super().save(*args, **kwargs)

    def get_status_display_custom(self):
        return dict(self.STATUSES).get(self.status, self.status)

    def get_pickup_display_custom(self):
        return dict(self.PICKUPS).get(self.pickup_location, self.pickup_location)


class Fine(models.Model):
    TYPES = [('late_return','Запізнення повернення'),('body_damage','Пошкодження кузову'),('interior_damage','Пошкодження салону'),('empty_tank','Неповний бак'),('accident','ДТП'),('traffic_fine','Штраф ДАІ'),('other','Інше')]
    SEVERITIES = [('low','Мінімальна'),('medium','Середня'),('high','Критична')]
    STATUSES = [('unpaid','Непогашений'),('paid','Сплачений'),('partial','Часткова'),('disputed','Оскаржується'),('waived','Скасований')]

    number = models.CharField('Номер', max_length=20, unique=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='fines')
    fine_type = models.CharField('Тип', max_length=30, choices=TYPES, default='other')
    severity = models.CharField('Серйозність', max_length=10, choices=SEVERITIES, default='medium')
    amount = models.DecimalField('Сума USD', max_digits=8, decimal_places=2)
    paid_amount = models.DecimalField('Сплачено USD', max_digits=8, decimal_places=2, default=0)
    status = models.CharField('Статус', max_length=10, choices=STATUSES, default='unpaid')
    description = models.TextField('Опис', blank=True)
    photo = models.ImageField('Фото', upload_to='fines/', blank=True, null=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_fines')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Штраф'
        verbose_name_plural = 'Штрафи'
        ordering = ['-created_at']

    def __str__(self): return f'{self.number}: {self.amount} USD'

    def save(self, *args, **kwargs):
        if not self.number:
            count = Fine.objects.count() + 1
            self.number = f'F-{count:03d}'
        super().save(*args, **kwargs)

    def get_type_display_custom(self):
        return dict(self.TYPES).get(self.fine_type, self.fine_type)

    def get_status_display_custom(self):
        return dict(self.STATUSES).get(self.status, self.status)

    def get_severity_display_custom(self):
        return dict(self.SEVERITIES).get(self.severity, self.severity)


class Payment(models.Model):
    TYPES = [('rental','Оренда'),('deposit','Застава'),('fine','Штраф'),('refund','Повернення')]
    STATUSES = [('success','Успішно'),('pending','Очікує'),('failed','Відхилено'),('refund','Повернення'),('deposit_held','Застава утримується'),('deposit_released','Застава звільнена')]
    METHODS = [('card','Картка'),('cash','Готівка'),('bank','Безготівковий')]

    transaction_id = models.CharField('ID', max_length=30, unique=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    fine = models.ForeignKey(Fine, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    payment_type = models.CharField('Тип', max_length=10, choices=TYPES, default='rental')
    method = models.CharField('Метод', max_length=10, choices=METHODS, default='card')
    amount = models.DecimalField('Сума USD', max_digits=10, decimal_places=2)
    status = models.CharField('Статус', max_length=20, choices=STATUSES, default='success')
    bank_ref = models.CharField('Банк. ID', max_length=50, blank=True)
    note = models.TextField('Примітка', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Платіж'
        verbose_name_plural = 'Платежі'
        ordering = ['-created_at']

    def __str__(self): return f'{self.transaction_id}: {self.amount} USD'

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f'TXN-{random.randint(1000,9999)}'
        super().save(*args, **kwargs)

    def get_status_display_custom(self):
        return dict(self.STATUSES).get(self.status, self.status)


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car')

    def __str__(self): return f'{self.user} → {self.car}'
