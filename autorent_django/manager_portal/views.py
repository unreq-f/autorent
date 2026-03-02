from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from core.models import Car, Booking, Fine, Payment, ClientProfile
from datetime import date
import json

def is_manager(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

manager_req = user_passes_test(is_manager, login_url='/auth/')


@manager_req
def dashboard(request):
    today = date.today()
    ctx = {
        'active_count': Booking.objects.filter(status__in=['active','pending']).count(),
        'rented_count': Car.objects.filter(status='rented').count(),
        'total_cars': Car.objects.count(),
        'today_count': Booking.objects.filter(created_at__date=today).count(),
        'pending_count': Booking.objects.filter(status='pending').count(),
        'unpaid_fines': Fine.objects.filter(status='unpaid').count(),
        'recent_bookings': Booking.objects.select_related('user','car').all()[:8],
        'monthly_revenue': Payment.objects.filter(
            created_at__year=today.year, created_at__month=today.month, status='success', payment_type='rental'
        ).aggregate(t=Sum('amount'))['t'] or 0,
    }
    ctx['occupancy'] = round(ctx['rented_count'] / ctx['total_cars'] * 100) if ctx['total_cars'] else 0
    return render(request, 'manager/dashboard.html', ctx)


@manager_req
def bookings(request):
    qs = Booking.objects.select_related('user','car').all()
    sf = request.GET.get('status','')
    q = request.GET.get('q','')
    if sf: qs = qs.filter(status=sf)
    if q: qs = qs.filter(Q(number__icontains=q)|Q(user__first_name__icontains=q)|Q(user__last_name__icontains=q)|Q(car__brand__icontains=q))
    counts = {s: Booking.objects.filter(status=s).count() for s,_ in Booking.STATUSES}
    counts['all'] = Booking.objects.count()
    return render(request, 'manager/bookings.html', {'bookings': qs, 'counts': counts, 'sf': sf})


@manager_req
def booking_edit(request, pk):
    b = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        b.status = request.POST.get('status', b.status)
        b.manager_note = request.POST.get('manager_note', b.manager_note)
        b.save()
        messages.success(request, f'Замовлення {b.number} оновлено.')
        return redirect('manager_bookings')
    return render(request, 'manager/booking_edit.html', {'b': b, 'statuses': Booking.STATUSES})


@manager_req
def cars(request):
    qs = Car.objects.all()
    sf_status = request.GET.get('status','')
    sf_class = request.GET.get('class','')
    q = request.GET.get('q','')
    if sf_status: qs = qs.filter(status=sf_status)
    if sf_class: qs = qs.filter(car_class=sf_class)
    if q: qs = qs.filter(Q(brand__icontains=q)|Q(model__icontains=q)|Q(plate__icontains=q))
    total = Car.objects.count()
    stats = {
        'free': Car.objects.filter(status='free').count(),
        'rented': Car.objects.filter(status='rented').count(),
        'service': Car.objects.filter(status='service').count(),
        'broken': Car.objects.filter(status='broken').count(),
        'total': total,
        'occupancy': round(Car.objects.filter(status='rented').count() / total * 100) if total else 0,
    }
    return render(request, 'manager/cars.html', {'cars': qs, 'stats': stats, 'car_classes': Car.CAR_CLASSES, 'car_statuses': Car.STATUSES})


@manager_req
def car_edit(request, pk=None):
    car = get_object_or_404(Car, pk=pk) if pk else None
    if request.method == 'POST':
        d = request.POST
        fields = ['brand','model','year','car_class','fuel','transmission','seats','engine','drive','color','plate','mileage','price_base','price_prime','deposit','status','description','features','emoji']
        if car:
            for f in fields: setattr(car, f, d.get(f, getattr(car, f)))
            car.is_featured = 'is_featured' in d
            if request.FILES.get('image'): car.image = request.FILES['image']
            car.save()
            messages.success(request, f'{car} оновлено.')
        else:
            car = Car.objects.create(**{f: d.get(f,'') for f in fields if d.get(f)}, is_featured='is_featured' in d)
            messages.success(request, f'{car} додано.')
        return redirect('manager_cars')
    return render(request, 'manager/car_edit.html', {'car': car, 'car_classes': Car.CAR_CLASSES, 'fuels': Car.FUELS, 'statuses': Car.STATUSES})


@manager_req
def clients(request):
    users = User.objects.filter(is_staff=False).prefetch_related('profile','bookings')
    q = request.GET.get('q','')
    seg = request.GET.get('segment','')
    if q: users = users.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(email__icontains=q)|Q(username__icontains=q))
    if seg: users = users.filter(profile__segment=seg)
    return render(request, 'manager/clients.html', {'users': users, 'segments': ClientProfile.SEGMENTS, 'seg': seg})


