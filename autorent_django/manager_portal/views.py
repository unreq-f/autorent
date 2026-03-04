from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from core.models import Car, Booking, Fine, Payment, ClientProfile, ContactMessage
from datetime import date
import json

def is_manager(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

manager_req = user_passes_test(is_manager, login_url='/auth/')


@manager_req
def dashboard(request):
    return redirect('manager_bookings')

@manager_req
def bookings(request):
    import csv
    from django.http import HttpResponse
    from datetime import date as date_cls

    # Handle new booking creation
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'new':
            try:
                car_pk   = request.POST.get('car_pk')
                car_obj  = get_object_or_404(Car, pk=car_pk) if car_pk else None
                if not car_obj:
                    messages.error(request, 'Оберіть автомобіль.')
                    return redirect('manager_bookings')

                date_from = date_cls.fromisoformat(request.POST.get('date_from',''))
                date_to   = date_cls.fromisoformat(request.POST.get('date_to',''))

                # Find or create user — first try direct pk from search
                client_user_pk = request.POST.get('client_user_pk','').strip()
                client_email   = request.POST.get('client_email','').strip()
                client_name    = request.POST.get('client_name','').strip()
                client_phone   = request.POST.get('client_phone','').strip()
                user = None
                if client_user_pk:
                    try:
                        user = User.objects.get(pk=int(client_user_pk))
                        # Update phone if provided
                        if client_phone:
                            p, _ = ClientProfile.objects.get_or_create(user=user)
                            if not p.phone: p.phone = client_phone; p.save()
                    except User.DoesNotExist:
                        pass
                if not user and client_email:
                    user, created = User.objects.get_or_create(
                        email=client_email,
                        defaults={'username': client_email.split('@')[0]}
                    )
                    if created and client_name:
                        parts = client_name.split(None, 1)
                        user.first_name = parts[0]
                        user.last_name  = parts[1] if len(parts) > 1 else ''
                        user.save()
                    p, _ = ClientProfile.objects.get_or_create(user=user)
                    if client_phone and not p.phone: p.phone = client_phone; p.save()
                if not user:
                    user = request.user  # fallback to manager

                pickup_loc = request.POST.get('pickup_location', 'office')
                delivery_address = request.POST.get('delivery_address','').strip()
                if pickup_loc not in ('delivery','delivery_out'):
                    delivery_address = ''

                return_loc = request.POST.get('return_location', 'office')
                return_address = request.POST.get('return_address','').strip()
                if return_loc not in ('delivery','delivery_out'):
                    return_address = ''

                promo_code_raw = request.POST.get('promo_code','').strip().upper()
                booking = Booking.objects.create(
                    user=user, car=car_obj,
                    date_from=date_from, date_to=date_to,
                    time_from=request.POST.get('time_from','10:00'),
                    time_to=request.POST.get('time_to','10:00'),
                    pickup_location=pickup_loc, delivery_address=delivery_address,
                    return_location=return_loc, return_address=return_address,
                    tariff=request.POST.get('tariff','base'),
                    payment_method=request.POST.get('payment_method','card'),
                    extra_gps='extra_gps' in request.POST,
                    extra_child_seat='extra_child_seat' in request.POST,
                    extra_wifi='extra_wifi' in request.POST,
                    extra_driver='extra_driver' in request.POST,
                    extra_tire='extra_tire' in request.POST,
                    extra_green_card='extra_green_card' in request.POST,
                    promo_code=promo_code_raw,
                    manager_note=request.POST.get('manager_note',''),
                    source='manager',
                )
                # Recalculate price with discount (client loyalty + promo)
                booking.total_price = booking.calculate_price()
                booking.save(update_fields=['total_price'])
                messages.success(request, f'✅ Замовлення {booking.number} створено.')
            except Exception as e:
                messages.error(request, f'Помилка: {e}')
        return redirect('manager_bookings')

    qs = Booking.objects.select_related('user','car').order_by('-date_from','-pk')
    sf      = request.GET.get('status','')
    q       = request.GET.get('q','')
    car_f   = request.GET.get('car','')
    tariff_f= request.GET.get('tariff','')
    date_f  = request.GET.get('date_from','')
    date_t  = request.GET.get('date_to','')

    if sf:       qs = qs.filter(status=sf)
    if car_f:    qs = qs.filter(car__pk=car_f)
    if tariff_f: qs = qs.filter(tariff=tariff_f)
    if date_f:   qs = qs.filter(date_from__gte=date_f)
    if date_t:   qs = qs.filter(date_to__lte=date_t)
    if q:        qs = qs.filter(
        Q(number__icontains=q)|Q(user__first_name__icontains=q)|
        Q(user__last_name__icontains=q)|Q(car__brand__icontains=q)|
        Q(car__model__icontains=q))

    # CSV export
    if request.GET.get('export') == 'csv':
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="bookings.csv"'
        resp.write('\ufeff')  # BOM for Excel
        w = csv.writer(resp)
        w.writerow(['№','Клієнт','Email','Авто','Від','До','Тариф','Сума','Статус','Місце'])
        for b in qs:
            w.writerow([b.number,
                        b.user.get_full_name() or b.user.username,
                        b.user.email,
                        str(b.car),
                        b.date_from, b.date_to,
                        b.get_tariff_display(),
                        b.total_price,
                        b.get_status_display(),
                        b.get_pickup_display_custom()])
        return resp

    counts = {s: Booking.objects.filter(status=s).count() for s,_ in Booking.STATUSES}
    counts['all'] = Booking.objects.count()
    # AJAX: оновлення лічильників
    if request.GET.get('counts_only'):
        return JsonResponse(counts)

    all_cars = Car.objects.values('pk','brand','model','price_base','price_prime','deposit').order_by('brand','model')
    return render(request, 'manager/bookings.html', {
        'bookings': qs, 'counts': counts, 'sf': sf,
        'all_cars': all_cars,
        'tariffs': Booking.TARIFFS,
        'statuses': Booking.STATUSES,
        'payment_methods': Booking.PAYMENTS,
        'pickups': Booking.PICKUPS,
        'filters': {'q':q,'car':car_f,'tariff':tariff_f,'date_from':date_f,'date_to':date_t},
    })


@manager_req
def booking_edit(request, pk):
    b = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        from datetime import date, time as time_cls
        b.status         = request.POST.get('status', b.status)
        b.manager_note   = request.POST.get('manager_note', b.manager_note)
        b.payment_method = request.POST.get('payment_method', b.payment_method)
        b.tariff         = request.POST.get('tariff', b.tariff)
        b.pickup_location  = request.POST.get('pickup_location', b.pickup_location)
        b.delivery_address = request.POST.get('delivery_address', b.delivery_address)
        b.return_location  = request.POST.get('return_location', b.return_location)
        b.return_address   = request.POST.get('return_address', b.return_address)
        promo = request.POST.get('promo_code', '').strip().upper()
        b.promo_code = promo
        try:
            b.date_from = date.fromisoformat(request.POST['date_from'])
            b.date_to   = date.fromisoformat(request.POST['date_to'])
        except (KeyError, ValueError):
            pass
        try:
            tf = request.POST.get('time_from','')
            tt = request.POST.get('time_to','')
            if tf: b.time_from = time_cls.fromisoformat(tf)
            if tt: b.time_to   = time_cls.fromisoformat(tt)
        except ValueError:
            pass
        # Recalculate price after changes
        b.total_price = b.calculate_price()
        if b.tariff == 'base':
            b.deposit_amount = b.car.deposit
        else:
            b.deposit_amount = 0
        b.save()
        messages.success(request, f'Замовлення {b.number} оновлено.')
        return redirect('manager_booking_edit', pk=pk)
    return render(request, 'manager/booking_edit.html', {'b': b, 'statuses': Booking.STATUSES})


@manager_req
def cars(request):
    import csv
    from django.http import HttpResponse
    qs = Car.objects.all().prefetch_related('photos').order_by('brand','model')
    sf_status = request.GET.get('status','')
    sf_class  = request.GET.get('class','')
    sf_fuel   = request.GET.get('fuel','')
    q         = request.GET.get('q','')
    if sf_status: qs = qs.filter(status=sf_status)
    if sf_class:  qs = qs.filter(car_class=sf_class)
    if sf_fuel:   qs = qs.filter(fuel=sf_fuel)
    if q: qs = qs.filter(Q(brand__icontains=q)|Q(model__icontains=q)|Q(plate__icontains=q))
    total = Car.objects.count()
    stats = {
        'free':    Car.objects.filter(status='free').count(),
        'rented':  Car.objects.filter(status='rented').count(),
        'service': Car.objects.filter(status='service').count(),
        'broken':  Car.objects.filter(status='broken').count(),
        'total':   total,
        'occupancy': round(Car.objects.filter(status='rented').count() / total * 100) if total else 0,
    }
    if request.GET.get('export') == 'csv':
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="cars.csv"'
        resp.write('﻿')
        w = csv.writer(resp)
        w.writerow(['Марка','Модель','Рік','Номер','Клас','Паливо','КПП','Пробіг','Ціна Base','Ціна Prime','Статус'])
        for c in qs:
            w.writerow([c.brand,c.model,c.year,c.plate,c.get_car_class_display(),c.get_fuel_display(),c.transmission,c.mileage,c.price_base,c.price_prime,c.get_status_display()])
        return resp
    return render(request, 'manager/cars.html', {
        'cars': qs, 'stats': stats,
        'all_cars': Car.objects.all(),
        'car_classes': Car.CAR_CLASSES,
        'car_statuses': Car.STATUSES,
        'car_fuels': Car.FUELS,
        'filters': {'q':q,'status':sf_status,'class':sf_class,'fuel':sf_fuel},
    })


@manager_req
def car_edit(request, pk=None):
    car = get_object_or_404(Car, pk=pk) if pk else None
    if request.method == 'POST':
        d = request.POST
        fields = ['brand','model','year','car_class','fuel','transmission','seats','engine','drive','color','plate','mileage','price_base','price_prime','deposit','status','description','features','emoji']
        # Fields that cannot be empty strings — must be None or a valid number
        decimal_fields = {'price_base', 'price_prime', 'deposit'}
        integer_fields = {'year', 'seats', 'mileage'}
        if car:
            for f in fields:
                val = d.get(f, '')
                if f in decimal_fields:
                    # Convert empty string to None (or keep existing value)
                    val = val.strip() if val else ''
                    if val == '':
                        val = getattr(car, f)  # keep old value if field is blank
                elif f in integer_fields:
                    val = val.strip() if val else ''
                    if val == '':
                        val = getattr(car, f)
                    else:
                        try:
                            val = int(val)
                        except (ValueError, TypeError):
                            val = getattr(car, f)
                else:
                    val = d.get(f, getattr(car, f))
                setattr(car, f, val)
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
def car_service(request, pk):
    from django.utils import timezone
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'POST':
        service_date = request.POST.get('service_date','')
        service_note = request.POST.get('service_note','')
        set_status   = request.POST.get('set_status','service')
        car.status = set_status
        if service_date:
            from datetime import date
            car.next_service = service_date
        if service_note and hasattr(car, 'description'):
            car.description = (car.description or '') + f'\n[ТО {timezone.now().strftime("%d.%m.%Y")}] {service_note}'
        car.save()
        messages.success(request, f'ТО для {car} призначено.')
        return redirect('manager_cars')
    return render(request, 'manager/car_service.html', {'car': car})


@manager_req
def car_search_json(request):
    q = request.GET.get('q','').strip()
    cars = Car.objects.filter(
        Q(brand__icontains=q)|Q(model__icontains=q)|Q(plate__icontains=q)
    ).values('pk','brand','model','plate','price_base','price_prime','deposit','status')[:12]
    result = []
    for c in cars:
        result.append({
            'pk': c['pk'],
            'label': f"{c['brand']} {c['model']} ({c['plate']})",
            'status': c['status'],
            'price_base':  float(c['price_base'] or 0),
            'price_prime': float(c['price_prime'] or 0),
            'deposit':     float(c['deposit'] or 0),
        })
    return JsonResponse(result, safe=False)


@manager_req
def clients(request):
    import csv
    from django.http import HttpResponse

    users = User.objects.filter(is_staff=False).select_related('profile').prefetch_related('bookings')
    q    = request.GET.get('q', '')
    seg  = request.GET.get('segment', '')
    sort = request.GET.get('sort', '')

    if q:
        users = users.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(email__icontains=q) | Q(username__icontains=q) |
            Q(profile__phone__icontains=q)
        )
    if seg:
        users = users.filter(profile__segment=seg)

    if sort == 'name':
        users = users.order_by('first_name', 'last_name')
    else:
        users = users.order_by('-date_joined')

    all_users = User.objects.filter(is_staff=False)
    stats = {
        'total':   all_users.count(),
        'new':     all_users.filter(profile__segment='new').count(),
        'regular': all_users.filter(profile__segment='regular').count(),
        'vip':     all_users.filter(profile__segment='vip').count(),
        'blocked': all_users.filter(profile__segment='blocked').count(),
    }

    if request.GET.get('export') == 'csv':
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="clients.csv"'
        resp.write('\ufeff')
        w = csv.writer(resp)
        w.writerow(["Im'ya", 'Email', 'Telefon', 'Misto', 'Segment', 'Znyzhka %', 'Zamovlen', 'Pasport', 'IPN', 'VP', 'Reestr'])
        for u in users:
            p = getattr(u, 'profile', None)
            w.writerow([
                u.get_full_name() or u.username, u.email,
                getattr(p,'phone',''), getattr(p,'city',''),
                getattr(p,'segment',''), getattr(p,'discount_pct',0),
                u.bookings.count(),
                getattr(p,'passport_number',''), getattr(p,'tax_id',''), getattr(p,'driver_license',''),
                u.date_joined.strftime('%d.%m.%Y'),
            ])
        return resp

    return render(request, 'manager/clients.html', {
        'users': users, 'segments': ClientProfile.SEGMENTS,
        'seg': seg, 'stats': stats,
    })

