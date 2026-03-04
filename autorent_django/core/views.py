from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Car, CarPhoto, Booking, ClientProfile, Fine, Payment, Wishlist, PromoCode, ContactMessage
import re


def index(request):
    featured = Car.objects.filter(is_popular=True).prefetch_related('photos')[:6]
    classes = Car.CAR_CLASSES
    return render(request, 'core/index.html', {'featured': featured, 'classes': classes})


@ensure_csrf_cookie
def catalog(request):
    cars = Car.objects.filter(status__in=['free', 'rented'])

    # Multi-value checkboxes
    class_multi = request.GET.getlist('class_multi')
    fuel_multi  = request.GET.getlist('fuel_multi')
    tr_multi    = request.GET.getlist('tr_multi')
    seats_multi = request.GET.getlist('seats_multi')

    # Single-value
    q         = request.GET.get('q', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    year_min  = request.GET.get('year_min', '')
    year_max  = request.GET.get('year_max', '')
    status    = request.GET.get('status', '')
    sort      = request.GET.get('sort', '')

    if class_multi: cars = cars.filter(car_class__in=class_multi)
    if fuel_multi:  cars = cars.filter(fuel__in=fuel_multi)
    if tr_multi:    cars = cars.filter(transmission__in=tr_multi)
    if seats_multi: cars = cars.filter(seats__in=[int(s) for s in seats_multi if s.isdigit()])
    if q:           cars = cars.filter(Q(brand__icontains=q) | Q(model__icontains=q))
    if price_min:   cars = cars.filter(price_base__gte=price_min)
    if price_max:   cars = cars.filter(price_base__lte=price_max)
    if year_min:    cars = cars.filter(year__gte=year_min)
    if year_max:    cars = cars.filter(year__lte=year_max)
    if status:      cars = cars.filter(status=status)

    sort_map = {
        'price_asc': 'price_base', 'price_desc': '-price_base',
        'year_desc': '-year',      'year_asc':  'year',
        'name':      'brand',
    }
    if sort in sort_map:
        cars = cars.order_by(sort_map[sort])

    total_all = Car.objects.filter(status__in=['free','rented']).count()
    wishlist_ids = (
        list(Wishlist.objects.filter(user=request.user).values_list('car_id', flat=True))
        if request.user.is_authenticated else []
    )

    # Auto-mark popular
    from django.db.models import Count as DbCount
    Car.objects.filter(status__in=['free','rented']).annotate(bc=DbCount('bookings')).filter(bc__gte=50, is_popular=False).update(is_popular=True)
    all_transmissions = sorted(set(Car.objects.values_list('transmission', flat=True)))
    all_seats         = sorted(set(Car.objects.values_list('seats', flat=True)))
    years             = list(Car.objects.values_list('year', flat=True))
    year_range        = (min(years) if years else 2018, max(years) if years else 2025)

    filters = {
        'class_multi': class_multi, 'fuel_multi': fuel_multi,
        'tr_multi': tr_multi,       'seats_multi': seats_multi,
        'q': q, 'price_min': price_min, 'price_max': price_max,
        'year_min': year_min, 'year_max': year_max,
        'status': status, 'sort': sort,
    }
    return render(request, 'core/catalog.html', {
        'cars':              cars,
        'total':             cars.count(),
        'total_all':         total_all,
        'car_classes':       Car.CAR_CLASSES,
        'fuel_types':        Car.FUELS,
        'all_transmissions': all_transmissions,
        'all_seats':         all_seats,
        'year_range':        year_range,
        'wishlist_ids':      wishlist_ids,
        'filters':           filters,
    })


def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    similar = Car.objects.filter(car_class=car.car_class).exclude(pk=pk)[:4]
    in_wishlist = Wishlist.objects.filter(user=request.user, car=car).exists() if request.user.is_authenticated else False
    photos = list(car.photos.all())
    return render(request, 'core/car_detail.html', {'car': car, 'similar': similar, 'in_wishlist': in_wishlist, 'photos': photos})


def conditions(request):
    return render(request, 'core/conditions.html')


def about(request):
    return render(request, 'core/about.html')


def contacts(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name    = request.POST.get('name', '').strip(),
            phone   = request.POST.get('phone', '').strip(),
            email   = request.POST.get('email', '').strip(),
            subject = request.POST.get('subject', 'other'),
            message = request.POST.get('message', '').strip(),
        )
        messages.success(request, '✅ Повідомлення надіслано! Відповімо протягом години.')
        return redirect('contacts')
    return render(request, 'core/contacts.html')


def booking_quick(request):
    from datetime import date as date_cls
    import json

    # Mark popular: if bookings >= 50 or admin flag
    from django.db.models import Count as DbCount
    cars = Car.objects.filter(status='free', is_popular=True).annotate(
        bcount=DbCount('bookings')
    ).order_by('car_class', 'brand')
    # Auto-mark popular
    for c in cars:
        if c.bcount >= 50 and not c.is_popular:
            c.is_popular = True
            Car.objects.filter(pk=c.pk).update(is_popular=True)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'Для бронювання потрібно увійти в систему.')
            return redirect('auth')
        try:
            date_from = date_cls.fromisoformat(request.POST.get('date_from', ''))
            date_to   = date_cls.fromisoformat(request.POST.get('date_to', ''))
        except ValueError:
            messages.error(request, 'Вкажіть коректні дати оренди.')
            return redirect('booking_quick')
        today = date_cls.today()
        if date_from < today:
            messages.error(request, 'Дата отримання не може бути в минулому.')
            return redirect('booking_quick')
        if date_to <= date_from:
            messages.error(request, 'Дата повернення має бути пізніше дати отримання.')
            return redirect('booking_quick')
        car = get_object_or_404(Car, pk=request.POST.get('car'))
        pickup_loc = request.POST.get('pickup_location', 'office')
        delivery_address = request.POST.get('delivery_address', '').strip()
        if pickup_loc not in ('delivery', 'delivery_out'):
            delivery_address = ''
        booking = Booking.objects.create(
            user=request.user, car=car,
            date_from=date_from, date_to=date_to,
            pickup_location=pickup_loc,
            delivery_address=delivery_address,
            tariff=request.POST.get('tariff', 'base'),
            payment_method=request.POST.get('payment_method', 'card'),
            source='quick',
        )
        messages.success(request, f'🎉 Бронювання {booking.number} успішно створено!')
        return redirect('profile')

    # Build JSON for car preview
    def _car_main_photo(c):
        ph = c.photos.filter(is_main=True).first() or c.photos.first()
        if ph: return ph.image.url
        return c.image.url if c.image else ''

    cars_json = json.dumps([{
        'pk':      c.pk,
        'name':    c.full_name,
        'year':    c.year,
        'price':   float(c.price_base),
        'cls':     c.get_car_class_display(),
        'fuel':    c.get_fuel_display(),
        'seats':   c.seats,
        'emoji':   c.emoji,
        'image':   _car_main_photo(c),
        'popular': c.is_popular,
    } for c in cars])

    return render(request, 'core/booking_quick.html', {
        'cars': cars, 'pickups': Booking.PICKUPS, 'cars_json': cars_json
    })