@manager_req
def client_edit(request, pk):
    u = get_object_or_404(User, pk=pk)
    profile, _ = ClientProfile.objects.get_or_create(user=u)
    if request.method == 'POST':
        profile.segment = request.POST.get('segment', profile.segment)
        profile.discount_pct = request.POST.get('discount_pct', 0)
        profile.manager_note = request.POST.get('manager_note','')
        profile.save()
        messages.success(request, 'Профіль клієнта оновлено.')
        return redirect('manager_clients')
    bookings = u.bookings.select_related('car').all()[:10]
    return render(request, 'manager/client_edit.html', {'cu': u, 'profile': profile, 'bookings': bookings, 'segments': ClientProfile.SEGMENTS})


@manager_req
def payments(request):
    qs = Payment.objects.select_related('booking__user','booking__car').all()[:100]
    sf = request.GET.get('status','')
    if sf: qs = Payment.objects.select_related('booking__user','booking__car').filter(status=sf)[:100]
    stats = {
        'total_revenue': Payment.objects.filter(status='success',payment_type='rental').aggregate(t=Sum('amount'))['t'] or 0,
        'deposits_held': Payment.objects.filter(status='deposit_held').aggregate(t=Sum('amount'))['t'] or 0,
        'pending': Payment.objects.filter(status='pending').count(),
        'success': Payment.objects.filter(status='success').count(),
    }
    return render(request, 'manager/payments.html', {'payments': qs, 'stats': stats, 'sf': sf, 'statuses': Payment.STATUSES})


@manager_req
def fines(request):
    qs = Fine.objects.select_related('booking__user','booking__car').all()
    sf = request.GET.get('status','')
    q = request.GET.get('q','')
    if sf: qs = qs.filter(status=sf)
    if q: qs = qs.filter(Q(booking__user__first_name__icontains=q)|Q(booking__user__last_name__icontains=q)|Q(booking__car__brand__icontains=q))
    stats = {
        'unpaid_count': Fine.objects.filter(status='unpaid').count(),
        'unpaid_amount': Fine.objects.filter(status='unpaid').aggregate(t=Sum('amount'))['t'] or 0,
        'paid_amount': Fine.objects.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0,
        'total': Fine.objects.count(),
    }
    return render(request, 'manager/fines.html', {'fines': qs, 'stats': stats, 'sf': sf, 'fine_types': Fine.TYPES, 'severities': Fine.SEVERITIES})


@manager_req
def fine_edit(request, pk=None):
    fine = get_object_or_404(Fine, pk=pk) if pk else None
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=request.POST.get('booking_id'))
        if fine:
            fine.status = request.POST.get('status', fine.status)
            fine.amount = request.POST.get('amount', fine.amount)
            fine.description = request.POST.get('description','')
            if request.FILES.get('photo'): fine.photo = request.FILES['photo']
            fine.save()
            messages.success(request, f'{fine.number} оновлено.')
        else:
            Fine.objects.create(
                booking=booking,
                fine_type=request.POST.get('fine_type','other'),
                severity=request.POST.get('severity','medium'),
                amount=request.POST.get('amount',0),
                description=request.POST.get('description',''),
                manager=request.user,
            )
            messages.success(request, 'Штраф виставлено.')
        return redirect('manager_fines')
    bookings = Booking.objects.select_related('user','car').filter(status__in=['active','completed'])
    return render(request, 'manager/fine_edit.html', {'fine': fine, 'bookings': bookings, 'fine_types': Fine.TYPES, 'severities': Fine.SEVERITIES, 'statuses': Fine.STATUSES})


@manager_req
def reports(request):
    today = date.today()
    months_data = []
    for i in range(6):
        m = today.month - i
        y = today.year
        while m <= 0: m += 12; y -= 1
        rev = Payment.objects.filter(created_at__year=y, created_at__month=m, status='success', payment_type='rental').aggregate(t=Sum('amount'))['t'] or 0
        bc = Booking.objects.filter(created_at__year=y, created_at__month=m).count()
        months_data.append({'year':y,'month':m,'revenue':float(rev),'bookings':bc,'label':f'{m:02d}/{y}'})
    months_data.reverse()
    top_cars = Car.objects.annotate(bc=Count('bookings')).order_by('-bc')[:5]
    ctx = {
        'months_json': json.dumps(months_data),
        'top_cars': top_cars,
        'total_revenue': Payment.objects.filter(status='success',payment_type='rental').aggregate(t=Sum('amount'))['t'] or 0,
        'total_bookings': Booking.objects.count(),
        'total_clients': User.objects.filter(is_staff=False).count(),
        'vip_clients': ClientProfile.objects.filter(segment='vip').count(),
        'free_cars': Car.objects.filter(status='free').count(),
        'rented_cars': Car.objects.filter(status='rented').count(),
        'total_cars': Car.objects.count(),
    }
    return render(request, 'manager/reports.html', ctx)


@manager_req
@require_POST
def booking_status_update(request, pk):
    b = get_object_or_404(Booking, pk=pk)
    ns = request.POST.get('status')
    if ns in dict(Booking.STATUSES):
        b.status = ns
        b.save()
    return JsonResponse({'ok': True, 'status': b.status})