@manager_req
def client_edit(request, pk):
    u = get_object_or_404(User, pk=pk)
    profile, _ = ClientProfile.objects.get_or_create(user=u)
    if request.method == 'POST':
        # User (auth) fields
        u.first_name = request.POST.get('first_name', u.first_name).strip()
        u.last_name  = request.POST.get('last_name',  u.last_name).strip()
        u.email      = request.POST.get('email',      u.email).strip()
        u.save()
        # Profile fields
        profile.phone            = request.POST.get('phone', '').strip()
        profile.city             = request.POST.get('city', '').strip()
        profile.address          = request.POST.get('address', '').strip()
        profile.birth_date       = request.POST.get('birth_date', '') or None
        profile.driver_license   = request.POST.get('driver_license', '').strip()
        profile.passport_number  = request.POST.get('passport_number', '').strip()
        profile.tax_id           = request.POST.get('tax_id', '').strip()
        profile.experience_years = int(request.POST.get('experience_years', 0) or 0)
        profile.segment          = request.POST.get('segment', profile.segment)
        profile.discount_pct     = int(request.POST.get('discount_pct', 0) or 0)
        profile.manager_note     = request.POST.get('manager_note', '')
        profile.save()
        messages.success(request, 'Профіль {} оновлено.'.format(u.get_full_name() or u.username))
        return redirect('manager_clients')
    bookings = u.bookings.select_related('car').order_by('-created_at')[:10]
    return render(request, 'manager/client_edit.html', {
        'cu': u, 'profile': profile, 'bookings': bookings, 'segments': ClientProfile.SEGMENTS
    })


