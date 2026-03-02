#!/bin/bash
echo "AutoRent Django Server"
echo "Сайт: http://localhost:8080"
echo "Менеджер: http://localhost:8080/manager/"
echo "Адмін: http://localhost:8080/admin/"
echo "---"
echo "admin/admin123 | test/test123"
echo ""
python manage.py runserver 8080