@login_required
def order(request, car_pk=None):
    car = get_object_or_404(Car, pk=car_pk) if car_pk else None

    # Check if user has required documents
    docs_missing = False
    if request.user.is_authenticated:
        try:
            p = request.user.profile
            if not p.driver_license or not p.passport_number or not p.tax_id:
                docs_missing = True
        except Exception:
            docs_missing = True

    if request.method == 'POST':
        from datetime import date, time as time_cls
        car_id  = request.POST.get('car') or car_pk
        car_obj = get_object_or_404(Car, pk=car_id)

        try:
            date_from = date.fromisoformat(request.POST['date_from'])
            date_to   = date.fromisoformat(request.POST['date_to'])
        except (KeyError, ValueError):
            messages.error(request, 'Будь ласка, вкажіть коректні дати оренди.')
            return redirect(request.path)

        today = date.today()
        if date_from < today:
            messages.error(request, 'Дата отримання не може бути в минулому.')
            return redirect(request.path)
        if date_to <= date_from:
            messages.error(request, 'Дата повернення має бути пізніше дати отримання.')
            return redirect(request.path)

        pickup_loc = request.POST.get('pickup_location', 'office')
        delivery_address = request.POST.get('delivery_address', '').strip()
        if pickup_loc not in ('delivery', 'delivery_out'):
            delivery_address = ''

        return_loc = request.POST.get('return_location', 'office')
        return_address = request.POST.get('return_address', '').strip()
        if return_loc not in ('delivery', 'delivery_out'):
            return_address = ''

        time_from_str = request.POST.get('time_from', '10:00')
        time_to_str   = request.POST.get('time_to', '10:00')

        booking = Booking.objects.create(
            user=request.user, car=car_obj,
            date_from=date_from, date_to=date_to,
            time_from=time_from_str, time_to=time_to_str,
            pickup_location=pickup_loc, delivery_address=delivery_address,
            return_location=return_loc, return_address=return_address,
            tariff=request.POST.get('tariff', 'base'),
            payment_method=request.POST.get('payment_method', 'card'),
            extra_gps='extra_gps' in request.POST,
            extra_child_seat='extra_child_seat' in request.POST,
            extra_wifi='extra_wifi' in request.POST,
            extra_driver='extra_driver' in request.POST,
            extra_tire='extra_tire' in request.POST,
            extra_green_card='extra_green_card' in request.POST,
            promo_code=request.POST.get('promo_code', '').strip().upper(),
        )
        messages.success(request, f'✅ Замовлення {booking.number} оформлено!')
        return redirect('profile')

    pickups_with_price = [
        ('office',       'Офіс, вул. Клочківська, 94а',       'безкоштовно'),
        ('airport',      'Аеропорт «Харків»',                  'безкоштовно'),
        ('station',      'Залізничний вокзал',                  'безкоштовно'),
        ('delivery',     'Доставка по місту (будь-яка адреса)', '+200 ₴'),
        ('delivery_out', 'Доставка поза містом',                '+500 ₴'),
    ]
    user_discount_pct = 0
    if request.user.is_authenticated:
        try:
            user_discount_pct = request.user.profile.discount_pct or 0
        except Exception:
            pass
    return render(request, 'core/order.html', {
        'car': car,
        'cars': Car.objects.filter(status='free'),
        'pickups': Booking.PICKUPS,
        'tariffs': Booking.TARIFFS,
        'payments': Booking.PAYMENTS,
        'pickups_with_price': pickups_with_price,
        'docs_missing': docs_missing,
        'user_discount_pct': user_discount_pct,
    })