@manager_req
def payments(request):
    import csv
    from django.http import HttpResponse, JsonResponse
    from datetime import date as date_cls
    from django.db.models import Q, Sum

    # ── Filters from GET ──
    sf     = request.GET.get("status", "")
    stype  = request.GET.get("type", "")
    meth   = request.GET.get("method", "")
    q      = request.GET.get("q", "")
    date_f = request.GET.get("date_from", "")
    date_t = request.GET.get("date_to", "")

    # ── Actual Payment records ──
    pay_qs = Payment.objects.select_related("booking__user", "booking__car", "fine__booking__user").order_by("-created_at")
    if sf:     pay_qs = pay_qs.filter(status=sf)
    if stype:  pay_qs = pay_qs.filter(payment_type=stype)
    if meth:   pay_qs = pay_qs.filter(method=meth)
    if q:
        pay_qs = pay_qs.filter(
            Q(transaction_id__icontains=q) |
            Q(booking__user__first_name__icontains=q) |
            Q(booking__user__last_name__icontains=q) |
            Q(booking__user__email__icontains=q) |
            Q(booking__number__icontains=q)
        )
    if date_f: pay_qs = pay_qs.filter(created_at__date__gte=date_f)
    if date_t: pay_qs = pay_qs.filter(created_at__date__lte=date_t)

    # ── Auto-aggregate: Bookings that need payment entries ──
    # Show bookings with relevant statuses as virtual rows in a separate list
    BOOKING_SHOW_STATUSES = ["awaiting_payment", "paid", "active", "completed"]
    FINE_SHOW_STATUSES    = ["unpaid", "paid"]

    auto_bookings = []
    auto_fines    = []

    # Only show auto-rows when no heavy type/status filter is active
    if not stype and not sf:
        bk_qs = Booking.objects.select_related("user", "car").filter(
            status__in=BOOKING_SHOW_STATUSES
        ).order_by("-created_at")
        if q:
            bk_qs = bk_qs.filter(
                Q(number__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__email__icontains=q)
            )
        if date_f: bk_qs = bk_qs.filter(date_from__gte=date_f)
        if date_t: bk_qs = bk_qs.filter(date_to__lte=date_t)
        auto_bookings = list(bk_qs)

        fine_qs = Fine.objects.select_related("booking__user", "booking__car").filter(
            status__in=FINE_SHOW_STATUSES
        ).order_by("-created_at")
        if q:
            fine_qs = fine_qs.filter(
                Q(number__icontains=q) |
                Q(booking__user__first_name__icontains=q) |
                Q(booking__user__last_name__icontains=q) |
                Q(booking__number__icontains=q)
            )
        auto_fines = list(fine_qs)

    # ── POST: add payment or change status ──
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_payment":
            bk_num = request.POST.get("booking_number", "").strip()
            bk = Booking.objects.filter(number__iexact=bk_num).first() if bk_num else None
            if not bk:
                bk_pk = request.POST.get("booking_pk")
                bk = Booking.objects.filter(pk=bk_pk).first() if bk_pk else None
            Payment.objects.create(
                booking=bk,
                payment_type=request.POST.get("payment_type", "rental"),
                method=request.POST.get("method", "card"),
                amount=request.POST.get("amount", 0),
                status=request.POST.get("status", "success"),
                bank_ref=request.POST.get("bank_ref", ""),
                note=request.POST.get("note", ""),
            )
            messages.success(request, "Платіж додано.")
        elif action == "change_status":
            p = get_object_or_404(Payment, pk=request.POST.get("payment_pk"))
            p.status = request.POST.get("new_status", p.status)
            p.save()
            messages.success(request, f"Статус {p.transaction_id} оновлено.")
        return redirect(request.get_full_path())

    # ── CSV export ──
    if request.GET.get("export") == "csv":
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = "attachment; filename=payments.csv"
        resp.write("\ufeff")
        w = csv.writer(resp)
        w.writerow(["ID","Дата","Клієнт","Замовлення","Тип","Метод","Сума","Статус","Банк ID","Примітка"])
        for p in pay_qs:
            client = p.booking.user.get_full_name() if p.booking else ("—" if not p.fine else p.fine.booking.user.get_full_name())
            bk_num = p.booking.number if p.booking else "—"
            w.writerow([p.transaction_id, p.created_at.strftime("%d.%m.%Y %H:%M"),
                        client, bk_num, p.get_payment_type_display(), p.get_method_display(),
                        p.amount, p.get_status_display_custom(), p.bank_ref, p.note])
        return resp

    # ── Stats ──
    today = date_cls.today()
    base  = Payment.objects
    counts = {s: base.filter(status=s).count() for s,_ in Payment.STATUSES}
    counts["all"] = base.count()
    stats = {
        "total_revenue": base.filter(status="success",payment_type="rental").aggregate(t=Sum("amount"))["t"] or 0,
        "month_revenue": base.filter(status="success",payment_type="rental",
                          created_at__year=today.year,created_at__month=today.month).aggregate(t=Sum("amount"))["t"] or 0,
        "today_revenue": base.filter(status="success",payment_type="rental",
                          created_at__date=today).aggregate(t=Sum("amount"))["t"] or 0,
        "deposits_held": base.filter(status="deposit_held").aggregate(t=Sum("amount"))["t"] or 0,
        "pending":       Booking.objects.filter(status="awaiting_payment").count(),
        "refunds":       base.filter(status="refund").aggregate(t=Sum("amount"))["t"] or 0,
        "auto_bk_count": len(auto_bookings),
        "auto_fine_count": len(auto_fines),
    }

    # Bookings list for new payment form search
    form_bookings = Booking.objects.select_related("user","car").filter(
        status__in=["awaiting_payment","paid","active","completed","pending"]
    ).order_by("-created_at")[:200]

    # Pre-filter deposit entries for template (avoids single-quote syntax issues)
    statuses_filtered = [(v, l) for v, l in Payment.STATUSES if v not in ('deposit_held', 'deposit_released')]
    types_filtered    = [(v, l) for v, l in Payment.TYPES    if v != 'deposit']
    pay_qs_filtered   = pay_qs.exclude(payment_type='deposit').exclude(status__in=['deposit_held','deposit_released'])
    # Build PD dict as safe JSON in view to avoid Django template parser issues with {%
    import json as _json
    pd_json = _json.dumps({
        str(p.pk): {
            "pk": p.pk,
            "txn": p.transaction_id or "",
            "date": p.created_at.strftime("%d.%m.%Y %H:%M") if p.created_at else "",
            "type": p.get_payment_type_display(),
            "tc": p.payment_type or "",
            "method": p.get_method_display(),
            "amount": str(int(p.amount)) if p.amount else "0",
            "status": p.status or "",
            "statusL": p.get_status_display_custom() if hasattr(p, 'get_status_display_custom') else p.get_status_display(),
            "bank_ref": p.bank_ref or "",
            "note": p.note or "",
            "client": p.booking.user.get_full_name() or p.booking.user.username if p.booking else "",
            "bk_num": p.booking.number if p.booking else "",
            "bk_url": f"/manager/bookings/?q={p.booking.number}" if p.booking else "",
            "total_full": str(int(p.booking.total_with_deposit)) if p.booking else "",
        }
        for p in pay_qs_filtered
    }, ensure_ascii=False)
    return render(request, "manager/payments.html", {
        "payments": pay_qs_filtered, "auto_bookings": auto_bookings, "auto_fines": auto_fines,
        "stats": stats, "counts": counts, "sf": sf,
        "statuses": Payment.STATUSES, "statuses_filtered": statuses_filtered,
        "types": Payment.TYPES, "types_filtered": types_filtered,
        "methods": Payment.METHODS,
        "filters": {"q": q, "type": stype, "method": meth, "date_from": date_f, "date_to": date_t},
        "form_bookings": form_bookings,
        "pd_json": pd_json,
    })


