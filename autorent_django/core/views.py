from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Car, Booking, ClientProfile, Fine, Payment, Wishlist


def index(request):
    featured = Car.objects.filter(is_featured=True)[:6]
    classes = Car.CAR_CLASSES
    return render(request, 'core/index.html', {'featured': featured, 'classes': classes})


def catalog(request):
    cars = Car.objects.all()
    car_class = request.GET.get('class','')
    fuel = request.GET.get('fuel','')
    q = request.GET.get('q','')
    price_max = request.GET.get('price_max','')
    status = request.GET.get('status','')

    if car_class: cars = cars.filter(car_class=car_class)
    if fuel: cars = cars.filter(fuel=fuel)
    if q: cars = cars.filter(Q(brand__icontains=q)|Q(model__icontains=q))
    if price_max: cars = cars.filter(price_base__lte=price_max)
    if status: cars = cars.filter(status=status)

    wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('car_id', flat=True)) if request.user.is_authenticated else []
    return render(request, 'core/catalog.html', {
        'cars': cars, 'total': cars.count(),
        'car_classes': Car.CAR_CLASSES, 'fuel_types': Car.FUELS,
        'wishlist_ids': wishlist_ids,
        'filters': {'class': car_class, 'fuel': fuel, 'q': q, 'price_max': price_max}
    })


def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    similar = Car.objects.filter(car_class=car.car_class).exclude(pk=pk)[:4]
    in_wishlist = Wishlist.objects.filter(user=request.user, car=car).exists() if request.user.is_authenticated else False
    return render(request, 'core/car_detail.html', {'car': car, 'similar': similar, 'in_wishlist': in_wishlist})


def conditions(request):
    return render(request, 'core/conditions.html')


def about(request):
    return render(request, 'core/about.html')


def contacts(request):
    if request.method == 'POST':
        messages.success(request, '✅ Повідомлення надіслано! Відповімо протягом години.')
        return redirect('contacts')
    return render(request, 'core/contacts.html')


def booking_quick(request):
    cars = Car.objects.filter(status='free')
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'Для бронювання потрібно увійти в систему.')
            return redirect('auth')
        car = get_object_or_404(Car, pk=request.POST.get('car'))
        booking = Booking.objects.create(
            user=request.user, car=car,
            date_from=request.POST.get('date_from'),
            date_to=request.POST.get('date_to'),
            pickup_location=request.POST.get('pickup_location', 'office'),
            tariff=request.POST.get('tariff', 'base'),
            payment_method=request.POST.get('payment_method', 'card'),
        )
        messages.success(request, f'🎉 Бронювання {booking.number} успішно створено!')
        return redirect('profile')
    return render(request, 'core/booking_quick.html', {'cars': cars, 'pickups': Booking.PICKUPS})


@login_required
def order(request, car_pk=None):
    car = get_object_or_404(Car, pk=car_pk) if car_pk else None
    if request.method == 'POST':
        car_id = request.POST.get('car') or car_pk
        car_obj = get_object_or_404(Car, pk=car_id)
        booking = Booking.objects.create(
            user=request.user, car=car_obj,
            date_from=request.POST['date_from'],
            date_to=request.POST['date_to'],
            pickup_location=request.POST.get('pickup_location','office'),
            tariff=request.POST.get('tariff','base'),
            payment_method=request.POST.get('payment_method','card'),
            extra_gps='extra_gps' in request.POST,
            extra_child_seat='extra_child_seat' in request.POST,
            extra_wifi='extra_wifi' in request.POST,
            extra_driver='extra_driver' in request.POST,
            extra_tire='extra_tire' in request.POST,
            extra_green_card='extra_green_card' in request.POST,
            promo_code=request.POST.get('promo_code',''),
        )
        messages.success(request, f'✅ Замовлення {booking.number} оформлено!')
        return redirect('profile')
    return render(request, 'core/order.html', {
        'car': car, 'cars': Car.objects.filter(status='free'),
        'pickups': Booking.PICKUPS, 'tariffs': Booking.TARIFFS, 'payments': Booking.PAYMENTS
    })


@login_required
def profile(request):
    profile, _ = ClientProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            u = request.user
            u.first_name = request.POST.get('first_name','')
            u.last_name = request.POST.get('last_name','')
            u.email = request.POST.get('email','')
            u.save()
            profile.phone = request.POST.get('phone','')
            profile.city = request.POST.get('city','')
            profile.driver_license = request.POST.get('driver_license','')
            profile.experience_years = request.POST.get('experience_years', 0)
            profile.save()
            messages.success(request, '✅ Профіль оновлено!')
        elif action == 'cancel_booking':
            b = get_object_or_404(Booking, pk=request.POST.get('booking_id'), user=request.user)
            b.status = 'cancelled'
            b.save()
            messages.success(request, 'Замовлення скасовано.')
        return redirect('profile')

    active_bookings = request.user.bookings.filter(status__in=['active','pending'])
    past_bookings = request.user.bookings.filter(status__in=['completed','cancelled'])
    wishlist = Wishlist.objects.filter(user=request.user).select_related('car')
    fines = Fine.objects.filter(booking__user=request.user).exclude(status='waived')
    return render(request, 'core/profile.html', {
        'profile': profile,
        'active_bookings': active_bookings,
        'past_bookings': past_bookings,
        'wishlist': wishlist,
        'fines': fines,
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


@login_required
@require_POST
def toggle_wishlist(request):
    car = get_object_or_404(Car, pk=request.POST.get('car_id'))
    obj, created = Wishlist.objects.get_or_create(user=request.user, car=car)
    if not created:
        obj.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})