@login_required
def profile(request):
    profile, _ = ClientProfile.objects.get_or_create(user=request.user)
    active_tab = 'bookings'
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            active_tab = 'settings'
            passport_raw = request.POST.get('passport_number', '').strip()
            tax_id_raw = request.POST.get('tax_id', '').strip()
            driver_license_raw = request.POST.get('driver_license', '').strip()
            errors = []
            # 2. Перевірки (Валідація)
            if passport_raw and not re.match(r'^([А-Яа-яІіЇїЄєҐґ]{2}\d{6}|\d{9})$', passport_raw):
                errors.append('Невірний формат паспорта. Введіть 9 цифр (ID-картка) або 2 літери та 6 цифр (книжечка).')
            if tax_id_raw and not re.match(r'^\d{10}$', tax_id_raw):
                errors.append('Ідентифікаційний код має містити рівно 10 цифр.')
            if driver_license_raw and not re.match(r'^[А-Яа-яІіЇїЄєҐґA-Za-z]{3}\d{6}$', driver_license_raw):
                errors.append(
                    'Невірний формат водійського посвідчення. Очікується 3 літери та 6 цифр (наприклад: ВХХ123456).')
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                u = request.user
                u.first_name = request.POST.get('first_name', '')
                u.last_name = request.POST.get('last_name', '')
                u.email = request.POST.get('email', '')
                u.save()
                profile.phone = request.POST.get('phone', '')
                profile.city = request.POST.get('city', '')
                profile.driver_license = driver_license_raw
                profile.passport_number = passport_raw
                profile.tax_id = tax_id_raw
                profile.experience_years = request.POST.get('experience_years', 0)
                profile.save(
                    update_fields=['phone', 'city', 'driver_license', 'passport_number', 'tax_id', 'experience_years'])
                messages.success(request, '✅ Профіль оновлено!')
                return redirect('profile')  # Робимо редирект тільки при успіху
        elif action == 'cancel_booking':
            b = get_object_or_404(Booking, pk=request.POST.get('booking_id'), user=request.user)
            b.status = 'cancelled'
            b.save()
            messages.success(request, 'Замовлення скасовано.')
            return redirect('profile')
    all_bookings = request.user.bookings.select_related('car').prefetch_related('car__photos').order_by('-pk')
    active_bookings = all_bookings.filter(status__in=['active', 'pending', 'awaiting_payment', 'paid'])
    past_bookings = all_bookings.filter(status__in=['completed', 'cancelled'])
    wishlist = Wishlist.objects.filter(user=request.user).select_related('car')
    fines = Fine.objects.filter(booking__user=request.user).exclude(status='waived')

    SEGMENT_RANK = {'new': 0, 'regular': 1, 'vip': 2, 'blocked': 3}
    if profile.segment not in ('blocked', 'vip'):
        completed_count = request.user.bookings.filter(status='completed').count()
        auto_seg = 'new' if completed_count == 0 else ('regular' if completed_count < 5 else 'vip')
        if SEGMENT_RANK.get(auto_seg, 0) > SEGMENT_RANK.get(profile.segment, 0):
            profile.segment = auto_seg
            profile.save(update_fields=['segment'])
    return render(request, 'core/profile.html', {
        'profile': profile,
        'active_bookings': active_bookings,
        'past_bookings': past_bookings,
        'all_bookings': all_bookings,
        'wishlist': wishlist,
        'fines': fines,
        'active_tab': active_tab,
    })


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    mode = request.GET.get('mode', 'login')
    if request.method == 'POST':
        mode = request.POST.get('mode', 'login')
        if mode == 'register':
            username = request.POST.get('username','').strip()
            email = request.POST.get('email','').strip()
            password = request.POST.get('password','')
            first_name = request.POST.get('first_name','')
            last_name = request.POST.get('last_name','')
            phone = request.POST.get('phone','')
            if not username or not password:
                messages.error(request, 'Логін та пароль обовʼязкові.')
                return render(request, 'registration/auth.html', {'mode': 'register'})
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Такий логін вже зайнятий.')
                return render(request, 'registration/auth.html', {'mode': 'register'})
            user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
            ClientProfile.objects.create(user=user, phone=phone)
            login(request, user)
            messages.success(request, f'🎉 Ласкаво просимо, {first_name or username}!')
            return redirect('profile')
        else:
            username = request.POST.get('username','')
            password = request.POST.get('password','')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect(request.GET.get('next', 'profile'))
            messages.error(request, 'Невірний логін або пароль.')
    return render(request, 'registration/auth.html', {'mode': mode})


def logout_view(request):
    logout(request)
    return redirect('index')


@require_POST
def toggle_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Потрібно увійти'}, status=401)
    car = get_object_or_404(Car, pk=request.POST.get('car_id'))
    obj, created = Wishlist.objects.get_or_create(user=request.user, car=car)
    if not created:
        obj.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


@require_POST
def check_promo(request):
    """AJAX: перевірити промокод і повернути знижку"""
    code = request.POST.get('code', '').strip().upper()
    if not code:
        return JsonResponse({'valid': False, 'error': 'Введіть промокод'})
    try:
        promo = PromoCode.objects.get(code__iexact=code)
        ok, msg = promo.is_valid()
        if ok:
            return JsonResponse({
                'valid':    True,
                'code':     promo.code,
                'discount': promo.discount_pct,
                'message':  f'Знижку {promo.discount_pct}% застосовано! 🎉'
            })
        else:
            return JsonResponse({'valid': False, 'error': msg})
    except PromoCode.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Промокод не знайдено'})


def terms(request):
    return render(request, 'core/terms.html')

def privacy(request):
    return render(request, 'core/privacy.html')