@manager_req
def booking_search(request):
    from django.http import JsonResponse
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})
    bks = Booking.objects.select_related("user","car").filter(
        Q(number__icontains=q) |
        Q(user__first_name__icontains=q) |
        Q(user__last_name__icontains=q) |
        Q(user__email__icontains=q)
    ).order_by("-created_at")[:15]
    results = []
    for b in bks:
        results.append({
            "pk": b.pk,
            "number": b.number,
            "client": b.user.get_full_name() or b.user.username,
            "car": str(b.car.brand) + " " + str(b.car.model) if b.car else "—",
            "amount": str(b.total_price),
            "status": b.status,
            "statusL": dict(Booking.STATUSES).get(b.status, b.status),
        })
    return JsonResponse({"results": results})


@manager_req
def fines(request):
    from django.db.models import Q, Sum
    qs = Fine.objects.select_related('booking__user','booking__car').order_by('-created_at')
    sf  = request.GET.get('status','')
    q   = request.GET.get('q','')
    if sf: qs = qs.filter(status=sf)
    if q:
        qs = qs.filter(
            Q(number__icontains=q)|
            Q(booking__number__icontains=q)|
            Q(booking__user__first_name__icontains=q)|
            Q(booking__user__last_name__icontains=q)|
            Q(booking__car__brand__icontains=q)
        )
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            f = get_object_or_404(Fine, pk=request.POST.get('fine_pk'))
            f.status = request.POST.get('status', f.status)
            paid_raw = request.POST.get('paid_amount', '').strip()
            f.paid_amount = paid_raw if paid_raw else f.paid_amount
            f.save()
            messages.success(request, f'{f.number} оновлено.')
        elif action == 'add':
            bk = get_object_or_404(Booking, pk=request.POST.get('booking_pk'))
            Fine.objects.create(
                booking=bk,
                fine_type=request.POST.get('fine_type','other'),
                severity=request.POST.get('severity','medium'),
                amount=request.POST.get('amount',0),
                description=request.POST.get('description',''),
                manager=request.user,
            )
            messages.success(request, 'Штраф виставлено.')
        return redirect(request.get_full_path())
    stats = {
        'unpaid_count':  Fine.objects.filter(status='unpaid').count(),
        'unpaid_amount': Fine.objects.filter(status='unpaid').aggregate(t=Sum('amount'))['t'] or 0,
        'paid_amount':   Fine.objects.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0,
        'total':         Fine.objects.count(),
    }
    bookings_for_form = Booking.objects.select_related('user','car').filter(
        status__in=['active','completed','paid']
    ).order_by('-created_at')[:100]
    # Підрахунок по кожному статусу для вкладок
    counts_all = Fine.objects.count()
    fine_statuses_counts = [
        (val, label, Fine.objects.filter(status=val).count())
        for val, label in Fine.STATUSES
    ]
    return render(request, 'manager/fines.html', {
        'fines': qs, 'stats': stats, 'sf': sf,
        'fine_statuses': Fine.STATUSES,
        'fine_statuses_counts': fine_statuses_counts,
        'fine_counts_all': counts_all,
        'fine_types': Fine.TYPES,
        'severities': Fine.SEVERITIES,
        'bookings_for_form': bookings_for_form,
    })

