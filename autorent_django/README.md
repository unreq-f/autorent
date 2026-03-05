# AutoRent Харків — Django Project

## Запуск проєкту

```bash
cd autorent_django
pip install django pillow
python manage.py runserver 8080
```

Відкрий: http://localhost:8080

## Облікові дані

### Адмін (is_superuser=True)
- Логін: `admin`
- Пароль: `Admin2026!`
- Адмін-панель: http://localhost:8080/admin/

### Менеджер-портал (is_staff=True)
- Логін: `manager`
- Пароль: `Manager2026!`
- Менеджер-портал: http://localhost:8080/manager/

### Тестові клієнти
- Логін: `client_kovalenko` / Пароль: `Client2026!`
- Логін: `client_bondarenko` / Пароль: `Client2026!`
- Профіль: http://localhost:8080/profile/

## Структура

```
autorent_django/
├── autorent/          # Налаштування Django
├── core/              # Основний додаток (моделі, views, urls)
│   ├── models.py      # Car, Booking, ClientProfile, Fine, Payment
│   └── views.py       # Всі клієнтські view
├── manager_portal/    # Менеджер-портал
│   └── views.py       # Dashboard, Bookings, Cars, Clients, Payments, Fines, Reports
├── templates/
│   ├── base.html      # Базовий шаблон (nav + footer)
│   ├── core/          # Сторінки клієнта (10 сторінок)
│   ├── manager/       # Менеджер-портал (7 сторінок)
│   └── registration/  # auth.html (вхід + реєстрація)
├── static/
│   ├── css/main.css   # CSS клієнтського сайту
│   └── css/manager.css # CSS менеджер-порталу
├── media/             # Завантажені файли (фото авто)
└── db.sqlite3         # База даних SQLite
```

## Сторінки клієнта
- `/` — Головна
- `/catalog/` — Каталог авто (з фільтрами)
- `/cars/<id>/` — Деталі авто
- `/conditions/` — Умови прокату
- `/about/` — Про нас
- `/contacts/` — Контакти (з формою)
- `/booking/` — Швидке бронювання
- `/order/` — Оформлення замовлення
- `/profile/` — Особистий кабінет
- `/auth/` — Вхід / Реєстрація

## Менеджер-портал
- `/manager/` — Дашборд
- `/manager/bookings/` — Замовлення
- `/manager/cars/` — Автопарк
- `/manager/clients/` — Клієнти
- `/manager/payments/` — Платежі
- `/manager/fines/` — Штрафи
- `/manager/reports/` — Звіти
- `/manager/promos/` — Промокоди
- `/manager/inquiries/` — Запити