@manager_req
def promos(request):
    from core.models import PromoCode
    from datetime import date as date_cls
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            code = request.POST.get('code','').strip().upper()
            if code:
                try:
                    PromoCode.objects.create(
                        code=code,
                        discount_pct=int(request.POST.get('discount_pct') or 10),
                        is_active=request.POST.get('is_active') == 'on',
                        valid_until=request.POST.get('valid_until') or None,
                        max_uses=int(request.POST.get('max_uses') or 0),
                    )
                    messages.success(request, f'Промокод {code} створено.')
                except Exception as e:
                    messages.error(request, f'Помилка: {e}')
        elif action == 'toggle':
            p = get_object_or_404(PromoCode, pk=request.POST.get('pk'))
            p.is_active = not p.is_active
            p.save()
            messages.success(request, f'{p.code} {"активовано" if p.is_active else "деактивовано"}.')
        elif action == 'delete':
            p = get_object_or_404(PromoCode, pk=request.POST.get('pk'))
            code = p.code; p.delete()
            messages.success(request, f'Промокод {code} видалено.')
        return redirect('manager_promos')
    from datetime import date as date_cls2
    today = date_cls.today()
    sf = request.GET.get('status', '')
    qs = PromoCode.objects.order_by('-created_at')
    if sf == 'active':
        qs = qs.filter(is_active=True)
    elif sf == 'inactive':
        qs = qs.filter(is_active=False)
    elif sf == 'expired':
        qs = [p for p in qs if p.valid_until and p.valid_until < today]
    counts = {
        'all':      PromoCode.objects.count(),
        'active':   PromoCode.objects.filter(is_active=True).count(),
        'inactive': PromoCode.objects.filter(is_active=False).count(),
        'expired':  sum(1 for p in PromoCode.objects.all() if p.valid_until and p.valid_until < today),
    }
    return render(request, 'manager/promos.html', {
        'promos': qs, 'today': today, 'sf': sf, 'counts': counts,
    })


@manager_req
def fine_edit(request, pk=None):
    fine = get_object_or_404(Fine, pk=pk) if pk else None
    if request.method == 'POST':
        bk_pk = request.POST.get('booking_pk') or request.POST.get('booking_id')
        booking = get_object_or_404(Booking, pk=bk_pk)
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
    return redirect('manager_dashboard')

@manager_req
@require_POST
def booking_status_update(request, pk):
    b = get_object_or_404(Booking, pk=pk)
    ns = request.POST.get('status')
    if ns in dict(Booking.STATUSES):
        b.status = ns
        b.save()
    return JsonResponse({'ok': True, 'status': b.status})


@manager_req
def car_photo_upload(request, pk):
    from core.models import CarPhoto
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'POST':
        files = request.FILES.getlist('photos')
        for idx, f in enumerate(files):
            caption = request.POST.get(f'caption_{idx}', '').strip()
            is_main = not car.photos.exists() and idx == 0
            CarPhoto.objects.create(car=car, image=f, caption=caption, is_main=is_main, order=idx)
        messages.success(request, f'Завантажено {len(files)} фото.')
    return redirect('manager_car_edit', pk=pk)


@manager_req
def car_photo_delete(request, photo_pk):
    from core.models import CarPhoto
    photo = get_object_or_404(CarPhoto, pk=photo_pk)
    car_pk = photo.car.pk
    if request.method == 'POST':
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, 'Фото видалено.')
    return redirect('manager_car_edit', pk=car_pk)


@manager_req
def car_photo_set_main(request, photo_pk):
    from core.models import CarPhoto
    photo = get_object_or_404(CarPhoto, pk=photo_pk)
    car_pk = photo.car.pk
    if request.method == 'POST':
        CarPhoto.objects.filter(car=photo.car).update(is_main=False)
        photo.is_main = True
        photo.save()
        messages.success(request, 'Головне фото оновлено.')
    return redirect('manager_car_edit', pk=car_pk)


@manager_req
def client_search_api(request):
    from django.http import JsonResponse
    from django.db.models import Q
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    qs = User.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q) |
        Q(email__icontains=q) | Q(profile__phone__icontains=q)
    ).select_related('profile')[:10]
    results = []
    for u in qs:
        ph = ''
        try: ph = u.profile.phone
        except: pass
        disc = 0
        try: disc = u.profile.discount_pct or 0
        except: pass
        results.append({
            'pk': u.pk,
            'name': u.get_full_name() or u.username,
            'email': u.email,
            'phone': ph,
            'discount': disc,
        })
    return JsonResponse({'results': results})


@login_required
@user_passes_test(is_manager)
def inquiries(request):
    status_filter = request.GET.get('status', '')
    qs = ContactMessage.objects.all()
    if status_filter:
        qs = qs.filter(status=status_filter)
    
    if request.method == 'POST':
        msg_id = request.POST.get('msg_id')
        action = request.POST.get('action')
        try:
            msg = ContactMessage.objects.get(pk=msg_id)
            if action == 'read':
                msg.status = 'read'
            elif action == 'replied':
                msg.status = 'replied'
                msg.reply  = request.POST.get('reply', '').strip()
            elif action == 'delete':
                msg.delete()
                messages.success(request, 'Повідомлення видалено.')
                return redirect('manager_inquiries')
            msg.save()
            messages.success(request, 'Статус оновлено.')
        except ContactMessage.DoesNotExist:
            pass
        return redirect(request.get_full_path())

    counts = {
        'new':     ContactMessage.objects.filter(status='new').count(),
        'read':    ContactMessage.objects.filter(status='read').count(),
        'replied': ContactMessage.objects.filter(status='replied').count(),
        'total':   ContactMessage.objects.count(),
    }
    return render(request, 'manager/inquiries.html', {'messages_list': qs, 'counts': counts, 'status_filter': status_filter})